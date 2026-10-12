"""014实际FastAPI字段/提交/下载契约，不调用模型。"""
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.services.execution import TaskService
from app.services.qa_review import QAReviewService
from test_qa_review_integration import drafts


@pytest.fixture
def client(tmp_path):
    from app.services.imports import ImportService
    from test_csv_import import encode,dialogue
    app=create_app(tmp_path)
    with TestClient(app) as client:
        db=app.state.database;imports=ImportService(db)
        values=[]
        for kind,rows in [('dialogues',[dialogue('0',question='问题0')]),('rules',[['r','规则','原文']]),('knowledge',[['k','知识','原文']])]:
            values.append(imports.save(kind,encode(kind,rows),'test.csv',str(uuid4()))[0]['id'])
        svc=TaskService(db);svc.test_sources=(*values,[])
        task,rows=drafts(svc,1)
        client.qa_id=rows[0]['id'];client.task_id=task['id']
        yield client


def edit(client,question='问,题\n"原文"',answer='答\n案',revision=0,op=None):
    return client.patch(f'/api/v1/qa/{client.qa_id}',json={'operation_id':op or str(uuid4()),'expected_revision':revision,'question':question,'answer':answer})


def approved(client):
    row=edit(client).json()['data']
    response=client.post(f'/api/v1/qa/{client.qa_id}/approve',json={'operation_id':str(uuid4()),'expected_revision':row['revision'],'confirm':True})
    assert response.status_code==200
    return response.json()['data']


def test_approval_export_download_original_bytes_operation_and_readonly_history(client):
    empty=client.post(f'/api/v1/qa/{client.qa_id}/approve',json={'operation_id':str(uuid4()),'expected_revision':0,'confirm':True})
    assert empty.status_code==422 and empty.json()['code']=='QA_INCOMPLETE'
    good=approved(client);op=str(uuid4())
    body={'operation_id':op,'selected_qa_ids':[client.qa_id],'expected_qa_revisions':{client.qa_id:good['revision']}}
    response=client.post('/api/v1/exports',json=body);assert response.status_code==201,response.text
    event=response.json()['data']
    file=client.get(event['download_url']);assert file.status_code==200 and file.content.startswith(b'\xef\xbb\xbf')
    assert event['id'] in file.headers['content-disposition'] and file.headers['content-type'].startswith('text/csv')
    assert client.get(f'/api/v1/operations/{op}').json()['data']['result_id']==event['id']
    assert client.post('/api/v1/exports',json=body).status_code==200
    assert len(client.get('/api/v1/exports').json()['items'])==1
    snapshot=client.get(f"/api/v1/exports/{event['id']}").json()['data']
    assert snapshot['items'][0]['answer']==good['answer']
    assert edit(client,'新问','新答',good['revision']).status_code==200
    assert client.get(event['download_url']).content==file.content
    assert client.get(f"/api/v1/exports/{event['id']}").json()['data']==snapshot
    assert client.get(f'/api/v1/exports?source_batch_id={client.task_id}').json()['items'][0]['id']==event['id']
    assert client.patch(f"/api/v1/exports/{event['id']}",json={}).status_code==405
    assert client.post('/api/v1/supplements',json={}).status_code==422


@pytest.mark.parametrize('field,value',[('question',None),('answer',12),('expected_revision',True),('expected_revision',-1),('category','其他')])
def test_edit_strict_types_unknown_fields_never_mutate(client,field,value):
    body={'operation_id':str(uuid4()),'expected_revision':0,'question':'问','answer':'答'};body[field]=value
    assert client.patch(f'/api/v1/qa/{client.qa_id}',json=body).status_code==422
    assert client.get(f'/api/v1/qa/{client.qa_id}').json()['data']['revision']==0


@pytest.mark.parametrize('confirm',[False,1,'true',None])
def test_explicit_confirmation_cannot_be_coerced(client,confirm):
    row=edit(client).json()['data']
    response=client.post(f'/api/v1/qa/{client.qa_id}/approve',json={'operation_id':str(uuid4()),'expected_revision':row['revision'],'confirm':confirm})
    assert response.status_code==422
    assert client.get(f'/api/v1/qa/{client.qa_id}').json()['data']['review_state']=='pending_review'


@pytest.mark.parametrize('revision',[True,-1,'1',None])
def test_export_requires_strict_nonnegative_revisions(client,revision):
    assert client.post('/api/v1/exports',json={'operation_id':str(uuid4()),'selected_qa_ids':[client.qa_id],'expected_qa_revisions':{client.qa_id:revision}}).status_code==422
    assert client.get('/api/v1/exports').json()['items']==[]


def test_missing_generation_record_and_nonexistent_history_not_found(client):
    unknown=str(uuid4())
    assert client.post(f'/api/v1/qa/{unknown}/approve',json={'operation_id':str(uuid4()),'expected_revision':0,'confirm':True}).status_code==404
    assert client.get(f'/api/v1/exports/{unknown}').status_code==404
    assert client.get(f'/api/v1/exports/{unknown}/file').status_code==404
    assert client.get('/api/v1/exports?limit=0').status_code==422
