"""013真实SQLite及调度契约；模型响应是确定性替身，不证明语义质量。"""
import asyncio
import json
from dataclasses import replace
from uuid import uuid4
import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from app.services.evaluation import EvaluationBuilder, EvaluationHooks, results
from app.services.batch_metrics import MetricsHooks, summary
from app.services.qa_generation import QAHooks, generations, eligible_gaps
from app.services.imports import ServiceError
from app.prompts.standard_question import prompt_config
from app.domain.model_contract import check_envelope
from app.models.execution import Task, Attempt, ExecutionItem
from app.models.qa import QA
from app.runtime.executor import Executor
from app.model_client.deepseek import DeepSeekTransport
from test_task_execution import service, until
from test_evaluation import save_value
from test_model_contract import missing, evaluation, envelope


def start(service,size=1):
    service.hooks=EvaluationHooks(MetricsHooks(QAHooks()))
    upload,rule,kb,_=service.test_sources
    plan=EvaluationBuilder(service.database,prompt_config())({'upload_id':upload,'rule_version_id':rule,'kb_version_id':kb})
    plan=replace(plan,case_ids=plan.case_ids[:size],items=plan.items[:size])
    return service.start(plan,str(uuid4())),plan


def gap_value(question='问题0',count=1,reason='两资料均无答案'):
    value=missing()
    value['knowledge_gaps']=[{'gap':f'缺失点{i}','snippet':question,'reason':reason} for i in range(count)]
    return value


def qsave(service,item,raw='{"standard_question":"具体时限是什么？"}'):
    prepared=service.prepare(item['id'],str(uuid4()))
    outcome=check_envelope('standard_question',envelope(raw),prepared['request']['history'],'')
    service.save(prepared,outcome)
    return prepared,outcome


@pytest.mark.parametrize('kind', ['primary','secondary','nonknowledge','conflict','conflict_compliance','qualified'])
def test_real_transition_eligibility(service,kind):
    task,_=start(service)
    value=gap_value()
    if kind=='secondary':value.update(primary_cause='违反平台规则，做出不当承诺',secondary_causes=['知识库缺少对应信息'])
    if kind=='nonknowledge':value.update(primary_cause='回复内容敷衍',knowledge_gaps=[])
    if kind=='conflict':value.update(primary_cause='其他／证据不足',has_material_conflict=True,knowledge_gaps=[])
    if kind=='conflict_compliance':value.update(primary_cause='违反平台规则，做出不当承诺',secondary_causes=['知识库缺少对应信息'],has_material_conflict=True)
    if kind=='qualified':value=evaluation()
    if kind in ('secondary','conflict','conflict_compliance'):value['scores']['accuracy']['score']=1
    _,outcome=save_value(service,service.pending()[0],value)
    assert outcome.success
    actual=service.get(task['id'])
    allowed=kind in ('primary','secondary')
    assert (actual['phase']=='qa_generation')==allowed
    assert len(service.pending())==int(allowed)
    if not allowed:assert actual['state']=='completed' and generations(service.database,task['id'])['drafts']==[]


def test_points_separate_sources_empty_answer_exact_evidence_and_window(service):
    task,plan=start(service,2)
    by_id={item['id']:item['case_id'] for item in service.get(task['id'])['items']}
    eitems=sorted(service.pending(),key=lambda item:plan.case_ids.index(by_id[item['id']]))
    save_value(service,eitems[0],gap_value('问题0',2,'字'*47+'👩\u200d💻'))
    assert service.get(task['id'])['phase']=='evaluating'
    save_value(service,eitems[1],gap_value('问题1',1))
    assert len(service.pending())==3
    before=results(service.database,task['id']); metrics=summary(service.database,task['id'])
    with pytest.raises(ServiceError):service.start(plan,str(uuid4()))
    with pytest.raises(ServiceError) as error:service.cancel(task['id'],service.get(task['id'])['revision'],str(uuid4()))
    assert error.value.code=='CANCEL_FORBIDDEN'
    for item in service.pending():
        prepared,outcome=qsave(service,item)
        assert outcome.success
        data=json.loads(prepared['request']['messages'][1]['content'])
        assert set(data)=={'original_question','original_reply','history','knowledge_gap'}
        assert set(data['knowledge_gap'])=={'gap','snippet','reason'}
        assert prepared['request']['messages'][0]['content']==prompt_config().full_prompt
    drafts=generations(service.database,task['id'])['drafts']
    assert len(drafts)==len({x['id'] for x in drafts})==len({x['gap_id'] for x in drafts})==3
    assert len({x['standard_question'] for x in drafts})==1
    assert all(x['answer']=='' and x['review_state']=='pending_review' and x['revision']==0 for x in drafts)
    saved={gap['id']:gap for row in before['results'] for gap in row['knowledge_gaps']}
    for row in drafts:
        gap=saved[row['gap_id']]
        assert row['knowledge_gap']=={key:gap[key] for key in ('gap','snippet','reason','location')}
        assert row['original_question']==row['history'][-1]['content']
        assert row['trace']['rule_version_id']==plan.rule_version_id
    assert results(service.database,task['id'])==before and summary(service.database,task['id'])==metrics
    assert service.get(task['id'])['state']=='completed'
    assert service.start(plan,str(uuid4()))['state']=='running'


