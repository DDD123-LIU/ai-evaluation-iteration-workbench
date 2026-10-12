"""真实本地HTTP启动、进程强杀和E结果恢复；SDK供应商为明确测试替身。"""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import httpx
from app.db.database import Database
from app.services.evaluation import results
from test_csv_import import encode, dialogue
from test_http_smoke import free_port, wait_ready, stop
from test_task_process import wait_state


def start(directory,log):
    root=Path(__file__).resolve().parents[1]; port=free_port()
    process=subprocess.Popen([sys.executable,'-m','uvicorn','evaluation_test_server:app','--host','127.0.0.1','--port',str(port),'--workers','1'],
        cwd=root,env={**os.environ,'WORKBENCH_DATA_DIR':str(directory),'PYTHONPATH':str(root/'tests')+os.pathsep+str(root)},
        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    return process,f'http://127.0.0.1:{port}'


def stop_tree(process):
    # Windows虚拟环境启动器会再创建解释器；终止整棵测试进程树后再读取同库。
    if os.name=='nt' and process.poll() is None:
        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],check=True,capture_output=True)
        process.wait(timeout=10)
    else:
        stop(process)



def read_in_fresh_process(directory,task_id):
    # 与真实重启一致：新进程打开SQLite，避免测试进程复用SQLite文件句柄状态。
    code="""
import json,sys
from pathlib import Path
from app.db.database import Database
from app.services.evaluation import results
from app.services.batch_metrics import summary
from app.services.qa_generation import generations
from sqlalchemy import text
D=Database(Path(sys.argv[1]));D.start()
try:
 with D.engine.connect() as c: integrity=c.execute(text('PRAGMA integrity_check')).scalar()
 print(json.dumps({'evaluation':results(D,sys.argv[2]),'summary':summary(D,sys.argv[2]),'qa':generations(D,sys.argv[2]),'integrity':integrity}))
finally:D.stop()
"""
    root=Path(__file__).resolve().parents[1]
    output=subprocess.run([sys.executable,'-c',code,str(directory),task_id],cwd=root,
        capture_output=True,text=True,check=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    value=json.loads(output.stdout)
    assert value['integrity']=='ok'
    return value


def test_http_evaluation_crash_restart_preserves_business_result(tmp_path):
    processes=[]
    with (tmp_path/'server.log').open('wb') as log:
        try:
            first,url=start(tmp_path,log); processes.append(first); wait_ready(first,url)
            ids={}
            for kind,rows in [('dialogues',[dialogue('0',question='问题0'),dialogue('1',question='问题1')]),('rules',[['r','规则','原文']]),('knowledge',[['k','知识','原文']])]:
                response=httpx.post(url+'/api/v1/uploads',data={'kind':kind,'operation_id':str(uuid4())},files={'file':('test.csv',encode(kind,rows),'text/csv')},timeout=5)
                assert response.status_code==201,response.text
                ids[kind]=response.json()['data']['id']
            body={'operation_id':str(uuid4()),'upload_id':ids['dialogues'],'rule_version_id':ids['rules'],'kb_version_id':ids['knowledge']}
            response=httpx.post(url+'/api/v1/evaluation-tasks',json=body,timeout=5)
            assert response.status_code==200,response.text
            task=response.json()['data']['id']
            before=wait_state(url,task,lambda value:value['progress']['succeeded']==1 and value['progress']['running']==1)
            stop_tree(first)
            second,url=start(tmp_path,log); processes.append(second); wait_ready(second,url)
            (tmp_path/'release').write_text('恢复',encoding='utf-8')
            after=wait_state(url,task,lambda value:value['state']=='completed')
            calls=[json.loads(line) for line in (tmp_path/'model-calls.jsonl').read_text(encoding='utf-8').splitlines()]
            assert [x['question'] for x in calls].count('问题0')==1 and [x['question'] for x in calls].count('问题1')==2
            assert sorted(item['attempt_count'] for item in after['items'])==[1,2]
            (tmp_path/'evaluation-recovery.json').write_text(json.dumps({'before':before,'after':after,'calls':calls},ensure_ascii=False,indent=2),encoding='utf-8')
        finally:
            for process in processes: stop_tree(process)
    saved=read_in_fresh_process(tmp_path,task)['evaluation']
    assert len(saved['results'])==2 and saved['final_errors']==[]
    assert all(x['composite_score']=='4.00' and not x['is_badcase'] for x in saved['results'])
    assert {x['trace']['kb_version_id'] for x in saved['results']}=={ids['knowledge']}
    (tmp_path/'evaluation-results.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
