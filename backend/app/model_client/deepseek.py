"""已认可G/E/Q配置、单次供应商请求及严格校验。重试归009。"""
import asyncio
import json
import logging
import math
import os
from dataclasses import replace
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path

import httpx
from jinja2 import Environment
from openai import AsyncOpenAI, APIStatusError, APIConnectionError, APITimeoutError
from tokenizers import Tokenizer

from app.domain.execution import LocalBlocked, Outcome
from app.domain.model_contract import ContractError, check_envelope, strict_json

BASE_URL='https://api.deepseek.com'
CONTEXT_LIMIT=1048576
PROMPTS={'evaluation':'evaluation-v2','reply_generation':'customer-reply-v4','standard_question':'standard-question-v2'}
# 新任务使用当前版本；恢复历史任务仍按其已持久化的旧版本和全文发送。
PROMPT_VERSIONS={stage:{version} for stage,version in PROMPTS.items()}
PROMPT_VERSIONS['standard_question'].add('standard-question-v1')
PROMPT_VERSIONS['evaluation'].add('evaluation-v1')
PROMPT_VERSIONS['evaluation'].add('evaluation-v3')
PROMPT_VERSIONS['reply_generation'].add('customer-reply-v1')
PROMPT_VERSIONS['reply_generation'].add('customer-reply-v2')
PROMPT_VERSIONS['reply_generation'].add('customer-reply-v3')


def settings(stage):
    shared={'stream':False,'response_format':{'type':'json_object'}}
    if stage=='evaluation':
        return {**shared,'thinking':{'type':'enabled'},'reasoning_effort':'high','max_tokens':32768}
    if stage in ('reply_generation','standard_question'):
        return {**shared,'thinking':{'type':'disabled'},'temperature':0,
            'max_tokens':8192 if stage=='reply_generation' else 2048}
    raise LocalBlocked('配置阶段未定义，未发送')


@lru_cache(maxsize=1)
def _tokenizer():
    directory=Path(__file__).parent/'assets'
    config=json.loads((directory/'tokenizer_config.json').read_text(encoding='utf-8'))
    return Tokenizer.from_file(str(directory/'tokenizer.json')),Environment().from_string(config['chat_template']),config['bos_token']['content']


def count_tokens(messages):
    tokenizer,template,bos=_tokenizer()
    rendered=template.render(messages=messages,bos_token=bos,add_generation_prompt=True)
    return len(tokenizer.encode(rendered,add_special_tokens=False).ids)


def retry_after(headers):
    value=headers.get('retry-after')
    if value is None:
        return None
    try:
        seconds=float(value)
    except ValueError:
        try:
            date=parsedate_to_datetime(value)
            if date.tzinfo is None:
                return None
            seconds=max(0,(date-datetime.now(timezone.utc)).total_seconds())
        except (ValueError,TypeError,OverflowError):
            return None
    return seconds if math.isfinite(seconds) and seconds>=0 else None


