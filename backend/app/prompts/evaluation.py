"""首版evaluation-v1完整资产；后续修改须升版并按约定确认。"""
import hashlib
import json
from pathlib import Path
from app.domain.execution import ConfigSpec
from app.model_client.deepseek import settings


def prompt_config():
    directory=Path(__file__).parent
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    raw=(directory/manifest['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['sha256']:
        raise ValueError('Prompt正文与冻结版本哈希不一致')
    return ConfigSpec('evaluation','model-contract-v1',manifest['version'],raw.decode('utf-8'),
        'deepseek-flash',settings('evaluation'),'DeepSeek-V4.1-Flash')
