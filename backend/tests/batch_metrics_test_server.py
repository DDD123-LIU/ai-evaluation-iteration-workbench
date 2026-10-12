"""仅012本地进程冒烟：复用011明确SDK替身，注入真实汇总hooks。"""
from evaluation_test_server import app
from app.services.evaluation import EvaluationHooks
from app.services.batch_metrics import MetricsHooks
app.state.tasks.hooks=EvaluationHooks(MetricsHooks())
