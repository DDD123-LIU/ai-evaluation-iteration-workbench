"""真实SDK＋本地HTTP替身，验证单次边界而非真实DeepSeek质量。"""
import asyncio
import json
import pytest
import httpx
from app.model_client.deepseek import DeepSeekTransport, settings, count_tokens, retry_after
from app.domain.execution import LocalBlocked
from test_model_contract import envelope, evaluation


def attempt(stage='evaluation'):
    return {'id':'a','item_id':'i','task_id':'t','ordinal':1,'epoch':0,
        'config':{'stage':stage,'contract_version':'model-contract-v1','prompt_version':{'evaluation':'evaluation-v1','reply_generation':'customer-reply-v1','standard_question':'standard-question-v1'}[stage],
            'request_model':'deepseek-flash','documented_release':'DeepSeek-V4.1-Flash','full_prompt':'测试专用 json 结构示例：{}','parameters':settings(stage)},
        'request':{'messages':[{'role':'system','content':'测试专用 json 结构示例：{}'},{'role':'user','content':'{}'}],
            'history':[{'role':'user','content':'何时生效？'}],'target_reply':'原回复'}}


def test_official_request_and_success_preserve_raw_metadata():
    async def run():
        sent=[]
        async def handler(request):
            sent.append(json.loads(request.content))
            assert request.url==httpx.URL('https://api.deepseek.com/chat/completions')
            assert request.headers['authorization']=='Bearer test-only-key'
            return httpx.Response(200,json=envelope(json.dumps(evaluation())))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        try:
            value=attempt(); client.validate(value)
            result=await client.start_once(value)
            assert result.success and result.payload['contract']==evaluation()
            assert result.envelope['model']=='DeepSeek-V4.1-Flash'
            assert len(sent)==1
            assert sent[0]['thinking']=={'type':'enabled'}
            assert sent[0]['reasoning_effort']=='high' and 'temperature' not in sent[0]
            assert sent[0]['response_format']=={'type':'json_object'} and sent[0]['stream'] is False
        finally:
            await client.close()
    asyncio.run(run())


@pytest.mark.parametrize('status',[400,401,402,422,429,500,503])
def test_sdk_never_retries_and_preserves_status(status):
    async def run():
        calls=[]
        async def handler(request):
            calls.append(request)
            return httpx.Response(status,headers={'Retry-After':'7'},json={'error':{'message':'供应商错误','type':'test'}})
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        try:
            result=await client.start_once(attempt())
            assert not result.success and result.error_category=='CALL_ERROR'
            assert result.envelope['http_status']==status and result.retry_after==7
            assert len(calls)==1
        finally: await client.close()
    asyncio.run(run())


def test_deadline_cleanup_finishes_before_return():
    async def run():
        cleanup=asyncio.Event(); release=asyncio.Event(); starts=[]
        async def handler(request):
            starts.append(request)
            try: await asyncio.sleep(20)
            finally:
                cleanup.set()
                await release.wait()
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10,request_deadline=.02)
        try:
            pending=client.start_once(attempt())
            await asyncio.wait_for(cleanup.wait(),2)
            assert not pending.done()
            release.set()
            result=await pending
            assert result.error_category=='CALL_ERROR' and len(starts)==1
        finally: await client.close()
    asyncio.run(run())


def test_late_result_after_deadline_not_accepted():
    async def run():
        async def handler(request):
            try: await asyncio.sleep(20)
            except asyncio.CancelledError: return httpx.Response(200,json=envelope(json.dumps(evaluation())))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10,request_deadline=.01)
        try: assert (await client.start_once(attempt())).error_category=='CALL_ERROR'
        finally: await client.close()
    asyncio.run(run())


def test_oversized_input_is_zero_send_local_block():
    client=DeepSeekTransport('test-only-key',token_counter=lambda _:1048577)
    try:
        with pytest.raises(LocalBlocked): client.validate(attempt())
    finally: asyncio.run(client.close())


def test_provider_credential_echo_is_not_persistable():
    async def run():
        async def handler(request):
            return httpx.Response(401,json={'error':{'message':'test-only-key'}})
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        try:
            result=await client.start_once(attempt())
            assert 'test-only-key' not in repr(result)
        finally: await client.close()
    asyncio.run(run())


