"""TX09/TX10：人工写入、乐观版本、同操作回执与原字节历史；不调用模型。"""
import csv
import io
import json
from contextlib import suppress
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.exports import ExportEvent, ExportItem, QAWriteReceipt
from app.models.qa import QA
from app.models.evaluation import Gap
from app.models.execution import ExecutionItem
from app.models.imports import CaseRecord, OperationCommit
from app.services.imports import ServiceError
from app.services.execution import dump

CATEGORY = '知识库缺少对应信息'
FIELDS = ('question', 'answer', 'source_case_number', 'category')


def csv_bytes(rows):
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\r\n')
    writer.writerow(['标准问', '参考答案', '来源案例编号', '问题分类'])
    writer.writerows([row[field] for field in FIELDS] for row in rows)
    return buffer.getvalue().encode('utf-8-sig')


def current(session, identifier):
    qa = session.get(QA, identifier)
    if qa is None:
        raise ServiceError(404, 'NOT_FOUND', 'QA成功草稿不存在，生成失败不能审核')
    item = session.get(ExecutionItem, qa.q_item_id)
    case = session.get(CaseRecord, item.case_id)
    gap = session.get(Gap, qa.gap_id)
    return qa, case, item, gap


def view(qa, case):
    return {'id': qa.id, 'question': qa.question, 'answer': qa.answer,
            'source_case_number': case.csv_case_id, 'category': qa.category,
            'review_state': qa.review_state, 'revision': qa.revision}


def complete(qa, case):
    values = view(qa, case)
    if any(not values[key].strip() for key in FIELDS) or qa.category != CATEGORY:
        raise ServiceError(422, 'QA_INCOMPLETE', '标准问、参考答案、来源案例编号、固定问题分类须完整')


def revision(qa, expected):
    if qa.revision != expected:
        raise ServiceError(409, 'REVISION_CONFLICT', 'QA版本已变化，请读取最新内容后由本人处理')


def event_view(event):
    stamp = datetime.fromisoformat(event.created_at).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S%f')[:-3] + 'Z'
    return {'id': event.id, 'created_at': event.created_at, 'byte_length': event.byte_length,
            'content_hash': event.content_hash, 'filename': f'qa-{stamp}-{event.id}.csv',
            'download_url': f'/api/v1/exports/{event.id}/file'}


def item_view(item):
    return {name: getattr(item, name) for name in ('id', 'event_id', 'ordinal', 'qa_id',
        'qa_revision', 'case_id', 'source_batch_id', *FIELDS)}


