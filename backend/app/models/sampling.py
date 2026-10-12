"""E14抽检范围、不可变初补轨迹与本人三维进度。"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from app.models.imports import Base


class SamplingRun(Base):
    __tablename__ = 'sampling_run'
    effect_task_id = Column(ForeignKey('effect_task.task_id', ondelete='CASCADE'), primary_key=True)
    population_size = Column(Integer, nullable=False)
    target_size = Column(Integer, nullable=False)
    population_json = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(String, nullable=False)


class Draw(Base):
    __tablename__ = 'draw'
    effect_task_id = Column(ForeignKey('sampling_run.effect_task_id', ondelete='CASCADE'), primary_key=True)
    draw_ordinal = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey('case_record.id'), nullable=False)
    kind = Column(String, nullable=False)
    unusable_reason = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('effect_task_id', 'case_id'),)


class HumanMark(Base):
    __tablename__ = 'human_mark'
    effect_task_id = Column(ForeignKey('sampling_run.effect_task_id', ondelete='CASCADE'), primary_key=True)
    case_id = Column(ForeignKey('case_record.id'), primary_key=True)
    accuracy = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    service = Column(String, nullable=True)
    revision = Column(Integer, nullable=False, default=0)
    __table_args__ = tuple(CheckConstraint(f"{key} IS NULL OR {key} IN ('改善','持平','变差')")
        for key in ('accuracy', 'intent', 'service'))


class SamplingReceipt(Base):
    __tablename__ = 'sampling_receipt'
    operation_id = Column(ForeignKey('operation_commit.operation_id'), primary_key=True)
    result_json = Column(Text, nullable=False)
