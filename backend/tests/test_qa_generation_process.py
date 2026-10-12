"""013本地HTTP＋强杀重启，QA成功不重复；不调用真实模型。"""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import httpx
from test_csv_import import encode, dialogue
from test_http_smoke import free_port,wait_ready
from test_task_process import wait_state
from test_evaluation_process import stop_tree,read_in_fresh_process


def start(directory,log):
    root=Path(__file__).resolve().parents[1];port=free_port()
    process=subprocess.Popen([sys.executable,'-m','uvicorn','qa_generation_test_server:app','--host','127.0.0.1','--port',str(port),'--workers','1'],
        cwd=root,env={**os.environ,'WORKBENCH_DATA_DIR':str(directory),'PYTHONPATH':str(root/'tests')+os.pathsep+str(root)},
        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    return process,f'http://127.0.0.1:{port}'


def test_default_application_qa_http_crash_restart_and_readonly_boundary(tmp_path):
    processes=[]
    with (tmp_path/'server.log').open('wb') as log:
        try:
            first,url=start(tmp_path,log);processes.append(first);wait_ready(first,url)
            ids={}
            for kind,rows in [('dialogues',[dialogue('0',question='问题0'),dialogue('1',question='问题1')]),('rules',[['r','规则','原文']]),('knowledge',[['k','知识','原文']])]:
                response=httpx.post(url+'/api/v1/uploads',data={'kind':kind,'operation_id':str(uuid4())},files={'file':('test.csv',encode(kind,rows),'text/csv')},timeout=5)
                assert response.status_code==201,response.text
                ids[kind]=response.json()['data']['id']
            body={'operation_id':str(uuid4()),'upload_id':ids['dialogues'],'rule_version_id':ids['rules'],'kb_version_id':ids['knowledge']}
            response=httpx.post(url+'/api/v1/evaluation-tasks',json=body,timeout=5);assert response.status_code==200,response.text
            task=response.json()['data']['id']
            before=wait_state(url,task,lambda x:x['phase']=='qa_generation' and sum(i['stage']=='standard_question' and i['state']=='succeeded' for i in x['items'])==1)
            listing=httpx.get(url+f'/api/v1/tasks/{task}/qa').json()['data']
            assert len(listing['drafts'])==len(listing['pending'])==1
            qa_id=listing['drafts'][0]['id'];assert 'history' not in listing['drafts'][0]
            detail=httpx.get(url+f'/api/v1/qa/{qa_id}').json()['data']
            assert detail['answer']=='' and detail['review_state']=='pending_review'
            assert detail['knowledge_gap']['snippet']=='问题0' and detail['trace']['prompt_version']=='standard-question-v2'
            # 014已获人工编辑/审核授权；缺operation/revision的请求仍不得更改草稿。
            assert httpx.patch(url+f'/api/v1/qa/{qa_id}',json={'answer':'缺少提交字段'}).status_code==422
            assert httpx.post(url+f'/api/v1/qa/{qa_id}/approve').status_code==422
            assert httpx.post(url+f'/api/v1/tasks/{task}/cancel',json={'operation_id':str(uuid4()),'expected_revision':before['revision']}).status_code==409
            assert httpx.post(url+'/api/v1/evaluation-tasks',json={**body,'operation_id':str(uuid4())}).status_code==409
            stop_tree(first)
            second,url=start(tmp_path,log);processes.append(second);wait_ready(second,url)
            (tmp_path/'release').write_text('恢复',encoding='utf-8')
            after=wait_state(url,task,lambda x:x['state']=='completed')
            final=httpx.get(url+f'/api/v1/tasks/{task}/qa').json()['data']
            assert len(final['drafts'])==2 and final['failures']==final['pending']==[]
            assert any(x['id']==qa_id and x['attempt_count']==1 for x in final['drafts'])
            assert sorted(x['attempt_count'] for x in final['drafts'])==[1,2]
            calls=[json.loads(line) for line in (tmp_path/'qa-calls.jsonl').read_text(encoding='utf-8').splitlines()]
            assert calls.count({'stage':'E','question':'问题0'})==calls.count({'stage':'E','question':'问题1'})==1
            assert calls.count({'stage':'Q','question':'问题0'})==1 and calls.count({'stage':'Q','question':'问题1'})==2
            (tmp_path/'qa-recovery.json').write_text(json.dumps({'before':before,'after':after,'draft':detail,'final':final,'calls':calls},ensure_ascii=False,indent=2),encoding='utf-8')
        finally:
            for process in processes:stop_tree(process)
    saved=read_in_fresh_process(tmp_path,task)
    assert len(saved['evaluation']['results'])==2 and len(saved['qa']['drafts'])==2
    (tmp_path/'qa-persisted.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
