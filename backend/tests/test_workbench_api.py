"""018页面读适配仍服从009/012/014既有持久规则。"""
from test_qa_review_api import client,approved,edit
from test_effects_api import Transport
from app.services.workbench import phase_progress

def test_overview_truth_and_readiness(client):
    response=client.get('/api/v1/workbench')
    assert response.status_code==200,response.text
    view=response.json()['data']
    assert not view['model_ready'] and not view['can_start']
    task=next(t for t in view['tasks'] if t['id']==client.task_id)
    assert task['source']['upload_id']
    assert task['summary']['data']['counts']['total']==1
    assert not task['capabilities']['can_cancel']
    assert task['phase_progress'][0]['total']==1
    client.app.state.executor.transport=Transport()
    assert client.get('/api/v1/workbench').json()['data']['model_ready']

def test_capabilities_empty_approved_and_edit(client):
    path='/api/v1/workbench/qa/'+client.qa_id+'/capabilities'
    view=client.get(path).json()['data']
    assert not view['can_approve'] and not view['can_export']
    assert view['source_case_number']=='0'
    row=approved(client)
    assert client.get(path).json()['data']['can_export']
    assert edit(client,'实际修改','新答',row['revision']).status_code==200
    view=client.get(path).json()['data']
    assert view['can_approve'] and not view['can_export']

def test_built_static_and_api_boundary(client):
    assert client.get('/').status_code==200
    assert 'id="root"' in client.get('/').text
    assert client.get('/api/v1/workbench').headers['content-type'].startswith('application/json')
    assert client.get('/api/v1/workbench/qa/00000000-0000-0000-0000-000000000000/capabilities').status_code==404

def test_effect_phase_denominator_and_upstream_failures():
    items=[{'stage':'reply_generation','side':side,'case_id':case,'state':state} for side in ('old','new') for case,state in [('a','succeeded'),('b','final_failed')]]
    items.append({'stage':'evaluation','side':'old','case_id':'a','state':'running'})
    rows=phase_progress({'kind':'effect','items':items},2)
    old=next(r for r in rows if r['stage']=='evaluation' and r['side']=='old')
    assert old['total']==2 and old['running']==1 and old['upstream_generation_failed']==1
    new=next(r for r in rows if r['stage']=='evaluation' and r['side']=='new')
    assert new['total']==2 and new['waiting_for_generation']==1 and new['upstream_generation_failed']==1
