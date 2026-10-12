"""补充关联的真实SQLite规则验证，不调用模型。"""
from uuid import uuid4
import pytest
from app.services.supplements import SupplementService
from app.services.qa_review import QAReviewService
from test_task_execution import service
from test_qa_review_integration import drafts, ready, selection
from app.services.imports import ServiceError, ImportService
from test_csv_import import encode


def seed(service, count=2):
    task, rows = drafts(service, count)
    review = QAReviewService(service.database)
    approved = [ready(review, row['id']) for row in rows]
    event, _ = selection(review, approved)
    items = review.detail(event['id'])['items']
    return task, approved, items, review


def test_selected_snapshots_deduplicate_cases(service):
    task, rows, items, review = seed(service)
    supplements = SupplementService(service.database)
    result, created = supplements.save(service.test_sources[2], task['id'], [x['id'] for x in items], True, str(uuid4()))
    assert created
    detail = supplements.detail(result['id'])
    assert len(detail['snapshots']) == 2
    assert len(detail['source_case_ids']) == 1
    assert detail['old_kb_id'] == service.test_sources[2]


def new_kb(service, title='新库'):
    return ImportService(service.database).save('knowledge', encode('knowledge', [['new', title, '本人补充内容']]), 'new.csv', str(uuid4()))[0]['id']


def test_A_snapshot_survives_edit_B_and_both_versions_can_be_selected(service):
    task, rows, items, review = seed(service, 1)
    A = items[0]
    changed, _ = review.edit(rows[0]['id'], '修改问', '修改答', rows[0]['revision'], str(uuid4()))
    svc = SupplementService(service.database)
    first, _ = svc.save(new_kb(service), task['id'], [A['id']], True, str(uuid4()))
    assert svc.detail(first['id'])['snapshots'][0]['answer'] == '人工答案'
    approved = review.approve(changed['id'], changed['revision'], True, str(uuid4()))[0]
    B, _ = selection(review, [approved])
    Bitem = review.detail(B['id'])['items'][0]
    both, _ = svc.save(new_kb(service), task['id'], [A['id'], Bitem['id'], A['id']], True, str(uuid4()))
    detail = svc.detail(both['id'])
    assert {x['answer'] for x in detail['snapshots']} == {'人工答案', '修改答'}
    assert len(detail['source_case_ids']) == 1
    assert len(detail['snapshots']) == 2


def test_multiple_versions_and_same_version_independent_records_with_original_materials(service):
    task, rows, items, _ = seed(service, 1)
    svc = SupplementService(service.database)
    kb1, kb2 = new_kb(service, '一'), new_kb(service, '二')
    records = [svc.save(kb, task['id'], [items[0]['id']], True, str(uuid4()))[0] for kb in (kb1, kb1, kb2)]
    assert len({x['id'] for x in records}) == 3
    assert len(svc.listing(new_kb_id=kb1, source_batch_id=task['id'])) == 2
    for row in records:
        data = svc.validation_input(row['id'])
        assert data['materials']['old_kb_id']['id'] == service.test_sources[2]
        assert data['materials']['rule_version_id']['id'] == service.test_sources[1]
        assert data['materials']['new_kb_id']['id'] == row['new_kb_id']
        assert data['snapshots'][0]['qa_id'] == rows[0]['id']
        assert data['cases'][0]['question'] == '问题0'


@pytest.mark.parametrize('mode,code', [('confirm','CONFIRM_REQUIRED'), ('empty','NO_VALIDATION_CASES'),
    ('qa','SNAPSHOT_NOT_FOUND'), ('unknown','SNAPSHOT_NOT_FOUND'), ('rule','KB_VERSION_INVALID'),
    ('missing_kb','KB_VERSION_INVALID'), ('missing_batch','SOURCE_BATCH_INVALID'), ('cross','CROSS_BATCH_SOURCE')])
