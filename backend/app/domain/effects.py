"""仅判可比及两侧指标，不计算人工改善/持平/变差结论。"""
from dataclasses import dataclass
from app.domain.execution import Plan
from app.domain.batch_metrics import calculate


@dataclass(frozen=True)
class EffectPlan(Plan):
    supplement_id: str
    source_batch_id: str
    new_kb_id: str


def comparison(old, new):
    reasons = []
    for side, stages in (('old', old), ('new', new)):
        for stage in ('generation', 'evaluation'):
            if stages[stage]['state'] != 'succeeded':
                reasons.append(f'{side}_{stage}_{stages[stage]["state"]}')
    if reasons:
        return {'comparable': False, 'reasons': reasons}
    for stage in ('generation', 'evaluation'):
        left, right = old[stage]['trace'], new[stage]['trace']
        if left['config'] != right['config']:
            reasons.append(f'configuration_mismatch_{stage}')
        for field in ('model', 'system_fingerprint'):
            values = [trace['response']['envelope'].get(field) for trace in (left, right)]
            valid = [isinstance(value, str) and bool(value.strip()) for value in values]
            for side, usable in zip(('old', 'new'), valid):
                if not usable: reasons.append(f'{side}_{stage}_{field}_unrecognized')
            if all(valid) and values[0] != values[1]: reasons.append(f'{stage}_{field}_drift')
        # 只去除允许不同的库与当前评测目标；此前H及规则必须完全一致。
        import json
        inputs = [json.loads(trace['request']['messages'][1]['content']) for trace in (left, right)]
        for value in inputs:
            value.pop('knowledge_base', None)
            if stage == 'evaluation': value.pop('target_reply', None)
        if inputs[0] != inputs[1]: reasons.append(f'input_mismatch_{stage}')
    return {'comparable': not reasons, 'reasons': reasons}


def side_metrics(cases, side):
    success = [row[side]['evaluation'] for row in cases if row[side]['generation']['state'] == 'succeeded'
        and row[side]['evaluation']['state'] == 'succeeded']
    result = calculate(len(cases), len(success), sum(not row['is_badcase'] for row in success),
        sum(sum(score['score'] for score in row['contract']['scores'].values()) for row in success))
    return {key: result[key] for key in ('counts', 'raw', 'display')}
