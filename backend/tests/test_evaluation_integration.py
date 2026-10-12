"""011＋010 SDK＋009 SQLite集成。后续阶段为显式测试替身，无真实模型语义结论。"""
import asyncio
import copy
import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from app.runtime.executor import Executor
from app.model_client.deepseek import DeepSeekTransport
from app.models.execution import Attempt, ExecutionItem
from app.models.evaluation import EvaluationResult, Gap, FinalError
from app.services.evaluation import EvaluationBuilder, EvaluationHooks, results
from app.services.imports import ImportService
from app.domain.model_contract import check_envelope
from test_evaluation import qconfig, DoneForTest, service
from test_task_execution import until
from test_csv_import import encode, dialogue
from test_model_contract import evaluation, missing, envelope


def one_plan(service):
    upload,rule,kb,_=service.test_sources
    plan=EvaluationBuilder(service.database,qconfig())({'upload_id':upload,'rule_version_id':rule,'kb_version_id':kb})
    return replace(plan,case_ids=plan.case_ids[:1],items=plan.items[:1])


def test_save_failure_rolls_back_result_gap_and_attempt_then_local_resave(service):
    service.hooks=EvaluationHooks(DoneForTest())
    task=service.start(one_plan(service),str(uuid4()))
    prepared=service.prepare(service.pending()[0]['id'],str(uuid4()))
    value=missing(); value['knowledge_gaps']=[{'gap':'时限','snippet':'问题0','reason':'无时限'},{'gap':'额度','snippet':'问题0','reason':'无额度'}]
    outcome=check_envelope('evaluation',envelope(json.dumps(value)),prepared['request']['history'],prepared['request']['target_reply'])
    assert outcome.success
    with service.database.engine.begin() as connection:
        connection.execute(text("CREATE TRIGGER fail_second_gap BEFORE INSERT ON gap WHEN NEW.gap_ordinal=2 BEGIN SELECT RAISE(ABORT,'模拟保存失败'); END"))
    with pytest.raises(SQLAlchemyError): service.save(prepared,outcome)
    with service.database.session() as session:
        assert list(session.scalars(select(EvaluationResult)))==list(session.scalars(select(Gap)))==[]
        assert session.get(Attempt,prepared['id']).state=='prepared'
    with service.database.engine.begin() as connection: connection.execute(text('DROP TRIGGER fail_second_gap'))
    service.save(prepared,outcome); service.save(prepared,outcome)
    assert len(results(service.database,task['id'])['results'][0]['knowledge_gaps'])==2
    assert service.get(task['id'])['items'][0]['attempt_count']==1


@pytest.mark.parametrize('scenario,accuracy,cause,secondary,conflict,qa',[
    ('两资料无答案纯兜底',3,'知识库缺少对应信息',[],False,True),
    ('两资料无答案含编造',1,'知识库缺少对应信息',[],False,True),
    ('资料有答案却兜底',1,'回复内容敷衍',[],False,False),
    ('违规承诺含缺失',1,'违反平台规则，做出不当承诺',['知识库缺少对应信息'],False,True),
    ('纯资料冲突',1,'其他／证据不足',[],True,False),
    ('冲突加违规和缺失',1,'违反平台规则，做出不当承诺',['知识库缺少对应信息'],True,False),
])
def test_fixed_special_contracts_persist_and_derive_without_rewriting(service,scenario,accuracy,cause,secondary,conflict,qa):
    # 此处输入是预先固定的合法合同，验证后处理，不模拟判断资料事实。
    service.hooks=EvaluationHooks(DoneForTest())
    task=service.start(one_plan(service),str(uuid4()))
    prepared=service.prepare(service.pending()[0]['id'],str(uuid4()))
    value=evaluation(); value['scores']['accuracy']={'score':accuracy,'reason':scenario}
    value.update(primary_cause=cause,secondary_causes=secondary,has_material_conflict=conflict)
    if cause=='知识库缺少对应信息' or '知识库缺少对应信息' in secondary:
        value['knowledge_gaps']=[{'gap':'时限','snippet':'问题0','reason':'两资料均未说明时限'}]
    outcome=check_envelope('evaluation',envelope(json.dumps(value)),prepared['request']['history'],prepared['request']['target_reply'])
    assert outcome.success
    service.save(prepared,outcome)
    saved=results(service.database,task['id'])['results'][0]
    assert saved['contract']==value and saved['qa_eligible']==qa and saved['is_badcase']


