"""仅本地测试进程使用的transport；产品app不导入此文件。"""
import asyncio
import json
import os
from pathlib import Path

from app.domain.execution import Outcome, Transition
from app.main import create_app

directory = Path(os.environ['WORKBENCH_DATA_DIR'])


class Once:
    def start_once(self, attempt):
        path = directory / 'calls.jsonl'
        existing = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
        with path.open('a', encoding='utf-8') as log:
            log.write(json.dumps({'item_id': attempt['item_id'], 'ordinal': attempt['ordinal']}) + '\n')
            log.flush()
        async def response():
            if existing:
                while not (directory / 'release').exists():
                    await asyncio.sleep(.01)
            return Outcome(True, {'local_test': True}, raw='测试响应')
        return response()


class Hooks:
    def item_saved(self, *args):
        return []
    def phase_finished(self, *args):
        return Transition('done', [])


app = create_app(directory, transport=Once(), task_hooks=Hooks())
