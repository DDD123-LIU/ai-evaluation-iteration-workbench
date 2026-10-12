"""F28/F29确定性判据；人工标签是模拟输入。"""
import pytest
from app.domain.sampling import target_size, draw_population, conclusion


@pytest.mark.parametrize('size,target', [(1,1),(5,1),(20,2),(25,3),(100,10)])
def test_target_round_up(size,target):
    assert target_size(size)==target


@pytest.mark.parametrize('size', [0,-1,True,1.5])
def test_invalid_population(size):
    with pytest.raises(ValueError): target_size(size)


def population(n, bad=()):
    return [{'case_id': str(i), 'comparable': i not in bad, 'reasons': ['failed'] if i in bad else []} for i in range(n)]


def test_initial_failures_random_replacements_without_repeating():
    calls=[]
    def sampler(values,k):
        calls.append((values,k))
        return values[:k]
    target,rows=draw_population(population(25,{0,1}),sampler)
    assert target==3
    assert [x['case_id'] for x in rows]==['0','1','2','3','4']
    assert [x['kind'] for x in rows]==['initial']*3+['replacement']*2
    assert rows[0]['unusable_reasons']==['failed']
    assert calls[1][1]==2 and '0' not in calls[1][0]


def test_insufficient_keeps_failed_draw_and_target():
    target,rows=draw_population(population(25,set(range(24))),lambda values,k:values[:k])
    assert target==3 and len(rows)==4
    assert len([x for x in rows if not x['unusable_reasons']])==1
    assert conclusion(target,[{}])=='validation_failed'


def test_unique_population_required():
    with pytest.raises(ValueError): draw_population(population(1)*2)


def test_task_identity_replays_identical_precommit_draw():
    from uuid import uuid4
    from app.domain.sampling import task_sampler
    task=str(uuid4())
    assert draw_population(population(100),task_sampler(task))==draw_population(population(100),task_sampler(task))


@pytest.mark.parametrize('dimension', ['accuracy','intent','service'])
def test_any_worse_rejects_before_remaining_marks_complete(dimension):
    assert conclusion(2,[{dimension:'变差'},{}])=='not_passed'


@pytest.mark.parametrize('mark', ['改善','持平'])
def test_full_marks_pass_and_missing_not_equal(mark):
    assert conclusion(1,[dict.fromkeys(('accuracy','intent','service'),mark)])=='passed'
    assert conclusion(1,[{'accuracy':mark}])=='pending_confirmation'
