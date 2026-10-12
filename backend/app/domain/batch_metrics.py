"""F13～15：整数原始量判阈值，Decimal只负责两位展示。"""
from decimal import Decimal, ROUND_HALF_UP


def calculate(total, succeeded, qualified, score_total):
    values=(total,succeeded,qualified,score_total)
    if any(type(v) is not int for v in values) or not total>0 or not 0<=qualified<=succeeded<=total:
        raise ValueError('指标原始量必须为有效整数，输入分母必须大于0')
    if not 3*succeeded<=score_total<=15*succeeded:
        raise ValueError('三维总分与成功数不一致')
    errors=total-succeeded
    def ratio(a,b):return {'numerator':a,'denominator':b} if b else None
    def display(a,b,percent=False):
        if not b:return None
        value=(Decimal(a)*(100 if percent else 1)/Decimal(b)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
        return format(value,'.2f')+('%' if percent else '')
    return {'counts':{'total':total,'succeeded':succeeded,'qualified':qualified,'badcase':succeeded-qualified,
                      'final_errors':errors,'score_total':score_total},
            'raw':{'pass_rate':ratio(qualified,succeeded),'average_score':ratio(score_total,succeeded*3),'error_rate':ratio(errors,total)},
            'display':{'pass_rate':display(qualified,succeeded,True),'average_score':display(score_total,succeeded*3),'error_rate':display(errors,total,True)},
            'batch_passed':errors*100<=total*5 and succeeded==qualified,
            'quality_warning':succeeded>0 and qualified*100<succeeded*95,
            'error_warning':errors*100>total*5}