@pytest.mark.parametrize('raw', ['{}','not-json','{"standard_question":""}','{"standard_question":"问","answer":"擅自补答"}'])
def test_three_failures_are_separate_not_reviewable_and_preserve_evaluation(service,raw):
    task,_=start(service);save_value(service,service.pending()[0],gap_value())
    before=results(service.database,task['id']);metrics=summary(service.database,task['id'])
    for _ in range(3):qsave(service,service.pending(ignore_due=True)[0],raw)
    output=generations(service.database,task['id'])
    assert output['drafts']==output['pending']==[] and len(output['failures'])==1
    assert output['failures'][0]['attempt_count']==3 and not output['failures'][0]['reviewable']
    assert service.get(task['id'])['state']=='completed' and service.pending()==[]
    assert results(service.database,task['id'])==before and summary(service.database,task['id'])==metrics


def test_qa_save_failure_rolls_back_then_same_attempt_resaves_idempotently(service):
    task,_=start(service);save_value(service,service.pending()[0],gap_value())
    prepared=service.prepare(service.pending()[0]['id'],str(uuid4()))
    outcome=check_envelope('standard_question',envelope('{"standard_question":"问？"}'),prepared['request']['history'],'')
    with service.database.engine.begin() as connection:connection.execute(text("CREATE TRIGGER fail_qa BEFORE INSERT ON qa BEGIN SELECT RAISE(ABORT,'模拟草稿保存失败'); END"))
    with pytest.raises(SQLAlchemyError):service.save(prepared,outcome)
    with service.database.session() as session:
        assert list(session.scalars(select(QA)))==[] and session.get(Attempt,prepared['id']).state=='prepared'
    with service.database.engine.begin() as connection:connection.execute(text('DROP TRIGGER fail_qa'))
    service.save(prepared,outcome);service.save(prepared,outcome)
    drafts=generations(service.database,task['id'])['drafts']
    assert len(drafts)==1 and drafts[0]['attempt_count']==1


def test_recovery_success_retained_unknown_attempts_exhaust_and_frozen_prompt(service,monkeypatch):
    task,_=start(service);save_value(service,service.pending()[0],gap_value(count=2))
    one,two=service.pending();qsave(service,one)
    first=generations(service.database,task['id'])['drafts'][0]
    def broken():raise OSError('最新Prompt不可读')
    monkeypatch.setattr('app.prompts.standard_question.prompt_config',broken)
    requests=[]
    for _ in range(3):
        prepared=service.prepare(service.pending(ignore_due=True)[0]['id'],str(uuid4()));requests.append(prepared['request'])
        service.recover()
    value=generations(service.database,task['id'])
    assert value['drafts']==[first] and value['failures'][0]['attempt_count']==3
    assert requests[0]==requests[1]==requests[2]
    assert service.get(task['id'])['state']=='completed'


def test_cancel_before_transition_discards_late_e_and_no_qa(service):
    task,_=start(service)
    prepared=service.prepare(service.pending()[0]['id'],str(uuid4()))
    outcome=check_envelope('evaluation',envelope(json.dumps(gap_value())),prepared['request']['history'],prepared['request']['target_reply'])
    service.cancel(task['id'],service.get(task['id'])['revision'],str(uuid4()))
    assert not service.save(prepared,outcome)
    assert generations(service.database,task['id'])=={'drafts':[],'failures':[],'pending':[]}
    assert results(service.database,task['id'])['results']==[]


