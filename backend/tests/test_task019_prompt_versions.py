"""Prompt版本接入及历史快照验证；不能证明模型语义通过。"""
import asyncio
from pathlib import Path
import pytest
from app.domain.execution import LocalBlocked
from app.model_client.deepseek import DeepSeekTransport, PROMPTS
from app.prompts.standard_question import prompt_config
from app.prompts.evaluation import prompt_config as evaluation_config
from app.prompts.customer_reply import prompt_config as reply_config
from test_model_client import attempt


def test_current_question_prompt_is_version_two():
    config = prompt_config()
    assert config.prompt_version == 'standard-question-v2'
    assert config.contract_version == 'model-contract-v1'
    assert config.parameters['temperature'] == 0
    assert config.parameters['max_tokens'] == 2048


def test_current_evaluation_and_generation_versions():
    config = evaluation_config()
    assert config.prompt_version == PROMPTS['evaluation'] == 'evaluation-v2'
    assert config.full_prompt == (Path(__file__).parents[1] / 'app/prompts/evaluation-v2.md').read_bytes().decode('utf-8')
    assert reply_config().prompt_version == 'customer-reply-v4'
    assert '不向用户描述内部规则或知识库资料缺失' in reply_config().full_prompt


@pytest.mark.parametrize('stage,version', [('evaluation','evaluation-v1'),('evaluation','evaluation-v2'),('evaluation','evaluation-v3'),
    ('reply_generation','customer-reply-v1'),('reply_generation','customer-reply-v2'),('reply_generation','customer-reply-v3'),('reply_generation','customer-reply-v4')])
def test_known_generation_and_evaluation_snapshot_versions(stage, version):
    async def run():
        client = DeepSeekTransport('test-only-key', token_counter=lambda _: 10)
        try:
            preview = attempt(stage)
            preview['config']['prompt_version'] = version
            client.validate(preview)
        finally:
            await client.close()
    asyncio.run(run())


@pytest.mark.parametrize('version', ['standard-question-v1', 'standard-question-v2'])
def test_known_question_prompt_snapshot_can_resume(version):
    async def run():
        client = DeepSeekTransport('test-only-key', token_counter=lambda _: 10)
        try:
            preview = attempt('standard_question')
            preview['config']['prompt_version'] = version
            client.validate(preview)
        finally:
            await client.close()
    asyncio.run(run())


def test_unknown_question_prompt_version_is_blocked_before_send():
    async def run():
        client = DeepSeekTransport('test-only-key', token_counter=lambda _: 10)
        try:
            preview = attempt('standard_question')
            preview['config']['prompt_version'] = 'standard-question-v999'
            with pytest.raises(LocalBlocked):
                client.validate(preview)
        finally:
            await client.close()
    asyncio.run(run())
