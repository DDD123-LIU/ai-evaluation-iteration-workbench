"""003 G-v1实际版本化Prompt；历史任务冻结全文及支持参数。"""
import hashlib
import json
from pathlib import Path
from app.domain.execution import ConfigSpec
from app.model_client.deepseek import settings


def prompt_config():
    folder = Path(__file__).parent
    manifest = json.loads((folder / 'customer-reply-manifest.json').read_text(encoding='utf-8'))
    raw = (folder / manifest['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['sha256']:
        raise ValueError('G Prompt正文与版本哈希不一致')
    return ConfigSpec('reply_generation', 'model-contract-v1', manifest['version'], raw.decode('utf-8'),
        'deepseek-flash', settings('reply_generation'), 'DeepSeek-V4.1-Flash')
