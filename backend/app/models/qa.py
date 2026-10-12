"""E10草稿，Q成功才建立；编辑/审核由014实现。"""
from sqlalchemy import Column,ForeignKey,String,Text,Integer,CheckConstraint
from app.models.imports import Base


class QA(Base):
    __tablename__='qa'
    id=Column(String(36),primary_key=True)
    q_item_id=Column(ForeignKey('execution_item.id',ondelete='CASCADE'),nullable=False,unique=True)
    gap_id=Column(ForeignKey('gap.id'),nullable=False,unique=True)
    original_question=Column(Text,nullable=False)
    question=Column(Text,nullable=False)
    answer=Column(Text,nullable=False)
    category=Column(Text,nullable=False)
    review_state=Column(String(20),nullable=False)
    revision=Column(Integer,nullable=False)
    __table_args__=(CheckConstraint("review_state IN ('pending_review','approved')"),CheckConstraint('revision>=0'))
