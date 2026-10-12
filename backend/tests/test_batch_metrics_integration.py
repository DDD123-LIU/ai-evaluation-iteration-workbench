"""012+011+009真实SQLite事务及本地HTTP契约；无模型调用。"""
import json
from dataclasses import replace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,text
from sqlalchemy.exc import SQLAlchemyError
from app.main import create_app
from app.models.batch_metrics import BatchSummary
from app.models.execution import Task,ExecutionItem
from app.domain.execution import Outcome,Transition
from app.services.batch_metrics import MetricsHooks,summary,cases
from app.services.evaluation import EvaluationHooks,EvaluationBuilder
from app.services.imports import ImportService,ServiceError
from test_task_execution import service
from test_evaluation import qconfig,save_value
from test_model_contract import evaluation,missing
from test_csv_import import encode,dialogue


def build(service,n=3):
    imports=ImportService(service.database)
    upload=imports.save('dialogues',encode('dialogues',[dialogue(str(i),question=f'问题{i}') for i in range(n)]),'numbers.csv',str(uuid4()))[0]['id']
    _,rule,kb,_=service.test_sources
    return EvaluationBuilder(service.database,qconfig())({'upload_id':upload,'rule_version_id':rule,'kb_version_id':kb})


def bad():
    value=evaluation();value['scores']['accuracy']['score']=3;value['primary_cause']='其他／证据不足';return value


def finish(service,item,value=None):
    if value is None:
        service.local_blocked(item['id'],'仅测试最终本地异常')
    else:save_value(service,item,value)


def setup(service,n=3):
    service.hooks=EvaluationHooks(MetricsHooks())
    task=service.start(build(service,n),str(uuid4()))
    by_id={item['id']:item for item in service.get(task['id'])['items']}
    return task,[by_id[item['id']] for item in service.pending()]


def test_confirmed_100_case_snapshot_problem_sets_and_restore(service):
    task,items=setup(service,100)
    for i,item in enumerate(items):
        value=evaluation()
        if 84<=i<90:
            value['scores']['accuracy']['score']=5;value['scores']['service']['score']=3;value['primary_cause']='其他／证据不足'
        finish(service,item,value if i<90 else None)
    data=summary(service.database,task['id'])['data']
    assert data['counts']=={'total':100,'succeeded':90,'qualified':84,'badcase':6,'final_errors':10,'score_total':1080}
    assert data['display']=={'pass_rate':'93.33%','average_score':'4.00','error_rate':'10.00%'}
    assert [a['kind'] for a in data['alerts']]==['quality','error'] and not data['batch_passed']
    expected_bad={i['case_id'] for i in items[84:90]};expected_error={i['case_id'] for i in items[90:]}
    assert set(data['alerts'][0]['problem_case_ids'])==expected_bad
    assert set(data['alerts'][1]['problem_case_ids'])==expected_error
    assert {c['case_id'] for c in cases(service.database,task['id'],'badcase')}==expected_bad
    assert {c['case_id'] for c in cases(service.database,task['id'],'errors')}==expected_error
    service.recover();assert summary(service.database,task['id'])['data']==data
    with service.database.session() as s:assert len(list(s.scalars(select(BatchSummary))))==1


def test_pending_cancelled_and_late_response_have_no_metrics(service):
    task,items=setup(service)
    finish(service,items[0],evaluation())
    assert summary(service.database,task['id'])=={'status':'pending','data':None}
    prepared=service.prepare(items[1]['id'],str(uuid4()))
    service.cancel(task['id'],service.get(task['id'])['revision'],str(uuid4()))
    assert service.save(prepared,Outcome(True,{})) is False
    assert summary(service.database,task['id'])=={'status':'cancelled','data':None}
    assert cases(service.database,task['id'])==[]
    with service.database.session() as s:assert list(s.scalars(select(BatchSummary)))==[]


