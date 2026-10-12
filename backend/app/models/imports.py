"""E01～E04和TX01提交索引；历史内容不提供修改入口。"""
import json

from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint, String, Text, LargeBinary, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DialogueUpload(Base):
    __tablename__ = "dialogue_upload"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    raw_csv: Mapped[bytes] = mapped_column(LargeBinary)
    filename: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[str] = mapped_column(String(40))
    row_count: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint("row_count BETWEEN 1 AND 100"),)


class CaseRecord(Base):
    __tablename__ = "case_record"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    upload_id: Mapped[str] = mapped_column(ForeignKey("dialogue_upload.id"))
    csv_case_id: Mapped[str] = mapped_column(Text)
    row_ordinal: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    original_reply: Mapped[str] = mapped_column(Text)
    chat_history: Mapped[str] = mapped_column(Text)
    history_json: Mapped[str] = mapped_column("H_json", Text)
    __table_args__ = (UniqueConstraint("upload_id", "csv_case_id"), UniqueConstraint("upload_id", "row_ordinal"), CheckConstraint("row_ordinal >= 1"))

    @property
    def history(self) -> list[dict[str, str]]:
        return json.loads(self.history_json)


class MaterialVersion(Base):
    __tablename__ = "material_version"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(4))
    raw_csv: Mapped[bytes] = mapped_column(LargeBinary)
    filename: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[str] = mapped_column(String(40))
    row_count: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint("kind IN ('rule', 'kb')"), CheckConstraint("row_count >= 1"))


class RuleRow(Base):
    __tablename__ = "rule_row"
    version_id: Mapped[str] = mapped_column(ForeignKey("material_version.id"), primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    row_ordinal: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("version_id", "row_ordinal"), CheckConstraint("row_ordinal >= 1"))


class KnowledgeRow(Base):
    __tablename__ = "kb_row"
    version_id: Mapped[str] = mapped_column(ForeignKey("material_version.id"), primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    row_ordinal: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("version_id", "row_ordinal"), CheckConstraint("row_ordinal >= 1"))


class OperationCommit(Base):
    __tablename__ = "operation_commit"
    operation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    request_hash: Mapped[str] = mapped_column(String(64))
    result_type: Mapped[str] = mapped_column(String(20))
    result_id: Mapped[str] = mapped_column(String(36))
    committed_at: Mapped[str] = mapped_column(String(40))
