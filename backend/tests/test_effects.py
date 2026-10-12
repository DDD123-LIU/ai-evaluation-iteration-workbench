"""016使用实际015来源与SQLite；模型响应仅是确定性输入。"""
from uuid import uuid4
from app.services.effects import EffectBuilder, EffectHooks, detail
from app.services.supplements import SupplementService
from test_task_execution import service
from test_supplements import seed, new_kb
import json
import pytest
from sqlalchemy import select
from app.models.execution import ExecutionItem, Attempt, TaskCase
from app.models.effects import GenerationResult, EffectTask
from app.models.qa import QA
from app.domain.model_contract import check_envelope
from test_model_contract import envelope, evaluation


def send(service, item, value=None, metadata=None):
    prepared = service.prepare(item['id'], str(uuid4()))
    stage = prepared['config']['stage']
    value = value or ({'reply': '本侧重新生成的回复'} if stage == 'reply_generation' else evaluation())
    response = envelope(json.dumps(value, ensure_ascii=False))
    if metadata: response.update(metadata)
    outcome = check_envelope(stage, response, prepared['request']['history'], prepared['request']['target_reply'])
    service.save(prepared, outcome)
    return prepared, outcome


def complete(service):
    while service.pending(ignore_due=True):
        for item in service.pending(ignore_due=True): send(service, item)


def setup_effect(service, count=1):
    original, _, items, _ = seed(service, count)
    record, _ = SupplementService(service.database).save(new_kb(service), original['id'],
        [x['id'] for x in items], True, str(uuid4()))
    service.hooks = EffectHooks()
    plan = EffectBuilder(service.database)(record['id'])
    return service.start(plan, str(uuid4())), plan, record


def test_source_dedup_and_both_sides_begin_with_generation(service):
    task, plan, record = setup_effect(service, 2)
    assert len(plan.case_ids) == 1
    assert {(i['side'], i['stage']) for i in task['items']} == {('old', 'reply_generation'), ('new', 'reply_generation')}
    data = detail(service.database, task['id'])
    assert data['source']['supplement_id'] == record['id']
    assert data['metrics']['status'] == 'pending'


def test_only_kb_differs_history_preserved_and_old_not_uploaded_reply(service):
    task, plan, _ = setup_effect(service)
    before = [json.loads(spec.request['messages'][1]['content']) for spec in plan.items]
    assert before[0]['knowledge_base'] != before[1]['knowledge_base']
    for value in before: value.pop('knowledge_base')
    assert before[0] == before[1]
    for item in service.pending():
        send(service, item, {'reply': '新生成,含"引号"\n后续行'})
    with service.database.session() as session:
        for item in session.scalars(select(ExecutionItem).where(ExecutionItem.task_id == task['id'], ExecutionItem.stage == 'evaluation')):
            request = json.loads(item.request_json)
            assert request['history'] == before[0]['history']
            assert request['target_reply'] == '新生成,含"引号"\n后续行'
            assert json.loads(request['messages'][1]['content'])['history'] == before[0]['history']
    complete(service)
    actual = detail(service.database, task['id'])
    assert actual['state'] == 'completed' and actual['cases'][0]['comparison']['comparable']
    for side in ('old', 'new'):
        row = actual['cases'][0][side]
        assert row['generation']['reply'] == '新生成,含"引号"\n后续行'
        assert row['evaluation']['trace']['request']['target_reply'] == row['generation']['reply']
        assert actual['metrics']['data'][side]['display'] == {'pass_rate': '100.00%', 'average_score': '4.00', 'error_rate': '0.00%'}
    assert actual['human_effect_conclusion'] == 'pending_confirmation'


