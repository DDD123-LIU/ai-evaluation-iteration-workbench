"""016多case真实SQLite/统一执行器并发、保存故障和精确指标。"""
import asyncio
import json
from uuid import uuid4
import pytest
from sqlalchemy import select, delete, func
from app.models.execution import ExecutionItem, Task, RuntimeSlot, Attempt
from app.models.imports import CaseRecord
from app.models.supplements import Supplement
from app.models.effects import EffectTask, GenerationResult
from app.services.effects import EffectBuilder, EffectHooks, detail
from app.services.supplements import SupplementService
from app.services.qa_review import QAReviewService
from app.services.qa_generation import generations
from app.domain.model_contract import check_envelope
from app.domain.execution import Outcome
from app.runtime.executor import Executor
from test_task_execution import service, until
from test_supplements import new_kb
from test_qa_review_integration import ready, selection
from test_qa_generation_integration import start, gap_value, qsave
from test_evaluation import save_value
from test_model_contract import envelope, evaluation
from test_effects import send, complete, setup_effect


def multi_source(service, size=3, chosen=None):
    original, plan = start(service, size)
    lookup = {item['id']: item['case_id'] for item in service.get(original['id'])['items']}
    for item in service.pending():
        with service.database.session() as session: question = session.get(CaseRecord, lookup[item['id']]).question
        save_value(service, item, gap_value(question))
    for item in service.pending(): qsave(service, item)
    review = QAReviewService(service.database)
    approved = [ready(review, row['id']) for row in generations(service.database, original['id'])['drafts']]
    event, _ = selection(review, approved)
    snapshots = review.detail(event['id'])['items']
    selected = snapshots if chosen is None else [snapshots[i] for i in chosen]
    record, _ = SupplementService(service.database).save(new_kb(service), original['id'], [x['id'] for x in selected], True, str(uuid4()))
    service.hooks = EffectHooks()
    effect_plan = EffectBuilder(service.database)(record['id'])
    return service.start(effect_plan, str(uuid4())), record, selected


def test_exact_multi_case_sources_both_side_partial_failure_and_metrics(service):
    task, _, chosen = multi_source(service)
    case_ids = detail(service.database, task['id'])['cases']
    target = case_ids[1]['case_id']
    for item in service.pending():
        with service.database.session() as session: row = session.get(ExecutionItem, item['id']); fail = row.case_id == target and row.side == 'old'
        if fail:
            for _ in range(3):
                prepared = service.prepare(item['id'], str(uuid4()))
                service.save(prepared, Outcome(False, error_category='CALL_ERROR', error_detail='生成错误'))
        else: send(service, item)
    complete(service)
    data = detail(service.database, task['id'])
    assert {row['case_id'] for row in data['cases']} == {row['case_id'] for row in chosen}
    assert data['metrics']['data']['old']['counts']['succeeded'] == 2
    assert data['metrics']['data']['old']['counts']['final_errors'] == 1
    assert data['metrics']['data']['old']['display']['error_rate'] == '33.33%'
    assert data['metrics']['data']['new']['counts']['succeeded'] == 3
    assert sum(row['comparison']['comparable'] for row in data['cases']) == 2


def test_only_chosen_two_cases_not_all_three(service):
    task, _, chosen = multi_source(service, chosen=[0, 2])
    assert len(task['items']) == 4
    complete(service)
    assert {row['case_id'] for row in detail(service.database, task['id'])['cases']} == {row['case_id'] for row in chosen}


def test_all_G_failure_no_fake_E_and_no_success_data(service):
    task, _, _ = multi_source(service)
    for item in service.pending(): service.local_blocked(item['id'], '输入超限，本地未发送，调用次数0')
    data = detail(service.database, task['id'])
    assert data['state'] == 'completed'
    for side in ('old', 'new'):
        assert data['metrics']['data'][side]['display'] == {'pass_rate': None, 'average_score': None, 'error_rate': '100.00%'}
        assert all(row[side]['evaluation']['attempt_count'] == 0 for row in data['cases'])
    with service.database.session() as session: assert session.get(RuntimeSlot, 1).task_id is None


