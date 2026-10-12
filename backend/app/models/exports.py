"""E11不可变导出事件/条目及TX09原提交回执；不增加审核状态。"""
from sqlalchemy import Column, String, Text, Integer, LargeBinary, ForeignKey, UniqueConstraint, CheckConstraint
from app.models.imports import Base


class ExportEvent(Base):
    __tablename__ = 'export_event'
    id = Column(String(36), primary_key=True)
    operation_id = Column(String(36), nullable=False, unique=True)
    created_at = Column(String(40), nullable=False)
    csv_bytes = Column(LargeBinary, nullable=False)
    byte_length = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    __table_args__ = (CheckConstraint('byte_length>0'),)


class ExportItem(Base):
    __tablename__ = 'export_item'
    id = Column(String(36), primary_key=True)
    event_id = Column(ForeignKey('export_event.id'), nullable=False)
    ordinal = Column(Integer, nullable=False)
    qa_id = Column(ForeignKey('qa.id'), nullable=False)
    qa_revision = Column(Integer, nullable=False)
    case_id = Column(ForeignKey('case_record.id'), nullable=False)
    source_batch_id = Column(ForeignKey('task.id'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source_case_number = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('event_id', 'ordinal'), UniqueConstraint('event_id', 'qa_id'),
                     CheckConstraint('ordinal>=1 AND qa_revision>=0'))


class QAWriteReceipt(Base):
    __tablename__ = 'qa_write_receipt'
    operation_id = Column(ForeignKey('operation_commit.operation_id'), primary_key=True)
    result_json = Column(Text, nullable=False)
