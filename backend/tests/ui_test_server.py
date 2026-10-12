"""018 Chrome专用隔离入口。正式app不引用本模块，不发外网请求。"""
import asyncio
import json
import os
from pathlib import Path
import httpx
from app.main import create_app
from app.model_client.deepseek import DeepSeekTransport
from test_model_contract import envelope,evaluation,missing

directory=Path(os.environ['WORKBENCH_DATA_DIR'])

async def handler(request):
    packet=json.loads(request.content)
    value=json.loads(packet['messages'][1]['content'])
    stage='evaluation' if 'target_reply' in value else 'standard_question' if 'knowledge_gap' in value else 'reply_generation'
    text=json.dumps(value,ensure_ascii=False)
    with (directory/'ui-calls.jsonl').open('a',encoding='utf-8') as log:
        log.write(json.dumps({'stage':stage,'input':value},ensure_ascii=False)+'\n')
    if '等待取消' in text:
        while not (directory/'release').exists():await asyncio.sleep(.02)
    if stage=='standard_question' and 'QA等待' in text:
        while not (directory/'qa-release').exists():await asyncio.sleep(.02)
    await asyncio.sleep(.1)
    if '异常案例' in text or stage=='standard_question' and 'QA失败' in text:
        return httpx.Response(503,headers={'retry-after':'0'},json={'error':{'message':'本地故障注入'}})
    if stage=='reply_generation' and '生成失败' in text and value['knowledge_base'][0]['source_id']=='new':
        return httpx.Response(503,headers={'retry-after':'0'},json={'error':{'message':'仅新侧生成故障'}})
    if stage=='standard_question':answer={'standard_question':'何时生效的标准规则是什么？'}
    elif stage=='reply_generation':answer={'reply':'本地隔离测试独立生成回复'}
    elif '何时生效' in text:
        answer=missing()
    else:answer=evaluation()
    response=envelope(json.dumps(answer,ensure_ascii=False))
    if '不可比' in text:response.pop('system_fingerprint',None)
    return httpx.Response(200,json=response)

transport=DeepSeekTransport('local-test-only',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
app=create_app(directory,transport=transport if os.environ.get('UI_TEST_MODEL')=='1' else None)
