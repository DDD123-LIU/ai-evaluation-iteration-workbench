"""E12不可变人工补充确认；同知识库允许多个独立记录。"""
from sqlalchemy import Column, String, ForeignKey
from app.models.imports import Base


class Supplement(Base):
    __tablename__ = 'supplement'
    id = Column(String(36), primary_key=True)
    new_kb_id = Column(ForeignKey('material_version.id'), nullable=False)
    source_batch_id = Column(ForeignKey('ordinary_task.task_id'), nullable=False)
    confirmed_at = Column(String(40), nullable=False)


class SupplementItem(Base):
    __tablename__ = 'supplement_item'
    supplement_id = Column(ForeignKey('supplement.id'), primary_key=True)
    export_item_id = Column(ForeignKey('export_item.id'), primary_key=True)
