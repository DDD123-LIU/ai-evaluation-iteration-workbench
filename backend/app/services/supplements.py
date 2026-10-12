"""TX09人工确认与历史来源同事务保存；不修改知识库、不创建效果任务。"""
from contextlib import suppress
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.supplements import Supplement, SupplementItem
from app.models.exports import ExportItem, ExportEvent
from app.models.execution import OrdinaryTask, Task, TaskCase
from app.models.imports import MaterialVersion, CaseRecord, OperationCommit
from app.services.execution import dump
from app.services.imports import ImportService, ServiceError
from app.services.qa_review import item_view, event_view


def summary(row):
    return {key: getattr(row, key) for key in ('id', 'new_kb_id', 'source_batch_id', 'confirmed_at')}


class SupplementService:
    def __init__(self, database):
        self.database = database

    def save(self, new_kb_id, source_batch_id, export_item_ids, confirm, operation_id):
        # 重复勾选不改变实际来源集合；顺序不产生不同操作语义。
        identifiers = sorted(set(export_item_ids))
        request_hash = sha256(dump({'new_kb_id': new_kb_id, 'source_batch_id': source_batch_id,
            'export_item_ids': identifiers, 'confirm': confirm}).encode('utf-8')).hexdigest()
        with self.database.write_lock, self.database.session() as session:
            try:
                previous = session.get(OperationCommit, operation_id)
                if previous:
                    if previous.kind != 'supplement' or previous.request_hash != request_hash:
                        raise ServiceError(409, 'OPERATION_CONFLICT', '同操作编号不能用于不同动作或内容')
                    row = session.get(Supplement, previous.result_id)
                    if row is None:
                        raise ServiceError(409, 'RESULT_INCONSISTENT', '已提交补充记录缺失')
                    return summary(row), False
                if confirm is not True:
                    raise ServiceError(422, 'CONFIRM_REQUIRED', '须本人明确确认实际加入的历史内容')
                if not identifiers:
                    raise ServiceError(422, 'NO_VALIDATION_CASES', '无可验证案例')
                kb = session.get(MaterialVersion, new_kb_id)
                if kb is None or kb.kind != 'kb':
                    raise ServiceError(422, 'KB_VERSION_INVALID', '请选择已导入的知识库版本')
                original = session.get(OrdinaryTask, source_batch_id)
                task = session.get(Task, source_batch_id)
                if original is None or task is None or task.state == 'cancelled':
                    raise ServiceError(422, 'SOURCE_BATCH_INVALID', '来源须为有效普通原批次，取消批次已作废')
                for identifier in identifiers:
                    item = session.get(ExportItem, identifier)
                    if item is None or session.get(ExportEvent, item.event_id) is None:
                        raise ServiceError(422, 'SNAPSHOT_NOT_FOUND', '须选择实际已导出的历史条目，不能使用未导出QA')
                    if item.source_batch_id != source_batch_id:
                        raise ServiceError(422, 'CROSS_BATCH_SOURCE', '历史来源必须属于同一原批次')
                    if session.get(TaskCase, (source_batch_id, item.case_id)) is None:
                        raise ServiceError(409, 'SOURCE_INCONSISTENT', '历史条目与原批次案例关联不一致')
                row = Supplement(id=str(uuid4()), new_kb_id=new_kb_id, source_batch_id=source_batch_id,
                    confirmed_at=datetime.now(timezone.utc).isoformat())
                session.add(row)
                session.flush()
                session.add_all([SupplementItem(supplement_id=row.id, export_item_id=x) for x in identifiers])
                session.flush()
                session.add(OperationCommit(operation_id=operation_id, kind='supplement', request_hash=request_hash,
                    result_type='supplement', result_id=row.id, committed_at=row.confirmed_at))
                session.flush()
                result = summary(row)
            except SQLAlchemyError:
                session.rollback()
                raise ServiceError(503, 'STORAGE_UNAVAILABLE', '补充关联保存失败，整份未提交') from None
            try:
                session.commit()
            except SQLAlchemyError:
                with suppress(SQLAlchemyError):
                    session.rollback()
                raise ServiceError(503, 'COMMIT_UNKNOWN', '提交结果未知，请查询原操作编号', 'unknown', operation_id) from None
            return result, True

    def detail(self, identifier):
        with self.database.session() as session:
            row = session.get(Supplement, identifier)
            if row is None:
                raise ServiceError(404, 'NOT_FOUND', '补充记录不存在')
            original = session.get(OrdinaryTask, row.source_batch_id)
            items = list(session.scalars(select(ExportItem).join(SupplementItem,
                SupplementItem.export_item_id == ExportItem.id).where(SupplementItem.supplement_id == identifier)
                .order_by(ExportItem.event_id, ExportItem.ordinal)))
            selected = {item.case_id for item in items}
            cases = list(session.scalars(select(CaseRecord).join(TaskCase, TaskCase.case_id == CaseRecord.id)
                .where(TaskCase.task_id == row.source_batch_id, CaseRecord.id.in_(selected)).order_by(TaskCase.ordinal)))
            result = summary(row)
            result.update({'confirmed': bool(row.confirmed_at), 'old_kb_id': original.kb_version_id,
                'rule_version_id': original.rule_version_id, 'upload_id': original.upload_id,
                'snapshots': [{**item_view(item), 'export': event_view(session.get(ExportEvent, item.event_id))} for item in items],
                'source_case_ids': [case.id for case in cases],
                'cases': [{'id': case.id, 'csv_case_id': case.csv_case_id, 'question': case.question,
                    'original_reply': case.original_reply, 'chat_history': case.chat_history, 'history': case.history} for case in cases]})
            result['can_validate'] = result['confirmed'] and bool(cases)
            result['message'] = '可验证案例已限定为本人所选来源' if result['can_validate'] else '无可验证案例'
            result['links'] = {'new_kb': f'/api/v1/materials/{row.new_kb_id}',
                'old_kb': f'/api/v1/materials/{original.kb_version_id}',
                'rules': f'/api/v1/materials/{original.rule_version_id}',
                'original_batch': f'/api/v1/tasks/{row.source_batch_id}',
                'upload': f'/api/v1/uploads/{original.upload_id}'}
            return result

    def validation_input(self, identifier):
        """016的只读消费契约：固定原资料与精确case集合，无任务创建副作用。"""
        result = self.detail(identifier)
        imports = ImportService(self.database)
        result['materials'] = {key: imports.get_record(result[key], True)
            for key in ('new_kb_id', 'old_kb_id', 'rule_version_id')}
        return result

    def listing(self, new_kb_id=None, source_batch_id=None, offset=0, limit=20):
        with self.database.session() as session:
            query = select(Supplement)
            if new_kb_id:
                query = query.where(Supplement.new_kb_id == new_kb_id)
            if source_batch_id:
                query = query.where(Supplement.source_batch_id == source_batch_id)
            return [summary(row) for row in session.scalars(query.order_by(Supplement.confirmed_at.desc(), Supplement.id)
                .offset(offset).limit(limit))]
