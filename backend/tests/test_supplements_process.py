"""015独立本地HTTP进程：已提交关联强杀后原操作重放及来源读回。"""
import json
from uuid import uuid4
import httpx
from test_task_execution import service
from test_supplements import seed, new_kb
from test_http_smoke import start_server, wait_ready
from test_evaluation_process import stop_tree


def test_supplement_crash_restart_keeps_snapshot_and_operation(service, tmp_path, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', '')
    task, rows, items, review = seed(service, 1)
    kb = new_kb(service)
    review.edit(rows[0]['id'], '已改问', '当前待审核答案', rows[0]['revision'], str(uuid4()))
    request = {'operation_id': str(uuid4()), 'new_kb_id': kb, 'source_batch_id': task['id'],
        'export_item_ids': [items[0]['id']], 'confirm': True}
    service.database.stop()
    processes = []
    with (tmp_path / 'server.log').open('wb') as log:
        try:
            first, url = start_server(tmp_path, log)
            processes.append(first)
            wait_ready(first, url)
            response = httpx.post(url + '/api/v1/supplements', json=request)
            assert response.status_code == 201, response.text
            result = response.json()['data']
            detail = httpx.get(url + '/api/v1/supplements/' + result['id']).json()['data']
            stop_tree(first)
            second, url = start_server(tmp_path, log)
            processes.append(second)
            wait_ready(second, url)
            assert httpx.get(url + '/api/v1/operations/' + request['operation_id']).json()['data']['result_id'] == result['id']
            replay = httpx.post(url + '/api/v1/supplements', json=request)
            assert replay.status_code == 200 and replay.json()['data'] == result
            assert httpx.get(url + '/api/v1/supplements/' + result['id']).json()['data'] == detail
            assert detail['snapshots'][0]['answer'] == '人工答案'
            assert len(httpx.get(url + '/api/v1/supplements').json()['items']) == 1
            (tmp_path / 'supplement-recovery.json').write_text(json.dumps({'request': request, 'result': result,
                'detail': detail}, ensure_ascii=False, indent=2), encoding='utf-8')
        finally:
            for process in processes: stop_tree(process)
