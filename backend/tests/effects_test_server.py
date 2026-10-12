"""仅016本地HTTP恢复测试入口：真实SDK适配接MockTransport，绝不发外网。"""
import asyncio
import json
import os
from pathlib import Path
import httpx
from app.main import create_app
from app.model_client.deepseek import DeepSeekTransport
from test_model_contract import envelope, evaluation

directory = Path(os.environ['WORKBENCH_DATA_DIR'])


async def handler(request):
    packet = json.loads(request.content)
    data = json.loads(packet['messages'][1]['content'])
    stage = 'evaluation' if 'target_reply' in data else 'reply_generation'
    side = 'new' if data['knowledge_base'][0]['source_id'] == 'new' else 'old'
    with (directory / 'effect-calls.jsonl').open('a', encoding='utf-8') as log:
        log.write(json.dumps({'stage': stage, 'side': side}, ensure_ascii=False) + '\n')
    if stage == 'reply_generation' and side == 'new':
        while not (directory / 'release').exists(): await asyncio.sleep(.01)
    value = {'reply': side + '侧实际模拟生成回复'} if stage == 'reply_generation' else evaluation()
    return httpx.Response(200, json=envelope(json.dumps(value, ensure_ascii=False)))


transport = DeepSeekTransport('test-only-key', http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), token_counter=lambda _: 10)
app = create_app(directory, transport=transport)
