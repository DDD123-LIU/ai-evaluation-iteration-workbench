"""真实SQLite事务故障及契约边界。"""
import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.domain.execution import Outcome, LocalBlocked, NoSend, ItemSpec, Transition
from app.main import create_app
from app.models.execution import Task, ExecutionItem, Attempt
from app.runtime.executor import Executor
from app.services.execution import TaskService
from app.services.imports import ServiceError
from test_task_execution import service, plan, Transport, until


def fault():
    return OperationalError('injected', {}, Exception('disk'))


def test_prepare_rollback_and_unknown_commit_readback(service):
    task = service.start(plan(service), str(uuid4()))
    item = service.pending()[0]
    token = str(uuid4())
    def before_commit(session):
        raise fault()
    event.listen(Session, 'before_commit', before_commit)
    try:
        with pytest.raises(OperationalError):
            service.prepare(item['id'], token)
    finally:
        event.remove(Session, 'before_commit', before_commit)
    assert service.get(task['id'])['items'][0]['attempt_count'] == 0
    def after_commit(session):
        raise fault()
    event.listen(Session, 'after_commit', after_commit)
    try:
        with pytest.raises(OperationalError):
            service.prepare(item['id'], token)
    finally:
        event.remove(Session, 'after_commit', after_commit)
    assert service.prepare(item['id'], token)['ordinal'] == 1
    assert service.get(task['id'])['items'][0]['attempt_count'] == 1


def test_save_commit_unknown_is_idempotent(service):
    task = service.start(plan(service), str(uuid4()))
    prepared = service.prepare(service.pending()[0]['id'], str(uuid4()))
    def after_commit(session):
        raise fault()
    event.listen(Session, 'after_commit', after_commit)
    try:
        with pytest.raises(OperationalError):
            service.save(prepared, Outcome(True, {'saved': True}))
    finally:
        event.remove(Session, 'after_commit', after_commit)
    assert service.save(prepared, Outcome(True, {'saved': True}))
    assert service.get(task['id'])['progress']['succeeded'] == 1


@pytest.mark.parametrize('category', ['CALL_ERROR', 'PARSE_ERROR', 'INCOMPLETE_RESULT'])
def test_three_attempts_per_unit_and_retry_after(service, category):
    task = service.start(plan(service), str(uuid4()))
    for ordinal in (1, 2, 3):
        prepared = service.prepare(service.pending(ignore_due=True)[0]['id'], str(uuid4()))
        assert prepared['ordinal'] == ordinal
        service.save(prepared, Outcome(False, error_category=category, retry_after=60 if ordinal == 1 else None))
        if ordinal < 3:
            assert service.pending() == []
    result = service.get(task['id'])
    assert result['state'] == 'completed'
    assert result['items'][0]['attempt_count'] == 3
    assert result['items'][0]['error_category'] == category


def test_local_blocked_zero_and_no_send_refund(service):
    task = service.start(plan(service, 2), str(uuid4()))
    one, two = service.pending()
    service.local_blocked(one['id'], '输入超限，未发送')
    prepared = service.prepare(two['id'], str(uuid4()))
    service.unsent(prepared)
    assert sorted(x['attempt_count'] for x in service.get(task['id'])['items']) == [0, 0]
    next_attempt = service.prepare(two['id'], str(uuid4()))
    assert next_attempt['ordinal'] == 1
    service.save(next_attempt, Outcome(True, {}))
    assert service.get(task['id'])['state'] == 'completed'


def test_cancel_commit_rollback_keeps_results_and_window(service):
    task = service.start(plan(service, 2), str(uuid4()))
    service.save(service.prepare(service.pending()[0]['id'], str(uuid4())), Outcome(True, {}))
    revision = service.get(task['id'])['revision']
    def before_commit(session):
        raise fault()
    event.listen(Session, 'before_commit', before_commit)
    try:
        with pytest.raises(OperationalError):
            service.cancel(task['id'], revision, str(uuid4()))
    finally:
        event.remove(Session, 'before_commit', before_commit)
    assert service.get(task['id'])['progress']['succeeded'] == 1
    with pytest.raises(ServiceError) as error:
        service.start(plan(service), str(uuid4()))
    assert error.value.code == 'TASK_BUSY'


