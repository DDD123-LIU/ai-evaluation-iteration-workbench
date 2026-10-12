"""TX01：原始文件、全部记录、提交索引在同一事务保存。"""
from datetime import datetime, timezone
from contextlib import suppress
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.domain.csv_import import parse_csv
from app.models.imports import DialogueUpload, CaseRecord, MaterialVersion, RuleRow, KnowledgeRow, OperationCommit


class ServiceError(Exception):
    def __init__(self, status, code, message, commit_state="not_committed", resource_id=None):
        self.status, self.code, self.message = status, code, message
        self.commit_state, self.resource_id = commit_state, resource_id


def summary(record):
    return {"id": record.id, "filename": record.filename, "uploaded_at": record.uploaded_at,
            "row_count": record.row_count, **({"kind": record.kind} if isinstance(record, MaterialVersion) else {})}


class ImportService:
    def __init__(self, database):
        self.database = database

    def save(self, kind, raw, filename, operation_id):
        digest = sha256(kind.encode("ascii") + b"\0" + raw).hexdigest()
        with self.database.write_lock, self.database.session() as session:
            try:
                previous = session.get(OperationCommit, operation_id)
                if previous is not None:
                    if previous.request_hash != digest:
                        raise ServiceError(409, "OPERATION_CONFLICT", "同一操作编号不能用于不同内容")
                    model = DialogueUpload if previous.result_type == "upload" else MaterialVersion
                    return summary(session.get(model, previous.result_id)), False
                parsed = parse_csv(kind, raw)
                identifier = str(uuid4())
                now = datetime.now(timezone.utc).isoformat()
                fields = dict(id=identifier, raw_csv=raw, filename=filename, uploaded_at=now, row_count=len(parsed.rows))
                if kind == "dialogues":
                    record, result_type = DialogueUpload(**fields), "upload"
                else:
                    record, result_type = MaterialVersion(**fields, kind="rule" if kind == "rules" else "kb"), "material"
                session.add(record)
                # 先写父记录以执行外键，再写子行；仍处于同一事务。
                session.flush()
                for ordinal, row in enumerate(parsed.rows, 1):
                    if kind == "dialogues":
                        number, question, reply, chat = row.cells
                        session.add(CaseRecord(id=str(uuid4()), upload_id=identifier, csv_case_id=number,
                            row_ordinal=ordinal, question=question, original_reply=reply, chat_history=chat,
                            history_json=json.dumps(row.history, ensure_ascii=False)))
                    else:
                        model = RuleRow if kind == "rules" else KnowledgeRow
                        number, title, content = row.cells
                        session.add(model(version_id=identifier, source_id=number, title=title, content=content, row_ordinal=ordinal))
                session.add(OperationCommit(operation_id=operation_id, kind=kind, request_hash=digest,
                    result_type=result_type, result_id=identifier, committed_at=now))
                session.flush()
            except SQLAlchemyError:
                session.rollback()
                raise ServiceError(503, "STORAGE_UNAVAILABLE", "本地保存失败，整份未提交；修复后可用同一操作编号重传") from None
            result = summary(record)
            try:
                session.commit()
            except SQLAlchemyError:
                # COMMIT期间连接异常不能冒称未提交；由提交索引核对。
                # 若异常发生在提交确认后，Session已提交，rollback会再次报错。
                with suppress(SQLAlchemyError):
                    session.rollback()
                raise ServiceError(503, "COMMIT_UNKNOWN", "提交结果待核对，请查询此操作编号后使用同编号重传", "unknown", operation_id) from None
            return result, True

    def list_records(self, material, kind, offset, limit):
        model = MaterialVersion if material else DialogueUpload
        query = select(model)
        if material and kind is not None:
            query = query.where(model.kind == ("rule" if kind == "rules" else "kb"))
        query = query.order_by(model.uploaded_at.desc(), model.id.desc()).offset(offset).limit(limit)
        with self.database.session() as session:
            return [summary(record) for record in session.scalars(query)]

    def get_record(self, identifier, material, *, file=False):
        with self.database.session() as session:
            model = MaterialVersion if material else DialogueUpload
            record = session.get(model, identifier)
            if record is None:
                raise ServiceError(404, "NOT_FOUND", "记录不存在", resource_id=identifier)
            if file:
                return record.raw_csv
            result = summary(record)
            if material:
                row_model = RuleRow if record.kind == "rule" else KnowledgeRow
                rows = session.scalars(select(row_model).where(row_model.version_id == identifier).order_by(row_model.row_ordinal))
                result["rows"] = [{"source_id": row.source_id, "title": row.title, "content": row.content, "row_ordinal": row.row_ordinal} for row in rows]
            else:
                rows = session.scalars(select(CaseRecord).where(CaseRecord.upload_id == identifier).order_by(CaseRecord.row_ordinal))
                result["cases"] = [{"id": row.id, "csv_case_id": row.csv_case_id, "question": row.question,
                    "original_reply": row.original_reply, "chat_history": row.chat_history,
                    "history": row.history, "row_ordinal": row.row_ordinal} for row in rows]
            return result

    def operation(self, identifier):
        with self.database.session() as session:
            record = session.get(OperationCommit, identifier)
            if record is None:
                raise ServiceError(404, "NOT_COMMITTED", "没有此操作的已提交记录；可用同编号重传", resource_id=identifier)
            return {"operation_id": record.operation_id, "kind": record.kind, "result_type": record.result_type,
                    "result_id": record.result_id, "committed_at": record.committed_at}
