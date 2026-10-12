"""007 E07～E09；不可变成功依据，派生均值及质量不重复持久化。"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from app.models.imports import Base


class EvaluationResult(Base):
    __tablename__='evaluation_result'
    item_id=Column(ForeignKey('execution_item.id',ondelete='CASCADE'),primary_key=True)
    contract_json=Column(Text,nullable=False)
    accuracy=Column(Integer,nullable=False)
    intent=Column(Integer,nullable=False)
    service=Column(Integer,nullable=False)
    accuracy_reason=Column(Text,nullable=False)
    intent_reason=Column(Text,nullable=False)
    service_reason=Column(Text,nullable=False)
    primary_cause=Column(Text)
    secondary_json=Column(Text,nullable=False)
    has_material_conflict=Column(Integer,nullable=False)
    __table_args__=(CheckConstraint('accuracy BETWEEN 1 AND 5 AND intent BETWEEN 1 AND 5 AND service BETWEEN 1 AND 5'),CheckConstraint('has_material_conflict IN (0,1)'),)


class Gap(Base):
    __tablename__='gap'
    id=Column(String(36),primary_key=True)
    result_item_id=Column(ForeignKey('evaluation_result.item_id',ondelete='CASCADE'),nullable=False)
    gap_ordinal=Column(Integer,nullable=False)
    gap_text=Column(Text,nullable=False)
    snippet=Column(Text,nullable=False)
    reason=Column(Text,nullable=False)
    location_json=Column(Text,nullable=False)
    __table_args__=(UniqueConstraint('result_item_id','gap_ordinal'),CheckConstraint('gap_ordinal>=1'),)


class FinalError(Base):
    __tablename__='final_error'
    item_id=Column(ForeignKey('execution_item.id',ondelete='CASCADE'),primary_key=True)
    category=Column(String(24),nullable=False)
    last_attempt_id=Column(ForeignKey('attempt.id'))
    __table_args__=(CheckConstraint("category IN ('CALL_ERROR','PARSE_ERROR','INCOMPLETE_RESULT')"),)