class DeepSeekTransport:
    def __init__(self, api_key, *, http_client=None, token_counter=count_tokens, request_deadline=300):
        if not isinstance(api_key,str) or not api_key.strip():
            raise LocalBlocked('缺少DeepSeek运行凭据，未发送')
        self._key=api_key
        self._counter=token_counter
        self.deadline=request_deadline
        self._active=set()
        # SDK调试模式可能输出完整请求。本模块只暴露结构化结果，不输出HTTP请求。
        for name in ('openai','httpx','httpcore'):
            logging.getLogger(name).setLevel(logging.WARNING)
        self.sdk=AsyncOpenAI(api_key=api_key,base_url=BASE_URL,max_retries=0,timeout=300,
            http_client=http_client or httpx.AsyncClient(timeout=300,follow_redirects=False,trust_env=False))

    def validate(self, preview):
        config=preview['config']; stage=config.get('stage')
        if stage not in PROMPTS or config.get('contract_version')!='model-contract-v1' or config.get('prompt_version') not in PROMPT_VERSIONS[stage]:
            raise LocalBlocked('配置或Prompt接口版本不匹配，未发送')
        try:
            parameters_match=json.dumps(config.get('parameters'),sort_keys=True,allow_nan=False)==json.dumps(settings(stage),sort_keys=True,allow_nan=False)
        except (TypeError,ValueError):
            parameters_match=False
        if config.get('request_model')!='deepseek-flash' or config.get('documented_release')!='DeepSeek-V4.1-Flash' or not parameters_match:
            raise LocalBlocked('模型或冻结参数不符合已认可配置，未发送')
        request=preview['request']; messages=request.get('messages')
        if not isinstance(messages,list) or len(messages)!=2 or [x.get('role') for x in messages if isinstance(x,dict)]!=['system','user']:
            raise LocalBlocked('请求封装必须是固定system和user消息，未发送')
        if any(set(x)!= {'role','content'} or not isinstance(x['content'],str) or not x['content'].strip() for x in messages):
            raise LocalBlocked('消息内容或字段不完整，未发送')
        if messages[0]['content']!=config.get('full_prompt') or 'json' not in config['full_prompt'].lower():
            raise LocalBlocked('Prompt正文与快照不一致或缺少json声明，未发送')
        if self._key in json.dumps(preview,ensure_ascii=False):
            raise LocalBlocked('请求包含运行凭据，未发送')
        history=request.get('history',[])
        if not isinstance(history,list) or any(not isinstance(x,dict) or set(x)!={'role','content'} or x['role'] not in ('user','assistant') or not isinstance(x['content'],str) for x in history):
            raise LocalBlocked('原history来源结构不完整，未发送')
        if stage=='evaluation' and ('history' not in request or not isinstance(request.get('target_reply'),str) or not request['target_reply'].strip()):
            raise LocalBlocked('评测缺少原history或本次target_reply，未发送')
        try:
            tokens=self._counter(messages)
        except Exception:
            raise LocalBlocked('离线tokenizer不可用，未发送，不能猜测输入能力') from None
        if type(tokens) is not int or tokens<0:
            raise LocalBlocked('token计数无效，未发送')
        if tokens>CONTEXT_LIMIT:
            raise LocalBlocked('输入超官方上下文能力，未发送，不截断原文')

    def start_once(self, prepared):
        self.validate(prepared)
        # 同步创建并交给HTTP执行任务，009取消门随后才释放。
        job=asyncio.create_task(self._wait_once(prepared))
        self._active.add(job)
        job.add_done_callback(self._active.discard)
        return job

    async def _wait_once(self, prepared):
        request=asyncio.create_task(self._send(prepared))
        try:
            done,_=await asyncio.wait({request},timeout=self.deadline)
            if request in done:
                return request.result()
            request.cancel()
            await asyncio.gather(request,return_exceptions=True)
            return Outcome(False,error_category='CALL_ERROR',error_detail='单次请求等待截止；连接清理已结束，外部处理及费用仍未知')
        except asyncio.CancelledError:
            request.cancel()
            await asyncio.gather(request,return_exceptions=True)
            raise

    async def _send(self, prepared):
        cfg=prepared['config']; parameters=dict(cfg['parameters']); thinking=parameters.pop('thinking')
        raw_response=None
        try:
            raw_response=await self.sdk.chat.completions.with_raw_response.create(
                model=cfg['request_model'],messages=prepared['request']['messages'],
                extra_body={'thinking':thinking},**parameters)
            status=raw_response.status_code; text=raw_response.text
            if self._key in text:
                return Outcome(False,error_category='CALL_ERROR',error_detail='供应商响应包含运行凭据，内容未保存',envelope={'http_status':status})
            if status!=200:
                return Outcome(False,error_category='CALL_ERROR',error_detail='HTTP响应不是200',envelope={'http_status':status},retry_after=retry_after(raw_response.headers))
            try:
                body=strict_json(text)
            except ContractError:
                return Outcome(False,error_category='CALL_ERROR',error_detail='供应商外壳不是严格JSON',envelope={'http_status':status,'raw_response':text})
            if self._key in json.dumps(body,ensure_ascii=False):
                return Outcome(False,error_category='CALL_ERROR',error_detail='供应商响应包含运行凭据，内容未保存',envelope={'http_status':status})
            req=prepared['request']
            result=check_envelope(cfg['stage'],body,req.get('history',[]),req.get('target_reply',''))
            return replace(result,envelope={**result.envelope,'http_status':status},retry_after=retry_after(raw_response.headers))
        except APIStatusError as error:
            body=error.response.text
            envelope={'http_status':error.status_code}
            try:
                decoded=json.dumps(strict_json(body),ensure_ascii=False)
            except ContractError:
                decoded=body
            if self._key not in body and self._key not in decoded:
                envelope['supplier_error']=body
            return Outcome(False,error_category='CALL_ERROR',error_detail='供应商HTTP错误',envelope=envelope,retry_after=retry_after(error.response.headers))
        except (APITimeoutError,APIConnectionError):
            return Outcome(False,error_category='CALL_ERROR',error_detail='供应商网络连接或等待失败')
        finally:
            if raw_response is not None:
                await raw_response.http_response.aclose()

    async def close(self):
        for job in list(self._active):
            job.cancel()
        await asyncio.gather(*self._active,return_exceptions=True)
        await self.sdk.close()


def from_environment():
    key=os.environ.get('DEEPSEEK_API_KEY')
    return DeepSeekTransport(key) if key and key.strip() else None