def test_official_offline_assets_and_default_token_counter():
    from pathlib import Path
    import hashlib
    import app.model_client.deepseek as module
    directory=Path(module.__file__).parent/'assets'
    provenance=json.loads((directory/'provenance.json').read_text(encoding='utf-8'))
    for name,digest in provenance['files'].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest
    messages=attempt()['request']['messages']
    assert type(count_tokens(messages)) is int and count_tokens(messages)>0
    client=DeepSeekTransport('test-only-key')
    try: client.validate(attempt())
    finally: asyncio.run(client.close())


@pytest.mark.parametrize('value',['NaN','Infinity','-1','bad-date'])
def test_invalid_retry_after_is_not_a_wait_value(value):
    assert retry_after(httpx.Headers({'retry-after':value})) is None


def test_retry_after_http_date_and_context_boundary():
    assert retry_after(httpx.Headers({'retry-after':'Wed, 21 Oct 2015 07:28:00 GMT'}))==0
    client=DeepSeekTransport('test-only-key',token_counter=lambda _:1048576)
    try: client.validate(attempt())
    finally: asyncio.run(client.close())


@pytest.mark.parametrize('value',[False,0.0])
def test_frozen_parameter_type_cannot_be_coerced(value):
    client=DeepSeekTransport('test-only-key',token_counter=lambda _:10)
    frozen=attempt('reply_generation'); frozen['config']['parameters']['temperature']=value
    try:
        with pytest.raises(LocalBlocked): client.validate(frozen)
    finally: asyncio.run(client.close())


@pytest.mark.parametrize('stage,field,budget',[('reply_generation','reply',8192),('standard_question','standard_question',2048)])
def test_non_thinking_request_configs(stage,field,budget):
    async def run():
        sent=[]
        async def handler(request):
            sent.append(json.loads(request.content))
            return httpx.Response(200,json=envelope(json.dumps({field:'测试文本'})))
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        try:
            assert (await client.start_once(attempt(stage))).success
            assert sent[0]['thinking']=={'type':'disabled'}
            assert sent[0]['temperature']==0 and sent[0]['max_tokens']==budget
            assert 'reasoning_effort' not in sent[0] and len(sent)==1
        finally: await client.close()
    asyncio.run(run())


def test_connection_failure_is_one_call_and_safe_error():
    async def run():
        calls=[]
        async def handler(request):
            calls.append(request)
            raise httpx.ConnectError('test-only-key',request=request)
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        try:
            result=await client.start_once(attempt())
            assert result.error_category=='CALL_ERROR' and len(calls)==1
            assert 'test-only-key' not in repr(result)
        finally: await client.close()
    asyncio.run(run())


@pytest.mark.parametrize('status',[200,401])
def test_escaped_credential_echo_is_not_persistable(status):
    async def run():
        async def handler(request):
            encoded=''.join('\\u%04x'%ord(char) for char in 'test-only-key')
            return httpx.Response(status,content='{"error":{"message":"'+encoded+'"}}',headers={'content-type':'application/json'})
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
        try:
            result=await client.start_once(attempt())
            assert result.error_category=='CALL_ERROR'
            assert 'supplier_error' not in result.envelope and 'raw_response' not in result.envelope
        finally: await client.close()
    asyncio.run(run())


def test_client_cleanup_failure_still_releases_database(tmp_path):
    from app.main import create_app
    from app.db.database import Database
    class CloseFailure:
        async def close(self): raise RuntimeError('模拟客户端清理失败')
    app=create_app(tmp_path,transport=CloseFailure())
    async def run():
        with pytest.raises(RuntimeError,match='模拟客户端清理失败'):
            async with app.router.lifespan_context(app): pass
        assert not app.state.database.directory_lock.is_locked
        restarted=Database(tmp_path)
        try: restarted.start()
        finally: restarted.stop()
    try: asyncio.run(run())
    finally: app.state.database.stop()


def test_tokenizer_engine_failure_is_unsent_local_block():
    def broken(_): raise RuntimeError('模拟分词器不可用')
    client=DeepSeekTransport('test-only-key',token_counter=broken)
    try:
        with pytest.raises(LocalBlocked,match='离线tokenizer不可用'): client.validate(attempt())
    finally: asyncio.run(client.close())
