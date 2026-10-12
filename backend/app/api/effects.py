"""016效果任务发起及完整依据读取；抽检和页面由后续提供。"""
from uuid import UUID
from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import SQLAlchemyError
from app.services.effects import EffectBuilder, detail
from app.services.imports import ServiceError

router = APIRouter(prefix='/api/v1')


class EffectStart(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID


@router.post('/supplements/{identifier}/effect-tasks')
async def start(identifier: UUID, body: EffectStart, request: Request):
    if request.app.state.executor.transport is None:
        raise ServiceError(409, 'DEPENDENCY_NOT_READY', '模型调用未就绪；未创建效果任务')
    plan = EffectBuilder(request.app.state.database)(str(identifier))
    try:
        result = request.app.state.tasks.start(plan, str(body.operation_id))
    except SQLAlchemyError:
        raise ServiceError(503, 'COMMIT_UNKNOWN', '启动结果未知，请先查询原操作编号', 'unknown', str(body.operation_id)) from None
    return {'data': result}


@router.get('/effect-tasks/{identifier}')
async def get(identifier: UUID, request: Request):
    return {'data': detail(request.app.state.database, str(identifier))}