@pytest.mark.parametrize('failure',['local','three_attempts'])
def test_zero_success_all_errors_completes_without_qa(service,failure):
    task,items=setup(service)
    for item in items:
        if failure=='local':finish(service,item)
        else:
            for _ in range(3):
                prepared=service.prepare(item['id'],str(uuid4()))
                service.save(prepared,Outcome(False,error_category='CALL_ERROR',error_detail='测试调用失败',retry_after=0))
    data=summary(service.database,task['id'])['data']
    assert data['display']=={'pass_rate':None,'average_score':None,'error_rate':'100.00%'}
    assert len(data['alerts'])==1 and data['alerts'][0]['kind']=='error'
    assert service.get(task['id'])['state']=='completed' and not data['batch_passed']
    assert all(i['stage']=='evaluation' for i in service.get(task['id'])['items'])
    assert all(i['attempt_count']==(0 if failure=='local' else 3) for i in service.get(task['id'])['items'])


def test_retry_does_not_add_case_or_final_error(service):
    task,items=setup(service,1)
    for n in range(2):
        prepared=service.prepare(items[0]['id'],str(uuid4()))
        service.save(prepared,Outcome(False,error_category='PARSE_ERROR',error_detail='测试',retry_after=0))
    finish(service,items[0],evaluation())
    data=summary(service.database,task['id'])['data']
    assert data['counts']['total']==data['counts']['succeeded']==1 and data['counts']['final_errors']==0
    assert service.get(task['id'])['items'][0]['attempt_count']==3


def test_summary_save_failure_rolls_back_last_result_and_local_resave(service):
    task,items=setup(service,1)
    with service.database.engine.begin() as c:c.exec_driver_sql("CREATE TRIGGER fail_summary BEFORE INSERT ON batch_summary BEGIN SELECT RAISE(ABORT,'test summary write failure'); END")
    prepared=service.prepare(items[0]['id'],str(uuid4()))
    from app.domain.model_contract import check_envelope
    from test_model_contract import envelope
    outcome=check_envelope('evaluation',envelope(json.dumps(evaluation())),prepared['request']['history'],prepared['request']['target_reply'])
    with pytest.raises(SQLAlchemyError):service.save(prepared,outcome)
    with service.database.session() as s:
        assert s.get(BatchSummary,task['id']) is None
        assert s.get(ExecutionItem,items[0]['id']).state=='running'
    with service.database.engine.begin() as c:c.exec_driver_sql('DROP TRIGGER fail_summary')
    assert service.save(prepared,outcome) and service.save(prepared,outcome)
    assert summary(service.database,task['id'])['data']['batch_passed']
    assert service.get(task['id'])['items'][0]['attempt_count']==1


def test_missing_qa_hook_blocks_instead_of_false_done(service):
    task,items=setup(service,1)
    value=missing();value['knowledge_gaps'][0]['snippet']='问题0'
    with pytest.raises(ServiceError) as e:finish(service,items[0],value)
    assert e.value.code=='DEPENDENCY_NOT_READY'
    assert service.get(task['id'])['state']=='running'
    with service.database.session() as s:assert s.get(BatchSummary,task['id']) is None


class QForTest:
    def item_saved(self,*args):return []
    def phase_finished(self,s,task):
        if task.phase=='qa_generation':return Transition('done',[])
        item=s.scalar(select(ExecutionItem).where(ExecutionItem.task_id==task.id))
        from app.domain.execution import ItemSpec
        return Transition('qa_generation',[ItemSpec(item.case_id,'standard_question','original','test-gap',{'messages':[]})])


def test_metrics_available_during_qa_and_q_failure_does_not_change_them(service):
    service.hooks=EvaluationHooks(MetricsHooks(QForTest()))
    task=service.start(build(service,1),str(uuid4()));item=service.pending()[0]
    value=missing();value['knowledge_gaps'][0]['snippet']='问题0';finish(service,item,value)
    before=summary(service.database,task['id'])
    assert before['status']=='available' and service.get(task['id'])['phase']=='qa_generation'
    with pytest.raises(ServiceError):service.cancel(task['id'],service.get(task['id'])['revision'],str(uuid4()))
    q=service.pending()[0]
    for _ in range(3):
        prepared=service.prepare(q['id'],str(uuid4()));service.save(prepared,Outcome(False,error_category='CALL_ERROR',retry_after=0))
    assert summary(service.database,task['id'])==before
    assert before['data']['counts']['final_errors']==0


