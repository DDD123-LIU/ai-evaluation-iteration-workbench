"""本模块接口/真实SQLite事务验证；无任务调度或模型调用。"""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.main import create_app
from app.models.imports import CaseRecord, DialogueUpload, MaterialVersion, OperationCommit
from test_csv_import import dialogue, encode


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "product")) as client:
        yield client


def upload(client, kind="dialogues", rows=None, operation_id=None, raw=None):
    if raw is None:
        raw = encode(kind, rows or ([dialogue()] if kind == "dialogues" else [["1", "名称", "内容"]]))
    return client.post("/api/v1/uploads", data={"kind": kind, "operation_id": operation_id or str(uuid4())}, files={"file": ("模拟.csv", raw, "text/csv")})


@pytest.mark.parametrize("kind", ["dialogues", "rules", "knowledge"])
def test_templates_upload_and_readback(client, kind):
    template = client.get(f"/api/v1/templates/{kind}")
    assert template.status_code == 200
    assert template.content.decode("utf-8-sig").splitlines()[0] == ",".join({"dialogues": ["案例编号", "用户问题", "客服回答", "聊天记录"], "rules": ["规则编号", "规则名称", "规则内容"], "knowledge": ["知识编号", "知识标题", "知识内容"]}[kind])
    response = upload(client, kind)
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    route = "uploads" if kind == "dialogues" else "materials"
    detail = client.get(f"/api/v1/{route}/{data['id']}").json()["data"]
    assert detail["row_count"] == 1
    assert detail["uploaded_at"].endswith("+00:00")
    assert client.get(f"/api/v1/{route}/{data['id']}/file").content == encode(kind, [dialogue()] if kind == "dialogues" else [["1", "名称", "内容"]])
    assert len(client.get(f"/api/v1/{route}").json()["items"]) == 1


def test_repeated_history_creates_separate_identity_and_preserves_case(client):
    raw = encode("dialogues", [dialogue(question="问题,\n包含引用\"", history="用户：问题,\n包含引用\"")], bom=True)
    first, second = upload(client, raw=raw), upload(client, raw=raw)
    assert first.status_code == second.status_code == 201
    assert first.json()["data"]["id"] != second.json()["data"]["id"]
    with client.app.state.database.session() as session:
        records = session.scalars(select(CaseRecord)).all()
        assert len(records) == 2
        assert records[0].question == "问题,\n包含引用\""
        assert records[0].chat_history == "用户：问题,\n包含引用\""
        assert records[0].history == [{"role": "user", "content": records[0].question}]


def test_any_error_zero_partial_writes(client):
    response = upload(client, rows=[dialogue(), dialogue("2", history="用户：不一致")])
    assert response.status_code == 422
    error = response.json()
    assert error["commit_state"] == "not_committed"
    assert error["field_errors"][0]["case_id"] == "2"
    with client.app.state.database.session() as session:
        assert session.scalars(select(DialogueUpload)).all() == []
        assert session.scalars(select(CaseRecord)).all() == []
        assert session.scalars(select(OperationCommit)).all() == []


@pytest.mark.parametrize("kind", ["rules", "knowledge"])
def test_material_failures_keep_previous_versions(client, kind):
    first = upload(client, kind).json()["data"]["id"]
    original = client.get(f"/api/v1/materials/{first}").json()
    for raw in [b"", encode(kind, [["1", "名称", ""]]), encode(kind, [["1", "A", "内容"], ["1", "B", "内容"]])]:
        assert upload(client, kind, raw=raw).status_code == 422
    second = upload(client, kind, rows=[["1", "新名称", "新内容"]]).json()["data"]["id"]
    assert second != first
    assert client.get(f"/api/v1/materials/{first}").json() == original
    assert len(client.get(f"/api/v1/materials?kind={kind}").json()["items"]) == 2


def test_operation_replay_and_payload_conflict(client):
    operation_id = str(uuid4())
    first = upload(client, operation_id=operation_id)
    replay = upload(client, operation_id=operation_id)
    assert first.status_code == 201 and replay.status_code == 200
    assert replay.json() == first.json()
    assert upload(client, operation_id=operation_id, rows=[dialogue(reply="修改")]).status_code == 409
    assert client.get(f"/api/v1/operations/{operation_id}").json()["data"]["result_id"] == first.json()["data"]["id"]


def test_storage_failure_rolls_back_all_rows(client):
    database = client.app.state.database
    with database.engine.begin() as connection:
        connection.exec_driver_sql("CREATE TRIGGER fail_import BEFORE INSERT ON case_record WHEN NEW.csv_case_id = '2' BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    response = upload(client, rows=[dialogue(), dialogue("2", question="第二问")])
    assert response.status_code == 503
    assert response.json()["commit_state"] == "not_committed"
    with database.session() as session:
        assert session.scalars(select(DialogueUpload)).all() == []
        assert session.scalars(select(CaseRecord)).all() == []
        assert session.scalars(select(OperationCommit)).all() == []


def test_persistence_restart_and_pragmas(tmp_path):
    directory = tmp_path / "product"
    with TestClient(create_app(directory)) as first:
        identifier = upload(first, "rules").json()["data"]["id"]
    with TestClient(create_app(directory)) as restarted:
        assert restarted.get(f"/api/v1/materials/{identifier}").status_code == 200
        with restarted.app.state.database.engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
            assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"
            assert connection.execute(text("PRAGMA synchronous")).scalar() == 2


def test_bad_http_fields_and_task_start_requires_complete_inputs(client):
    assert upload(client, operation_id="not-a-uuid").status_code == 422
    assert upload(client, kind="invalid", raw=b"bad").status_code == 422
    missing = client.post("/api/v1/evaluation-tasks", json={})
    assert missing.status_code == 422
    assert set(missing.json()) == {"code", "message", "resource_id", "field_errors", "commit_state"}
    assert client.get("/api/v1/materials?limit=101").status_code == 422
