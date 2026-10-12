"""014 SQLite真实人工事务/不可变快照/故障/并发，不调用模型。"""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import csv
import io
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from alembic import command
from alembic.config import Config
from pathlib import Path
from app.models.qa import QA
from app.models.exports import ExportEvent, ExportItem, QAWriteReceipt
from app.models.imports import CaseRecord, OperationCommit
from app.services.qa_review import QAReviewService
from app.services.qa_generation import generations
from app.services.imports import ServiceError
from test_task_execution import service
from test_evaluation import save_value
from test_qa_generation_integration import start, gap_value, qsave


def drafts(service,count=2):
    task,_=start(service)
    save_value(service,service.pending()[0],gap_value(count=count))
    for item in service.pending():qsave(service,item)
    return task, generations(service.database,task['id'])['drafts']


def ready(review,identifier,question='标准问',answer='人工答案'):
    row,_=review.edit(identifier,question,answer,0,str(uuid4()))
    return review.approve(identifier,row['revision'],True,str(uuid4()))[0]


def selection(review,rows,operation_id=None):
    return review.export([x['id'] for x in rows],{x['id']:x['revision'] for x in rows},operation_id or str(uuid4()))


def test_manual_confirmation_required_missing_answer_and_edit_state(service):
    task,rows=drafts(service,1);review=QAReviewService(service.database);identifier=rows[0]['id']
    with pytest.raises(ServiceError) as error:review.approve(identifier,0,True,str(uuid4()))
    assert error.value.code=='QA_INCOMPLETE'
    row,_=review.edit(identifier,'问','本人填写答案',0,str(uuid4()))
    with pytest.raises(ServiceError) as error:review.approve(identifier,row['revision'],False,str(uuid4()))
    assert error.value.code=='CONFIRM_REQUIRED'
    approved=review.approve(identifier,row['revision'],True,str(uuid4()))[0]
    assert approved['review_state']=='approved'
    unchanged=review.edit(identifier,'问','本人填写答案',approved['revision'],str(uuid4()))[0]
    assert unchanged==approved
    assert generations(service.database,task['id'])['drafts'][0]['review_state']=='approved'
    changed=review.edit(identifier,'问','人工答案修订',approved['revision'],str(uuid4()))[0]
    assert changed['review_state']=='pending_review' and changed['revision']==approved['revision']+1
    with pytest.raises(ServiceError):selection(review,[changed])
    again=review.approve(identifier,changed['revision'],True,str(uuid4()))[0]
    assert selection(review,[again])[1]


@pytest.mark.parametrize('field',['question','answer','source_case_number','category'])
def test_each_required_field_and_fixed_category_block_approval_and_export(service,field):
    _,rows=drafts(service,1);review=QAReviewService(service.database)
    good=ready(review,rows[0]['id'])
    with service.database.session() as session,session.begin():
        qa=session.get(QA,good['id'])
        if field=='source_case_number':session.get(CaseRecord,rows[0]['case_id']).csv_case_id=' '
        else:setattr(qa,field,' ' if field!='category' else '其他／证据不足')
    for action in [lambda:review.approve(good['id'],good['revision'],True,str(uuid4())),lambda:selection(review,[good])]:
        with pytest.raises(ServiceError) as error:action()
        assert error.value.code=='QA_INCOMPLETE'
    assert review.list_exports()==[]


