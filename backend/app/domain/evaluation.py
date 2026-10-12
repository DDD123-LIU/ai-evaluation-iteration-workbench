"""只派生单条结论，不猜语义、重写评分或聚合批次。"""
from decimal import Decimal, ROUND_HALF_UP
from app.domain.model_contract import CAUSES


def derived(contract, kind='ordinary'):
    scores=[contract['scores'][name]['score'] for name in ('accuracy','intent','service')]
    bad=any(score<4 for score in scores)
    knowledge=contract['primary_cause']==CAUSES[0] or CAUSES[0] in contract['secondary_causes']
    return {'composite_score':format((Decimal(sum(scores))/3).quantize(Decimal('.01'),rounding=ROUND_HALF_UP),'.2f'),
        'is_badcase':bad,'qa_eligible':kind=='ordinary' and bad and knowledge and not contract['has_material_conflict']}