def test_knowledge_gaps_saved_on_both_sides_without_Q_and_no_human_conclusion(service):
    task, _, _ = setup_effect(service)
    for item in service.pending(): send(service, item)
    for item in service.pending(): send(service, item, gap_value())
    data = detail(service.database, task['id'])
    assert data['cases'][0]['comparison']['comparable']
    for side in ('old', 'new'):
        assert data['cases'][0][side]['evaluation']['knowledge_gaps'][0]['snippet'] == '问题0'
        assert data['cases'][0][side]['evaluation']['is_badcase']
        assert not data['cases'][0][side]['evaluation']['qa_eligible']
    assert generations(service.database, task['id']) == {'drafts': [], 'failures': [], 'pending': []}
    assert data['human_effect_conclusion'] == 'pending_confirmation'


@pytest.mark.parametrize('committed', [False, True])
def test_start_commit_unknown_uses_original_operation_and_single_slot(service, monkeypatch, committed):
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import OperationalError
    from app.services.imports import ImportService, ServiceError
    task, plan, _ = setup_effect(service)
    complete(service)
    op = str(uuid4())
    # begin事务由SessionTransaction提交，使用engine commit事件在实际提交后模拟确认丢失。
    from sqlalchemy import event
    engine = service.database.engine
    with monkeypatch.context() as patch:
        if committed:
            from sqlalchemy.orm import SessionTransaction
            original = SessionTransaction.commit
            def committed_unknown(transaction, *args, **kwargs):
                root = transaction._parent is None
                original(transaction, *args, **kwargs)
                if root: raise OperationalError('injected', {}, Exception('commit acknowledgment'))
            patch.setattr(SessionTransaction, 'commit', committed_unknown)
        else:
            def reject(connection): raise OperationalError('injected', {}, Exception('disk'))
            event.listen(engine, 'commit', reject)
        try:
            with pytest.raises(OperationalError): service.start(plan, op)
        finally:
            if not committed: event.remove(engine, 'commit', reject)
    imports = ImportService(service.database)
    if committed:
        saved = imports.operation(op)['result_id']
        assert service.start(plan, op)['id'] == saved
    else:
        with pytest.raises(ServiceError): imports.operation(op)
        saved = service.start(plan, op)['id']
    with service.database.session() as session:
        assert session.get(RuntimeSlot, 1).task_id == saved
        assert session.get(EffectTask, saved) is not None


def test_reject_unconfirmed_record_and_tampered_scope_before_start(service):
    from dataclasses import replace
    from app.services.imports import ServiceError
    task, plan, record = setup_effect(service)
    complete(service)
    wrong = replace(plan, case_ids=service.test_sources[3][:2])
    with pytest.raises(ServiceError): service.start(wrong, str(uuid4()))
    with service.database.session() as session:
        session.get(Supplement, record['id']).confirmed_at = ''
        session.commit()
    with pytest.raises(ServiceError) as error: EffectBuilder(service.database)(record['id'])
    assert error.value.code == 'NO_VALIDATION_CASES'


def test_effect_executor_max_three_global_concurrency_and_no_Q(service):
    async def run():
        task, _, _ = multi_source(service, size=3)
        class Transport:
            active = 0
            maximum = 0
            calls = []
            def start_once(self, prepared):
                self.calls.append((prepared['item_id'], prepared['config']['stage']))
                async def answer():
                    self.active += 1
                    self.maximum = max(self.maximum, self.active)
                    try:
                        await asyncio.sleep(.025)
                        value = {'reply': '本侧新生成'} if prepared['config']['stage'] == 'reply_generation' else evaluation()
                        return check_envelope(prepared['config']['stage'], envelope(json.dumps(value)), prepared['request']['history'], prepared['request']['target_reply'])
                    finally: self.active -= 1
                return answer()
        transport = Transport()
        executor = Executor(service, transport, scan_interval=.001, storage_retry=.001)
        await executor.start()
        try:
            await until(lambda: service.get(task['id'])['state'] == 'completed')
        finally: await executor.stop()
        assert transport.maximum == 3
        assert len(transport.calls) == 12 and len({row[0] for row in transport.calls}) == 12
        assert {row[1] for row in transport.calls} == {'reply_generation', 'evaluation'}
        assert detail(service.database, task['id'])['metrics']['data']['new']['counts']['succeeded'] == 3
    asyncio.run(run())
