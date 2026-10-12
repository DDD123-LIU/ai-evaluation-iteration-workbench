"""真实本地Uvicorn冒烟，使用临时库，无模型、部署或正式样本。"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx

from test_csv_import import dialogue, encode


def free_port():
    with socket.socket() as socket_:
        socket_.bind(("127.0.0.1", 0))
        return socket_.getsockname()[1]


def start_server(directory, log):
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--workers", "1"],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "WORKBENCH_DATA_DIR": str(directory)},
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    return process, f"http://127.0.0.1:{port}"


def wait_ready(process, url):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("本地服务提前退出，见pytest临时目录日志")
        try:
            if httpx.get(url + "/api/v1/uploads", timeout=1).status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.2)
    raise AssertionError("本地服务启动超时")


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_real_http_import_lock_crash_restart(tmp_path):
    directory = tmp_path / "isolated-data"
    processes = []
    with (tmp_path / "http.log").open("wb") as log:
        try:
            first, url = start_server(directory, log)
            processes.append(first)
            wait_ready(first, url)
            saved = []
            with httpx.Client(base_url=url, timeout=10) as client:
                assert client.get("/docs").status_code == 200
                for kind in ("dialogues", "rules", "knowledge"):
                    raw = encode(kind, [dialogue()] if kind == "dialogues" else [["1", "标题", '内容,\n"引用"']], bom=True)
                    response = client.post("/api/v1/uploads", data={"kind": kind, "operation_id": str(uuid4())}, files={"file": ("模拟.csv", raw, "text/csv")})
                    assert response.status_code == 201, response.text
                    route = "uploads" if kind == "dialogues" else "materials"
                    path = f"/api/v1/{route}/{response.json()['data']['id']}"
                    assert client.get(path + "/file").content == raw
                    saved.append((path, raw))
                invalid = client.post("/api/v1/uploads", data={"kind": "rules", "operation_id": str(uuid4())}, files={"file": ("错误.csv", b"invalid")})
                assert invalid.status_code == 422
            second, _ = start_server(directory, log)
            processes.append(second)
            assert second.wait(timeout=20) != 0
            # 强制终止模拟进程中断，不经应用lifespan清理。
            stop(first)
            restarted, restart_url = start_server(directory, log)
            processes.append(restarted)
            wait_ready(restarted, restart_url)
            with httpx.Client(base_url=restart_url, timeout=10) as client:
                for path, raw in saved:
                    assert client.get(path).status_code == 200
                    assert client.get(path + "/file").content == raw
        finally:
            for process in processes:
                stop(process)
