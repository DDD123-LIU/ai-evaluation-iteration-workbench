"""单worker本地运行；启动取得目录锁并完成迁移，关闭释放连接。"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.api.imports import router
from app.db.database import Database
from app.domain.csv_import import ImportValidationError
from app.services.imports import ImportService, ServiceError
from app.services.execution import TaskService
from app.runtime.executor import Executor
from app.api.tasks import router as tasks_router
from app.api.qa_review import router as qa_review_router
from app.api.supplements import router as supplements_router
from app.api.effects import router as effects_router
from app.api.sampling import router as sampling_router
from app.api.workbench import router as workbench_router


def error_response(status, code, message, resource_id=None, field_errors=None, commit_state="not_committed"):
    return JSONResponse(status_code=status, content={"code": code, "message": message, "resource_id": resource_id,
        "field_errors": field_errors or [], "commit_state": commit_state})


def create_app(data_dir: Path | None = None, *, transport=None, task_builder=None, task_hooks=None):
    directory = data_dir or Path(os.environ.get("WORKBENCH_DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))
    database = Database(Path(directory))
    if task_builder is None and task_hooks is None:
        from app.prompts.standard_question import prompt_config
        from app.services.evaluation import EvaluationBuilder, EvaluationHooks
        from app.services.batch_metrics import MetricsHooks
        from app.services.qa_generation import QAHooks
        task_builder = EvaluationBuilder(database, prompt_config())
        from app.services.effects import TaskHooks
        task_hooks = TaskHooks(EvaluationHooks(MetricsHooks(QAHooks())))
    if transport is None:
        from app.model_client.deepseek import from_environment
        transport = from_environment()
    tasks = TaskService(database, task_hooks)
    executor = Executor(tasks, transport)

    @asynccontextmanager
    async def lifespan(app):
        database.start()
        try:
            await executor.start()
            yield
        finally:
            try:
                await executor.stop()
            finally:
                try:
                    if transport is not None and hasattr(transport, "close"):
                        await transport.close()
                finally:
                    database.stop()

    app = FastAPI(title="本地工作台：CSV资料与持久任务执行", lifespan=lifespan)
    app.state.database = database
    app.state.imports = ImportService(database)
    app.state.tasks = tasks
    app.state.executor = executor
    app.state.task_builder = task_builder
    app.include_router(router)
    app.include_router(tasks_router)
    app.include_router(qa_review_router)
    app.include_router(supplements_router)
    app.include_router(effects_router)
    app.include_router(sampling_router)
    app.include_router(workbench_router)
    # 018构建产物同源提供；API保持原路由及错误处理，不把404伪装成页面。
    from fastapi.staticfiles import StaticFiles
    frontend_dist = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
    if frontend_dist.exists():
        app.mount('/', StaticFiles(directory=frontend_dist, html=True), name='workbench-ui')

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        code = "NOT_FOUND" if error.status_code == 404 else "METHOD_NOT_ALLOWED" if error.status_code == 405 else "HTTP_ERROR"
        return error_response(error.status_code, code, str(error.detail))

    @app.exception_handler(ImportValidationError)
    async def csv_error(request: Request, error: ImportValidationError):
        return error_response(422, "CSV_INVALID", "整份文件未导入，请修正后重传", field_errors=error.errors)

    @app.exception_handler(RequestValidationError)
    async def request_error(request: Request, error: RequestValidationError):
        fields = [{"field": ".".join(str(part) for part in item["loc"]), "code": item["type"], "message": item["msg"]} for item in error.errors()]
        return error_response(422, "REQUEST_INVALID", "请求字段无效", field_errors=fields)

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, error: ServiceError):
        return error_response(error.status, error.code, error.message, error.resource_id, commit_state=error.commit_state)

    @app.exception_handler(SQLAlchemyError)
    async def storage_error(request: Request, error: SQLAlchemyError):
        return error_response(503, "STORAGE_UNAVAILABLE", "本地数据库暂不可读，请修复后重新查询", commit_state="unknown")

    return app


app = create_app()
