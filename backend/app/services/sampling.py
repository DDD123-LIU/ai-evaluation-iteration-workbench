"""TX07/TX09：终态抽检轨迹及本人操作回执，复用现有SQLite写锁。"""
import json
from contextlib import suppress
from datetime import datetime, timezone
from hashlib import sha256
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.domain.sampling import draw_population, task_sampler, conclusion, DIMENSIONS, MARKS
from app.models.sampling import SamplingRun, Draw, HumanMark, SamplingReceipt
from app.models.execution import Task
from app.models.imports import OperationCommit
from app.services.execution import dump
from app.services.imports import ServiceError


def create_run(session, task_id, cases):
    if session.get(SamplingRun, task_id):
        return
    population = [{'case_id': row['case_id'], **row['comparison']} for row in cases]
    target, draws = draw_population(population, task_sampler(task_id))
    valid = [row for row in draws if not row['unusable_reasons']]
    session.add(SamplingRun(effect_task_id=task_id, population_size=len(population), target_size=target,
        population_json=dump(population), status=conclusion(target, [{} for _ in valid]),
        created_at=datetime.now(timezone.utc).isoformat()))
    session.flush()
    for ordinal, row in enumerate(draws, 1):
        session.add(Draw(effect_task_id=task_id, draw_ordinal=ordinal, case_id=row['case_id'],
            kind=row['kind'], unusable_reason=dump(row['unusable_reasons'])))
    for row in valid:
        session.add(HumanMark(effect_task_id=task_id, case_id=row['case_id'], revision=0))
    session.flush()


def run_view(session, task_id):
    run = session.get(SamplingRun, task_id)
    if run is None:
        return None
    marks = list(session.scalars(select(HumanMark).where(HumanMark.effect_task_id == task_id)))
    by_id = {row.case_id: row for row in marks}
    draws = []
    for row in session.scalars(select(Draw).where(Draw.effect_task_id == task_id).order_by(Draw.draw_ordinal)):
        mark = by_id.get(row.case_id)
        draws.append({'ordinal': row.draw_ordinal, 'case_id': row.case_id, 'kind': row.kind,
            'unusable_reasons': json.loads(row.unusable_reason), 'mark': None if mark is None else
            {**{key: getattr(mark, key) for key in DIMENSIONS}, 'revision': mark.revision}})
    return {'effect_task_id': task_id, 'population_size': run.population_size, 'target_size': run.target_size,
        'population': json.loads(run.population_json), 'created_at': run.created_at, 'draws': draws,
        'valid_count': len(marks), 'marking_allowed': len(marks) == run.target_size,
        'status': run.status, 'human_effect_conclusion': run.status}


class SamplingService:
    def __init__(self, database):
        self.database = database

    def get(self, task_id):
        with self.database.write_lock, self.database.session() as session:
            task = session.get(Task, task_id)
            if task is None or task.kind != 'effect':
                raise ServiceError(404, 'NOT_FOUND', '效果任务不存在')
            if task.state != 'completed':
                return {'effect_task_id': task_id, 'status': 'cancelled' if task.state == 'cancelled' else 'automatic_pending',
                    'population': [], 'draws': [], 'human_effect_conclusion': None, 'marking_allowed': False}
            if session.get(SamplingRun, task_id) is None:
                # 兼容已认可016历史终态，只补建缺失轨迹；一旦提交永不重抽。
                from app.services.effects import detail_in_session
                try:
                    create_run(session, task_id, detail_in_session(session, task_id)['cases'])
                    session.commit()
                except SQLAlchemyError:
                    with suppress(SQLAlchemyError): session.rollback()
                    raise ServiceError(503, 'SAMPLING_SAVE_UNKNOWN', '抽检保存结果未知，请重新查询本任务；不显示未提交抽样') from None
            return run_view(session, task_id)

    def mark(self, task_id, case_id, values, expected_revision, operation_id):
        if set(values) != set(DIMENSIONS) or any(value is not None and value not in MARKS for value in values.values()):
            raise ServiceError(422, 'MARK_INVALID', '三维只能为改善、持平、变差或未标记')
        body = {'task_id': task_id, 'case_id': case_id, 'values': values, 'expected_revision': expected_revision}
        request_hash = sha256(dump(body).encode('utf-8')).hexdigest()
        with self.database.write_lock, self.database.session() as session:
            previous = session.get(OperationCommit, operation_id)
            if previous:
                if previous.kind != 'sampling_mark' or previous.request_hash != request_hash:
                    raise ServiceError(409, 'OPERATION_CONFLICT', '同一操作编号不能用于不同内容')
                receipt = session.get(SamplingReceipt, operation_id)
                if receipt is None: raise ServiceError(409, 'RESULT_INCONSISTENT', '原操作回执缺失')
                return json.loads(receipt.result_json), False
            task = session.get(Task, task_id)
            run = session.get(SamplingRun, task_id)
            if task is None or task.kind != 'effect': raise ServiceError(404, 'NOT_FOUND', '效果任务不存在')
            if task.state != 'completed' or run is None:
                raise ServiceError(409, 'MARKING_UNAVAILABLE', '自动阶段未完成或抽检尚未保存')
            marks = list(session.scalars(select(HumanMark).where(HumanMark.effect_task_id == task_id)))
            if len(marks) != run.target_size:
                raise ServiceError(409, 'INSUFFICIENT_SAMPLES', '可比较样本不足，验证失败，不能人工标记')
            mark = session.get(HumanMark, (task_id, case_id))
            if mark is None: raise ServiceError(422, 'NOT_SELECTED', '只能标记本次有效抽检案例')
            if type(expected_revision) is not int or mark.revision != expected_revision:
                raise ServiceError(409, 'REVISION_CONFLICT', '人工标记版本已变化，请读取后由本人处理')
            try:
                if any(getattr(mark, key) != value for key, value in values.items()):
                    for key, value in values.items(): setattr(mark, key, value)
                    mark.revision += 1
                run.status = conclusion(run.target_size, [{key: getattr(row, key) for key in DIMENSIONS} for row in marks])
                session.flush()
                result = run_view(session, task_id)
                session.add(OperationCommit(operation_id=operation_id, kind='sampling_mark', request_hash=request_hash,
                    result_type='sampling', result_id=task_id, committed_at=datetime.now(timezone.utc).isoformat()))
                session.flush()
                session.add(SamplingReceipt(operation_id=operation_id, result_json=dump(result)))
                session.flush()
            except SQLAlchemyError:
                session.rollback()
                raise ServiceError(503, 'STORAGE_UNAVAILABLE', '人工标记未提交；可用原编号原请求重传') from None
            try:
                session.commit()
            except SQLAlchemyError:
                with suppress(SQLAlchemyError): session.rollback()
                raise ServiceError(503, 'COMMIT_UNKNOWN', '提交结果未知，请先查询原操作编号', 'unknown', operation_id) from None
            return result, True
