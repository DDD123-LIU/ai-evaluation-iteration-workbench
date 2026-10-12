"""人工审核与所选导出；历史读取不引用当前问答、不产生新事件。"""
from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Request, Response, Query
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr
from app.services.qa_review import QAReviewService

router = APIRouter(prefix='/api/v1')


class EditQA(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    expected_revision: int = Field(ge=0, strict=True)
    question: StrictStr
    answer: StrictStr


class ApproveQA(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    expected_revision: int = Field(ge=0, strict=True)
    confirm: StrictBool


class ExportQA(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    selected_qa_ids: list[UUID] = Field(min_length=1)
    expected_qa_revisions: dict[UUID, Annotated[int, Field(ge=0, strict=True)]]


def service(request):
    return QAReviewService(request.app.state.database)


@router.patch('/qa/{qa_id}')
def edit(qa_id: UUID, body: EditQA, request: Request):
    result, _ = service(request).edit(str(qa_id), body.question, body.answer, body.expected_revision, str(body.operation_id))
    return {'data': result}


@router.post('/qa/{qa_id}/approve')
def approve(qa_id: UUID, body: ApproveQA, request: Request):
    result, _ = service(request).approve(str(qa_id), body.expected_revision, body.confirm, str(body.operation_id))
    return {'data': result}


@router.post('/exports')
def export(body: ExportQA, request: Request, response: Response):
    result, created = service(request).export([str(x) for x in body.selected_qa_ids],
        {str(key): value for key, value in body.expected_qa_revisions.items()}, str(body.operation_id))
    response.status_code = 201 if created else 200
    return {'data': result}


@router.get('/exports')
def listing(request: Request, source_batch_id: UUID | None = None,
            offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    return {'items': service(request).list_exports(str(source_batch_id) if source_batch_id else None, offset, limit)}


@router.get('/exports/{event_id}')
def detail(event_id: UUID, request: Request):
    return {'data': service(request).detail(str(event_id))}


@router.get('/exports/{event_id}/file')
def file(event_id: UUID, request: Request):
    raw, filename = service(request).file(str(event_id))
    return Response(raw, media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
