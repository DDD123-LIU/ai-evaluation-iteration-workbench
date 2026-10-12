"""E05：一份终态派生快照；不保存可编辑的第二份评分。"""
from sqlalchemy import Column, ForeignKey, Text
from app.models.imports import Base


class BatchSummary(Base):
    __tablename__='batch_summary'
    task_id=Column(ForeignKey('task.id',ondelete='CASCADE'),primary_key=True)
    payload_json=Column(Text,nullable=False)
