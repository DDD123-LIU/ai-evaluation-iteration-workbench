"""真实本地HTTP服务经SDK调用；地址仍为官方origin，通过本地传输层转送。"""
import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import httpx
from app.model_client.deepseek import DeepSeekTransport
from test_model_client import attempt
from test_model_contract import envelope, evaluation


def test_real_socket_sdk_call_and_clean_close():
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append((self.path,json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            body=json.dumps(envelope(json.dumps(evaluation()))).encode()
            self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,*args):
            pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True); thread.start()
    class LocalOnly(httpx.AsyncBaseTransport):
        def __init__(self):
            self.transport=httpx.AsyncHTTPTransport(retries=0)
        async def handle_async_request(self,request):
            assert request.url.host=='api.deepseek.com'
            local=httpx.Request(request.method,f'http://127.0.0.1:{server.server_port}{request.url.path}',headers=request.headers,content=request.content,extensions=request.extensions)
            return await self.transport.handle_async_request(local)
        async def aclose(self): await self.transport.aclose()
    async def run():
        client=DeepSeekTransport('test-only-key',http_client=httpx.AsyncClient(transport=LocalOnly()),token_counter=lambda _:10)
        try:
            result=await client.start_once(attempt())
            assert result.success and result.payload['contract']==evaluation()
            assert len(received)==1 and received[0][0]=='/chat/completions'
        finally: await client.close()
    try: asyncio.run(run())
    finally: server.shutdown(); server.server_close(); thread.join(timeout=5)