def test_select_exact_set_repeat_and_A_B_immutable_with_pending_current(service):
    task,rows=drafts(service,3);review=QAReviewService(service.database)
    good=[ready(review,row['id'],f'标准问{i}',f'答案{i}\n逗号,及"引号"') for i,row in enumerate(rows)]
    chosen=good[:2];A,new=selection(review,chosen)
    assert new
    original=review.file(A['id'])[0];details=review.detail(A['id'])
    assert {x['qa_id'] for x in details['items']}=={x['id'] for x in chosen}
    parsed=list(csv.reader(io.StringIO(original.decode('utf-8-sig'),newline='')))
    assert parsed[1:]==[[x[k] for k in ('question','answer','source_case_number','category')] for x in details['items']]
    repeat,_=selection(review,chosen)
    assert repeat['id']!=A['id'] and review.file(repeat['id'])[0]==original
    first=chosen[0];changed=review.edit(first['id'],'修订标准问','修订答案',first['revision'],str(uuid4()))[0]
    assert review.detail(A['id'])==details and review.file(A['id'])[0]==original
    assert review.detail(A['id'])['items'][0]['source_batch_id']==task['id']
    approved=review.approve(first['id'],changed['revision'],True,str(uuid4()))[0]
    B,_=selection(review,[approved]);assert review.file(B['id'])[0]!=original
    review.edit(first['id'],'再次修改','还未确认',approved['revision'],str(uuid4()))
    assert review.file(A['id'])[0]==original and review.detail(A['id'])==details
    assert len(review.list_exports(task['id']))==3
    assert review.list_exports(str(uuid4()))==[]


def test_operation_replay_returns_original_revision_and_exact_export_no_new_event(service):
    _,rows=drafts(service,1);review=QAReviewService(service.database);identifier=rows[0]['id'];op=str(uuid4())
    saved,created=review.edit(identifier,'问','答案',0,op)
    assert created
    approved=review.approve(identifier,saved['revision'],True,str(uuid4()))[0]
    assert review.edit(identifier,'问','答案',0,op)==(saved,False)
    export_op=str(uuid4());original,_=selection(review,[approved],export_op)
    review.edit(identifier,'变化','变化',approved['revision'],str(uuid4()))
    assert selection(review,[approved],export_op)==(original,False)
    assert len(review.list_exports())==1
    with pytest.raises(ServiceError) as error:review.edit(identifier,'不同','答案',0,op)
    assert error.value.code=='OPERATION_CONFLICT'
    with pytest.raises(ServiceError):review.approve(identifier,0,True,op)


@pytest.mark.parametrize('kind',['empty','missing_revision','extra_revision','missing_qa','pending','stale'])
def test_invalid_selection_never_leaves_export(service,kind):
    _,rows=drafts(service,1);review=QAReviewService(service.database);good=ready(review,rows[0]['id'])
    ids=[good['id']];versions={good['id']:good['revision']}
    if kind=='empty':ids=[];versions={}
    if kind=='missing_revision':versions={}
    if kind=='extra_revision':versions[str(uuid4())]=0
    if kind=='missing_qa':ids=[str(uuid4())];versions={ids[0]:0}
    if kind=='pending':review.edit(good['id'],'编辑','编辑',good['revision'],str(uuid4()));versions[good['id']]+=1
    if kind=='stale':versions[good['id']]-=1
    with pytest.raises(ServiceError):review.export(ids,versions,str(uuid4()))
    assert review.list_exports()==[]


@pytest.mark.parametrize('table',['export_event','export_item','operation_commit','qa_write_receipt'])
def test_export_failure_rolls_back_everything_and_same_operation_can_retry(service,table):
    _,rows=drafts(service,2);review=QAReviewService(service.database);good=[ready(review,x['id']) for x in rows];op=str(uuid4())
    clause=' WHEN NEW.ordinal=2' if table=='export_item' else ''
    with service.database.engine.begin() as conn:conn.execute(text(f"CREATE TRIGGER fail_export BEFORE INSERT ON {table}{clause} BEGIN SELECT RAISE(ABORT,'模拟导出事务故障'); END"))
    with pytest.raises(ServiceError) as error:selection(review,good,op)
    assert error.value.commit_state=='not_committed' and error.value.code=='STORAGE_UNAVAILABLE'
    with service.database.session() as session:
        assert list(session.scalars(select(ExportEvent)))==list(session.scalars(select(ExportItem)))==[]
        assert session.get(OperationCommit,op) is None and session.get(QAWriteReceipt,op) is None
        assert all(session.get(QA,x['id']).review_state=='approved' for x in good)
    with service.database.engine.begin() as conn:conn.execute(text('DROP TRIGGER fail_export'))
    assert selection(review,good,op)[1]


