"""014真实生产HTTP重启；离线确定性草稿输入，无模型发送。"""
import json
from hashlib import sha256
from uuid import uuid4
import httpx
from test_task_execution import service
from test_qa_review_integration import drafts
from test_http_smoke import start_server,wait_ready
from test_evaluation_process import stop_tree


def test_production_http_export_snapshot_survives_crash_restart(service,tmp_path,monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY','')
    task,rows=drafts(service,1);identifier=rows[0]['id']
    service.database.stop();processes=[]
    with (tmp_path/'server.log').open('wb') as log:
        try:
            first,url=start_server(tmp_path,log);processes.append(first);wait_ready(first,url)
            body={'operation_id':str(uuid4()),'expected_revision':0,'question':'标准问,含"引用"','answer':'人工答案\n第二行'}
            response=httpx.patch(url+f'/api/v1/qa/{identifier}',json=body);assert response.status_code==200,response.text
            saved=response.json()['data']
            approval=httpx.post(url+f'/api/v1/qa/{identifier}/approve',json={'operation_id':str(uuid4()),'expected_revision':saved['revision'],'confirm':True})
            assert approval.status_code==200;approved=approval.json()['data']
            export_body={'operation_id':str(uuid4()),'selected_qa_ids':[identifier],'expected_qa_revisions':{identifier:approved['revision']}}
            exported=httpx.post(url+'/api/v1/exports',json=export_body);assert exported.status_code==201,exported.text
            A=exported.json()['data'];raw=httpx.get(url+A['download_url']).content
            detail=httpx.get(url+f"/api/v1/exports/{A['id']}").json()['data']
            (tmp_path/'export-A.csv').write_bytes(raw)
            assert A['content_hash']==sha256(raw).hexdigest()
            # 导出已提交后强杀，客户端未记住成功亦能按原operation查回。
            stop_tree(first)
            second,url=start_server(tmp_path,log);processes.append(second);wait_ready(second,url)
            assert httpx.get(url+f"/api/v1/operations/{export_body['operation_id']}").json()['data']['result_id']==A['id']
            replay=httpx.post(url+'/api/v1/exports',json=export_body)
            assert replay.status_code==200 and replay.json()['data']==A
            changed=httpx.patch(url+f'/api/v1/qa/{identifier}',json={**body,'operation_id':str(uuid4()),'expected_revision':approved['revision'],'answer':'尚未再次确认'})
            assert changed.status_code==200 and changed.json()['data']['review_state']=='pending_review'
            assert httpx.get(url+A['download_url']).content==raw
            assert httpx.get(url+f"/api/v1/exports/{A['id']}").json()['data']==detail
            assert len(httpx.get(url+'/api/v1/exports').json()['items'])==1
            assert httpx.get(url+f'/api/v1/qa/{identifier}').json()['data']['answer']=='尚未再次确认'
            (tmp_path/'export-recovery.json').write_text(json.dumps({'task_id':task['id'],'export':A,'snapshot':detail,'current':changed.json()['data'],'replayed':replay.json()['data']},ensure_ascii=False,indent=2),encoding='utf-8')
        finally:
            for process in processes:stop_tree(process)
