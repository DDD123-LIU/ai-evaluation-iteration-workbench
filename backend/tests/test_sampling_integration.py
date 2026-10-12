"""017真实SQLite终态、标记、故障及历史恢复。"""
import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.models.sampling import SamplingRun, Draw, HumanMark
from app.models.execution import RuntimeSlot, Task
from app.services.sampling import SamplingService
from app.services.imports import ServiceError
from test_task_execution import service
from test_effects import setup_effect, complete, send


def ready(service):
    task,_,_=setup_effect(service)
    complete(service)
    return task['id'], SamplingService(service.database)


def mark(svc,task,values=None,revision=0,operation=None):
    case=svc.get(task)['draws'][0]['case_id']
    return svc.mark(task,case,values or dict.fromkeys(('accuracy','intent','service'),'持平'),revision,operation or str(uuid4()))


def test_atomic_terminal_sampling_and_release(service):
    task,svc=ready(service)
    with service.database.session() as session:
        assert session.get(SamplingRun,task)
        assert session.get(Task,task).state=='completed'
        assert session.get(RuntimeSlot,1).task_id is None
    row=svc.get(task)
    assert row['population_size']==row['target_size']==row['valid_count']==1
    assert row['status']=='pending_confirmation' and row['marking_allowed']
    assert row['draws'][0]['mark']['accuracy'] is None


def test_partial_marks_full_marks_worse_and_replay(service):
    task,svc=ready(service)
    op=str(uuid4())
    partial={'accuracy':'改善','intent':None,'service':None}
    first,_=mark(svc,task,partial,operation=op)
    assert first['status']=='pending_confirmation'
    assert mark(svc,task,partial,operation=op)==(first,False)
    with pytest.raises(ServiceError) as err: mark(svc,task,revision=0)
    assert err.value.code=='REVISION_CONFLICT'
    full,_=mark(svc,task,revision=1)
    assert full['status']=='passed'
    worse,_=mark(svc,task,{'accuracy':'变差','intent':None,'service':None},2)
    assert worse['status']=='not_passed'
    with pytest.raises(ServiceError) as err: mark(svc,task,operation=op)
    assert err.value.code=='OPERATION_CONFLICT'


def test_refresh_and_database_restart_keep_draw_and_progress(service):
    task,svc=ready(service)
    first,_=mark(svc,task,{'accuracy':'改善','intent':None,'service':'持平'})
    service.database.stop(); service.database.start()
    service.recover()
    assert svc.get(task)==first
    assert svc.get(task)==first


def test_metadata_failure_preserves_trace_insufficient_and_forbids_mark(service):
    task,_,_=setup_effect(service)
    for item in service.pending(): send(service,item,metadata={'system_fingerprint':None})
    complete(service)
    svc=SamplingService(service.database); row=svc.get(task['id'])
    assert row['population_size']==row['target_size']==1 and row['valid_count']==0
    assert row['status']=='validation_failed'
    assert row['draws'][0]['unusable_reasons'] and not row['marking_allowed']
    with pytest.raises(ServiceError) as err: mark(svc,task['id'])
    assert err.value.code=='INSUFFICIENT_SAMPLES'
    service.database.stop(); service.database.start()
    assert svc.get(task['id'])==row


def test_pending_cancelled_and_wrong_task_do_not_draw(service):
    task,_,_=setup_effect(service); svc=SamplingService(service.database)
    assert svc.get(task['id'])['status']=='automatic_pending'
    with pytest.raises(ServiceError):svc.mark(task['id'],service.test_sources[-1][0],dict.fromkeys(('accuracy','intent','service'),'持平'),0,str(uuid4()))
    service.cancel(task['id'],service.get(task['id'])['revision'],str(uuid4()))
    assert svc.get(task['id'])['status']=='cancelled'
    with service.database.session() as session: assert session.get(SamplingRun,task['id']) is None
    with pytest.raises(ServiceError):svc.get(str(uuid4()))


def test_unselected_case_invalid_mark_and_original_save(service):
    task,svc=ready(service)
    with pytest.raises(ServiceError) as err:
        svc.mark(task,str(uuid4()),dict.fromkeys(('accuracy','intent','service'),'持平'),0,str(uuid4()))
    assert err.value.code=='NOT_SELECTED'
    with pytest.raises(ServiceError):mark(svc,task,{'accuracy':'自动通过'})
    result,_=mark(svc,task)
    repeat,_=mark(svc,task,revision=1)
    assert repeat==result


def test_mark_flush_failure_atomic_rollback(service,monkeypatch):
    task,svc=ready(service); before=svc.get(task)
    original=Session.flush
    def fail(session,*args,**kwargs):
        if any(isinstance(row,HumanMark) for row in session.dirty):
            raise OperationalError('test',{},Exception('保存失败'))
        return original(session,*args,**kwargs)
    with monkeypatch.context() as context:
        context.setattr(Session,'flush',fail)
        with pytest.raises(ServiceError) as err:mark(svc,task)
    assert err.value.code=='STORAGE_UNAVAILABLE' and svc.get(task)==before


@pytest.mark.parametrize('committed',[False,True])
def test_unknown_mark_commit_original_operation_recovers(service,monkeypatch,committed):
    task,svc=ready(service); op=str(uuid4()); original=Session.commit
    def fail(session):
        if committed: original(session)
        raise OperationalError('test',{},Exception('提交回执丢失'))
    with monkeypatch.context() as context:
        context.setattr(Session,'commit',fail)
        with pytest.raises(ServiceError) as err:mark(svc,task,operation=op)
    assert err.value.code=='COMMIT_UNKNOWN'
    result,created=mark(svc,task,operation=op)
    assert result['status']=='passed' and created is not committed
    assert svc.get(task)==result


