"""018只读页面适配，复用既有权威规则，不新增业务状态。"""
from sqlalchemy import select,func
from app.models.execution import RuntimeSlot, OrdinaryTask,TaskCase
from app.models.effects import EffectTask
from app.models.sampling import SamplingRun
from app.services.qa_review import current, complete
from app.services.imports import ServiceError


def overview(request):
    database=request.app.state.database
    with database.session() as session:
        slot=session.get(RuntimeSlot,1)
        ready=request.app.state.executor.transport is not None
        active=slot.task_id if slot else None
        tasks=[]
        for task in request.app.state.tasks.list():
            task['phase_progress']=phase_progress(task,session.scalar(select(func.count()).select_from(TaskCase).where(TaskCase.task_id==task['id'])))
            task['capabilities']={'can_cancel':task['state']=='running' and task['phase']!='qa_generation'}
            source=session.get(OrdinaryTask,task['id']) if task['kind']=='ordinary' else session.get(EffectTask,task['id'])
            fields=('upload_id','rule_version_id','kb_version_id') if task['kind']=='ordinary' else ('supplement_id','source_batch_id','old_kb_id','new_kb_id','rule_version_id')
            task['source']={key:getattr(source,key) for key in fields} if source else None
            run=session.get(SamplingRun,task['id'])
            task['human_effect_conclusion']=run.status if run else None
            if task['kind']=='ordinary':
                from app.api.tasks import task_summary
                task['summary']=task_summary(database,task['id'])
                metrics=task['summary']['data']
                if metrics:
                    for alert in metrics['alerts']:
                        quality=alert['kind']=='quality'
                        alert.update(metric_name='通过率' if quality else '异常率',
                            display_value=metrics['display']['pass_rate' if quality else 'error_rate'],
                            threshold='通过率 < 95%' if quality else '异常率 > 5%')
            tasks.append(task)
        return {'tasks':tasks,'active_task_id':active,'model_ready':ready,'can_start':bool(slot) and not active and ready,
            'start_reason':'自动任务正在运行，无排队' if active else '模型未配置，无法启动；可查看历史记录' if not ready else '可启动自动任务',
            'runtime_error':request.app.state.executor.last_error}


def phase_progress(task,population):
    """只归组已持久的调用单元。效果E未建立时明示等待G或上游失败，不缩分母。"""
    groups=[('evaluation','original'),('standard_question','original')] if task['kind']=='ordinary' else [
        (stage,side) for side in ('old','new') for stage in ('reply_generation','evaluation')]
    rows=[]
    for stage,side in groups:
        items=[i for i in task['items'] if i['stage']==stage and i['side']==side]
        if task['kind']=='ordinary' and not items:continue
        counts={state:sum(i['state']==state for i in items) for state in ('succeeded','final_failed','running','pending')}
        counts.update(waiting_for_generation=0,upstream_generation_failed=0)
        if task['kind']=='effect' and stage=='evaluation':
            present={i['case_id'] for i in items}
            for item in task['items']:
                if item['stage']=='reply_generation' and item['side']==side and item['case_id'] not in present:
                    key='upstream_generation_failed' if item['state']=='final_failed' else 'waiting_for_generation'
                    counts[key]+=1
        rows.append({'stage':stage,'side':side,'total':len(items) if task['kind']=='ordinary' else population,**counts})
    return rows


def qa_capabilities(database,identifier):
    with database.session() as session:
        qa,case,_,_=current(session,identifier)
        try:
            complete(qa,case)
            valid=True
        except ServiceError:
            valid=False
        return {'can_edit':True,'can_approve':valid,'can_export':valid and qa.review_state=='approved',
            'source_case_number':case.csv_case_id,
            'reason':'请补全标准问和参考答案并保存后，由本人确认' if not valid else '内容由本人审核，模型不保证答案正确'}
