"""E05/E06内部执行结构；业务评分、QA、抽检表由后续模块建立。"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, CheckConstraint, UniqueConstraint, Index, text
from app.models.imports import Base


class Task(Base):
    __tablename__ = 'task'
    id = Column(String(36), primary_key=True)
    kind = Column(String(16), nullable=False)
    phase = Column(String(24), nullable=False)
    state = Column(String(16), nullable=False)
    revision = Column(Integer, nullable=False, default=0)
    cancel_epoch = Column(Integer, nullable=False, default=0)
    started_at = Column(String(40), nullable=False)
    automatic_ended_at = Column(String(40))
    elapsed_ms = Column(Integer)
    __table_args__ = (CheckConstraint("kind IN ('ordinary','effect')"),
        CheckConstraint("state IN ('running','completed','cancelled')"),
        CheckConstraint("phase IN ('evaluating','qa_generation','effect_automatic','done')"),
        CheckConstraint('revision >= 0 AND cancel_epoch >= 0'),
        Index('one_running_task', 'state', unique=True, sqlite_where=text("state='running'")))


class RuntimeSlot(Base):
    __tablename__ = 'runtime_slot'
    id = Column(Integer, primary_key=True)
    task_id = Column(ForeignKey('task.id'), unique=True)
    __table_args__ = (CheckConstraint('id=1'),)


class TaskCase(Base):
    __tablename__ = 'task_case'
    task_id = Column(ForeignKey('task.id', ondelete='CASCADE'), primary_key=True)
    case_id = Column(ForeignKey('case_record.id'), primary_key=True)
    ordinal = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint('task_id', 'ordinal'), CheckConstraint('ordinal >= 1'))


class OrdinaryTask(Base):
    __tablename__ = 'ordinary_task'
    task_id = Column(ForeignKey('task.id', ondelete='CASCADE'), primary_key=True)
    upload_id = Column(ForeignKey('dialogue_upload.id'), nullable=False)
    rule_version_id = Column(ForeignKey('material_version.id'), nullable=False)
    kb_version_id = Column(ForeignKey('material_version.id'), nullable=False)


class ConfigSnapshot(Base):
    __tablename__ = 'config_snapshot'
    id = Column(String(36), primary_key=True)
    task_id = Column(ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    stage = Column(String(24), nullable=False)
    contract_version = Column(Text, nullable=False)
    prompt_version = Column(Text, nullable=False)
    full_prompt = Column(Text, nullable=False)
    request_model = Column(Text, nullable=False)
    documented_release = Column(Text, nullable=False)
    parameters_json = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('task_id', 'stage'),)


class ExecutionItem(Base):
    __tablename__ = 'execution_item'
    id = Column(String(36), primary_key=True)
    task_id = Column(ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    case_id = Column(ForeignKey('case_record.id'), nullable=False)
    stage = Column(String(24), nullable=False)
    side = Column(String(8), nullable=False)
    gap_key = Column(Text, nullable=False)
    state = Column(String(16), nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    result_id = Column(String(36))
    request_json = Column(Text, nullable=False)
    next_attempt_at = Column(String(40))
    error_category = Column(String(16))
    error_detail = Column(Text)
    __table_args__ = (UniqueConstraint('task_id', 'case_id', 'stage', 'side', 'gap_key'),
        CheckConstraint('attempt_count BETWEEN 0 AND 3'),
        CheckConstraint("stage IN ('evaluation','standard_question','reply_generation')"),
        CheckConstraint("side IN ('original','old','new')"),
        CheckConstraint("state IN ('pending','running','succeeded','final_failed')"))


class Attempt(Base):
    __tablename__ = 'attempt'
    id = Column(String(36), primary_key=True)
    item_id = Column(ForeignKey('execution_item.id', ondelete='CASCADE'), nullable=False)
    ordinal = Column(Integer, nullable=False)
    state = Column(String(16), nullable=False)
    request_json = Column(Text, nullable=False)
    config_id = Column(ForeignKey('config_snapshot.id'), nullable=False)
    started_at = Column(String(40), nullable=False)
    ended_at = Column(String(40))
    response_envelope_json = Column(Text)
    raw_content = Column(Text)
    error_category = Column(String(16))
    error_detail = Column(Text)
    __table_args__ = (UniqueConstraint('item_id', 'ordinal'), CheckConstraint('ordinal BETWEEN 1 AND 3'))