class QAReviewService:
    def __init__(self, database):
        self.database = database

    def _write(self, operation_id, kind, body, action):
        request_hash = sha256(dump({'kind': kind, 'body': body}).encode('utf-8')).hexdigest()
        with self.database.write_lock, self.database.session() as session:
            try:
                previous = session.get(OperationCommit, operation_id)
                if previous:
                    if previous.kind != kind or previous.request_hash != request_hash:
                        raise ServiceError(409, 'OPERATION_CONFLICT', '同一操作编号不能用于不同动作或内容')
                    receipt = session.get(QAWriteReceipt, operation_id)
                    if receipt is None:
                        raise ServiceError(409, 'RESULT_INCONSISTENT', '原操作回执缺失，不能重复执行')
                    return json.loads(receipt.result_json), False
                result = action(session)
                session.add(OperationCommit(operation_id=operation_id, kind=kind, request_hash=request_hash,
                    result_type='export' if kind=='qa_export' else 'qa', result_id=result['id'],
                    committed_at=datetime.now(timezone.utc).isoformat()))
                session.flush()
                session.add(QAWriteReceipt(operation_id=operation_id, result_json=dump(result)))
                session.flush()
            except SQLAlchemyError:
                session.rollback()
                raise ServiceError(503, 'STORAGE_UNAVAILABLE', '本地保存失败，本次操作未提交；可用原编号原请求重传') from None
            try:
                session.commit()
            except SQLAlchemyError:
                with suppress(SQLAlchemyError):
                    session.rollback()
                raise ServiceError(503, 'COMMIT_UNKNOWN', '提交结果未知，请先查询原操作编号', 'unknown', operation_id) from None
            return result, True

    def edit(self, identifier, question, answer, expected_revision, operation_id):
        def action(session):
            qa, case, _, _ = current(session, identifier)
            revision(qa, expected_revision)
            if qa.question != question or qa.answer != answer:
                qa.question, qa.answer = question, answer
                qa.review_state = 'pending_review'
                qa.revision += 1
            return view(qa, case)
        return self._write(operation_id, 'qa_edit', {'id': identifier, 'question': question,
            'answer': answer, 'expected_revision': expected_revision}, action)

    def approve(self, identifier, expected_revision, confirm, operation_id):
        def action(session):
            qa, case, _, _ = current(session, identifier)
            revision(qa, expected_revision)
            if confirm is not True:
                raise ServiceError(422, 'CONFIRM_REQUIRED', '须本人明确确认内容才能通过')
            complete(qa, case)
            if qa.review_state != 'approved':
                qa.review_state = 'approved'
                qa.revision += 1
            return view(qa, case)
        return self._write(operation_id, 'qa_approve', {'id': identifier,
            'expected_revision': expected_revision, 'confirm': confirm}, action)

    def export(self, selected_qa_ids, expected_qa_revisions, operation_id):
        identifiers = sorted(set(selected_qa_ids))
        if not identifiers or set(identifiers) != set(expected_qa_revisions):
            raise ServiceError(422, 'SELECTION_INVALID', '须选择QA并提供与选择集合完全相同的版本映射')
        def action(session):
            sources = []
            for identifier in identifiers:
                qa, case, item, gap = current(session, identifier)
                revision(qa, expected_qa_revisions[identifier])
                if qa.review_state != 'approved':
                    raise ServiceError(409, 'QA_NOT_APPROVED', '所选QA尚未通过或修改后待重新审核')
                complete(qa, case)
                sources.append((qa, case, item, gap))
            sources.sort(key=lambda row: (row[2].task_id, row[1].row_ordinal, row[3].gap_ordinal))
            raw = csv_bytes([view(qa, case) for qa, case, _, _ in sources])
            event = ExportEvent(id=str(uuid4()), operation_id=operation_id,
                created_at=datetime.now(timezone.utc).isoformat(), csv_bytes=raw,
                byte_length=len(raw), content_hash=sha256(raw).hexdigest())
            session.add(event)
            session.flush()
            items = []
            for ordinal, (qa, case, source, _) in enumerate(sources, 1):
                item = ExportItem(id=str(uuid4()), event_id=event.id, ordinal=ordinal, qa_id=qa.id,
                    qa_revision=qa.revision, case_id=case.id, source_batch_id=source.task_id,
                    question=qa.question, answer=qa.answer, source_case_number=case.csv_case_id, category=qa.category)
                session.add(item)
                items.append(item)
            session.flush()
            return {**event_view(event), 'item_ids': [item.id for item in items]}
        return self._write(operation_id, 'qa_export', {'selected_qa_ids': identifiers,
            'expected_qa_revisions': expected_qa_revisions}, action)

    def list_exports(self, source_batch_id=None, offset=0, limit=20):
        query = select(ExportEvent)
        if source_batch_id is not None:
            query = query.where(ExportEvent.id.in_(select(ExportItem.event_id).where(ExportItem.source_batch_id==source_batch_id)))
        with self.database.session() as session:
            return [event_view(event) for event in session.scalars(query.order_by(ExportEvent.created_at.desc(), ExportEvent.id.desc()).offset(offset).limit(limit))]

    def detail(self, identifier):
        with self.database.session() as session:
            event = session.get(ExportEvent, identifier)
            if event is None:
                raise ServiceError(404, 'NOT_FOUND', '导出记录不存在')
            items = session.scalars(select(ExportItem).where(ExportItem.event_id==identifier).order_by(ExportItem.ordinal))
            return {**event_view(event), 'items': [item_view(item) for item in items]}

    def file(self, identifier):
        with self.database.session() as session:
            event = session.get(ExportEvent, identifier)
            if event is None:
                raise ServiceError(404, 'NOT_FOUND', '导出记录不存在')
            return event.csv_bytes, event_view(event)['filename']
