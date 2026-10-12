"""017真实本地HTTP进程重启后抽补轨迹及人工进度不变。"""
import json
from uuid import uuid4
import httpx
from test_task_execution import service
from test_sampling_integration import ready,mark
from test_effects_process import start_process
from test_http_smoke import wait_ready
from test_evaluation_process import stop_tree


def test_http_restart_keeps_sampling_and_partial_marks(service,tmp_path):
    task,svc=ready(service)
    before,_=mark(svc,task,{'accuracy':'改善','intent':None,'service':'持平'})
    service.database.stop()
    records=[]
    with (tmp_path/'server.log').open('wb') as log:
        for turn in range(2):
            process,url=start_process(tmp_path,log)
            try:
                wait_ready(process,url)
                path=url+'/api/v1/effect-tasks/'+task+'/sampling'
                read=httpx.get(path).json()['data']
                assert read==before
                assert httpx.get(path).json()['data']==before
                records.append(read)
                if turn==1:
                    selected=read['draws'][0]
                    body={'operation_id':str(uuid4()),'expected_revision':1,'accuracy':'改善','intent':'持平','service':'持平'}
                    result=httpx.patch(path+'/'+selected['case_id'],json=body).json()['data']
                    assert result['status']=='passed'
                    assert httpx.get(url+'/api/v1/effect-tasks/'+task).json()['data']['human_effect_conclusion']=='passed'
                    records.append(result)
            finally:stop_tree(process)
    (tmp_path/'sampling-restart.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
