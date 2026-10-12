"""015真实API字段、人工确认及历史追溯，不启动效果任务。"""
from uuid import uuid4
import pytest
from test_qa_review_api import client, approved


def body(client):
    qa = approved(client)
    event = client.post('/api/v1/exports', json={'operation_id': str(uuid4()),
        'selected_qa_ids': [qa['id']], 'expected_qa_revisions': {qa['id']: qa['revision']}}).json()['data']
    snapshot = client.get('/api/v1/exports/' + event['id']).json()['data']['items'][0]
    from app.models.execution import OrdinaryTask
    with client.app.state.database.session() as session:
        kb = session.get(OrdinaryTask, client.task_id).kb_version_id
    return {'operation_id': str(uuid4()), 'new_kb_id': kb, 'source_batch_id': client.task_id,
        'export_item_ids': [snapshot['id']], 'confirm': True}


def test_confirmation_history_list_operation_and_no_effect_endpoint(client):
    request = body(client)
    response = client.post('/api/v1/supplements', json=request)
    assert response.status_code == 201, response.text
    result = response.json()['data']
    assert client.post('/api/v1/supplements', json=request).json()['data'] == result
    assert client.post('/api/v1/supplements', json=request).status_code == 200
    detail = client.get('/api/v1/supplements/' + result['id']).json()['data']
    assert detail['confirmed'] and detail['can_validate'] and len(detail['source_case_ids']) == 1
    assert detail['snapshots'][0]['qa_id'] == client.qa_id
    assert client.get('/api/v1/operations/' + request['operation_id']).json()['data']['result_id'] == result['id']
    assert len(client.get('/api/v1/supplements', params={'new_kb_id': request['new_kb_id']}).json()['items']) == 1
    assert client.post('/api/v1/supplements/' + result['id'] + '/effect-tasks', json={}).status_code == 422
    assert client.patch('/api/v1/supplements/' + result['id'], json={}).status_code == 405


@pytest.mark.parametrize('field,value', [('confirm', False), ('confirm', 'true'), ('confirm', 1),
    ('confirm', None), ('export_item_ids', []), ('new_kb_id', 'bad'), ('source_batch_id', None), ('extra', True)])
def test_invalid_request_creates_no_record(client, field, value):
    request = body(client)
    request[field] = value
    response = client.post('/api/v1/supplements', json=request)
    assert response.status_code == 422
    assert client.get('/api/v1/supplements').json()['items'] == []
    if field == 'export_item_ids': assert response.json()['message'] == '无可验证案例'


def test_unknown_record_and_invalid_paging(client):
    assert client.get('/api/v1/supplements/' + str(uuid4())).status_code == 404
    assert client.get('/api/v1/supplements?limit=0').status_code == 422
    assert client.get('/api/v1/supplements?offset=-1').status_code == 422