def test_invalid_selection_never_commits_or_creates_task(service, mode, code):
    from sqlalchemy import select, func
    from app.models.execution import Task
    from app.models.supplements import Supplement
    task, rows, items, _ = seed(service, 1)
    kb, batch, chosen, confirm = service.test_sources[2], task['id'], [items[0]['id']], True
    if mode == 'confirm': confirm = False
    if mode == 'empty': chosen = []
    if mode == 'qa': chosen = [drafts(service, 1)[1][0]['id']]
    if mode == 'unknown': chosen = [str(uuid4())]
    if mode == 'rule': kb = service.test_sources[1]
    if mode == 'missing_kb': kb = str(uuid4())
    if mode == 'missing_batch': batch = str(uuid4())
    if mode == 'cross': batch = seed(service, 1)[0]['id']
    with service.database.session() as session:
        before = session.scalar(select(func.count()).select_from(Task))
    with pytest.raises(ServiceError) as error:
        SupplementService(service.database).save(kb, batch, chosen, confirm, str(uuid4()))
    assert error.value.code == code
    with service.database.session() as session:
        assert session.scalar(select(func.count()).select_from(Task)) == before
        assert session.scalar(select(func.count()).select_from(Supplement)) == 0


def test_mixed_export_rejected_even_when_export_event_itself_allows_multiple_batches(service):
    first, a = drafts(service, 1)
    second, b = drafts(service, 1)
    review = QAReviewService(service.database)
    event, _ = selection(review, [ready(review, x['id']) for x in (a[0], b[0])])
    items = review.detail(event['id'])['items']
    with pytest.raises(ServiceError) as error:
        SupplementService(service.database).save(new_kb(service), first['id'], [x['id'] for x in items], True, str(uuid4()))
    assert error.value.code == 'CROSS_BATCH_SOURCE'


def test_only_selected_case_not_other_historical_badcases(service):
    from test_qa_generation_integration import start, gap_value, qsave
    from test_evaluation import save_value
    from app.models.imports import CaseRecord
    task, plan = start(service, size=3)
    by_id = {x['id']: x['case_id'] for x in service.get(task['id'])['items']}
    for item in service.pending():
        with service.database.session() as session:
            question = session.get(CaseRecord, by_id[item['id']]).question
        save_value(service, item, gap_value(question=question))
    for item in service.pending(): qsave(service, item)
    from app.services.qa_generation import generations
    review = QAReviewService(service.database)
    rows = generations(service.database, task['id'])['drafts']
    event, _ = selection(review, [ready(review, x['id']) for x in rows])
    items = review.detail(event['id'])['items']
    svc = SupplementService(service.database)
    result, _ = svc.save(new_kb(service), task['id'], [items[1]['id']], True, str(uuid4()))
    assert svc.detail(result['id'])['source_case_ids'] == [items[1]['case_id']]
    all_result, _ = svc.save(new_kb(service), task['id'], [x['id'] for x in reversed(items)], True, str(uuid4()))
    assert svc.detail(all_result['id'])['source_case_ids'] == list(plan.case_ids)


def test_same_operation_replay_conflict_and_concurrent_single_record(service):
    from concurrent.futures import ThreadPoolExecutor
    task, _, items, _ = seed(service)
    svc = SupplementService(service.database)
    op = str(uuid4())
    args = (new_kb(service), task['id'], [x['id'] for x in items], True, op)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: svc.save(*args), range(2)))
    assert sum(x[1] for x in outcomes) == 1
    assert outcomes[0][0] == outcomes[1][0]
    assert svc.save(args[0], args[1], [items[1]['id'], items[0]['id'], items[0]['id']], True, op)[0] == outcomes[0][0]
    with pytest.raises(ServiceError) as error:
        svc.save(args[0], args[1], [items[0]['id']], True, op)
    assert error.value.code == 'OPERATION_CONFLICT'


