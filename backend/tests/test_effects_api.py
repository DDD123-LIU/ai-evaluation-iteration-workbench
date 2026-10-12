"""016生产路由/DTO与统一执行器；仅测试层模型替身。"""
import asyncio
import json
import time
from uuid import uuid4
import pytest
from app.domain.model_contract import check_envelope
from app.services.imports import ImportService
from test_csv_import import encode
from test_model_contract import envelope, evaluation
from test_qa_review_api import client, approved


def source(client):
    row = approved(client)
    event = client.post('/api/v1/exports', json={'operation_id': str(uuid4()), 'selected_qa_ids': [row['id']], 'expected_qa_revisions': {row['id']: row['revision']}}).json()['data']
    item = client.get('/api/v1/exports/' + event['id']).json()['data']['items'][0]
    kb = ImportService(client.app.state.database).save('knowledge', encode('knowledge', [['new', '新库', '本人加入的内容']]), 'new.csv', str(uuid4()))[0]['id']
    record = client.post('/api/v1/supplements', json={'operation_id': str(uuid4()), 'new_kb_id': kb,
        'source_batch_id': client.task_id, 'export_item_ids': [item['id']], 'confirm': True}).json()['data']
    return record


class Transport:
    def start_once(self, prepared):
        async def answer():
            await asyncio.sleep(.01)
            value = {'reply': '独立生成客服回复'} if prepared['config']['stage'] == 'reply_generation' else evaluation()
            return check_envelope(prepared['config']['stage'], envelope(json.dumps(value)), prepared['request']['history'], prepared['request']['target_reply'])
        return answer()


def test_start_query_and_original_operation_replay_sampling_available(client):
    record = source(client)
    client.app.state.executor.transport = Transport()
    op = str(uuid4())
    path = '/api/v1/supplements/' + record['id'] + '/effect-tasks'
    response = client.post(path, json={'operation_id': op})
    assert response.status_code == 200, response.text
    task = response.json()['data']
    assert client.post(path, json={'operation_id': op}).json()['data']['id'] == task['id']
    for _ in range(100):
        data = client.get('/api/v1/effect-tasks/' + task['id']).json()['data']
        if data['state'] == 'completed': break
        time.sleep(.025)
    assert data['state'] == 'completed' and data['metrics']['status'] == 'available'
    assert data['cases'][0]['comparison']['comparable'] and data['human_effect_conclusion'] == 'pending_confirmation'
    assert client.get('/api/v1/effect-tasks/' + task['id'] + '/sampling').json()['data']['status'] == 'pending_confirmation'
    assert client.get('/api/v1/operations/' + op).json()['data']['result_id'] == task['id']
    again = client.post(path, json={'operation_id': str(uuid4())})
    assert again.status_code == 200 and again.json()['data']['id'] != task['id']


@pytest.mark.parametrize('body', [{}, {'operation_id': 'bad'}, {'operation_id': str(uuid4()), 'new_kb_id': str(uuid4())}])
def test_invalid_fields_no_task(client, body):
    record = source(client)
    client.app.state.executor.transport = Transport()
    assert client.post('/api/v1/supplements/' + record['id'] + '/effect-tasks', json=body).status_code == 422


def test_missing_key_and_unknown_source_do_not_create_task(client):
    record = source(client)
    path = '/api/v1/supplements/' + record['id'] + '/effect-tasks'
    assert client.post(path, json={'operation_id': str(uuid4())}).json()['code'] == 'DEPENDENCY_NOT_READY'
    client.app.state.executor.transport = Transport()
    assert client.post('/api/v1/supplements/' + str(uuid4()) + '/effect-tasks', json={'operation_id': str(uuid4())}).status_code == 404
    assert client.get('/api/v1/effect-tasks/' + client.task_id).status_code == 404
