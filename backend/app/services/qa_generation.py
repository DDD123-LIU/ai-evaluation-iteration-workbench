"""013 E→Q及只读来源；009/010仍唯一计次、调用、校验边界。"""
import json
from uuid import uuid5,NAMESPACE_URL
from sqlalchemy import select
from app.domain.execution import ItemSpec,Transition
from app.domain.evaluation import derived
from app.domain.model_contract import CAUSES
from app.models.qa import QA
from app.models.evaluation import Gap,EvaluationResult
from app.models.execution import Task,TaskCase,ExecutionItem,ConfigSnapshot,Attempt,OrdinaryTask
from app.models.imports import CaseRecord
from app.services.execution import dump
from app.services.imports import ServiceError


def eligible_gaps(session,task):
    if task.kind!='ordinary' or task.state!='running' or task.phase!='evaluating':return []
    items=list(session.scalars(select(ExecutionItem).where(ExecutionItem.task_id==task.id,ExecutionItem.stage=='evaluation')))
    sources=list(session.scalars(select(TaskCase).where(TaskCase.task_id==task.id).order_by(TaskCase.ordinal)))
    if not sources or len(items)!=len(sources) or any(item.state not in ('succeeded','final_failed') for item in items):return []
    by_case={item.case_id:item for item in items}; output=[]
    if set(by_case)!={source.case_id for source in sources}:
        raise ServiceError(409,'RESULT_INCONSISTENT','评测结果与批次case不一致')
    for source in sources:
        item=by_case.get(source.case_id)
        if item is None or item.state!='succeeded':continue
        result=session.get(EvaluationResult,item.id)
        if result is None:raise ServiceError(409,'RESULT_INCONSISTENT','成功评测缺少持久结果')
        if derived(json.loads(result.contract_json))['qa_eligible']:
            gaps=list(session.scalars(select(Gap).where(Gap.result_item_id==item.id).order_by(Gap.gap_ordinal)))
            if not gaps:raise ServiceError(409,'RESULT_INCONSISTENT','应生成QA的缺失点未保存')
            output.extend((item,gap) for gap in gaps)
    return output


def request_for(case,gap,config,task_id):
    data={'original_question':case.question,'original_reply':case.original_reply,'history':case.history,
          'knowledge_gap':{'gap':gap.gap_text,'snippet':gap.snippet,'reason':gap.reason}}
    return {'messages':[{'role':'system','content':config.full_prompt},{'role':'user','content':dump(data)}],
            'history':case.history,'source':{'task_id':task_id,'case_id':case.id,'gap_id':gap.id}}


class QAHooks:
    def phase_finished(self,session,task):
        if task.kind!='ordinary' or task.state!='running':raise ServiceError(409,'QA_FORBIDDEN','只接普通运行任务，不为取消或效果任务生成QA')
        if task.phase=='qa_generation':
            if session.scalar(select(ExecutionItem.id).where(ExecutionItem.task_id==task.id,ExecutionItem.stage=='standard_question',ExecutionItem.state.in_(('pending','running')))):
                raise ServiceError(409,'QA_NOT_FINISHED','QA尚未全终态，不能释放窗口')
            return Transition('done',[])
        if task.phase!='evaluating':raise ServiceError(409,'QA_FORBIDDEN','不在评测交接阶段')
        items=list(session.scalars(select(ExecutionItem).where(ExecutionItem.task_id==task.id,ExecutionItem.stage=='evaluation')))
        if not items or any(i.state not in ('succeeded','final_failed') for i in items):raise ServiceError(409,'EVALUATION_NOT_FINISHED','评测未完成，不生成QA')
        config=session.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id==task.id,ConfigSnapshot.stage=='standard_question'))
        if config is None:raise ServiceError(409,'DEPENDENCY_NOT_READY','Q配置未提前冻结')
        output=[]
        for item,gap in eligible_gaps(session,task):
            case=session.get(CaseRecord,item.case_id)
            output.append(ItemSpec(case.id,'standard_question','original',gap.id,request_for(case,gap,config,task.id)))
        return Transition('qa_generation',output) if output else Transition('done',[])

    def item_saved(self,session,task,item,outcome):
        if item.stage!='standard_question' or task.kind!='ordinary' or task.phase!='qa_generation':raise ServiceError(409,'QA_FORBIDDEN','只能保存普通QA阶段结果')
        if not outcome.success:return []
        if session.scalar(select(QA.id).where(QA.q_item_id==item.id)):return []
        gap=session.get(Gap,item.gap_key)
        if gap is None:raise ServiceError(409,'RESULT_INCONSISTENT','Q来源缺失点不存在')
        source=session.get(ExecutionItem,gap.result_item_id)
        if source.task_id!=task.id or source.case_id!=item.case_id:raise ServiceError(409,'RESULT_INCONSISTENT','Q来源跨批次或case')
        case=session.get(CaseRecord,item.case_id)
        session.add(QA(id=str(uuid5(NAMESPACE_URL,'qa:'+gap.id)),q_item_id=item.id,gap_id=gap.id,
            original_question=case.question,question=outcome.payload['contract']['standard_question'],answer='',
            category=CAUSES[0],review_state='pending_review',revision=0))
        return []