def test_concurrent_reads_same_draw_and_revision_conflict(service):
    task,svc=ready(service)
    with ThreadPoolExecutor(2) as pool: rows=list(pool.map(lambda _:svc.get(task),range(2)))
    assert rows[0]==rows[1]
    def save(_):
        try:return mark(svc,task)[0]['status']
        except ServiceError as err:return err.code
    with ThreadPoolExecutor(2) as pool: results=list(pool.map(save,range(2)))
    assert sorted(results)==['REVISION_CONFLICT','passed']


def test_history_missing_run_first_read_persists_once(service):
    task,svc=ready(service)
    with service.database.session() as session,session.begin():session.delete(session.get(SamplingRun,task))
    first=svc.get(task)
    assert svc.get(task)==first


def test_terminal_sampling_failure_keeps_window_and_last_result_uncommitted(service,monkeypatch):
    task,_,_=setup_effect(service)
    for item in service.pending(ignore_due=True):send(service,item)
    while len(service.pending(ignore_due=True))>1:
        send(service,service.pending(ignore_due=True)[0])
    original=Session.flush
    last=service.pending(ignore_due=True)[0]
    prepared=service.prepare(last['id'],str(uuid4()))
    from app.domain.model_contract import check_envelope
    from test_model_contract import envelope,evaluation
    outcome=check_envelope('evaluation',envelope(json.dumps(evaluation())),prepared['request']['history'],prepared['request']['target_reply'])
    def fail(session,*args,**kwargs):
        if any(isinstance(row,SamplingRun) for row in session.new):raise OperationalError('test',{},Exception('抽检保存失败'))
        return original(session,*args,**kwargs)
    with monkeypatch.context() as context:
        context.setattr(Session,'flush',fail)
        with pytest.raises(OperationalError):service.save(prepared,outcome)
    with service.database.session() as session:
        assert session.get(Task,task['id']).state=='running'
        assert session.get(RuntimeSlot,1).task_id==task['id']
        assert session.get(SamplingRun,task['id']) is None
    # 当前进程沿009原响应重存，不新增模型请求或计次。
    service.save(prepared,outcome)
    assert SamplingService(service.database).get(task['id'])['status']=='pending_confirmation'
    assert service.get(task['id'])['state']=='completed'
    assert all(item['attempt_count']==1 for item in service.get(task['id'])['items'])


def test_real_multiple_cases_failure_replacement_and_independent_badcase_conclusion(service,monkeypatch):
    from test_qa_generation_integration import start,gap_value,qsave
    from test_evaluation import save_value
    from app.services.qa_generation import generations
    from app.services.qa_review import QAReviewService
    from test_qa_review_integration import ready as approve,selection
    from test_supplements import new_kb
    from app.services.supplements import SupplementService
    from app.services.effects import EffectBuilder,EffectHooks,detail
    import app.domain.sampling as domain
    ordinary,_=start(service,size=5)
    for item in service.pending():
        preview=service.preview(item['id'])
        question=preview['request']['history'][-1]['content']
        save_value(service,item,gap_value(question=question))
    for item in service.pending():qsave(service,item)
    review=QAReviewService(service.database)
    approved=[approve(review,row['id']) for row in generations(service.database,ordinary['id'])['drafts']]
    event,_=selection(review,approved)
    record,_=SupplementService(service.database).save(new_kb(service),ordinary['id'],
        [row['id'] for row in review.detail(event['id'])['items']],True,str(uuid4()))
    service.hooks=EffectHooks()
    plan=EffectBuilder(service.database)(record['id'])
    task=service.start(plan,str(uuid4()))
    first=plan.case_ids[0]
    for item in service.pending():
        from app.models.execution import ExecutionItem
        with service.database.session() as session: case_id=session.get(ExecutionItem,item['id']).case_id
        send(service,item,metadata={'system_fingerprint':None} if case_id==first else None)
    # 固定测试替身选择首项，生产random.sample不替换；确保真正走失败补抽路径。
    original=domain.draw_population
    monkeypatch.setattr('app.services.sampling.draw_population',lambda rows,sampler:original(rows,lambda values,k:values[:k]))
    for item in service.pending():
        preview=service.preview(item['id'])
        send(service,item,gap_value(question=preview['request']['history'][-1]['content']))
    svc=SamplingService(service.database); row=svc.get(task['id'])
    assert row['population_size']==5 and row['target_size']==1 and row['valid_count']==1
    assert row['draws'][0]['case_id']==first and row['draws'][0]['unusable_reasons']
    assert row['draws'][1]['kind']=='replacement' and row['draws'][1]['case_id']!=first
    final,_=svc.mark(task['id'],row['draws'][1]['case_id'],dict.fromkeys(('accuracy','intent','service'),'持平'),0,str(uuid4()))
    assert final['status']=='passed'
    data=detail(service.database,task['id'])
    assert data['human_effect_conclusion']=='passed'
    assert all(case['new']['evaluation']['is_badcase'] for case in data['cases'])
    before=final
    service.database.stop();service.database.start();service.recover()
    assert svc.get(task['id'])==before


def test_upgrade_from_016_preserves_results_and_rebuilds_missing_sampling(service):
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    from app.services.effects import detail
    task,svc=ready(service)
    before=detail(service.database,task)
    config=Config();config.set_main_option('script_location',str(Path(__file__).resolve().parents[1]/'migrations'))
    with service.database.engine.begin() as connection:
        config.attributes['connection']=connection;command.downgrade(config,'0008_effects')
    with service.database.engine.begin() as connection:
        config.attributes['connection']=connection;command.upgrade(config,'head')
    rebuilt=svc.get(task)
    assert rebuilt['status']=='pending_confirmation'
    assert detail(service.database,task)==before
