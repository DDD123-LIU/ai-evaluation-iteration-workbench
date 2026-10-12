"""017抽检轨迹读取和本人三维标记；不提供挑样或重新抽样入口。"""
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field
from app.services.sampling import SamplingService

router = APIRouter(prefix='/api/v1/effect-tasks')
Mark = Literal['改善', '持平', '变差'] | None


class MarkInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    expected_revision: int = Field(ge=0, strict=True)
    accuracy: Mark
    intent: Mark
    service: Mark


@router.get('/{task_id}/sampling')
def get(task_id: UUID, request: Request):
    return {'data': SamplingService(request.app.state.database).get(str(task_id))}


@router.patch('/{task_id}/sampling/{case_id}')
def mark(task_id: UUID, case_id: UUID, body: MarkInput, request: Request):
    values = body.model_dump(include={'accuracy', 'intent', 'service'})
    result, _ = SamplingService(request.app.state.database).mark(str(task_id), str(case_id), values,
        body.expected_revision, str(body.operation_id))
    return {'data': result}
