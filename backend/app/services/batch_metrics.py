"""012普通全E终态快照及预警集合；不执行Q或模型调用。"""
import json
from sqlalchemy import select, delete
from app.domain.batch_metrics import calculate
from app.domain.evaluation import derived
from app.domain.execution import Transition
from app.models.batch_metrics import BatchSummary
from app.models.execution import Task, TaskCase, ExecutionItem, OrdinaryTask
from app.models.evaluation import EvaluationResult, FinalError
from app.models.imports import CaseRecord
from app.services.imports import ServiceError
from app.services.execution import dump
from app.services.evaluation import results


def freeze(session, task):
    """调用方持有009写事务；只有全部原始E终态才产生一份快照。"""
    if task.state=='cancelled':
        session.execute(delete(BatchSummary).where(BatchSummary.task_id==task.id))
        return {'status':'cancelled','data':None}
    if task.kind!='ordinary':return {'status':'not_applicable','data':None}
    existing=session.get(BatchSummary,task.id)
    if existing:return {'status':'available','data':json.loads(existing.payload_json)}
    source=list(session.scalars(select(TaskCase).where(TaskCase.task_id==task.id).order_by(TaskCase.ordinal)))
    if not 1<=len(source)<=100:raise ServiceError(409,'RESULT_INCONSISTENT','固定批次集合为空或超限，不能计算有效指标')
    items=list(session.scalars(select(ExecutionItem).where(ExecutionItem.task_id==task.id,ExecutionItem.stage=='evaluation',ExecutionItem.side=='original')))
    if len(items)!=len(source) or {i.case_id for i in items}!={c.case_id for c in source}:
        raise ServiceError(409,'RESULT_INCONSISTENT','评测项与固定case集合不一致')
    if any(i.state not in ('succeeded','final_failed') for i in items):return {'status':'pending','data':None}
    by_case={i.case_id:i for i in items}; succeeded=qualified=score_total=0; badcases=[]; errors=[]
    for case in source:
        item=by_case[case.case_id]; value=session.get(EvaluationResult,item.id); error=session.get(FinalError,item.id)
        if item.state=='succeeded':
            if value is None or error is not None:raise ServiceError(409,'RESULT_INCONSISTENT','成功case缺结果或同时有最终异常')
            contract=json.loads(value.contract_json); quality=derived(contract)
            succeeded+=1; score_total+=sum(contract['scores'][n]['score'] for n in ('accuracy','intent','service'))
            if quality['is_badcase']:badcases.append(case.case_id)
            else:qualified+=1
        else:
            if error is None or value is not None:raise ServiceError(409,'RESULT_INCONSISTENT','最终异常case缺记录或同时有成功结果')
            errors.append(case.case_id)
    ordinary=session.get(OrdinaryTask,task.id)
    if ordinary is None:raise ServiceError(409,'RESULT_INCONSISTENT','普通批次缺固定来源版本')
    payload={'task_id':task.id,'source':{'upload_id':ordinary.upload_id,'rule_version_id':ordinary.rule_version_id,'kb_version_id':ordinary.kb_version_id},
             **calculate(len(source),succeeded,qualified,score_total),'alerts':[]}
    for kind,active,case_ids,filter_name in [('quality',payload['quality_warning'],badcases,'badcase'),('error',payload['error_warning'],errors,'errors')]:
        if active:payload['alerts'].append({'kind':kind,'task_id':task.id,'problem_case_ids':case_ids,
                                           'target':{'path':f'/api/v1/tasks/{task.id}/cases','filter':filter_name}})
    session.add(BatchSummary(task_id=task.id,payload_json=dump(payload)));session.flush()
    return {'status':'available','data':payload}


def summary(database,task_id):
    # 已有011终态历史可在首次读取时幂等补建；后续读取使用同一快照。
    with database.write_lock,database.session() as session,session.begin():
        task=session.get(Task,task_id)
        if task is None:raise ServiceError(404,'NOT_FOUND','任务不存在')
        return freeze(session,task)


class MetricsHooks:
    """组合在EvaluationHooks之后，真实QA hooks之前；不自行生成Q。"""
    def __init__(self,next_hooks=None):self.next_hooks=next_hooks

    def item_saved(self,session,task,item,outcome):
        if self.next_hooks is None:raise ServiceError(409,'DEPENDENCY_NOT_READY','QA结果须由真实后续模块处理')
        return self.next_hooks.item_saved(session,task,item,outcome)

    def phase_finished(self,session,task):
        if task.kind!='ordinary':raise ServiceError(409,'DEPENDENCY_NOT_READY','效果任务由016接入，不复用普通批次结论')
        data=freeze(session,task)
        if data['status']!='available':raise ServiceError(409,'RESULT_INCONSISTENT','未全评测终态，不能交接阶段')
        if task.phase=='evaluating':
            values=session.scalars(select(EvaluationResult).join(ExecutionItem,EvaluationResult.item_id==ExecutionItem.id).where(ExecutionItem.task_id==task.id))
            if not any(derived(json.loads(value.contract_json))['qa_eligible'] for value in values):
                # 无应生成点（含全部异常），不进入QA，不调用其后续构造器。
                return Transition('done',[])
        if self.next_hooks is not None:return self.next_hooks.phase_finished(session,task)
        raise ServiceError(409,'DEPENDENCY_NOT_READY','有应生成QA或正在QA阶段，须接真实013接口，不提前完成任务')

    def cancelled(self,session,task):
        session.execute(delete(BatchSummary).where(BatchSummary.task_id==task.id))
        if self.next_hooks is not None and hasattr(self.next_hooks,'cancelled'):self.next_hooks.cancelled(session,task)


def cases(database,task_id,filter_name='all'):
    if filter_name not in ('all','badcase','errors'):raise ServiceError(422,'FILTER_INVALID','case集合过滤条件无效')
    saved=results(database,task_id)
    if saved['cancelled']:return []
    evaluations={row['case_id']:row for row in saved['results']}; errors={row['case_id']:row for row in saved['final_errors']}
    with database.session() as session:
        task=session.get(Task,task_id)
        if task.kind!='ordinary':raise ServiceError(409,'DEPENDENCY_NOT_READY','效果case由016提供')
        output=[]
        for source in session.scalars(select(TaskCase).where(TaskCase.task_id==task_id).order_by(TaskCase.ordinal)):
            value=evaluations.get(source.case_id);error=errors.get(source.case_id)
            if filter_name=='badcase' and not (value and value['is_badcase']):continue
            if filter_name=='errors' and error is None:continue
            record=session.get(CaseRecord,source.case_id)
            output.append({'task_id':task_id,'case_id':record.id,'case_number':record.csv_case_id,'question':record.question,
                           'original_reply':record.original_reply,'history':record.history,'evaluation':value,'final_error':error})
        return output
