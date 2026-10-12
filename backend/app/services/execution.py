"""TX02～TX08：每次修改独立事务；发送绝不在事务内等待。"""
import json
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import select, delete

from app.domain.execution import Outcome, Transition
from app.models.execution import Task, RuntimeSlot, TaskCase, OrdinaryTask, ConfigSnapshot, ExecutionItem, Attempt
from app.models.imports import CaseRecord, MaterialVersion, OperationCommit
from app.services.imports import ServiceError


def now():
    return datetime.now(timezone.utc).isoformat()


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class TaskService:
    def __init__(self, database, hooks=None):
        self.database, self.hooks = database, hooks

    def _task(self, session, task_id):
        task = session.get(Task, task_id)
        if task is None:
            raise ServiceError(404, 'NOT_FOUND', '任务不存在')
        return task

    def _operation(self, s, operation_id, kind, content, result_id=None):
        digest = sha256(dump(content).encode('utf-8')).hexdigest()
        previous = s.get(OperationCommit, operation_id)
        if previous:
            if previous.kind != kind or previous.request_hash != digest:
                raise ServiceError(409, 'OPERATION_CONFLICT', '同一操作编号不能用于不同内容')
            return previous.result_id
        if result_id:
            s.add(OperationCommit(operation_id=operation_id, kind=kind, request_hash=digest,
                result_type='task', result_id=result_id, committed_at=now()))
        return None

    def start(self, plan, operation_id):
        content = asdict(plan)
        with self.database.write_lock, self.database.session() as s, s.begin():
            previous = self._operation(s, operation_id, 'task_start', content)
            if previous:
                return self._view(s, self._task(s, previous))
            slot = s.get(RuntimeSlot, 1)
            if slot is None:
                raise RuntimeError('运行窗口缺失，禁止新建任务')
            if slot.task_id:
                raise ServiceError(409, 'TASK_BUSY', '另一个自动任务仍在运行，无排队')
            self._validate_plan(s, plan)
            task = Task(id=str(uuid4()), kind=plan.kind,
                phase='evaluating' if plan.kind == 'ordinary' else 'effect_automatic',
                state='running', revision=0, cancel_epoch=0, started_at=now())
            s.add(task)
            s.flush()
            slot.task_id = task.id
            for ordinal, case_id in enumerate(plan.case_ids, 1):
                s.add(TaskCase(task_id=task.id, case_id=case_id, ordinal=ordinal))
            if plan.kind == 'ordinary':
                s.add(OrdinaryTask(task_id=task.id, upload_id=plan.upload_id,
                    rule_version_id=plan.rule_version_id, kb_version_id=plan.kb_version_id))
            for config in plan.configs:
                s.add(ConfigSnapshot(id=str(uuid4()), task_id=task.id, stage=config.stage,
                    contract_version=config.contract_version, prompt_version=config.prompt_version,
                    full_prompt=config.full_prompt, request_model=config.request_model,
                    documented_release=config.documented_release, parameters_json=dump(config.parameters)))
            s.flush()
            if self.hooks and hasattr(self.hooks, 'started'):
                self.hooks.started(s, task, plan)
            self._add_items(s, task, plan.items)
            self._operation(s, operation_id, 'task_start', content, task.id)
            s.flush()
            return self._view(s, task)

    def _validate_plan(self, s, plan):
        if plan.kind not in ('ordinary', 'effect') or not 1 <= len(plan.case_ids) <= 100 or len(set(plan.case_ids)) != len(plan.case_ids):
            raise ServiceError(422, 'PLAN_INVALID', '任务类型或来源case集合不合法')
        records = list(s.scalars(select(CaseRecord).where(CaseRecord.id.in_(plan.case_ids))))
        if len(records) != len(plan.case_ids) or any(x.upload_id != plan.upload_id for x in records):
            raise ServiceError(422, 'PLAN_INVALID', 'case必须来自固定来源批次')
        for identifier, kind in ((plan.rule_version_id, 'rule'), (plan.kb_version_id, 'kb')):
            version = s.get(MaterialVersion, identifier)
            if version is None or version.kind != kind:
                raise ServiceError(422, 'PLAN_INVALID', '规则或知识版本不存在或类型错误')
        stages = [x.stage for x in plan.configs]
        if len(stages) != len(set(stages)) or any(x not in ('evaluation', 'standard_question', 'reply_generation') for x in stages):
            raise ServiceError(422, 'PLAN_INVALID', '配置阶段无效或重复')
        if not plan.items or (plan.kind == 'ordinary' and 'standard_question' not in stages):
            raise ServiceError(422, 'PLAN_INVALID', '任务为空或未冻结QA配置')
        required = {'evaluation', 'standard_question'} if plan.kind == 'ordinary' else {'evaluation', 'reply_generation'}
        if not required.issubset(stages) or any(x.stage != ('evaluation' if plan.kind == 'ordinary' else 'reply_generation') for x in plan.items):
            raise ServiceError(422, 'PLAN_INVALID', '初始阶段或后续冻结配置不完整')
        for cfg in plan.configs:
            if not all((cfg.contract_version, cfg.prompt_version, cfg.full_prompt, cfg.request_model, cfg.documented_release)):
                raise ServiceError(422, 'PLAN_INVALID', '完整配置必须在启动前冻结')
        for item in plan.items:
            if item.case_id not in plan.case_ids or item.stage not in stages:
                raise ServiceError(422, 'PLAN_INVALID', '调用单元缺少固定case或配置')

    def _add_items(self, s, task, specs):
        for spec in specs:
            if s.get(TaskCase, (task.id, spec.case_id)) is None:
                # 新启动的TaskCase由flush后可读；后续钩子也不得改变来源。
                s.flush()
                if s.get(TaskCase, (task.id, spec.case_id)) is None:
                    raise ValueError('调用单元不属于任务来源')
            config = s.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id == task.id, ConfigSnapshot.stage == spec.stage))
            if config is None or (task.kind == 'ordinary' and spec.side != 'original') or (task.kind == 'effect' and spec.side not in ('old', 'new')):
                raise ValueError('调用单元阶段或侧不合法')
            if (spec.stage == 'standard_question') != bool(spec.gap_key):
                raise ValueError('仅QA单元必须有gap身份')
            s.add(ExecutionItem(id=str(uuid4()), task_id=task.id, case_id=spec.case_id,
                stage=spec.stage, side=spec.side, gap_key=spec.gap_key, state='pending',
                attempt_count=0, request_json=dump(spec.request)))
        s.flush()

    def _view(self, s, task):
        items = list(s.scalars(select(ExecutionItem).where(ExecutionItem.task_id == task.id).order_by(ExecutionItem.id)))
        return {'id': task.id, 'kind': task.kind, 'phase': task.phase, 'state': task.state,
            'revision': task.revision, 'cancel_epoch': task.cancel_epoch, 'started_at': task.started_at,
            'automatic_ended_at': task.automatic_ended_at, 'elapsed_ms': task.elapsed_ms,
            'progress': {'total': len(items), **{state: sum(x.state == state for x in items) for state in ('pending', 'running', 'succeeded', 'final_failed')}},
            'items': [{'id': x.id, 'task_id': x.task_id, 'case_id': x.case_id, 'stage': x.stage, 'side': x.side,
                'gap_key': x.gap_key, 'state': x.state, 'attempt_count': x.attempt_count,
                'result_id': x.result_id, 'error_category': x.error_category, 'error_detail': x.error_detail} for x in items]}

    def get(self, task_id):
        with self.database.session() as s:
            return self._view(s, self._task(s, task_id))

    def list(self):
        with self.database.session() as s:
            return [self._view(s, t) for t in s.scalars(select(Task).order_by(Task.started_at.desc()))]

    def downstream_items(self, task_id):
        with self.database.session() as s:
            task = self._task(s, task_id)
            if task.state == 'cancelled':
                return []
            return [x for x in self._view(s, task)['items'] if x['state'] == 'succeeded']

    def pending(self, ignore_due=False):
        with self.database.session() as s:
            query = select(ExecutionItem).join(Task).where(Task.state == 'running', ExecutionItem.state == 'pending')
            if not ignore_due:
                query = query.where((ExecutionItem.next_attempt_at.is_(None)) | (ExecutionItem.next_attempt_at <= now()))
            return [{'id': x.id, 'task_id': x.task_id} for x in s.scalars(query.order_by(ExecutionItem.id))]

    def prepare(self, item_id, token):
        with self.database.write_lock, self.database.session() as s, s.begin():
            previous = s.get(Attempt, token)
            if previous:
                if previous.item_id != item_id:
                    raise ValueError('attempt身份冲突')
                if previous.state != 'prepared':
                    return None
                return self._prepared(s, previous)
            item = s.get(ExecutionItem, item_id)
            if item is None:
                return None
            task = self._task(s, item.task_id)
            if task.state != 'running' or item.state != 'pending' or item.attempt_count >= 3:
                return None
            cfg = s.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id == task.id, ConfigSnapshot.stage == item.stage))
            item.attempt_count += 1
            item.state, item.next_attempt_at = 'running', None
            task.revision += 1
            attempt = Attempt(id=token, item_id=item.id, ordinal=item.attempt_count, state='prepared',
                request_json=item.request_json, config_id=cfg.id, started_at=now())
            s.add(attempt)
            s.flush()
            return self._prepared(s, attempt)

    def _prepared(self, s, attempt):
        item = s.get(ExecutionItem, attempt.item_id)
        task = self._task(s, item.task_id)
        cfg = s.get(ConfigSnapshot, attempt.config_id)
        return {'id': attempt.id, 'item_id': item.id, 'task_id': task.id, 'epoch': task.cancel_epoch,
            'ordinal': attempt.ordinal, 'request': json.loads(attempt.request_json), 'config': {
                'id': cfg.id, 'stage': cfg.stage, 'contract_version': cfg.contract_version,
                'prompt_version': cfg.prompt_version, 'full_prompt': cfg.full_prompt,
                'request_model': cfg.request_model, 'documented_release': cfg.documented_release,
                'parameters': json.loads(cfg.parameters_json)}}

    def unsent(self, prepared):
        with self.database.write_lock, self.database.session() as s, s.begin():
            attempt = s.get(Attempt, prepared['id'])
            if attempt is None:
                return
            item = s.get(ExecutionItem, attempt.item_id)
            if attempt.state != 'prepared' or item.attempt_count != attempt.ordinal:
                raise ValueError('不能撤销可能已完成的发送')
            item.attempt_count -= 1
            item.state = 'pending'
            item.next_attempt_at = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
            self._task(s, item.task_id).revision += 1
            # 只对当前进程证明未交给transport的预留删除；重启未知请求绝不走此处。
            s.delete(attempt)

    def local_blocked(self, item_id, detail):
        with self.database.write_lock, self.database.session() as s, s.begin():
            item = s.get(ExecutionItem, item_id)
            if item is None or item.state != 'pending':
                return
            task = self._task(s, item.task_id)
            item.state, item.error_category, item.error_detail = 'final_failed', 'CALL_ERROR', detail
            task.revision += 1
            self._advance(s, task)

    def preview(self, item_id):
        """010发送前能力校验所需的冻结输入；不增加请求次数。"""
        with self.database.session() as s:
            item = s.get(ExecutionItem, item_id)
            if item is None:
                return None
            task = self._task(s, item.task_id)
            if task.state != 'running' or item.state != 'pending':
                return None
            cfg = s.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id == task.id, ConfigSnapshot.stage == item.stage))
            return {'item_id': item.id, 'task_id': task.id, 'request': json.loads(item.request_json),
                'config': {'stage': cfg.stage, 'request_model': cfg.request_model, 'parameters': json.loads(cfg.parameters_json),
                    'full_prompt': cfg.full_prompt, 'contract_version': cfg.contract_version,
                    'prompt_version': cfg.prompt_version, 'documented_release': cfg.documented_release}}

    def save(self, prepared, outcome):
        with self.database.write_lock, self.database.session() as s, s.begin():
            task = self._task(s, prepared['task_id'])
            if task.state == 'cancelled' or task.cancel_epoch != prepared['epoch']:
                return False
            if not isinstance(outcome, Outcome) or (not outcome.success and outcome.error_category not in ('CALL_ERROR', 'PARSE_ERROR', 'INCOMPLETE_RESULT')):
                raise ValueError('010必须返回成功或约定异常分类')
            if outcome.retry_after is not None and (outcome.retry_after < 0 or outcome.retry_after == float('inf') or outcome.retry_after != outcome.retry_after):
                raise ValueError('Retry-After必须是有限非负秒数')
            attempt = s.get(Attempt, prepared['id'])
            if attempt is None:
                raise ValueError('尝试记录丢失')
            if attempt.state != 'prepared':
                return True
            item = s.get(ExecutionItem, attempt.item_id)
            attempt.state = 'succeeded' if outcome.success else 'failed'
            attempt.ended_at, attempt.response_envelope_json, attempt.raw_content = now(), dump(asdict(outcome)), outcome.raw
            attempt.error_category, attempt.error_detail = outcome.error_category, outcome.error_detail
            item.error_category, item.error_detail = outcome.error_category, outcome.error_detail
            if outcome.success:
                item.state, item.result_id = 'succeeded', attempt.id
            elif item.attempt_count >= 3:
                item.state = 'final_failed'
            else:
                item.state = 'pending'
                delay = outcome.retry_after if outcome.retry_after is not None else (2 if item.attempt_count == 1 else 5)
                item.next_attempt_at = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat()
            task.revision += 1
            if self.hooks:
                successors = self.hooks.item_saved(s, task, item, outcome)
                if successors and (task.kind != 'effect' or item.stage != 'reply_generation' or not outcome.success
                    or any(x.stage != 'evaluation' or x.case_id != item.case_id or x.side != item.side for x in successors)):
                    raise ValueError('只有成功G可在保存事务创建对应同侧E；Q必须在全E终态交接')
                self._add_items(s, task, successors)
            self._advance(s, task)
            return True

    def _advance(self, s, task):
        s.flush()
        if task.state != 'running' or s.scalar(select(ExecutionItem.id).where(ExecutionItem.task_id == task.id, ExecutionItem.state.in_(('pending', 'running')))):
            return
        transition = self.hooks.phase_finished(s, task) if self.hooks else Transition('done', [])
        if transition.phase == 'qa_generation' and task.kind == 'ordinary' and task.phase == 'evaluating' and transition.items:
            if any(x.stage != 'standard_question' for x in transition.items):
                raise ValueError('QA交接只能创建Q单元')
            self._add_items(s, task, transition.items)
            task.phase = 'qa_generation'
        elif transition.phase == 'done' and not transition.items:
            task.phase, task.state, task.automatic_ended_at = 'done', 'completed', now()
            task.elapsed_ms = int((datetime.fromisoformat(task.automatic_ended_at) - datetime.fromisoformat(task.started_at)).total_seconds() * 1000)
            s.get(RuntimeSlot, 1).task_id = None
        else:
            raise ValueError('业务阶段交接非法')
        task.revision += 1

    def cancel(self, task_id, revision, operation_id):
        content = {'task_id': task_id, 'revision': revision}
        with self.database.write_lock, self.database.session() as s, s.begin():
            previous = self._operation(s, operation_id, 'task_cancel', content)
            task = self._task(s, task_id)
            if previous:
                return self._view(s, task)
            if task.revision != revision:
                raise ServiceError(409, 'REVISION_CONFLICT', '任务已变化，请重新读取后确认取消')
            if task.state != 'running' or task.phase == 'qa_generation':
                raise ServiceError(409, 'CANCEL_FORBIDDEN', '当前阶段不能取消')
            task.state, task.automatic_ended_at = 'cancelled', now()
            task.cancel_epoch += 1
            task.revision += 1
            # 后续业务表须经同一事务清理钩子，不得保存取消任务有效结果。
            if self.hooks and hasattr(self.hooks, 'cancelled'):
                self.hooks.cancelled(s, task)
            for model in (ExecutionItem, ConfigSnapshot, TaskCase, OrdinaryTask):
                s.execute(delete(model).where(model.task_id == task_id))
            s.get(RuntimeSlot, 1).task_id = None
            self._operation(s, operation_id, 'task_cancel', content, task_id)
            s.flush()
            return self._view(s, task)

    def recover(self):
        with self.database.write_lock, self.database.session() as s, s.begin():
            running = list(s.scalars(select(Task).where(Task.state == 'running')))
            slot = s.get(RuntimeSlot, 1)
            if slot is None or len(running) > 1 or slot.task_id != (running[0].id if running else None):
                raise RuntimeError('运行窗口与持久任务不一致，禁止自动重置')
            for task in running:
                for item in s.scalars(select(ExecutionItem).where(ExecutionItem.task_id == task.id)):
                    attempts = list(s.scalars(select(Attempt).where(Attempt.item_id == item.id).order_by(Attempt.ordinal)))
                    if len(attempts) != item.attempt_count or [x.ordinal for x in attempts] != list(range(1, item.attempt_count + 1)):
                        raise RuntimeError('持久计次不一致，禁止重复发送')
                    if item.state == 'succeeded' and (not attempts or attempts[-1].state != 'succeeded' or not attempts[-1].response_envelope_json):
                        raise RuntimeError('成功单元缺少持久响应，禁止伪装成功或重调')
                    if item.state == 'pending' and item.attempt_count >= 3:
                        raise RuntimeError('待执行单元额度已耗尽，禁止静默卡住或增加额度')
                    if item.state == 'running':
                        if not attempts or attempts[-1].state != 'prepared':
                            raise RuntimeError('运行单元缺少预留尝试')
                        last = attempts[-1]
                        last.state, last.ended_at = 'failed', now()
                        last.error_category, last.error_detail = 'CALL_ERROR', '重启前已预留发送但无持久结果；外部处理未知'
                        item.state = 'final_failed' if item.attempt_count >= 3 else 'pending'
                        item.error_category, item.error_detail = last.error_category, last.error_detail
                        item.next_attempt_at = (datetime.now(timezone.utc) + timedelta(seconds=2 if item.attempt_count == 1 else 5)).isoformat()
                        task.revision += 1
                self._advance(s, task)