@pytest.mark.parametrize('failure',['missing_gap','local_block'])
def test_final_error_persists_actual_three_or_zero_and_no_success(service,failure):
    async def run():
        service.hooks=EvaluationHooks(DoneForTest())
        calls=[]
        async def handler(request):
            calls.append(request)
            value=missing(); value['knowledge_gaps'][0]={'gap':'时限','snippet':'问题0'}
            return httpx.Response(200,headers={'Retry-After':'0'},json=envelope(json.dumps(value)))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:1048577 if failure=='local_block' else 10)
        runner=Executor(service,client,scan_interval=.005)
        task=service.start(one_plan(service),str(uuid4()))
        await runner.start()
        try:
            await until(lambda:service.get(task['id'])['state']=='completed')
            data=results(service.database,task['id'])
            assert data['results']==[] and len(data['final_errors'])==1
            error=data['final_errors'][0]
            assert error['attempt_count']==len(calls)==(0 if failure=='local_block' else 3)
            assert (error['last_attempt_id'] is None)==(failure=='local_block')
            assert error['category']==('CALL_ERROR' if failure=='local_block' else 'INCOMPLETE_RESULT')
        finally: await runner.stop(); await client.close()
    asyncio.run(run())


def test_f32_paired_requests_are_independent_and_expectations_never_sent(service):
    async def run():
        fixture=json.loads((Path(__file__).parent/'fixtures/f32_expectations.json').read_text(encoding='utf-8'))
        imports=ImportService(service.database)
        rule=imports.save('rules',encode('rules',[['r','退款',fixture['business_rule']]]),'rule.csv',str(uuid4()))[0]['id']
        kb=imports.save('knowledge',encode('knowledge',[['k','退款',fixture['knowledge']]]),'kb.csv',str(uuid4()))[0]['id']
        sent=[]; identities=[]
        async def handler(request):
            body=json.loads(request.content); data=json.loads(body['messages'][1]['content']); sent.append(data)
            assert set(data)=={'history','target_reply','business_rules','knowledge_base','rubric','schema_version'}
            assert 'expected' not in data and 'formal_acceptance_set' not in data
            value=evaluation(); value['scores']['accuracy']={'score':1,'reason':'退款保证违反平台规则'}
            value['primary_cause']='违反平台规则，做出不当承诺'
            return httpx.Response(200,json=envelope(json.dumps(value)))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        service.hooks=EvaluationHooks(DoneForTest()); runner=Executor(service,client,scan_interval=.005)
        await runner.start()
        try:
            for index,reply in enumerate(fixture['replies']):
                row=dialogue(str(index),question=fixture['question']); row[2]=reply
                upload=imports.save('dialogues',encode('dialogues',[row]),'pair.csv',str(uuid4()))[0]['id']
                plan=EvaluationBuilder(service.database,qconfig())({'upload_id':upload,'rule_version_id':rule,'kb_version_id':kb})
                task=service.start(plan,str(uuid4())); identities.append(task['id'])
                await until(lambda:service.get(task['id'])['state']=='completed')
                saved=results(service.database,task['id'])['results'][0]
                assert saved['contract']['scores']['accuracy']['score']==fixture['expected']['accuracy']
                assert saved['is_badcase']==fixture['expected']['is_badcase']
                assert saved['contract']['primary_cause']==fixture['expected']['primary_cause']
                assert saved['attempt_count']==1 and saved['trace']['request']['target_reply']==reply
            assert len(set(identities))==2 and len(sent)==2
            assert [data['target_reply'] for data in sent]==fixture['replies']
        finally: await runner.stop(); await client.close()
    asyncio.run(run())


def test_retries_use_frozen_prompt_and_data_without_loading_latest(service,monkeypatch):
    async def run():
        service.hooks=EvaluationHooks(DoneForTest())
        plan=one_plan(service); task=service.start(plan,str(uuid4()))
        def unavailable(): raise OSError('模拟当前Prompt文件不可读；历史快照仍应执行')
        monkeypatch.setattr('app.services.evaluation.prompt_config',unavailable)
        sent=[]
        async def handler(request):
            sent.append(json.loads(request.content))
            return httpx.Response(200,headers={'Retry-After':'0'},json=envelope('{}' if len(sent)==1 else json.dumps(evaluation())))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        runner=Executor(service,client,scan_interval=.005); await runner.start()
        try:
            await until(lambda:service.get(task['id'])['state']=='completed')
            assert len(sent)==2 and sent[0]==sent[1]
            saved=results(service.database,task['id'])['results'][0]
            assert saved['trace']['full_prompt']==plan.configs[0].full_prompt and saved['attempt_count']==2
        finally: await runner.stop(); await client.close()
    asyncio.run(run())
