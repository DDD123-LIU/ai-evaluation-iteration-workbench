"""仅013本地进程测试入口：真实生产组装，供应商HTTP为明确替身。"""
import asyncio
import json
import os
from pathlib import Path
import httpx
from app.main import create_app
from app.model_client.deepseek import DeepSeekTransport
from test_qa_generation_integration import gap_value
from test_model_contract import envelope

directory=Path(os.environ['WORKBENCH_DATA_DIR'])


async def handler(request):
    data=json.loads(json.loads(request.content)['messages'][1]['content'])
    stage='Q' if 'knowledge_gap' in data else 'E'
    question=data.get('original_question',data['history'][-1]['content'])
    with (directory/'qa-calls.jsonl').open('a',encoding='utf-8') as log:
        log.write(json.dumps({'stage':stage,'question':question},ensure_ascii=False)+'\n')
    if stage=='Q' and question=='问题1':
        while not (directory/'release').exists():await asyncio.sleep(.01)
    raw=json.dumps(gap_value(question)) if stage=='E' else json.dumps({'standard_question':'具体时限是什么？'})
    return httpx.Response(200,json=envelope(raw))


client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
app=create_app(directory,transport=client)
