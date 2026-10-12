"""D03读取已持久评测终态；不计算指标，不新增分类决策。"""
import json
from sqlalchemy import select
from app.models.execution import Task, TaskCase, ExecutionItem, Attempt
from app.services.imports import ServiceError


def case_outcomes(database, task_id):
    with database.session() as session:
        task=session.get(Task,task_id)
        if task is None:
            raise ServiceError(404,'NOT_FOUND','任务不存在')
        if task.state=='cancelled':
            return {'eligible':False,'cancelled':True,'successes':[],'final_errors':[]}
        if task.kind!='ordinary':
            raise ServiceError(409,'TASK_KIND_MISMATCH','效果完整链结果由016承接')
        cases=list(session.scalars(select(TaskCase).where(TaskCase.task_id==task_id).order_by(TaskCase.ordinal)))
        successes,errors=[],[]
        for source in cases:
            item=session.scalar(select(ExecutionItem).where(ExecutionItem.task_id==task_id,
                ExecutionItem.case_id==source.case_id,ExecutionItem.stage=='evaluation',ExecutionItem.side=='original',ExecutionItem.gap_key==''))
            if item is None or item.state in ('pending','running'):
                return {'eligible':False,'cancelled':False,'successes':[],'final_errors':[]}
            if item.state=='succeeded':
                attempt=session.get(Attempt,item.result_id)
                if attempt is None or attempt.state!='succeeded' or not attempt.response_envelope_json:
                    raise RuntimeError('成功结果缺少持久依据')
                result=json.loads(attempt.response_envelope_json)
                successes.append({'case_id':source.case_id,'item_id':item.id,'attempt_count':item.attempt_count,
                    'last_attempt_id':attempt.id,'result':result['payload'],'envelope':result['envelope']})
            elif item.state=='final_failed':
                last=session.scalar(select(Attempt).where(Attempt.item_id==item.id).order_by(Attempt.ordinal.desc()))
                errors.append({'case_id':source.case_id,'item_id':item.id,'attempt_count':item.attempt_count,
                    'category':item.error_category,'detail':item.error_detail,'last_attempt_id':last.id if last else None})
            else:
                raise RuntimeError('未知评测终态')
        if len(successes)+len(errors)!=len(cases) or not cases:
            raise RuntimeError('成功与最终异常没有完整覆盖来源case')
        return {'eligible':True,'cancelled':False,'input_count':len(cases),'successes':successes,'final_errors':errors}
