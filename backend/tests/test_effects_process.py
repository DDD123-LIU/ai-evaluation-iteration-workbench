"""016真实SDK边界与HTTP进程强杀恢复，外网完全替身隔离。"""
import json
import os
import subprocess
import sys
from pathlib import Path
import httpx
from test_task_execution import service
from test_effects import setup_effect, send
from test_http_smoke import free_port, wait_ready
from test_task_process import wait_state
from test_evaluation_process import stop_tree


def start_process(directory, log):
    root = Path(__file__).resolve().parents[1]
    port = free_port()
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'effects_test_server:app', '--host', '127.0.0.1', '--port', str(port), '--workers', '1'],
        cwd=root, env={**os.environ, 'WORKBENCH_DATA_DIR': str(directory), 'PYTHONPATH': str(root/'tests') + os.pathsep + str(root)},
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    return process, f'http://127.0.0.1:{port}'


def test_effect_generation_and_E_recover_without_recalling_success(service, tmp_path):
    task, _, _ = setup_effect(service)
    old = next(item for item in task['items'] if item['side'] == 'old')
    saved, _ = send(service, {'id': old['id']}, {'reply': '重启前已保存的旧侧生成'})
    service.database.stop()
    processes = []
    with (tmp_path/'server.log').open('wb') as log:
        try:
            first, url = start_process(tmp_path, log)
            processes.append(first)
            wait_ready(first, url)
            before = wait_state(url, task['id'], lambda row: row['progress']['succeeded'] == 2 and row['progress']['running'] == 1)
            stop_tree(first)
            second, url = start_process(tmp_path, log)
            processes.append(second)
            wait_ready(second, url)
            (tmp_path/'release').write_text('继续测试', encoding='utf-8')
            after = wait_state(url, task['id'], lambda row: row['state'] == 'completed')
            actual = httpx.get(url + '/api/v1/effect-tasks/' + task['id']).json()['data']
            calls = [json.loads(line) for line in (tmp_path/'effect-calls.jsonl').read_text(encoding='utf-8').splitlines()]
            assert calls.count({'stage': 'reply_generation', 'side': 'new'}) == 2
            assert {'stage': 'reply_generation', 'side': 'old'} not in calls
            assert calls.count({'stage': 'evaluation', 'side': 'old'}) == 1
            assert calls.count({'stage': 'evaluation', 'side': 'new'}) == 1
            assert actual['cases'][0]['old']['generation']['reply'] == '重启前已保存的旧侧生成'
            assert actual['cases'][0]['comparison']['comparable']
            assert actual['cases'][0]['new']['generation']['attempt_count'] == 2
            assert httpx.get(url + '/api/v1/tasks/' + task['id'] + '/qa').json()['data'] == {'drafts': [], 'failures': [], 'pending': []}
            (tmp_path/'effects-recovery.json').write_text(json.dumps({'before': before, 'after': after, 'detail': actual, 'calls': calls}, ensure_ascii=False, indent=2), encoding='utf-8')
        finally:
            for process in processes: stop_tree(process)