def test_historical_terminal_results_backfill_once_and_api_contract(service):
    from test_evaluation import DoneForTest
    service.hooks=EvaluationHooks(DoneForTest())
    task=service.start(build(service,2),str(uuid4()))
    for i,item in enumerate(service.pending()):finish(service,item,bad() if i==0 else None)
    data=summary(service.database,task['id'])
    assert summary(service.database,task['id'])==data
    from app.db.database import Database
    # 关闭原锁，以本地TestClient重启同库；没有模型transport，不重调成功项。
    service.database.stop()
    with TestClient(create_app(service.database.directory)) as client:
        detail=client.get(f"/api/v1/tasks/{task['id']}")
        assert detail.status_code==200 and detail.json()['data']['summary']==data
        assert client.get('/api/v1/tasks').json()['data'][0]['summary']==data
        for alert in data['data']['alerts']:
            response=client.get(alert['target']['path'],params={'filter':alert['target']['filter']})
            assert response.status_code==200
            assert {r['case_id'] for r in response.json()['data']}==set(alert['problem_case_ids'])
            for row in response.json()['data']:
                response=client.get(f"/api/v1/tasks/{task['id']}/cases/{row['case_id']}")
                assert response.status_code==200 and response.json()['data']['case_id']==row['case_id']
                assert response.json()['data']['history']
                assert 'history' not in row and 'original_reply' not in row
                assert (row['evaluation'] is None)!=(row['final_error'] is None)
        assert client.get(f"/api/v1/tasks/{task['id']}/cases?filter=unknown").status_code==422
        assert client.get(f"/api/v1/tasks/{task['id']}/cases/{uuid4()}").status_code==404
    service.database.start()

@pytest.mark.parametrize('n,errors,badcount,quality,errorwarn,passed',[(100,5,0,False,False,True),(100,6,0,False,True,False),(20,0,1,False,False,False)])
def test_persisted_exact_thresholds_and_no_warning_badcase(service,n,errors,badcount,quality,errorwarn,passed):
    task,items=setup(service,n)
    for i,item in enumerate(items):finish(service,item,None if i>=n-errors else bad() if i<badcount else evaluation())
    m=summary(service.database,task['id'])['data']
    assert (m['quality_warning'],m['error_warning'],m['batch_passed'])==(quality,errorwarn,passed)
    assert len(m['alerts'])==int(quality)+int(errorwarn)


def test_unavailable_results_never_become_fake_success_metrics(service):
    from test_task_execution import plan
    task=service.start(plan(service,1),str(uuid4()))
    prepared=service.prepare(service.pending()[0]['id'],str(uuid4()))
    service.save(prepared,Outcome(True,{}))
    with pytest.raises(ServiceError) as e:summary(service.database,task['id'])
    assert e.value.code=='RESULT_INCONSISTENT'
    with service.database.session() as s:assert s.get(BatchSummary,task['id']) is None


def test_task_not_found_and_wrong_filter_are_explicit(service):
    with pytest.raises(ServiceError) as e:summary(service.database,str(uuid4()))
    assert e.value.status==404
    task,_=setup(service)
    with pytest.raises(ServiceError) as e:cases(service.database,task['id'],'unknown')
    assert e.value.status==422


def test_summary_never_uses_rounded_individual_composites(service):
    task,items=setup(service,2)
    one=bad();one['scores']['accuracy']['score']=5;one['scores']['intent']['score']=5;one['scores']['service']['score']=3
    two=bad();two['scores']['accuracy']['score']=5;two['scores']['intent']['score']=5;two['scores']['service']['score']=1
    finish(service,items[0],one);finish(service,items[1],two)
    m=summary(service.database,task['id'])['data']
    assert m['raw']['average_score']=={'numerator':24,'denominator':6}
    assert m['display']['average_score']=='4.00' and m['counts']['badcase']==2

@pytest.mark.parametrize('value',[None,'qualified','other_badcase'])
def test_no_eligible_never_invokes_qa_constructor(service,value):
    class Forbidden:
        def phase_finished(self,*args):raise AssertionError('无eligible不能调用Q构造器')
    service.hooks=EvaluationHooks(MetricsHooks(Forbidden()))
    task=service.start(build(service,1),str(uuid4()));item=service.pending()[0]
    finish(service,item,None if value is None else evaluation() if value=='qualified' else bad())
    assert service.get(task['id'])['state']=='completed'
    assert summary(service.database,task['id'])['status']=='available'