@pytest.mark.parametrize('kind,state,phase',[('effect','running','evaluating'),('ordinary','cancelled','evaluating'),('ordinary','running','qa_generation')])
def test_forbidden_task_selector_returns_no_gaps(service,kind,state,phase):
    task,_=start(service)
    with service.database.session() as session:
        row=session.get(Task,task['id']);row.kind=kind;row.state=state;row.phase=phase
        assert eligible_gaps(session,row)==[]


@pytest.mark.parametrize('success_on',[1,3,None])
def test_sdk_executor_actual_call_count_and_partial_qa_failure(service,success_on):
    async def run():
        task,_=start(service);counts={'E':0,'Q':0};active=0;maximum=0
        async def handler(request):
            nonlocal active,maximum
            data=json.loads(json.loads(request.content)['messages'][1]['content'])
            stage='Q' if 'knowledge_gap' in data else 'E';counts[stage]+=1
            active+=1;maximum=max(maximum,active);await asyncio.sleep(.01);active-=1
            raw=json.dumps(gap_value()) if stage=='E' else ('{"standard_question":"时限是什么？"}' if success_on==counts['Q'] else '{}')
            return httpx.Response(200,headers={'Retry-After':'0'},json=envelope(raw))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        runner=Executor(service,client,scan_interval=.005);await runner.start()
        try:
            await until(lambda:service.get(task['id'])['state']=='completed')
            assert counts=={'E':1,'Q':success_on or 3} and maximum<=3
            output=generations(service.database,task['id'])
            assert len(output['drafts'])==int(success_on is not None)
            assert len(output['failures'])==int(success_on is None)
            assert len(results(service.database,task['id'])['results'])==1
        finally:await runner.stop();await client.close()
    asyncio.run(run())


def test_three_concurrent_qa_partial_call_error_and_success_preserve_e(service):
    async def run():
        task,_=start(service);save_value(service,service.pending()[0],gap_value(count=5))
        before=results(service.database,task['id']);metrics=summary(service.database,task['id'])
        calls={};active=0;maximum=0
        async def handler(request):
            nonlocal active,maximum
            data=json.loads(json.loads(request.content)['messages'][1]['content'])
            assert 'knowledge_gap' in data
            gap=data['knowledge_gap']['gap'];calls[gap]=calls.get(gap,0)+1
            active+=1;maximum=max(maximum,active);await asyncio.sleep(.04);active-=1
            if gap=='缺失点0':return httpx.Response(500,headers={'Retry-After':'0'},json={'error':{'message':'明确测试故障'}})
            return httpx.Response(200,json=envelope('{"standard_question":"时限是多少？"}'))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        runner=Executor(service,client,scan_interval=.005);await runner.start()
        try:
            await until(lambda:service.get(task['id'])['state']=='completed')
            output=generations(service.database,task['id'])
            assert maximum==3 and calls=={'缺失点0':3,**{f'缺失点{i}':1 for i in range(1,5)}}
            assert len(output['drafts'])==4 and len(output['failures'])==1
            assert output['failures'][0]['error_category']=='CALL_ERROR'
            assert results(service.database,task['id'])==before and summary(service.database,task['id'])==metrics
        finally:await runner.stop();await client.close()
    asyncio.run(run())


def test_invalid_gap_reason_51_rejected_upstream_without_new_evidence_call(service):
    task,_=start(service)
    for _ in range(3):
        item=service.pending(ignore_due=True)[0]
        _,outcome=save_value(service,item,gap_value(reason='字'*48+'👩\u200d💻'))
        assert not outcome.success and outcome.error_category=='INCOMPLETE_RESULT'
    output=generations(service.database,task['id'])
    assert output=={'drafts':[],'failures':[],'pending':[]}
    actual=service.get(task['id'])
    assert actual['state']=='completed' and len(actual['items'])==1 and actual['items'][0]['attempt_count']==3


def test_success_without_qa_is_reported_as_inconsistent_not_pending(service):
    task,_=start(service);save_value(service,service.pending()[0],gap_value())
    qsave(service,service.pending()[0])
    with service.database.engine.begin() as connection:connection.execute(text('DELETE FROM qa'))
    with pytest.raises(ServiceError) as error:generations(service.database,task['id'])
    assert error.value.code=='RESULT_INCONSISTENT'
