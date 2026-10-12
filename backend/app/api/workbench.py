"""018页面所需只读资格信息，所有写入仍走008～017原接口。"""
from uuid import UUID
from fastapi import APIRouter,Request
from app.services.workbench import overview,qa_capabilities

router=APIRouter(prefix='/api/v1/workbench')


@router.get('')
def get(request:Request):
    return {'data':overview(request)}


@router.get('/qa/{identifier}/capabilities')
def qa(identifier:UUID,request:Request):
    return {'data':qa_capabilities(request.app.state.database,str(identifier))}