def test_recovery_slot_corruption_fails_closed(service):
    service.start(plan(service), str(uuid4()))
    with service.database.engine.begin() as connection:
        connection.execute(text('UPDATE runtime_slot SET task_id=NULL'))
    with pytest.raises(RuntimeError, match='运行窗口'):
        service.recover()


def test_effect_generation_to_evaluation_atomic_and_release(service):
    class Hooks:
        def item_saved(self, session, task, item, outcome):
            if item.stage == 'reply_generation' and outcome.success:
                return [ItemSpec(item.case_id, 'evaluation', item.side, '', {'messages': [{'role': 'assistant', 'content': outcome.payload['reply']}]})]
            return []
        def phase_finished(self, session, task):
            return Transition('done', [])
    service.hooks = Hooks()
    task = service.start(plan(service, kind='effect'), str(uuid4()))
    prepared = service.prepare(service.pending()[0]['id'], str(uuid4()))
    service.save(prepared, Outcome(True, {'reply': '测试生成回复'}))
    assert service.get(task['id'])['state'] == 'running'
    assert len(service.get(task['id'])['items']) == 2
    service.save(service.prepare(service.pending()[0]['id'], str(uuid4())), Outcome(True, {}))
    assert service.get(task['id'])['state'] == 'completed'
    service.start(plan(service), str(uuid4()))


def test_cancel_before_last_e_does_not_make_q(service):
    class Hooks:
        def item_saved(self, *args):
            raise AssertionError('取消后不能写入业务结果')
        def phase_finished(self, *args):
            raise AssertionError('取消后不能创建Q')
    service.hooks = Hooks()
    task = service.start(plan(service), str(uuid4()))
    prepared = service.prepare(service.pending()[0]['id'], str(uuid4()))
    service.cancel(task['id'], service.get(task['id'])['revision'], str(uuid4()))
    assert not service.save(prepared, Outcome(True, {}))
    assert not service.save(prepared, object())


