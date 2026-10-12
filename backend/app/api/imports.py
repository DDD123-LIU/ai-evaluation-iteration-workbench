"""模板、上传、不可变历史及提交结果查询，不含后续任务入口。"""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import Response, JSONResponse
from app.domain.csv_import import HEADERS
from app.services.imports import ServiceError

Kind = Literal["dialogues", "rules", "knowledge"]
MaterialKind = Literal["rules", "knowledge"]
router = APIRouter(prefix="/api/v1")


@router.get("/templates/{kind}")
def template(kind: Kind):
    return Response((",".join(HEADERS[kind]) + "\r\n").encode("utf-8-sig"), media_type="text/csv; charset=utf-8")


async def exact_upload_fields(request: Request):
    form = await request.form()
    allowed = {"kind", "operation_id", "file"}
    if set(form) - allowed or any(len(form.getlist(key)) != 1 for key in allowed if key in form):
        raise ServiceError(422, "REQUEST_INVALID", "上传只允许kind、operation_id、file三个字段，且不得重复")


@router.post("/uploads", dependencies=[Depends(exact_upload_fields)])
def upload(request: Request, kind: Annotated[Kind, Form()], operation_id: Annotated[UUID, Form()], file: Annotated[UploadFile, File()]):
    try:
        raw = file.file.read()
    except OSError:
        raise ServiceError(503, "UPLOAD_READ_FAILED", "本地上传文件读取失败，未导入任何数据") from None
    result, created = request.app.state.imports.save(kind, raw, file.filename or "", str(operation_id))
    return JSONResponse({"data": result}, status_code=201 if created else 200)


@router.get("/uploads")
def uploads(request: Request, offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return {"items": request.app.state.imports.list_records(False, None, offset, limit)}


@router.get("/materials")
def materials(request: Request, kind: MaterialKind | None = None, offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return {"items": request.app.state.imports.list_records(True, kind, offset, limit)}


@router.get("/uploads/{identifier}")
def upload_detail(request: Request, identifier: UUID):
    return {"data": request.app.state.imports.get_record(str(identifier), False)}


@router.get("/uploads/{identifier}/file")
def upload_file(request: Request, identifier: UUID):
    return Response(request.app.state.imports.get_record(str(identifier), False, file=True), media_type="text/csv; charset=utf-8")


@router.get("/materials/{identifier}")
def material_detail(request: Request, identifier: UUID):
    return {"data": request.app.state.imports.get_record(str(identifier), True)}


@router.get("/materials/{identifier}/file")
def material_file(request: Request, identifier: UUID):
    return Response(request.app.state.imports.get_record(str(identifier), True, file=True), media_type="text/csv; charset=utf-8")


@router.get("/operations/{identifier}")
def operation(request: Request, identifier: UUID):
    return {"data": request.app.state.imports.operation(str(identifier))}
