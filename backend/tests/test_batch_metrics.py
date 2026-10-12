"""F13～15/U05：独立固定数值预期，不调用模型。"""
import pytest
from app.domain.batch_metrics import calculate


def test_confirmed_example():
    m=calculate(100,90,84,1080)
    assert m['display']=={'pass_rate':'93.33%','average_score':'4.00','error_rate':'10.00%'}
    assert m['quality_warning'] and m['error_warning'] and not m['batch_passed']
    assert m['raw']['pass_rate']=={'numerator':84,'denominator':90}


@pytest.mark.parametrize('n,s,q,t,quality,error,passed',[
    (100,100,95,1200,False,False,False),
    (100,95,95,1140,False,False,True),
    (100,94,94,1128,False,True,False),
    (100,100,99,1200,False,False,False),
    (1,1,1,12,False,False,True),
    (1,1,0,11,True,False,False),
    (100,0,0,0,False,True,False),
])
def test_exact_boundaries(n,s,q,t,quality,error,passed):
    m=calculate(n,s,q,t)
    assert (m['quality_warning'],m['error_warning'],m['batch_passed'])==(quality,error,passed)


def test_no_success_is_null_not_zero():
    m=calculate(100,0,0,0)
    assert m['display']=={'pass_rate':None,'average_score':None,'error_rate':'100.00%'}
    assert m['raw']['pass_rate'] is None and m['raw']['average_score'] is None


def test_rounded_display_never_controls_threshold():
    # 大分母仅测试纯数学比较，不允许产品创建超过100条的批次。
    m=calculate(20001,20001,19000,240012)
    assert m['display']['pass_rate']=='95.00%' and m['quality_warning']
    m=calculate(20001,19000,19000,228000)
    assert m['display']['error_rate']=='5.00%' and m['error_warning']


@pytest.mark.parametrize('args',[(0,0,0,0),(1,2,1,12),(1,1,2,12),(1,0,0,1),(1,1,1,16),(1,1,1,2),(-1,0,0,0),(True,1,1,12),(1,1.0,1,12)])
def test_invalid_counts_are_not_valid_metrics(args):
    with pytest.raises(ValueError):calculate(*args)