def test_api_status_and_missing_model_module(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/api/v1/tasks').json()['data'] == []
        response = client.post('/api/v1/evaluation-tasks', json={key: str(uuid4()) for key in ('operation_id', 'upload_id', 'rule_version_id', 'kb_version_id')})
        assert response.status_code == 409
        assert response.json()['code'] == 'DEPENDENCY_NOT_READY'
        assert client.get('/api/v1/tasks').json()['data'] == []


def test_prepare_failure_sends_zero_until_fixed(service, monkeypatch):
    async def run():
        transport = Transport(service)
        runner = Executor(service, transport, scan_interval=.005, storage_retry=.01)
        task = service.start(plan(service), str(uuid4()))
        real_prepare = service.prepare
        blocked = True
        def prepare(*args):
            if blocked:
                raise fault()
            return real_prepare(*args)
        monkeypatch.setattr(service, 'prepare', prepare)
        await runner.start()
        try:
            await until(lambda: bool(runner.storage_blocked))
            assert transport.calls == []
            assert service.get(task['id'])['items'][0]['attempt_count'] == 0
            blocked = False
            await until(lambda: len(transport.calls) == 1)
            transport.events[0].set()
            await until(lambda: service.get(task['id'])['state'] == 'completed')
        finally:
            await runner.stop()
    asyncio.run(run())


def test_cancel_revision_replay_and_source_retained(service):
    task = service.start(plan(service, 2), str(uuid4()))
    service.prepare(service.pending()[0]['id'], str(uuid4()))
    with pytest.raises(ServiceError) as error:
        service.cancel(task['id'], task['revision'], str(uuid4()))
    assert error.value.code == 'REVISION_CONFLICT'
    revision = service.get(task['id'])['revision']
    op = str(uuid4())
    result = service.cancel(task['id'], revision, op)
    assert service.cancel(task['id'], revision, op) == result
    from app.models.imports import CaseRecord, MaterialVersion
    with service.database.session() as s:
        assert len(list(s.scalars(select(CaseRecord)))) == 8
        assert len(list(s.scalars(select(MaterialVersion)))) == 2


def test_real_response_transaction_failure_has_no_partial_qa(service):
    class Hooks:
        def item_saved(self, *args):
            return []
        def phase_finished(self, session, task):
            return Transition('qa_generation', [ItemSpec(service.test_sources[3][0], 'standard_question', 'original', 'g', {'messages': []})])
    service.hooks = Hooks()
    task = service.start(plan(service), str(uuid4()))
    prepared = service.prepare(service.pending()[0]['id'], str(uuid4()))
    def before_commit(session):
        raise fault()
    event.listen(Session, 'before_commit', before_commit)
    try:
        with pytest.raises(OperationalError):
            service.save(prepared, Outcome(True, {}))
    finally:
        event.remove(Session, 'before_commit', before_commit)
    value = service.get(task['id'])
    assert value['phase'] == 'evaluating' and len(value['items']) == 1
    assert value['items'][0]['attempt_count'] == 1 and value['items'][0]['state'] == 'running'
    service.save(prepared, Outcome(True, {}))
    assert service.get(task['id'])['phase'] == 'qa_generation'


def test_transport_exception_retried_only_by009(service):
    class Failing:
        calls = 0
        def start_once(self, prepared):
            self.calls += 1
            async def response():
                return Outcome(False, error_category='CALL_ERROR', retry_after=0)
            return response()
    async def run():
        task = service.start(plan(service), str(uuid4()))
        transport = Failing()
        runner = Executor(service, transport, scan_interval=.005)
        await runner.start()
        try:
            await until(lambda: service.get(task['id'])['state'] == 'completed')
            assert transport.calls == 3
            assert service.get(task['id'])['items'][0]['attempt_count'] == 3
        finally:
            await runner.stop()
    asyncio.run(run())


def test_transport_local_validation_zero_calls(service):
    class Blocked:
        def validate(self, preview):
            assert preview['config']['request_model'] == 'test'
            assert 'messages' in preview['request']
            raise LocalBlocked('输入超限，未发送')
        def start_once(self, prepared):
            raise AssertionError('本地校验阻断后不得发送')
    async def run():
        task = service.start(plan(service), str(uuid4()))
        runner = Executor(service, Blocked(), scan_interval=.005)
        await runner.start()
        try:
            await until(lambda: service.get(task['id'])['state'] == 'completed')
            assert service.get(task['id'])['items'][0]['attempt_count'] == 0
        finally:
            await runner.stop()
    asyncio.run(run())


def test_concurrent_last_e_and_cancel_have_one_commit_winner(service):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    class Hooks:
        def item_saved(self, *args):
            return []
        def phase_finished(self, session, task):
            return Transition('qa_generation', [ItemSpec(service.test_sources[3][0], 'standard_question', 'original', 'race', {'messages': []})])
    service.hooks = Hooks()
    task = service.start(plan(service), str(uuid4()))
    prepared = service.prepare(service.pending()[0]['id'], str(uuid4()))
    revision = service.get(task['id'])['revision']
    barrier = Barrier(2)
    def save():
        barrier.wait()
        return service.save(prepared, Outcome(True, {}))
    def cancel():
        barrier.wait()
        try:
            return service.cancel(task['id'], revision, str(uuid4()))
        except ServiceError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as workers:
        saved, cancelled = workers.submit(save), workers.submit(cancel)
        saved.result()
        cancelled.result()
    value = service.get(task['id'])
    if value['state'] == 'cancelled':
        assert value['items'] == []
    else:
        assert value['phase'] == 'qa_generation'
        assert len([x for x in value['items'] if x['stage'] == 'standard_question']) == 1


def test_api_progress_and_cancel(service, tmp_path):
    task = service.start(plan(service, 2), str(uuid4()))
    service.database.stop()
    with TestClient(create_app(tmp_path)) as client:
        value = client.get('/api/v1/tasks/' + task['id']).json()['data']
        assert value['progress']['pending'] == 2
        assert client.get('/api/v1/tasks').json()['data'][0]['id'] == task['id']
        response = client.post('/api/v1/tasks/' + task['id'] + '/cancel', json={'operation_id': str(uuid4()), 'expected_revision': value['revision']})
        assert response.status_code == 200
        assert response.json()['data']['state'] == 'cancelled'
        assert client.get('/api/v1/tasks/' + task['id']).json()['data']['items'] == []


def test_api_builder_uses_module_contract(service, tmp_path):
    from app.domain.execution import Plan
    frozen = plan(service)
    service.database.stop()
    class Hooks:
        def item_saved(self, *args):
            return []
        def phase_finished(self, *args):
            return Transition('done', [])
    class Immediate:
        def start_once(self, attempt):
            async def response():
                return Outcome(True, {})
            return response()
    with TestClient(create_app(tmp_path, transport=Immediate(), task_builder=lambda _: frozen, task_hooks=Hooks())) as client:
        payload = {'operation_id': str(uuid4()), 'upload_id': frozen.upload_id, 'rule_version_id': frozen.rule_version_id, 'kb_version_id': frozen.kb_version_id}
        response = client.post('/api/v1/evaluation-tasks', json=payload)
        assert response.status_code == 200
        assert client.post('/api/v1/evaluation-tasks', json=payload).json()['data']['id'] == response.json()['data']['id']


def test_incremental_migration_preserves008_history(service):
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    from app.db.database import Database
    from app.models.imports import DialogueUpload, MaterialVersion
    db = service.database
    with db.session() as s:
        before = [(x.id, x.raw_csv) for model in (DialogueUpload, MaterialVersion) for x in s.scalars(select(model))]
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'migrations'))
    with db.engine.begin() as connection:
        config.attributes['connection'] = connection
        command.downgrade(config, '0001_imports')
    db.stop()
    restarted = Database(db.directory)
    restarted.start()
    try:
        with restarted.session() as s:
            after = [(x.id, x.raw_csv) for model in (DialogueUpload, MaterialVersion) for x in s.scalars(select(model))]
        assert before == after
        with restarted.engine.connect() as connection:
            assert connection.execute(text('PRAGMA foreign_key_check')).all() == []
            assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar() == '0009_sampling'
    finally:
        restarted.stop()


