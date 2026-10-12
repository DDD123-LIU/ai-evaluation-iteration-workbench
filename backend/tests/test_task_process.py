"""真实Uvicorn进程中断及重启，不与TestClient组混跑。"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx

from test_task_execution import service, plan
from test_http_smoke import free_port, wait_ready, stop


def start(directory, log):
    root = Path(__file__).resolve().parents[1]
    port = free_port()
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'task_test_server:app', '--host', '127.0.0.1', '--port', str(port), '--workers', '1'],
        cwd=root, env={**os.environ, 'WORKBENCH_DATA_DIR': str(directory), 'PYTHONPATH': str(root / 'tests') + os.pathsep + str(root)},
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    return process, f'http://127.0.0.1:{port}'


def wait_state(url, task_id, predicate):
    for _ in range(250):
        result = httpx.get(url + '/api/v1/tasks/' + task_id, timeout=2)
        assert result.status_code == 200, result.text
        value = result.json()['data']
        if predicate(value):
            return value
        time.sleep(.03)
    raise AssertionError('后台任务未达到预期状态')


def test_real_http_crash_restart_success_not_repeated(service, tmp_path):
    task = service.start(plan(service, 2), str(uuid4()))
    service.database.stop()
    processes = []
    with (tmp_path / 'server.log').open('wb') as log:
        try:
            first, url = start(tmp_path, log)
            processes.append(first)
            wait_ready(first, url)
            before = wait_state(url, task['id'], lambda x: x['progress']['succeeded'] == 1 and x['progress']['running'] == 1)
            succeeded = next(x['id'] for x in before['items'] if x['state'] == 'succeeded')
            # 浏览器连接结束后后端仍运行；随后强制终止进程，不执行lifespan。
            first.kill()
            first.wait(timeout=10)
            second, url = start(tmp_path, log)
            processes.append(second)
            wait_ready(second, url)
            (tmp_path / 'release').write_text('恢复', encoding='utf-8')
            after = wait_state(url, task['id'], lambda x: x['state'] == 'completed')
            calls = [json.loads(line) for line in (tmp_path / 'calls.jsonl').read_text(encoding='utf-8').splitlines()]
            assert len([x for x in calls if x['item_id'] == succeeded]) == 1
            assert sorted(x['attempt_count'] for x in after['items']) == [1, 2]
            assert len(calls) == 3
            (tmp_path / 'recovery-evidence.json').write_text(json.dumps({'before': before, 'after': after, 'calls': calls}, ensure_ascii=False, indent=2), encoding='utf-8')
        finally:
            for process in processes:
                stop(process)
