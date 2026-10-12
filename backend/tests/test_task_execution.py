"""TASK-009确定性替身；不判断评分语义，不调用模型。"""
import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.database import Database
from app.domain.execution import ConfigSpec, ItemSpec, Plan, Outcome, Transition
from app.models.execution import Attempt, ExecutionItem
from app.models.imports import CaseRecord
from app.services.execution import TaskService
from app.services.imports import ImportService, ServiceError
from app.runtime.executor import Executor
from test_csv_import import encode, dialogue


@pytest.fixture
def service(tmp_path):
    db = Database(tmp_path)
    db.start()
    imp = ImportService(db)
    upload = imp.save('dialogues', encode('dialogues', [dialogue(str(i), question=f'问题{i}') for i in range(8)]), 'd.csv', str(uuid4()))
    rule = imp.save('rules', encode('rules', [['r', '规则', '原文']]), 'r.csv', str(uuid4()))
    kb = imp.save('knowledge', encode('knowledge', [['k', '知识', '原文']]), 'k.csv', str(uuid4()))
    svc = TaskService(db)
    with db.session() as s:
        cases = list(s.scalars(select(CaseRecord.id)))
    svc.test_sources = (upload[0]['id'], rule[0]['id'], kb[0]['id'], cases)
    yield svc
    db.stop()


def plan(svc, size=1, kind='ordinary'):
    upload, rule, kb, cases = svc.test_sources
    return Plan(kind, upload, rule, kb, cases[:size],
        [ConfigSpec(stage, '1.0', 'test', '测试正文', 'test', {}, 'test') for stage in ('evaluation', 'standard_question', 'reply_generation')],
        [ItemSpec(case, 'evaluation' if kind == 'ordinary' else 'reply_generation', 'original' if kind == 'ordinary' else 'old', '', {'messages': []}) for case in cases[:size]])


def test_window_idempotence_and_durable_count(service):
    p = plan(service)
    op = str(uuid4())
    task = service.start(p, op)
    assert service.start(p, op)['id'] == task['id']
    with pytest.raises(ServiceError) as error:
        service.start(p, str(uuid4()))
    assert error.value.code == 'TASK_BUSY'
    item = service.pending()[0]
    token = str(uuid4())
    first = service.prepare(item['id'], token)
    assert service.prepare(item['id'], token) == first
    assert service.get(task['id'])['items'][0]['attempt_count'] == 1
    service.recover()
    assert service.get(task['id'])['items'][0]['attempt_count'] == 1
    for _ in range(2):
        item = service.pending(ignore_due=True)[0]
        service.prepare(item['id'], str(uuid4()))
        service.recover()
    result = service.get(task['id'])
    assert result['state'] == 'completed'
    assert result['items'][0]['state'] == 'final_failed'
    assert result['items'][0]['attempt_count'] == 3


def test_success_restart_and_cancel_purge(service):
    task = service.start(plan(service, 2), str(uuid4()))
    one, two = service.pending()
    attempt = service.prepare(one['id'], str(uuid4()))
    service.save(attempt, Outcome(True, {'answer': '保存'}, raw='原文'))
    service.recover()
    assert [x['id'] for x in service.pending()] == [two['id']]
    late = service.prepare(two['id'], str(uuid4()))
    service.cancel(task['id'], service.get(task['id'])['revision'], str(uuid4()))
    assert not service.save(late, Outcome(True, {'late': True}))
    result = service.get(task['id'])
    assert result['state'] == 'cancelled' and result['items'] == []
    with service.database.session() as s:
        assert list(s.scalars(select(Attempt))) == []
    assert service.downstream_items(task['id']) == []


