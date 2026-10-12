"""011组装、事务保存及只读结果；009/010仍是唯一执行/校验边界。"""
import json
from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select
from app.domain.execution import Plan, ItemSpec
from app.domain.evaluation import derived
from app.models.imports import DialogueUpload, CaseRecord, MaterialVersion, RuleRow, KnowledgeRow
from app.models.execution import Task, OrdinaryTask, ExecutionItem, Attempt, ConfigSnapshot
from app.models.evaluation import EvaluationResult, Gap, FinalError
from app.prompts.evaluation import prompt_config
from app.services.execution import dump
from app.services.imports import ServiceError


def request_for(history,target_reply,rules,knowledge,config):
    data={'history':history,'target_reply':target_reply,'business_rules':rules,'knowledge_base':knowledge,
        'rubric':config.full_prompt,'schema_version':config.contract_version}
    return {'messages':[{'role':'system','content':config.full_prompt},{'role':'user','content':dump(data)}],
        'history':history,'target_reply':target_reply}


class EvaluationBuilder:
    def __init__(self,database,qa_config):
        if qa_config is None or qa_config.stage!='standard_question' or not qa_config.full_prompt.strip():
            raise ServiceError(409,'DEPENDENCY_NOT_READY','普通任务须由后续模块提供真实冻结Q配置，不使用占位Prompt')
        self.database,self.qa_config=database,qa_config

    def __call__(self,body):
        get=lambda name:str(body[name] if isinstance(body,dict) else getattr(body,name))
        upload_id,rule_id,kb_id=(get(name) for name in ('upload_id','rule_version_id','kb_version_id'))
        cfg=prompt_config()
        with self.database.session() as session:
            if session.get(DialogueUpload,upload_id) is None:
                raise ServiceError(404,'NOT_FOUND','对话来源不存在')
            for identifier,kind in ((rule_id,'rule'),(kb_id,'kb')):
                record=session.get(MaterialVersion,identifier)
                if record is None or record.kind!=kind:
                    raise ServiceError(422,'VERSION_INVALID','资料版本不存在或类型不符')
            def rows(model,identifier):
                return [{'source_id':row.source_id,'title':row.title,'content':row.content} for row in session.scalars(select(model).where(model.version_id==identifier).order_by(model.row_ordinal))]
            rules,knowledge=rows(RuleRow,rule_id),rows(KnowledgeRow,kb_id)
            cases=list(session.scalars(select(CaseRecord).where(CaseRecord.upload_id==upload_id).order_by(CaseRecord.row_ordinal)))
            if not cases or len(cases)>100 or not rules or not knowledge:
                raise ServiceError(422,'SOURCE_INVALID','须有1～100条来源case及完整非空资料')
            items=[ItemSpec(case.id,'evaluation','original','',request_for(case.history,case.original_reply,rules,knowledge,cfg)) for case in cases]
            return Plan('ordinary',upload_id,rule_id,kb_id,[case.id for case in cases],[cfg,self.qa_config],items)


def _final_error(session,item):
    if item.stage!='evaluation' or item.state!='final_failed': return
    if session.get(EvaluationResult,item.id): raise ValueError('成功和最终异常不能同时存在')
    if session.get(FinalError,item.id): return
    last=session.scalar(select(Attempt).where(Attempt.item_id==item.id).order_by(Attempt.ordinal.desc()))
    session.add(FinalError(item_id=item.id,category=item.error_category,last_attempt_id=last.id if last else None))