@pytest.mark.parametrize('flush_number', [1, 2, 3])
def test_each_transaction_stage_failure_rolls_back(service, monkeypatch, flush_number):
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import select, func
    from app.models.supplements import Supplement, SupplementItem
    from app.models.imports import OperationCommit
    task, _, items, _ = seed(service, 1)
    real = Session.flush
    calls = 0
    def fail(session, *args, **kwargs):
        nonlocal calls
        if session.new:
            calls += 1
            if calls == flush_number: raise OperationalError('injected', {}, Exception('disk'))
        return real(session, *args, **kwargs)
    monkeypatch.setattr(Session, 'flush', fail)
    op = str(uuid4())
    with pytest.raises(ServiceError) as error:
        SupplementService(service.database).save(service.test_sources[2], task['id'], [items[0]['id']], True, op)
    assert error.value.commit_state == 'not_committed'
    with service.database.session() as session:
        assert session.scalar(select(func.count()).select_from(Supplement)) == 0
        assert session.scalar(select(func.count()).select_from(SupplementItem)) == 0
        assert session.get(OperationCommit, op) is None


@pytest.mark.parametrize('committed', [True, False])
def test_commit_unknown_read_operation_before_replay(service, monkeypatch, committed):
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import OperationalError
    task, _, items, _ = seed(service, 1)
    svc = SupplementService(service.database)
    op = str(uuid4())
    args = (service.test_sources[2], task['id'], [items[0]['id']], True, op)
    real = Session.commit
    def fail(session):
        if committed: real(session)
        raise OperationalError('injected', {}, Exception('commit acknowledgement'))
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'commit', fail)
        with pytest.raises(ServiceError) as error: svc.save(*args)
        assert error.value.code == 'COMMIT_UNKNOWN' and error.value.resource_id == op
    imports = ImportService(service.database)
    if committed:
        original = imports.operation(op)['result_id']
        assert svc.save(*args)[0]['id'] == original
    else:
        with pytest.raises(ServiceError): imports.operation(op)
        assert svc.save(*args)[1]


def test_migration_preserves_export_bytes_and_old_qa(service):
    from pathlib import Path
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text
    task, rows, items, review = seed(service, 1)
    before = review.detail(items[0]['event_id'])
    raw = review.file(items[0]['event_id'])[0]
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'migrations'))
    with service.database.engine.begin() as conn:
        config.attributes['connection'] = conn
        command.downgrade(config, '0006_qa_exports')
        command.upgrade(config, 'head')
        assert conn.execute(text('PRAGMA foreign_key_check')).fetchall() == []
    assert review.detail(items[0]['event_id']) == before
    assert review.file(items[0]['event_id'])[0] == raw


def test_cancelled_original_source_is_rejected(service):
    from app.models.execution import Task
    task, _, items, _ = seed(service, 1)
    with service.database.session() as session:
        session.get(Task, task['id']).state = 'cancelled'
        session.commit()
    with pytest.raises(ServiceError) as error:
        SupplementService(service.database).save(new_kb(service), task['id'], [items[0]['id']], True, str(uuid4()))
    assert error.value.code == 'SOURCE_BATCH_INVALID'


def test_empty_historical_association_read_reports_no_cases_without_creating_task(service):
    from sqlalchemy import delete, select, func
    from app.models.supplements import SupplementItem
    from app.models.execution import Task
    task, _, items, _ = seed(service, 1)
    svc = SupplementService(service.database)
    record, _ = svc.save(new_kb(service), task['id'], [items[0]['id']], True, str(uuid4()))
    # 故障注入覆盖无来源读取；正常确认入口已拒绝空选择。
    with service.database.session() as session:
        before = session.scalar(select(func.count()).select_from(Task))
        session.execute(delete(SupplementItem).where(SupplementItem.supplement_id == record['id']))
        session.commit()
    detail = svc.validation_input(record['id'])
    assert not detail['can_validate'] and detail['message'] == '无可验证案例'
    assert detail['source_case_ids'] == []
    with service.database.session() as session:
        assert session.scalar(select(func.count()).select_from(Task)) == before