def test_atomic_qa_transition_blocks_cancel_and_releases_only_at_terminal(service):
    class Hooks:
        def item_saved(self, session, task, item, outcome):
            return []
        def phase_finished(self, session, task):
            if task.phase == 'evaluating':
                return Transition('qa_generation', [ItemSpec(service.test_sources[3][0], 'standard_question', 'original', 'g1', {'messages': []})])
            return Transition('done', [])
    service.hooks = Hooks()
    task = service.start(plan(service), str(uuid4()))
    service.save(service.prepare(service.pending()[0]['id'], str(uuid4())), Outcome(True, {}))
    assert service.get(task['id'])['phase'] == 'qa_generation'
    with pytest.raises(ServiceError) as error:
        service.cancel(task['id'], service.get(task['id'])['revision'], str(uuid4()))
    assert error.value.code == 'CANCEL_FORBIDDEN'
    with pytest.raises(ServiceError):
        service.start(plan(service), str(uuid4()))
    for _ in range(3):
        service.save(service.prepare(service.pending(ignore_due=True)[0]['id'], str(uuid4())), Outcome(False, error_category='PARSE_ERROR'))
    assert service.get(task['id'])['state'] == 'completed'
    service.start(plan(service), str(uuid4()))


class Transport:
    def __init__(self, svc):
        self.svc, self.calls, self.events = svc, [], []
        self.active = self.peak = 0
    def start_once(self, attempt):
        # 交给transport的时刻必须晚于持久计次。
        with self.svc.database.session() as s:
            assert s.get(Attempt, attempt['id']).ordinal == attempt['ordinal']
        self.calls.append(attempt)
        event = asyncio.Event()
        self.events.append(event)
        self.active += 1
        self.peak = max(self.peak, self.active)
        async def response():
            try:
                await event.wait()
                return Outcome(True, {'ok': True})
            finally:
                self.active -= 1
        return response()


async def until(predicate):
    for _ in range(400):
        if predicate():
            return
        await asyncio.sleep(.005)
    raise AssertionError('等待条件未满足')


def test_cancelled_inflight_still_occupies_global_three(service):
    async def run():
        transport = Transport(service)
        runner = Executor(service, transport, scan_interval=.005, storage_retry=.01)
        first = service.start(plan(service, 8), str(uuid4()))
        await runner.start()
        try:
            await until(lambda: len(transport.calls) == 3)
            await runner.cancel(first['id'], service.get(first['id'])['revision'], str(uuid4()))
            second = service.start(plan(service, 2, 'effect'), str(uuid4()))
            await asyncio.sleep(.04)
            assert len(transport.calls) == 3
            transport.events[0].set()
            await until(lambda: len(transport.calls) == 4)
            assert transport.peak == 3
            for event in transport.events:
                event.set()
            await until(lambda: len(transport.calls) == 5)
            for event in transport.events:
                event.set()
            await until(lambda: service.get(second['id'])['state'] == 'completed')
            assert service.get(first['id'])['items'] == []
        finally:
            await runner.stop()
    asyncio.run(run())


def test_save_failure_retains_response_and_freezes_new_calls(service, monkeypatch):
    async def run():
        transport = Transport(service)
        runner = Executor(service, transport, scan_interval=.005, storage_retry=.05)
        task = service.start(plan(service, 8), str(uuid4()))
        real_save = service.save
        blocked = True
        def save(*args, **kwargs):
            if blocked:
                from sqlalchemy.exc import OperationalError
                raise OperationalError('fault', {}, Exception('disk'))
            return real_save(*args, **kwargs)
        monkeypatch.setattr(service, 'save', save)
        await runner.start()
        try:
            await until(lambda: len(transport.calls) == 3)
            transport.events[0].set()
            await until(lambda: task['id'] in runner.storage_blocked)
            await asyncio.sleep(.025)
            assert len(transport.calls) == 3
            blocked = False
            await until(lambda: service.get(task['id'])['progress']['succeeded'] == 1)
            assert len([x for x in transport.calls if x['item_id'] == transport.calls[0]['item_id']]) == 1
            await runner.cancel(task['id'], service.get(task['id'])['revision'], str(uuid4()))
            for e in transport.events:
                e.set()
        finally:
            await runner.stop()
    asyncio.run(run())
