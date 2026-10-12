"""003完整结构契约。只校验字段和来源，不决定业务语义或生成Prompt。"""
import json
from jsonschema import Draft202012Validator
from app.domain.execution import Outcome

CAUSES = ('知识库缺少对应信息', 'AI 理解错了用户意图', '回复内容敷衍', '违反平台规则，做出不当承诺', '其他／证据不足')
TEXT = {'type':'string', 'minLength':1}


def obj(properties):
    return {'type':'object','required':list(properties),'additionalProperties':False,'properties':properties}


SCORE = obj({'score':{'type':'integer','minimum':1,'maximum':5},'reason':TEXT})
SCHEMAS = {
    'reply_generation':obj({'reply':TEXT}),
    'standard_question':obj({'standard_question':TEXT}),
    'evaluation':obj({'scores':obj({k:SCORE for k in ('accuracy','intent','service')}),
        'primary_cause':{'enum':[*CAUSES,None]},
        'secondary_causes':{'type':'array','items':{'enum':list(CAUSES[:4])},'uniqueItems':True,'maxItems':4},
        'knowledge_gaps':{'type':'array','items':obj({'gap':TEXT,'snippet':TEXT,'reason':TEXT})},
        'has_material_conflict':{'type':'boolean'}}),
}
VALIDATORS = {stage:Draft202012Validator(schema) for stage,schema in SCHEMAS.items()}


class ContractError(ValueError):
    def __init__(self, category, detail):
        super().__init__(detail)
        self.category, self.detail = category, detail


def strict_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:
                raise ValueError('重复JSON键')
            result[key]=value
        return result
    def constant(_):
        raise ValueError('非标准JSON数字')
    try:
        value=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
        # 孤立代理项无法按UTF-8保存，不把它冒充Unicode字符。
        json.dumps(value,ensure_ascii=False,allow_nan=False).encode('utf-8')
        return value
    except (ValueError,TypeError,UnicodeError,RecursionError):
        raise ContractError('PARSE_ERROR','不是单个严格JSON值，或包含重复键/非标准数字/非法Unicode') from None


def required_text(value):
    if not value.strip():
        raise ContractError('INCOMPLETE_RESULT','必填文本为空白')


def reason(value):
    value=value.replace('\r\n','\n').replace('\r','\n')
    required_text(value)
    if len(value)>50:
        raise ContractError('INCOMPLETE_RESULT','reason超过50 Unicode码点')
    return value


def check_content(stage, raw, history, target_reply):
    value=strict_json(raw)
    if stage not in VALIDATORS:
        raise ValueError('未定义模型阶段')
    if not VALIDATORS[stage].is_valid(value):
        raise ContractError('INCOMPLETE_RESULT','字段缺失、额外字段、类型/枚举/范围不合法')
    if stage!='evaluation':
        required_text(value['reply' if stage=='reply_generation' else 'standard_question'])
        return {'contract':value,'evidence_locations':[]}
    for dimension in value['scores'].values():
        if type(dimension['score']) is not int:
            raise ContractError('INCOMPLETE_RESULT','score必须是词法整数，不能是布尔或4.0')
        dimension['reason']=reason(dimension['reason'])
    primary, secondary, gaps = value['primary_cause'],value['secondary_causes'],value['knowledge_gaps']
    accuracy=value['scores']['accuracy']['score']
    bad=any(x['score']<4 for x in value['scores'].values())
    if (bad and primary is None) or (not bad and (primary is not None or secondary or gaps or value['has_material_conflict'])):
        raise ContractError('INCOMPLETE_RESULT','合格或Badcase字段条件矛盾')
    if primary in secondary:
        raise ContractError('INCOMPLETE_RESULT','主因不能重复成为次因')
    if primary==CAUSES[3] and accuracy!=1:
        raise ContractError('INCOMPLETE_RESULT','合规主因要求准确性1')
    if value['has_material_conflict'] and (accuracy!=1 or primary not in (CAUSES[3],CAUSES[4])):
        raise ContractError('INCOMPLETE_RESULT','资料冲突的准确性或主因不合法')
    knowledge=primary==CAUSES[0] or CAUSES[0] in secondary
    if bool(gaps)!=knowledge:
        raise ContractError('INCOMPLETE_RESULT','知识缺失必须有完整证据，其他分类必须空集合')
    locations=[]
    for gap in gaps:
        required_text(gap['gap']); required_text(gap['snippet'])
        gap['reason']=reason(gap['reason'])
        location=None
        for index,message in enumerate(history):
            start=message['content'].find(gap['snippet'])
            if start>=0:
                location={'source':'history','message_index':index,'start':start,'end':start+len(gap['snippet'])}
                break
        if location is None:
            start=target_reply.find(gap['snippet'])
            if start>=0:
                location={'source':'target_reply','start':start,'end':start+len(gap['snippet'])}
        if location is None:
            raise ContractError('INCOMPLETE_RESULT','snippet不能在单条原消息或本次回复连续定位')
        locations.append(location)
    return {'contract':value,'evidence_locations':locations}


def check_envelope(stage, envelope, history, target_reply):
    raw=''
    try:
        if not isinstance(envelope,dict) or envelope.get('object')!='chat.completion':
            raise ContractError('CALL_ERROR','响应外壳不是chat.completion')
        choices=envelope.get('choices')
        if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict):
            raise ContractError('CALL_ERROR','必须恰有一个有效choice')
        choice=choices[0]; message=choice.get('message')
        if not isinstance(message,dict) or message.get('role')!='assistant' or message.get('tool_calls') or message.get('function_call'):
            raise ContractError('CALL_ERROR','缺少assistant文本消息或包含工具结果')
        content=message.get('content')
        raw=content if isinstance(content,str) else ''
        if choice.get('finish_reason')!='stop' or not raw.strip():
            raise ContractError('INCOMPLETE_RESULT','响应未完整终止或content为空')
        result=check_content(stage,raw,history,target_reply)
        warnings=[]
        for name in ('model','system_fingerprint','id'):
            if not isinstance(envelope.get(name),str) or not envelope[name].strip():
                warnings.append(name+'_unrecognized')
        if type(envelope.get('created')) is not int or envelope['created']<=0:
            warnings.append('created_unrecognized')
        usage=envelope.get('usage'); usable={}
        if isinstance(usage,dict):
            for name in ('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens'):
                if name in usage and type(usage[name]) is int and usage[name]>=0:
                    usable[name]=usage[name]
            if any(name not in usable for name in ('prompt_tokens','completion_tokens','total_tokens')):
                warnings.append('usage_unknown_or_partial')
        else:
            warnings.append('usage_unknown_or_partial')
        result.update(trace_warnings=warnings,usage=usable or None)
        return Outcome(True,result,raw=raw,envelope=envelope)
    except ContractError as error:
        return Outcome(False,raw=raw,error_category=error.category,error_detail=error.detail,envelope=envelope if isinstance(envelope,dict) else {})
