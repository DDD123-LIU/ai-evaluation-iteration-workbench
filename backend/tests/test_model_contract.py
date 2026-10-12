"""003 C02/C03与U04；合成协议值，不是正式业务验收集。"""
import copy
import json
import pytest

from app.domain.model_contract import check_content, check_envelope, ContractError

CAUSES = ['知识库缺少对应信息', 'AI 理解错了用户意图', '回复内容敷衍', '违反平台规则，做出不当承诺', '其他／证据不足']


def evaluation():
    return {'scores': {k: {'score': 4, 'reason': '依据充分'} for k in ('accuracy','intent','service')},
        'primary_cause': None, 'secondary_causes': [], 'knowledge_gaps': [], 'has_material_conflict': False}


def missing():
    value = evaluation()
    value['scores']['accuracy']['score'] = 3
    value['primary_cause'] = CAUSES[0]
    value['knowledge_gaps'] = [{'gap': '具体时限', 'snippet': '何时生效', 'reason': '资料未说明具体时限'}]
    return value


def envelope(content):
    return {'object':'chat.completion', 'id':'resp-test', 'created':1, 'model':'DeepSeek-V4.1-Flash',
        'system_fingerprint':'fp', 'usage':{'prompt_tokens':2, 'completion_tokens':3, 'total_tokens':5},
        'choices':[{'index':0, 'finish_reason':'stop', 'message':{'role':'assistant','content':content}}]}


def check(value, history=None, target='原待评回复'):
    return check_content('evaluation', json.dumps(value, ensure_ascii=False), history or [{'role':'user','content':'何时生效？'}], target)


@pytest.mark.parametrize('stage,value', [('reply_generation',{'reply':'原文'}), ('standard_question',{'standard_question':'何时生效？'}), ('evaluation',evaluation())])
def test_complete_outputs(stage, value):
    assert check_content(stage,json.dumps(value),[], '')['contract'] == value


@pytest.mark.parametrize('raw', ['```json\n{}\n```','{}{}','说明{}','{"reply":"a","reply":"b"}','{"reply":NaN}','{"reply":Infinity}'])
def test_strict_parse_failure(raw):
    with pytest.raises(ContractError) as error:
        check_content('reply_generation',raw,[], '')
    assert error.value.category == 'PARSE_ERROR'


@pytest.mark.parametrize('score', [0,6,True,False,'4',4.0,None])
def test_score_strict_integer_and_range(score):
    value = evaluation()
    value['scores']['accuracy']['score'] = score
    with pytest.raises(ContractError) as error:
        check(value)
    assert error.value.category == 'INCOMPLETE_RESULT'


@pytest.mark.parametrize('field', list(evaluation()))
def test_all_e_root_fields_required(field):
    value = evaluation()
    del value[field]
    with pytest.raises(ContractError):
        check(value)


@pytest.mark.parametrize('reason,valid', [('字'*49,True),('字'*50,True),('字'*51,False),('字'*48+'\r\n!',True),('字'*49+'\r!',False),('字'*47+'👩\u200d💻',True),('字'*48+'👩\u200d💻',False),(' ',False)])
def test_unicode_codepoints_and_newlines(reason, valid):
    value = evaluation()
    value['scores']['service']['reason'] = reason
    if valid:
        result=check(value)['contract']
        assert '\r' not in result['scores']['service']['reason']
    else:
        with pytest.raises(ContractError):
            check(value)


def test_gap_all_keys_and_original_message_location():
    result=check(missing())
    assert result['evidence_locations'][0] == {'source':'history', 'message_index':0,'start':0,'end':4}
    for field in ('gap','snippet','reason'):
        value=missing()
        del value['knowledge_gaps'][0][field]
        with pytest.raises(ContractError):
            check(value)
    value=missing()
    value['knowledge_gaps'][0]['snippet']='原待评回复'
    assert check(value)['evidence_locations'][0]['source']=='target_reply'
    value['knowledge_gaps'][0]['snippet']='生效原'
    with pytest.raises(ContractError):
        check(value, target='原待评回复')


@pytest.mark.parametrize('mutate', [
    lambda v:v.update(primary_cause=CAUSES[0]),
    lambda v:v.update(has_material_conflict=True),
    lambda v:v.update(secondary_causes=[CAUSES[1]]),
    lambda v:v.update(knowledge_gaps=missing()['knowledge_gaps']),
])
def test_qualified_consistency(mutate):
    value=evaluation(); mutate(value)
    with pytest.raises(ContractError): check(value)


@pytest.mark.parametrize('secondary', [[CAUSES[0]],[CAUSES[4]],[CAUSES[1],CAUSES[1]],['未知枚举']])
def test_secondary_constraints(secondary):
    value=missing(); value['secondary_causes']=secondary
    with pytest.raises(ContractError): check(value)


def test_conflict_and_compliance_condition():
    value=evaluation(); value['scores']['accuracy']['score']=1
    value['primary_cause']=CAUSES[4]; value['has_material_conflict']=True
    check(value)
    value['primary_cause']=CAUSES[3]; check(value)
    value['scores']['accuracy']['score']=2
    with pytest.raises(ContractError): check(value)


@pytest.mark.parametrize('stage,value', [('reply_generation',{'reply':''}),('reply_generation',{'reply':'x','extra':1}),('standard_question',{'standard_question':'x','answer':''}),('evaluation',[])])
def test_empty_extra_wrong_root(stage,value):
    with pytest.raises(ContractError): check_content(stage,json.dumps(value),[], '')


def test_metadata_warning_does_not_change_success_or_retry():
    value=envelope(json.dumps(evaluation())); value.update(model=None,system_fingerprint=' ',id=False,created=True,usage={'prompt_tokens':True})
    result=check_envelope('evaluation',value,[], '')
    assert result.success and len(result.payload['trace_warnings'])>=5
    assert result.envelope['model'] is None
    assert result.payload['usage'] is None


@pytest.mark.parametrize('change,category', [({'object':'wrong'},'CALL_ERROR'),({'choices':[]},'CALL_ERROR')])
def test_invalid_envelope(change,category):
    value=envelope('{}'); value.update(change)
    result=check_envelope('reply_generation',value,[], '')
    assert not result.success and result.error_category==category


@pytest.mark.parametrize('finish', ['length','content_filter','tool_calls','aborted'])
def test_nonstop_never_success(finish):
    value=envelope('{"reply":"x"}'); value['choices'][0]['finish_reason']=finish
    assert check_envelope('reply_generation',value,[], '').error_category=='INCOMPLETE_RESULT'
