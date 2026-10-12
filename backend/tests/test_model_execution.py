"""010真实SDK＋009持久调度，业务hooks仅为测试替身。"""
import asyncio
import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select, text

from app.domain.execution import ConfigSpec, ItemSpec, Transition
from app.models.execution import Attempt, ExecutionItem
from app.runtime.executor import Executor
from app.model_client.deepseek import DeepSeekTransport, settings
from test_task_execution import service, plan, until
from test_model_contract import evaluation, envelope


def model_plan(service,size=1):
    original=plan(service,size)
    prompt='测试专用 json 输出结构：{}'
    configs=[ConfigSpec(stage,'model-contract-v1',version,prompt,'deepseek-flash',settings(stage),'DeepSeek-V4.1-Flash') for stage,version in [('evaluation','evaluation-v1'),('standard_question','standard-question-v1')]]
    items=[ItemSpec(x.case_id,'evaluation','original','',{'messages':[{'role':'system','content':prompt},{'role':'user','content':'{}'}],
        'history':[{'role':'user','content':'测试问题'}],'target_reply':'测试回复'}) for x in original.items]
    return replace(original,configs=configs,items=items)


@pytest.mark.parametrize('sequence,expected', [(['success'],1),(['parse','schema','success'],3),(['call','call','call'],3),(['schema','schema','schema'],3)])
def test_first_third_and_exhausted_no_fourth(service,sequence,expected):
    async def run():
        calls=[]
        async def handler(request):
            index=len(calls); calls.append(json.loads(request.content))
            if sequence[index]=='call': return httpx.Response(503,headers={'Retry-After':'0'},json={'error':{'message':'故障'}})
            content='bad-json' if sequence[index]=='parse' else '{}' if sequence[index]=='schema' else json.dumps(evaluation())
            return httpx.Response(200,headers={'Retry-After':'0'},json=envelope(content))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        runner=Executor(service,client,scan_interval=.005)
        task=service.start(model_plan(service),str(uuid4()))
        await runner.start()
        try:
            await until(lambda: service.get(task['id'])['state']=='completed')
            await asyncio.sleep(.02)
            result=service.get(task['id'])
            assert len(calls)==expected
            assert result['items'][0]['attempt_count']==expected
            assert result['items'][0]['state']==('succeeded' if sequence[-1]=='success' else 'final_failed')
            with service.database.session() as s:
                saved=list(s.scalars(select(Attempt)))
                assert len(saved)==expected
                assert all(x.response_envelope_json for x in saved)
        finally: await runner.stop(); await client.close()
    asyncio.run(run())


def test_final_case_sets_mutually_exclusive_and_badcase_does_not_retry(service):
    async def run():
        p=model_plan(service,3)
        # 为测试分派，在不增加模型协议字段的本地来源字段记录角色。
        items=[replace(x,request={**x.request,'target_reply':str(index),'messages':[x.request['messages'][0],{'role':'user','content':json.dumps({'test_index':index})}]}) for index,x in enumerate(p.items)]
        p=replace(p,items=items)
        calls=[]
        async def handler(request):
            calls.append(request)
            index=json.loads(json.loads(request.content)['messages'][1]['content'])['test_index']
            value=evaluation()
            if index==1:
                value['scores']['accuracy']['score']=3
                value['primary_cause']='其他／证据不足'
            content='{}' if index==2 else json.dumps(value)
            return httpx.Response(200,headers={'Retry-After':'0'},json=envelope(content))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        runner=Executor(service,client,scan_interval=.005)
        task=service.start(p,str(uuid4()))
        await runner.start()
        try:
            await until(lambda: service.get(task['id'])['state']=='completed')
            value=service.get(task['id']); success={x['case_id'] for x in value['items'] if x['state']=='succeeded'}
            failures={x['case_id'] for x in value['items'] if x['state']=='final_failed'}
            assert success.isdisjoint(failures) and len(success|failures)==3 and len(success)==2 and len(failures)==1
            assert len(calls)==5
            assert all(x['attempt_count']==1 for x in value['items'] if x['state']=='succeeded')
            from app.services.model_results import case_outcomes
            persisted=case_outcomes(service.database,task['id'])
            assert persisted['eligible'] and persisted['input_count']==3
            assert len(persisted['successes'])==2 and len(persisted['final_errors'])==1
            assert persisted['final_errors'][0]['category']=='INCOMPLETE_RESULT' and persisted['final_errors'][0]['attempt_count']==3
            assert any(x['result']['contract']['scores']['accuracy']['score']==3 for x in persisted['successes'])
        finally: await runner.stop(); await client.close()
    asyncio.run(run())


def test_cancel_inflight_real_sdk_reply_discarded(service):
    async def run():
        release=asyncio.Event(); started=asyncio.Event(); calls=[]
        async def handler(request):
            calls.append(request); started.set(); await release.wait()
            return httpx.Response(200,json=envelope(json.dumps(evaluation())))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        runner=Executor(service,client,scan_interval=.005)
        task=service.start(model_plan(service),str(uuid4()))
        await runner.start()
        try:
            await asyncio.wait_for(started.wait(),2)
            await runner.cancel(task['id'],service.get(task['id'])['revision'],str(uuid4()))
            release.set(); await until(lambda: not runner.workers)
            assert service.get(task['id'])['items']==[] and len(calls)==1
            with service.database.session() as s: assert list(s.scalars(select(Attempt)))==[]
            from app.services.model_results import case_outcomes
            assert case_outcomes(service.database,task['id'])=={'eligible':False,'cancelled':True,'successes':[],'final_errors':[]}
        finally: release.set(); await runner.stop(); await client.close()
    asyncio.run(run())


def test_restart_saved_success_and_sent_unsaved_count(service):
    async def run():
        p=model_plan(service,2); task=service.start(p,str(uuid4()))
        first,second=service.pending()
        from app.domain.model_contract import check_envelope
        service.save(service.prepare(first['id'],str(uuid4())),check_envelope('evaluation',envelope(json.dumps(evaluation())),[],''))
        service.prepare(second['id'],str(uuid4()))
        service.recover()
        with service.database.engine.begin() as c: c.execute(text('UPDATE execution_item SET next_attempt_at=NULL'))
        calls=[]
        async def handler(request):
            calls.append(request); return httpx.Response(200,json=envelope(json.dumps(evaluation())))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        runner=Executor(service,client,scan_interval=.005)
        await runner.start()
        try:
            await until(lambda: service.get(task['id'])['state']=='completed')
            assert len(calls)==1
            assert sorted(x['attempt_count'] for x in service.get(task['id'])['items'])==[1,2]
        finally: await runner.stop(); await client.close()
    asyncio.run(run())