def test_runtime_prepare_commit_unknown_calls_once(service, monkeypatch):
    async def run():
        task = service.start(plan(service), str(uuid4()))
        real_prepare = service.prepare
        failed = False
        def unknown(*args):
            nonlocal failed
            value = real_prepare(*args)
            if not failed:
                failed = True
                raise fault()
            return value
        monkeypatch.setattr(service, 'prepare', unknown)
        transport = Transport(service)
        runner = Executor(service, transport, scan_interval=.005, storage_retry=.01)
        await runner.start()
        try:
            await until(lambda: len(transport.calls) == 1)
            assert transport.calls[0]['ordinal'] == 1
            transport.events[0].set()
            await until(lambda: service.get(task['id'])['state'] == 'completed')
            assert len(transport.calls) == 1
        finally:
            await runner.stop()
    asyncio.run(run())


def test_no_send_boundary_refunds_before_retry(service):
    class OnceUnsent:
        calls = 0
        def start_once(self, prepared):
            self.calls += 1
            if self.calls == 1:
                raise NoSend('尚未交给transport')
            async def response():
                return Outcome(True, {})
            return response()
    async def run():
        task = service.start(plan(service), str(uuid4()))
        transport = OnceUnsent()
        runner = Executor(service, transport, scan_interval=.005)
        await runner.start()
        try:
            await until(lambda: transport.calls == 1 and service.get(task['id'])['items'][0]['attempt_count'] == 0)
            # 测试读取真实退避期限，随后只在测试库推进到可运行时刻。
            with service.database.engine.begin() as c:
                c.execute(text('UPDATE execution_item SET next_attempt_at=NULL'))
            await until(lambda: service.get(task['id'])['state'] == 'completed')
            assert service.get(task['id'])['items'][0]['attempt_count'] == 1
            assert transport.calls == 2
        finally:
            await runner.stop()
    asyncio.run(run())