@pytest.mark.parametrize('stage', ['reply_generation', 'evaluation'])
@pytest.mark.parametrize('success_on', [1, 3, None])
def test_each_stage_budget_and_success_stop(service, stage, success_on):
    from app.domain.execution import Outcome
    task, _, _ = setup_effect(service)
    if stage == 'evaluation':
        for item in service.pending(): send(service, item)
    with service.database.session() as session:
        target = session.scalar(select(ExecutionItem.id).where(ExecutionItem.task_id == task['id'], ExecutionItem.side == 'old', ExecutionItem.stage == stage))
    for ordinal in range(1, (success_on or 3) + 1):
        if ordinal == success_on: send(service, {'id': target})
        else:
            prepared = service.prepare(target, str(uuid4()))
            service.save(prepared, Outcome(False, error_category='PARSE_ERROR', error_detail='测试解析失败'))
    assert service.prepare(target, str(uuid4())) is None
    complete(service)
    data = detail(service.database, task['id'])
    view = data['cases'][0]['old']['generation' if stage == 'reply_generation' else 'evaluation']
    assert view['attempt_count'] == (success_on or 3)
    assert view['state'] == ('succeeded' if success_on else 'final_failed')
    assert view['trace']['config']['prompt_version'] == ('customer-reply-v4' if stage == 'reply_generation' else 'evaluation-v2')
    if stage == 'reply_generation' and success_on is None:
        assert data['cases'][0]['old']['evaluation']['state'] == 'upstream_generation_failed'
        assert data['cases'][0]['old']['evaluation']['attempt_count'] == 0
    assert not data['cases'][0]['old']['evaluation'].get('qa_eligible', False)
    with service.database.session() as session:
        assert session.scalar(select(ExecutionItem.id).where(ExecutionItem.task_id == task['id'], ExecutionItem.stage == 'standard_question')) is None


@pytest.mark.parametrize('field,value', [('model', None), ('model', ''), ('model', ' '), ('model', 7),
    ('model', 'changed'), ('system_fingerprint', None), ('system_fingerprint', False), ('system_fingerprint', 'different')])
@pytest.mark.parametrize('stage', ['reply_generation', 'evaluation'])
def test_trace_metadata_missing_invalid_or_drift_keeps_business_success_without_retry(service, field, value, stage):
    task, _, _ = setup_effect(service)
    while service.pending():
        for item in service.pending():
            with service.database.session() as session:
                row = session.get(ExecutionItem, item['id'])
                changed = row.side == 'new' and row.stage == stage
            send(service, item, metadata={field: value} if changed else None)
    data = detail(service.database, task['id'])
    assert not data['cases'][0]['comparison']['comparable']
    for side in ('old', 'new'):
        assert data['cases'][0][side]['generation']['state'] == 'succeeded'
        assert data['cases'][0][side]['generation']['attempt_count'] == 1
        assert data['metrics']['data'][side]['counts']['succeeded'] == 1


def test_G_E_models_can_differ_but_each_type_must_match_both_sides(service):
    task, _, _ = setup_effect(service)
    while service.pending():
        for item in service.pending():
            stage = service.preview(item['id'])['config']['stage']
            send(service, item, metadata={'model': 'G-model' if stage == 'reply_generation' else 'E-model',
                'system_fingerprint': 'G-fp' if stage == 'reply_generation' else 'E-fp'})
    assert detail(service.database, task['id'])['cases'][0]['comparison']['comparable']


def test_missing_trace_key_is_not_same_as_no_drift(service):
    task, _, _ = setup_effect(service)
    for item in service.pending():
        prepared = service.prepare(item['id'], str(uuid4()))
        response = envelope('{"reply":"已生成正文"}')
        response.pop('model')
        response.pop('system_fingerprint')
        outcome = check_envelope('reply_generation', response, prepared['request']['history'], '')
        assert outcome.success
        service.save(prepared, outcome)
    complete(service)
    assert not detail(service.database, task['id'])['cases'][0]['comparison']['comparable']


def test_recover_unknown_sent_attempt_preserves_success_and_independent_budgets(service):
    task, _, _ = setup_effect(service)
    pending = service.pending()
    success, _ = send(service, pending[0])
    unknown = service.prepare(pending[1]['id'], str(uuid4()))
    service.recover()
    assert service.prepare(success['item_id'], str(uuid4())) is None
    complete(service)
    result = detail(service.database, task['id'])
    counts = [result['cases'][0][side]['generation']['attempt_count'] for side in ('old', 'new')]
    assert sorted(counts) == [1, 2]
    for side in ('old', 'new'): assert result['cases'][0][side]['evaluation']['attempt_count'] == 1