class EvaluationHooks:
    def __init__(self,next_hooks):
        if next_hooks is None:
            raise ServiceError(409,'DEPENDENCY_NOT_READY','完整普通任务须接入真实后续阶段，不提前释放窗口')
        self.next_hooks=next_hooks

    def item_saved(self,session,task,item,outcome):
        if item.stage!='evaluation': return self.next_hooks.item_saved(session,task,item,outcome)
        if outcome.success:
            if session.get(FinalError,item.id): raise ValueError('最终异常不能再写成功')
            if session.get(EvaluationResult,item.id): return []
            value=outcome.payload['contract']; scores=value['scores']
            session.add(EvaluationResult(item_id=item.id,contract_json=dump(value),accuracy=scores['accuracy']['score'],
                intent=scores['intent']['score'],service=scores['service']['score'],
                accuracy_reason=scores['accuracy']['reason'],intent_reason=scores['intent']['reason'],service_reason=scores['service']['reason'],
                primary_cause=value['primary_cause'],secondary_json=dump(value['secondary_causes']),has_material_conflict=int(value['has_material_conflict'])))
            session.flush()
            locations=outcome.payload['evidence_locations']
            if len(locations)!=len(value['knowledge_gaps']): raise ValueError('010完整证据与定位不匹配')
            for ordinal,(gap,location) in enumerate(zip(value['knowledge_gaps'],locations),1):
                session.add(Gap(id=str(uuid5(NAMESPACE_URL,f'{item.id}:gap:{ordinal}')),result_item_id=item.id,
                    gap_ordinal=ordinal,gap_text=gap['gap'],snippet=gap['snippet'],reason=gap['reason'],location_json=dump(location)))
        else: _final_error(session,item)
        return []

    def phase_finished(self,session,task):
        # B03和重启耗尽由009产生；在其终态事务内补足最终异常，不伪造调用。
        for item in session.scalars(select(ExecutionItem).where(ExecutionItem.task_id==task.id,ExecutionItem.stage=='evaluation')):
            _final_error(session,item)
        session.flush()
        return self.next_hooks.phase_finished(session,task)

    def cancelled(self,session,task):
        if hasattr(self.next_hooks,'cancelled'): self.next_hooks.cancelled(session,task)
        # 已有009删除execution_item，数据库级联删除结果、gap及final_error。


def results(database,task_id):
    with database.session() as session:
        task=session.get(Task,task_id)
        if task is None: raise ServiceError(404,'NOT_FOUND','任务不存在')
        if task.state=='cancelled': return {'cancelled':True,'results':[],'final_errors':[]}
        items=list(session.scalars(select(ExecutionItem).where(ExecutionItem.task_id==task_id,ExecutionItem.stage=='evaluation').order_by(ExecutionItem.id)))
        output,errors=[],[]
        ordinary=session.get(OrdinaryTask,task_id)
        for item in items:
            error=session.get(FinalError,item.id)
            if error:
                errors.append({'case_id':item.case_id,'item_id':item.id,'side':item.side,'category':error.category,
                    'attempt_count':item.attempt_count,'detail':item.error_detail,'last_attempt_id':error.last_attempt_id})
                continue
            saved=session.get(EvaluationResult,item.id)
            if saved is None: continue
            cfg=session.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id==task_id,ConfigSnapshot.stage=='evaluation'))
            attempt=session.get(Attempt,item.result_id)
            gaps=list(session.scalars(select(Gap).where(Gap.result_item_id==item.id).order_by(Gap.gap_ordinal)))
            value=json.loads(saved.contract_json)
            trace={'config_id':cfg.id,'contract_version':cfg.contract_version,'prompt_version':cfg.prompt_version,'full_prompt':cfg.full_prompt,
                'request_model':cfg.request_model,'documented_release':cfg.documented_release,'parameters':json.loads(cfg.parameters_json),
                'attempt_id':attempt.id,'request':json.loads(attempt.request_json),'response':json.loads(attempt.response_envelope_json)}
            if ordinary: trace.update(upload_id=ordinary.upload_id,rule_version_id=ordinary.rule_version_id,kb_version_id=ordinary.kb_version_id)
            output.append({'case_id':item.case_id,'item_id':item.id,'side':item.side,'contract':value,**derived(value,task.kind),
                'attempt_count':item.attempt_count,'knowledge_gaps':[{'id':gap.id,'ordinal':gap.gap_ordinal,'gap':gap.gap_text,'snippet':gap.snippet,
                    'reason':gap.reason,'location':json.loads(gap.location_json)} for gap in gaps],'trace':trace})
        return {'cancelled':False,'results':output,'final_errors':errors}
