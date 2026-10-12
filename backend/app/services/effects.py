"""016来源绑定、G→E原子交接和只读对比；009/010保持唯一执行边界。"""
import json
from sqlalchemy import select, delete
from app.domain.execution import ItemSpec, Transition
from app.domain.effects import EffectPlan, comparison, side_metrics
from app.domain.evaluation import derived
from app.models.effects import EffectTask, GenerationResult
from app.models.execution import Task, TaskCase, OrdinaryTask, ExecutionItem, Attempt, ConfigSnapshot
from app.models.imports import CaseRecord, RuleRow, KnowledgeRow
from app.models.supplements import Supplement, SupplementItem
from app.models.exports import ExportItem
from app.models.evaluation import EvaluationResult
from app.prompts.customer_reply import prompt_config as generation_config
from app.prompts.evaluation import prompt_config as evaluation_config
from app.services.evaluation import EvaluationHooks, request_for
from app.services.supplements import SupplementService
from app.services.imports import ServiceError
from app.services.execution import dump


def material_rows(session, model, identifier):
    return [{'source_id': row.source_id, 'title': row.title, 'content': row.content}
        for row in session.scalars(select(model).where(model.version_id == identifier).order_by(model.row_ordinal))]


def generation_request(history, rules, knowledge, config):
    data = {'history': history, 'business_rules': rules, 'knowledge_base': knowledge,
        'schema_version': config.contract_version}
    return {'messages': [{'role': 'system', 'content': config.full_prompt}, {'role': 'user', 'content': dump(data)}],
        'history': history, 'target_reply': ''}


class EffectBuilder:
    def __init__(self, database):
        self.database = database

    def __call__(self, identifier):
        source = SupplementService(self.database).validation_input(identifier)
        if not source['confirmed'] or not source['can_validate']:
            raise ServiceError(422, 'NO_VALIDATION_CASES', '补充尚未确认或无可验证案例')
        g, e = generation_config(), evaluation_config()
        convert = lambda rows: [{key: row[key] for key in ('source_id', 'title', 'content')} for row in rows]
        rules = convert(source['materials']['rule_version_id']['rows'])
        items = []
        for case in source['cases']:
            for side, version in (('old', 'old_kb_id'), ('new', 'new_kb_id')):
                knowledge = convert(source['materials'][version]['rows'])
                items.append(ItemSpec(case['id'], 'reply_generation', side, '', generation_request(case['history'], rules, knowledge, g)))
        return EffectPlan('effect', source['upload_id'], source['rule_version_id'], source['old_kb_id'],
            source['source_case_ids'], [g, e], items, identifier, source['source_batch_id'], source['new_kb_id'])


