"""017 HTTP接口人工输入及重传；没有页面或真实人工业务判断。"""
import time
from uuid import uuid4
import pytest
from test_qa_review_api import client
from test_effects_api import source, Transport


def started(client):
    record=source(client)
    client.app.state.executor.transport=Transport()
    task=client.post('/api/v1/supplements/'+record['id']+'/effect-tasks',json={'operation_id':str(uuid4())}).json()['data']
    path='/api/v1/effect-tasks/'+task['id']+'/sampling'
    for _ in range(100):
        data=client.get(path).json()['data']
        if data['status']!='automatic_pending':break
        time.sleep(.025)
    assert data['status']=='pending_confirmation'
    return task,path,data


def test_read_patch_partial_full_and_effect_detail(client):
    task,path,before=started(client)
    case=before['draws'][0]['case_id']
    body={'operation_id':str(uuid4()),'expected_revision':0,'accuracy':'改善','intent':None,'service':None}
    partial=client.patch(path+'/'+case,json=body)
    assert partial.status_code==200 and partial.json()['data']['status']=='pending_confirmation'
    assert client.patch(path+'/'+case,json=body).json()==partial.json()
    body.update(operation_id=str(uuid4()),expected_revision=1,intent='持平',service='改善')
    full=client.patch(path+'/'+case,json=body).json()['data']
    assert full['status']=='passed'
    assert client.get(path).json()['data']==full
    assert client.get('/api/v1/effect-tasks/'+task['id']).json()['data']['human_effect_conclusion']=='passed'
    assert client.get('/api/v1/operations/'+body['operation_id']).json()['data']['result_id']==task['id']


@pytest.mark.parametrize('changes',[{'accuracy':'自动通过'},{'expected_revision':True},{'expected_revision':-1},{'operation_id':'bad'},{'new_score':5}])
def test_invalid_input_no_change(client,changes):
    _,path,before=started(client)
    body={'operation_id':str(uuid4()),'expected_revision':0,'accuracy':'改善','intent':'持平','service':'持平',**changes}
    assert client.patch(path+'/'+before['draws'][0]['case_id'],json=body).status_code==422
    assert client.get(path).json()['data']==before


def test_conflict_and_no_redraw_endpoint(client):
    _,path,before=started(client);case=before['draws'][0]['case_id']
    body={'operation_id':str(uuid4()),'expected_revision':0,'accuracy':'变差','intent':None,'service':None}
    assert client.patch(path+'/'+case,json=body).json()['data']['status']=='not_passed'
    body['operation_id']=str(uuid4())
    assert client.patch(path+'/'+case,json=body).json()['code']=='REVISION_CONFLICT'
    assert client.post(path,json={}).status_code==405
