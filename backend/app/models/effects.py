"""E13固定两侧资料与G结果；不维护人工抽检或效果结论。"""
from sqlalchemy import Column, String, Text, ForeignKey
from app.models.imports import Base


class EffectTask(Base):
    __tablename__ = 'effect_task'
    task_id = Column(ForeignKey('task.id', ondelete='CASCADE'), primary_key=True)
    supplement_id = Column(ForeignKey('supplement.id'), nullable=False)
    source_batch_id = Column(ForeignKey('task.id'), nullable=False)
    old_kb_id = Column(ForeignKey('material_version.id'), nullable=False)
    new_kb_id = Column(ForeignKey('material_version.id'), nullable=False)
    rule_version_id = Column(ForeignKey('material_version.id'), nullable=False)


class GenerationResult(Base):
    __tablename__ = 'generation_result'
    item_id = Column(ForeignKey('execution_item.id', ondelete='CASCADE'), primary_key=True)
    reply = Column(Text, nullable=False)
