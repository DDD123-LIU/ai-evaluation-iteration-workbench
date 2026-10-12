"""003 Q首份完整Prompt资产；历史读取冻结正文，不替换版本。"""
import hashlib,json
from pathlib import Path
from app.domain.execution import ConfigSpec
from app.model_client.deepseek import settings


def prompt_config():
    folder=Path(__file__).parent
    manifest=json.loads((folder/'standard-question-manifest.json').read_text(encoding='utf-8'))
    raw=(folder/manifest['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['sha256']:raise ValueError('Q Prompt正文与版本哈希不一致')
    return ConfigSpec('standard_question','model-contract-v1',manifest['version'],raw.decode('utf-8'),
                      'deepseek-flash',settings('standard_question'),'DeepSeek-V4.1-Flash')