def generations(database,task_id):
    with database.session() as session:
        task=session.get(Task,task_id)
        if task is None:raise ServiceError(404,'NOT_FOUND','任务不存在')
        if task.state=='cancelled':return {'drafts':[],'failures':[],'pending':[]}
        output={'drafts':[],'failures':[],'pending':[]}
        ordinary=session.get(OrdinaryTask,task_id)
        for item in session.scalars(select(ExecutionItem).where(ExecutionItem.task_id==task_id,ExecutionItem.stage=='standard_question').order_by(ExecutionItem.id)):
            identity={'task_id':task_id,'case_id':item.case_id,'gap_id':item.gap_key,'q_item_id':item.id,'attempt_count':item.attempt_count}
            qa=session.scalar(select(QA).where(QA.q_item_id==item.id))
            if qa:
                case=session.get(CaseRecord,item.case_id);gap=session.get(Gap,qa.gap_id)
                config=session.scalar(select(ConfigSnapshot).where(ConfigSnapshot.task_id==task_id,ConfigSnapshot.stage=='standard_question'))
                attempt=session.get(Attempt,item.result_id)
                output['drafts'].append({**identity,'id':qa.id,'original_question':qa.original_question,'standard_question':qa.question,
                    'answer':qa.answer,'category':qa.category,'review_state':qa.review_state,'revision':qa.revision,
                    'original_reply':case.original_reply,'history':case.history,
                    'knowledge_gap':{'gap':gap.gap_text,'snippet':gap.snippet,'reason':gap.reason,'location':json.loads(gap.location_json)},
                    'trace':{'upload_id':ordinary.upload_id,'rule_version_id':ordinary.rule_version_id,'kb_version_id':ordinary.kb_version_id,
                        'evaluation_item_id':gap.result_item_id,'config_id':config.id,'prompt_version':config.prompt_version,'full_prompt':config.full_prompt,
                        'contract_version':config.contract_version,'request_model':config.request_model,'parameters':json.loads(config.parameters_json),
                        'documented_release':config.documented_release,'attempt_id':attempt.id,'request':json.loads(attempt.request_json),
                        'response':json.loads(attempt.response_envelope_json)}})
            elif item.state=='final_failed':
                output['failures'].append({**identity,'error_category':item.error_category,'error_detail':item.error_detail,'reviewable':False})
            elif item.state=='succeeded':
                raise ServiceError(409,'RESULT_INCONSISTENT','成功Q结果缺少草稿')
            else:output['pending'].append({**identity,'state':item.state})
        return output


def draft_detail(database,qa_id):
    with database.session() as session:
        qa=session.get(QA,qa_id)
        if qa is None:raise ServiceError(404,'NOT_FOUND','QA草稿不存在')
        task_id=session.get(ExecutionItem,qa.q_item_id).task_id
    return next(row for row in generations(database,task_id)['drafts'] if row['id']==qa_id)