def test_recovery_exhausted_generation_does_not_create_E(service):
    from app.domain.execution import Outcome
    task, _, _ = setup_effect(service)
    identifier = service.pending()[0]['id']
    for _ in range(2):
        prepared = service.prepare(identifier, str(uuid4()))
        service.save(prepared, Outcome(False, error_category='CALL_ERROR', error_detail='调用失败'))
    service.prepare(identifier, str(uuid4()))
    service.recover()
    complete(service)
    data = detail(service.database, task['id'])
    failed_side = next(side for side in ('old', 'new') if data['cases'][0][side]['generation']['state'] == 'final_failed')
    assert data['cases'][0][failed_side]['generation']['attempt_count'] == 3
    assert data['cases'][0][failed_side]['evaluation']['attempt_count'] == 0
    assert data['metrics']['data'][failed_side]['display'] == {'pass_rate': None, 'average_score': None, 'error_rate': '100.00%'}


def test_cancel_clears_effect_results_drops_late_response_preserves_supplement(service):
    task, _, record = setup_effect(service)
    send(service, service.pending()[0])
    late = service.prepare(service.pending()[0]['id'], str(uuid4()))
    current = service.get(task['id'])
    service.cancel(task['id'], current['revision'], str(uuid4()))
    outcome = check_envelope(late['config']['stage'], envelope('{"reply":"迟到回复"}'), late['request']['history'], '')
    assert not service.save(late, outcome)
    actual = detail(service.database, task['id'])
    assert actual['cases'] == [] and actual['metrics']['status'] == 'cancelled'
    assert SupplementService(service.database).detail(record['id'])['can_validate']
    with service.database.session() as session:
        assert session.get(EffectTask, task['id']) is None
        assert not list(session.scalars(select(GenerationResult)))


def test_busy_window_replay_and_same_supplement_new_independent_task(service):
    from app.services.imports import ServiceError
    task, plan, record = setup_effect(service)
    with pytest.raises(ServiceError) as error: service.start(plan, str(uuid4()))
    assert error.value.code == 'TASK_BUSY'
    complete(service)
    op = str(uuid4())
    next_task = service.start(EffectBuilder(service.database)(record['id']), op)
    assert next_task['id'] != task['id']
    assert service.start(EffectBuilder(service.database)(record['id']), op)['id'] == next_task['id']
    assert detail(service.database, task['id'])['state'] == 'completed'


def test_generation_save_and_E_creation_transaction_failure_does_not_repeat_provider(service, monkeypatch):
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import OperationalError
    task, _, _ = setup_effect(service)
    prepared = service.prepare(service.pending()[0]['id'], str(uuid4()))
    outcome = check_envelope('reply_generation', envelope('{"reply":"仅调用一次"}'), prepared['request']['history'], '')
    original = Session.flush
    def fail(session, *args, **kwargs):
        if any(isinstance(value, GenerationResult) for value in session.new):
            raise OperationalError('test', {}, Exception('disk'))
        return original(session, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'flush', fail)
        with pytest.raises(OperationalError): service.save(prepared, outcome)
    with service.database.session() as session:
        assert session.get(GenerationResult, prepared['item_id']) is None
        assert session.get(Attempt, prepared['id']).state == 'prepared'
    assert service.save(prepared, outcome)
    assert service.save(prepared, outcome)
    with service.database.session() as session:
        item = session.get(ExecutionItem, prepared['item_id'])
        evaluations = list(session.scalars(select(ExecutionItem).where(ExecutionItem.task_id == task['id'], ExecutionItem.stage == 'evaluation', ExecutionItem.side == item.side)))
        assert len(evaluations) == 1 and item.attempt_count == 1


def test_no_source_or_unconfirmed_cannot_start_effect(service):
    from app.models.supplements import Supplement, SupplementItem
    from sqlalchemy import delete
    from app.services.imports import ServiceError
    task, _, record = setup_effect(service)
    complete(service)
    with service.database.session() as session:
        session.execute(delete(SupplementItem).where(SupplementItem.supplement_id == record['id']))
        session.commit()
    with pytest.raises(ServiceError) as error: EffectBuilder(service.database)(record['id'])
    assert error.value.code == 'NO_VALIDATION_CASES'