def test_edit_receipt_failure_rolls_back_content_and_state(service):
    _,rows=drafts(service,1);review=QAReviewService(service.database);good=ready(review,rows[0]['id']);op=str(uuid4())
    with service.database.engine.begin() as conn:conn.execute(text("CREATE TRIGGER fail_receipt BEFORE INSERT ON qa_write_receipt BEGIN SELECT RAISE(ABORT,'故障'); END"))
    with pytest.raises(ServiceError):review.edit(good['id'],'新问','新答',good['revision'],op)
    with service.database.session() as session:
        qa=session.get(QA,good['id']);assert qa.question==good['question'] and qa.review_state=='approved' and qa.revision==good['revision']
    with service.database.engine.begin() as conn:conn.execute(text('DROP TRIGGER fail_receipt'))


@pytest.mark.parametrize('committed',[False,True])
def test_commit_confirmation_unknown_reads_original_operation(service,monkeypatch,committed):
    _,rows=drafts(service,1);review=QAReviewService(service.database);good=ready(review,rows[0]['id']);op=str(uuid4());original=Session.commit
    def uncertain(session):
        if committed:original(session)
        raise OperationalError('COMMIT',{},Exception('模拟提交确认丢失'))
    monkeypatch.setattr(Session,'commit',uncertain)
    with pytest.raises(ServiceError) as error:selection(review,[good],op)
    assert error.value.commit_state=='unknown' and error.value.resource_id==op
    monkeypatch.setattr(Session,'commit',original)
    result,created=selection(review,[good],op)
    assert created is (not committed) and len(review.list_exports())==1


def test_concurrent_edit_and_export_use_one_consistent_version(service):
    _,rows=drafts(service,1);review=QAReviewService(service.database);good=ready(review,rows[0]['id']);barrier=Barrier(2)
    def edit():
        barrier.wait();return review.edit(good['id'],'修改','修改',good['revision'],str(uuid4()))
    def export():
        barrier.wait()
        try:return selection(review,[good])[0]
        except ServiceError as error:return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(edit);b=pool.submit(export);a.result();outcome=b.result()
    if isinstance(outcome,dict):
        item=review.detail(outcome['id'])['items'][0]
        assert item['question']==good['question'] and item['answer']==good['answer'] and item['qa_revision']==good['revision']
    else:assert outcome=='REVISION_CONFLICT' and review.list_exports()==[]
    with pytest.raises(ServiceError) as error:review.edit(good['id'],'过期覆盖','过期',good['revision'],str(uuid4()))
    assert error.value.code=='REVISION_CONFLICT'


def test_incremental_migration_preserves_existing_qa_and_evidence(service):
    task,rows=drafts(service,1)
    config=Config();config.set_main_option('script_location',str(Path(__file__).resolve().parents[1]/'migrations'))
    with service.database.engine.begin() as conn:
        config.attributes['connection']=conn;command.downgrade(config,'0005_qa_generation')
    before=generations(service.database,task['id'])
    with service.database.engine.begin() as conn:
        config.attributes['connection']=conn;command.upgrade(config,'head')
    assert generations(service.database,task['id'])==before
    with service.database.engine.connect() as conn:
        assert conn.execute(text('PRAGMA foreign_key_check')).fetchall()==[]
        assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar()=='0009_sampling'


def test_export_across_source_batches_is_allowed_and_preserves_global_source(service):
    first,a=drafts(service,1);second,b=drafts(service,1);review=QAReviewService(service.database)
    good=[ready(review,x['id']) for x in [a[0],b[0]]]
    event,_=selection(review,good)
    snapshots=review.detail(event['id'])['items']
    assert len(snapshots)==2 and {x['source_batch_id'] for x in snapshots}=={first['id'],second['id']}
    assert [x['id'] for x in review.list_exports(first['id'])]==[event['id']]
    assert [x['id'] for x in review.list_exports(second['id'])]==[event['id']]


def test_duplicate_selected_ids_do_not_duplicate_snapshot_items(service):
    _,rows=drafts(service,1);review=QAReviewService(service.database);good=ready(review,rows[0]['id'])
    event,_=review.export([good['id'],good['id']],{good['id']:good['revision']},str(uuid4()))
    assert len(review.detail(event['id'])['items'])==1
