"""后端持久进度及取消；真实普通任务组装由011接入。"""
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.services.imports import ServiceError
from app.services.batch_metrics import summary, cases
from app.services.qa_generation import generations, draft_detail

router = APIRouter(prefix='/api/v1')


def task_summary(database, task_id):
    # 调度进度仍可读取；缺少完整业务结果时明确不可统计，不能伪造指标。
    try:
        return summary(database, task_id)
    except ServiceError as error:
        if error.code != 'RESULT_INCONSISTENT':
            raise
        return {'status': 'unavailable', 'data': None, 'error': error.code, 'message': error.message}


class EvaluationStart(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    upload_id: UUID
    rule_version_id: UUID
    kb_version_id: UUID


class CancelRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    expected_revision: int = Field(ge=0, strict=True)


@router.get('/tasks')
async def list_tasks(request: Request):
    database = request.app.state.database
    data = request.app.state.tasks.list()
    for task in data:
        task['summary'] = task_summary(database, task['id'])
    return {'data': data, 'runtime_error': request.app.state.executor.last_error}


@router.get('/tasks/{task_id}')
async def get_task(task_id: UUID, request: Request):
    runtime = request.app.state.executor
    result = request.app.state.tasks.get(str(task_id))
    result['summary'] = task_summary(request.app.state.database, str(task_id))
    return {'data': result, 'storage_unavailable': str(task_id) in runtime.storage_blocked,
        'runtime_error': runtime.last_error}


@router.get('/tasks/{task_id}/cases')
async def task_cases(task_id: UUID, request: Request, filter: Literal['all', 'badcase', 'errors'] = 'all'):
    values = cases(request.app.state.database, str(task_id), filter)
    data = []
    for value in values:
        evaluation = value['evaluation']
        error = value['final_error']
        data.append({'task_id': value['task_id'], 'case_id': value['case_id'],
            'case_number': value['case_number'], 'question': value['question'],
            'evaluation': None if evaluation is None else {
                'scores': {name: score['score'] for name, score in evaluation['contract']['scores'].items()},
                'composite_score': evaluation['composite_score'], 'is_badcase': evaluation['is_badcase'],
                'primary_cause': evaluation['contract']['primary_cause']},
            'final_error': None if error is None else {
                'category': error['category'], 'attempt_count': error['attempt_count']}})
    return {'data': data}


@router.get('/tasks/{task_id}/cases/{case_id}')
async def task_case(task_id: UUID, case_id: UUID, request: Request):
    values = cases(request.app.state.database, str(task_id))
    value = next((row for row in values if row['case_id'] == str(case_id)), None)
    if value is None:
        raise ServiceError(404, 'NOT_FOUND', 'case不属于此批次或批次已取消')
    return {'data': value}


@router.post('/tasks/{task_id}/cancel')
async def cancel_task(task_id: UUID, body: CancelRequest, request: Request):
    result = await request.app.state.executor.cancel(str(task_id), body.expected_revision, str(body.operation_id))
    return {'data': result}


@router.get('/tasks/{task_id}/qa')
async def task_qa(task_id: UUID, request: Request):
    values = generations(request.app.state.database, str(task_id))
    # 列表只给摘要；完整上下文、证据及版本由详情接口返回。
    fields = ('id', 'task_id', 'case_id', 'gap_id', 'original_question',
              'standard_question', 'review_state', 'attempt_count')
    values['drafts'] = [{key: row[key] for key in fields} for row in values['drafts']]
    return {'data': values}


@router.get('/qa/{qa_id}')
async def qa_detail(qa_id: UUID, request: Request):
    return {'data': draft_detail(request.app.state.database, str(qa_id))}


@router.post('/evaluation-tasks')
async def start_evaluation(body: EvaluationStart, request: Request):
    builder = request.app.state.task_builder
    if builder is None or request.app.state.executor.transport is None or request.app.state.tasks.hooks is None:
        raise ServiceError(409, 'DEPENDENCY_NOT_READY', '模型单次调用及评测组装模块尚未接入')
    plan = builder(body)
    return {'data': request.app.state.tasks.start(plan, str(body.operation_id))}
