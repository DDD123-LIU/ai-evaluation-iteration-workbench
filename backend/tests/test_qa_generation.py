"""F19～21/D05测试先行，不使用真实模型或正式样本。"""
from app.prompts.standard_question import prompt_config
from app.services.qa_generation import QAHooks,eligible_gaps,request_for


def test_prompt_full_contract():
    cfg=prompt_config()
    assert cfg.stage=='standard_question' and cfg.prompt_version=='standard-question-v2'
    assert cfg.parameters['max_tokens']==2048 and cfg.parameters['temperature']==0
    for word in ['standard_question','原问题','答案','reason','json']:
        assert word in cfg.full_prompt
