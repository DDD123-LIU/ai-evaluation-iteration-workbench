"""009统一重试。取消门内持久化并交给transport，门外等待响应。"""
import asyncio
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.domain.execution import Outcome, NoSend, LocalBlocked


class Executor:
    def __init__(self, service, transport=None, scan_interval=.1, storage_retry=5):
        self.service, self.transport = service, transport
        self.scan_interval, self.storage_retry = scan_interval, storage_retry
        self.gate = asyncio.Lock()
        self.slots = asyncio.BoundedSemaphore(3)
        self.storage_blocked = set()
        self._blocked_counts = {}
        self.workers = {}
        self.scanner = None
        self.stopping = False
        self.last_error = None
        self.execution_error = None

    async def start(self):
        self.service.recover()
        self.stopping = False
        self.scanner = asyncio.create_task(self._scan())

    async def stop(self):
        self.stopping = True
        if self.scanner:
            self.scanner.cancel()
            await asyncio.gather(self.scanner, return_exceptions=True)
        for worker in self.workers.values():
            worker.cancel()
        await asyncio.gather(*self.workers.values(), return_exceptions=True)
        self.workers.clear()

    async def cancel(self, task_id, revision, operation_id):
        async with self.gate:
            return self.service.cancel(task_id, revision, operation_id)

    async def _scan(self):
        while not self.stopping:
            try:
                if self.transport:
                    for item in self.service.pending():
                        if item['id'] not in self.workers and item['task_id'] not in self.storage_blocked:
                            worker = asyncio.create_task(self._execute(item))
                            self.workers[item['id']] = worker
                            worker.add_done_callback(lambda completed, key=item['id']: self._finished(key, completed))
                self.last_error = self.execution_error
            except SQLAlchemyError as error:
                self.last_error = 'storage_unavailable: ' + type(error).__name__
            await asyncio.sleep(self.storage_retry if self.last_error else self.scan_interval)

    def _finished(self, key, worker):
        self.workers.pop(key, None)
        if not worker.cancelled() and worker.exception():
            # 编程/业务钩子错误保持窗口，展示诊断，不转成模型失败反复调用。
            self.execution_error = 'execution_error: ' + type(worker.exception()).__name__
            self.last_error = self.execution_error

    async def _local(self, task_id, action):
        blocked = False
        try:
            while True:
                try:
                    return action()
                except SQLAlchemyError:
                    if not blocked:
                        blocked = True
                        self._blocked_counts[task_id] = self._blocked_counts.get(task_id, 0) + 1
                        self.storage_blocked.add(task_id)
                    await asyncio.sleep(self.storage_retry)
        finally:
            if blocked:
                self._blocked_counts[task_id] -= 1
                if not self._blocked_counts[task_id]:
                    self.storage_blocked.discard(task_id)

    async def _execute(self, item):
        async with self.slots:
            while item['task_id'] in self.storage_blocked:
                await asyncio.sleep(self.storage_retry)
            token = str(uuid4())
            # 预留失败时不持有取消门睡眠；相同token读回处理COMMIT返回未知。
            prepared = None
            while prepared is None:
                try:
                    async with self.gate:
                        if item['task_id'] in self.storage_blocked:
                            break
                        validator = getattr(self.transport, 'validate', None)
                        try:
                            if validator:
                                preview = self.service.preview(item['id'])
                                if preview is None:
                                    return
                                validator(preview)
                        except LocalBlocked as error:
                            self.service.local_blocked(item['id'], str(error))
                            return
                        prepared = self.service.prepare(item['id'], token)
                        if prepared is None:
                            return
                        try:
                            response = self.transport.start_once(prepared)
                        except NoSend:
                            awaitable_action = lambda: self.service.unsent(prepared)
                            response = None
                        except Exception as error:
                            async def failed(message=type(error).__name__):
                                return Outcome(False, error_category='CALL_ERROR', error_detail=message)
                            response = failed()
                    if response is None:
                        await self._local(item['task_id'], awaitable_action)
                        return
                except SQLAlchemyError:
                    # prepare可能已提交：下一次使用原token，而不是再增加一次。
                    prepared = None
                    self._blocked_counts[item['task_id']] = self._blocked_counts.get(item['task_id'], 0) + 1
                    self.storage_blocked.add(item['task_id'])
                    try:
                        await asyncio.sleep(self.storage_retry)
                    finally:
                        self._blocked_counts[item['task_id']] -= 1
                        if not self._blocked_counts[item['task_id']]:
                            self.storage_blocked.discard(item['task_id'])
            if prepared is None:
                return
            try:
                outcome = await response
            except Exception as error:
                outcome = Outcome(False, error_category='CALL_ERROR', error_detail=type(error).__name__)
            # 不再调用供应商；在当前进程保留响应直到成功保存或已取消丢弃。
            await self._local(item['task_id'], lambda: self.service.save(prepared, outcome))