class EffectHooks:
    def __init__(self):
        # 复用011结果写入与最终异常补建；完成出口只返回done，永不交给QA hooks。
        self.evaluation = EvaluationHooks(self)

    def started(self, session, task, plan):
        if not isinstance(plan, EffectPlan):
            raise ServiceError(422, 'EFFECT_PLAN_INVALID', '效果任务须从已确认补充记录建立')
        source = session.get(Supplement, plan.supplement_id)
        original = session.get(OrdinaryTask, plan.source_batch_id)
        selected = set(session.scalars(select(ExportItem.case_id).join(SupplementItem,
            SupplementItem.export_item_id == ExportItem.id).where(SupplementItem.supplement_id == plan.supplement_id)))
        if source is None or not source.confirmed_at or original is None or not selected:
            raise ServiceError(422, 'NO_VALIDATION_CASES', '补充尚未确认或无可验证案例')
        if (source.source_batch_id != plan.source_batch_id or source.new_kb_id != plan.new_kb_id
            or original.kb_version_id != plan.kb_version_id or original.rule_version_id != plan.rule_version_id
            or original.upload_id != plan.upload_id or set(plan.case_ids) != selected):
            raise ServiceError(409, 'SOURCE_INCONSISTENT', '效果依据必须完全来自本次补充记录')
        expected = {(case_id, side, 'reply_generation') for case_id in plan.case_ids for side in ('old', 'new')}
        if len(plan.items) != len(expected) or {(item.case_id, item.side, item.stage) for item in plan.items} != expected:
            raise ServiceError(422, 'EFFECT_PLAN_INVALID', '每个来源case须独立建立旧新两个生成项')
        if {config.stage for config in plan.configs} != {'reply_generation', 'evaluation'}:
            raise ServiceError(422, 'EFFECT_PLAN_INVALID', '效果仅冻结G/E配置，不允许QA阶段')
        session.add(EffectTask(task_id=task.id, supplement_id=source.id, source_batch_id=source.source_batch_id,
            old_kb_id=original.kb_version_id, new_kb_id=source.new_kb_id, rule_version_id=original.rule_version_id))
        session.flush()

    def item_saved(self, session, task, item, outcome):
        if item.stage == 'evaluation':
            return self.evaluation.item_saved(session, task, item, outcome)
        if item.stage != 'reply_generation':
            raise ValueError('效果任务禁止QA及其他阶段')
        if not outcome.success:
            return []
        if session.get(GenerationResult, item.id):
            return []
        reply = outcome.payload['contract']['reply']
        session.add(GenerationResult(item_id=item.id, reply=reply))
        session.flush()
        source = session.get(EffectTask, task.id)
        cfg = session.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id == task.id, ConfigSnapshot.stage == 'evaluation'))
        case = session.get(CaseRecord, item.case_id)
        rules = material_rows(session, RuleRow, source.rule_version_id)
        knowledge = material_rows(session, KnowledgeRow, source.old_kb_id if item.side == 'old' else source.new_kb_id)
        return [ItemSpec(item.case_id, 'evaluation', item.side, '', request_for(case.history, reply, rules, knowledge, cfg))]

    def phase_finished(self, session, task):
        # EvaluationHooks回到此方法时，全部E最终异常已补建。避免递归只调用补建函数。
        from app.services.evaluation import _final_error
        for item in session.scalars(select(ExecutionItem).where(ExecutionItem.task_id == task.id, ExecutionItem.stage == 'evaluation')):
            _final_error(session, item)
        session.flush()
        from app.services.sampling import create_run
        create_run(session, task.id, detail_in_session(session, task.id)['cases'])
        return Transition('done', [])

    def cancelled(self, session, task):
        session.execute(delete(EffectTask).where(EffectTask.task_id == task.id))
        # G/E及证据随009清理execution_item级联删除；不修改原补充记录。


class TaskHooks:
    """按已有task.kind分发业务钩子，共用一个009服务和执行器。"""
    def __init__(self, ordinary):
        self.ordinary, self.effect = ordinary, EffectHooks()

    def started(self, session, task, plan):
        if task.kind == 'effect': self.effect.started(session, task, plan)

    def item_saved(self, session, task, item, outcome):
        return (self.effect if task.kind == 'effect' else self.ordinary).item_saved(session, task, item, outcome)

    def phase_finished(self, session, task):
        return (self.effect if task.kind == 'effect' else self.ordinary).phase_finished(session, task)

    def cancelled(self, session, task):
        return (self.effect if task.kind == 'effect' else self.ordinary).cancelled(session, task)


