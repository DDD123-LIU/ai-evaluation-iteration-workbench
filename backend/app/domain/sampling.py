"""RULE-06：不缩参与分母的随机初抽、补抽和人工结论。"""
import random

DIMENSIONS = ('accuracy', 'intent', 'service')
MARKS = ('改善', '持平', '变差')


def task_sampler(task_id):
    # UUID任务身份固定种子，只用于提交前故障重放；不同任务独立抽样。
    return random.Random(task_id).sample


def target_size(size):
    if type(size) is not int or size < 1:
        raise ValueError('参与数量必须为正整数')
    return (size + 9) // 10


def draw_population(population, sampler=random.sample):
    identifiers = [row['case_id'] for row in population]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('参与case必须唯一')
    target = target_size(len(identifiers))
    by_id = {row['case_id']: row for row in population}
    initial = sampler(identifiers, target)
    draws = [{'case_id': key, 'kind': 'initial', 'unusable_reasons': by_id[key]['reasons']
        if not by_id[key]['comparable'] else []} for key in initial]
    missing = target - sum(not row['unusable_reasons'] for row in draws)
    remaining = [key for key in identifiers if key not in initial and by_id[key]['comparable']]
    draws.extend({'case_id': key, 'kind': 'replacement', 'unusable_reasons': []}
        for key in sampler(remaining, min(missing, len(remaining))))
    return target, draws


def conclusion(target, marks):
    if len(marks) < target:
        return 'validation_failed'
    if any(row.get(key) == '变差' for row in marks for key in DIMENSIONS):
        return 'not_passed'
    if any(row.get(key) is None for row in marks for key in DIMENSIONS):
        return 'pending_confirmation'
    return 'passed'
