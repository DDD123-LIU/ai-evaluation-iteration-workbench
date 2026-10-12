"""仅本地进程恢复测试入口；生产main不加载此SDK响应/后续阶段替身。"""
import asyncio
import json
import os
from pathlib import Path
import httpx
from app.main import create_app
from app.model_client.deepseek import DeepSeekTransport
from app.services.evaluation import EvaluationBuilder, EvaluationHooks
from test_evaluation import qconfig, DoneForTest
from test_model_contract import evaluation, envelope

directory=Path(os.environ['WORKBENCH_DATA_DIR'])


async def handler(request):
    data=json.loads(json.loads(request.content)['messages'][1]['content'])
    question=data['history'][-1]['content']
    with (directory/'model-calls.jsonl').open('a',encoding='utf-8') as log:
        log.write(json.dumps({'question':question,'target_reply':data['target_reply']},ensure_ascii=False)+'\n')
    if question=='问题1':
        while not (directory/'release').exists(): await asyncio.sleep(.01)
    return httpx.Response(200,json=envelope(json.dumps(evaluation())))


client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),token_counter=lambda _:10)
app=create_app(directory,transport=client,task_hooks=EvaluationHooks(DoneForTest()))
app.state.task_builder=EvaluationBuilder(app.state.database,qconfig())