def stage_view(session, task_id, case_id, side, stage):
    item = session.scalar(select(ExecutionItem).where(ExecutionItem.task_id == task_id,
        ExecutionItem.case_id == case_id, ExecutionItem.side == side, ExecutionItem.stage == stage))
    if item is None:
        return {'state': 'upstream_generation_failed' if stage == 'evaluation' else 'missing', 'attempt_count': 0}
    value = {'item_id': item.id, 'state': item.state, 'attempt_count': item.attempt_count,
        'error_category': item.error_category, 'error_detail': item.error_detail}
    cfg = session.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id == task_id, ConfigSnapshot.stage == stage))
    attempts = list(session.scalars(select(Attempt).where(Attempt.item_id == item.id).order_by(Attempt.ordinal)))
    latest = session.get(Attempt, item.result_id) if item.result_id else (attempts[-1] if attempts else None)
    config = None if cfg is None else {key: getattr(cfg, key) for key in
        ('id', 'stage', 'contract_version', 'prompt_version', 'full_prompt', 'request_model', 'documented_release')}
    if config is not None: config['parameters'] = json.loads(cfg.parameters_json)
    value['trace'] = {'config': config, 'request': json.loads(item.request_json),
        'response': json.loads(latest.response_envelope_json) if latest and latest.response_envelope_json else None,
        'attempts': [{'id': attempt.id, 'ordinal': attempt.ordinal, 'state': attempt.state,
            'started_at': attempt.started_at, 'ended_at': attempt.ended_at, 'error_category': attempt.error_category,
            'error_detail': attempt.error_detail, 'request': json.loads(attempt.request_json),
            'response': json.loads(attempt.response_envelope_json) if attempt.response_envelope_json else None} for attempt in attempts]}
    if item.state == 'succeeded':
        if stage == 'reply_generation':
            result = session.get(GenerationResult, item.id)
            if result is None: value['state'] = 'trace_incomplete'
            else: value['reply'] = result.reply
        else:
            result = session.get(EvaluationResult, item.id)
            if result is None: value['state'] = 'trace_incomplete'
            else:
                value['contract'] = json.loads(result.contract_json)
                value.update(derived(value['contract'], 'effect'))
                from app.models.evaluation import Gap
                value['knowledge_gaps'] = [{'id': gap.id, 'gap': gap.gap_text, 'snippet': gap.snippet,
                    'reason': gap.reason, 'location': json.loads(gap.location_json)} for gap in session.scalars(
                        select(Gap).where(Gap.result_item_id == item.id).order_by(Gap.gap_ordinal))]
        if config is None or value['trace']['response'] is None:
            value['state'] = 'trace_incomplete'
    return value


def detail(database, task_id):
    with database.session() as session:
        return detail_in_session(session, task_id)


def detail_in_session(session, task_id):
        task = session.get(Task, task_id)
        if task is None or task.kind != 'effect': raise ServiceError(404, 'NOT_FOUND', '效果任务不存在')
        if task.state == 'cancelled': return {'task_id': task_id, 'state': 'cancelled', 'source': None, 'cases': [], 'metrics': {'status': 'cancelled', 'data': None}}
        source = session.get(EffectTask, task_id)
        if source is None: raise ServiceError(409, 'RESULT_INCONSISTENT', '效果任务缺固定来源')
        cases = []
        for entry in session.scalars(select(TaskCase).where(TaskCase.task_id == task_id).order_by(TaskCase.ordinal)):
            original = session.get(CaseRecord, entry.case_id)
            row = {'case_id': entry.case_id, 'case_number': original.csv_case_id, 'question': original.question, 'history': original.history}
            for side in ('old', 'new'):
                row[side] = {name: stage_view(session, task_id, entry.case_id, side, stage)
                    for name, stage in (('generation', 'reply_generation'), ('evaluation', 'evaluation'))}
                if row[side]['generation']['state'] in ('pending', 'running') and row[side]['evaluation']['state'] == 'upstream_generation_failed':
                    row[side]['evaluation']['state'] = 'waiting_for_generation'
            row['comparison'] = comparison(row['old'], row['new'])
            cases.append(row)
        metrics = {'status': 'pending', 'data': None}
        if task.state == 'completed':
            metrics = {'status': 'available', 'data': {side: side_metrics(cases, side) for side in ('old', 'new')}} if cases else {'status': 'unavailable', 'data': None}
        return {'task_id': task_id, 'state': task.state, 'source': {key: getattr(source, key) for key in
            ('supplement_id', 'source_batch_id', 'old_kb_id', 'new_kb_id', 'rule_version_id')},
            'cases': cases, 'metrics': metrics, 'human_effect_conclusion': sampling_conclusion(session, task_id)}


def sampling_conclusion(session, task_id):
    from app.models.sampling import SamplingRun
    run = session.get(SamplingRun, task_id)
    return run.status if run else None
