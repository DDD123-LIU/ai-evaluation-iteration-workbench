"""本人实际补充确认及不可变来源查询；页面整合和效果任务留后续。"""
from uuid import UUID
from fastapi import APIRouter, Request, Response, Query
from pydantic import BaseModel, ConfigDict, StrictBool
from app.services.supplements import SupplementService

router = APIRouter(prefix='/api/v1/supplements')


class ConfirmSupplement(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    new_kb_id: UUID
    source_batch_id: UUID
    export_item_ids: list[UUID]
    confirm: StrictBool


@router.post('')
def create(body: ConfirmSupplement, request: Request, response: Response):
    result, created = SupplementService(request.app.state.database).save(str(body.new_kb_id),
        str(body.source_batch_id), [str(x) for x in body.export_item_ids], body.confirm, str(body.operation_id))
    response.status_code = 201 if created else 200
    return {'data': result}


@router.get('')
def listing(request: Request, new_kb_id: UUID | None = None, source_batch_id: UUID | None = None,
            offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    return {'items': SupplementService(request.app.state.database).listing(
        str(new_kb_id) if new_kb_id else None, str(source_batch_id) if source_batch_id else None, offset, limit)}


@router.get('/{identifier}')
def detail(identifier: UUID, request: Request):
    return {'data': SupplementService(request.app.state.database).detail(str(identifier))}
