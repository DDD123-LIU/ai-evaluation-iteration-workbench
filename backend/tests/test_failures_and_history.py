"""F01～04/D01/D02：数据库实错、提交结果未知及不可变历史。"""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from filelock import Timeout
from sqlalchemy import event, inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.main import create_app
from app.models.imports import MaterialVersion, OperationCommit
from test_import_api import client, upload
from test_csv_import import encode


@pytest.mark.parametrize("kind,table", [("rules", "rule_row"), ("knowledge", "kb_row")])
def test_failed_material_transaction_preserves_existing_version(client, kind, table):
    old = upload(client, kind).json()["data"]["id"]
    original = client.get(f"/api/v1/materials/{old}").json()
    with client.app.state.database.engine.begin() as connection:
        connection.exec_driver_sql(f"CREATE TRIGGER fail_material BEFORE INSERT ON {table} WHEN NEW.source_id = '2' BEGIN SELECT RAISE(ABORT, 'test storage error'); END")
    operation = str(uuid4())
    response = upload(client, kind, rows=[["1", "第一条", "内容"], ["2", "第二条", "内容"]], operation_id=operation)
    assert response.status_code == 503
    assert response.json()["commit_state"] == "not_committed"
    assert client.get(f"/api/v1/materials/{old}").json() == original
    assert len(client.get("/api/v1/materials").json()["items"]) == 1
    assert client.get(f"/api/v1/operations/{operation}").status_code == 404


def test_commit_confirmation_lost_can_read_and_replay(client):
    operation = str(uuid4())
    def lost_confirmation(session):
        raise OperationalError("COMMIT confirmation lost", {}, OSError("模拟提交后连接错误"))
    event.listen(Session, "after_commit", lost_confirmation, once=True)
    try:
        response = upload(client, operation_id=operation)
    finally:
        event.remove(Session, "after_commit", lost_confirmation)
    assert response.status_code == 503
    assert response.json()["commit_state"] == "unknown"
    assert response.json()["resource_id"] == operation
    saved = client.get(f"/api/v1/operations/{operation}").json()["data"]
    replay = upload(client, operation_id=operation)
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == saved["result_id"]
    assert len(client.get("/api/v1/uploads").json()["items"]) == 1


def test_same_operation_concurrent_network_replay_one_record(client):
    operation = str(uuid4())
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda _: upload(client, "rules", operation_id=operation), range(4)))
    assert sorted(response.status_code for response in responses) == [200, 200, 200, 201]
    assert len({response.json()["data"]["id"] for response in responses}) == 1
    with client.app.state.database.session() as session:
        assert len(session.scalars(select(MaterialVersion)).all()) == 1
        assert len(session.scalars(select(OperationCommit)).all()) == 1


def test_second_instance_rejected_and_release_allows_restart(tmp_path):
    with TestClient(create_app(tmp_path)):
        with pytest.raises(Timeout):
            with TestClient(create_app(tmp_path)):
                pass
    with TestClient(create_app(tmp_path)) as restarted:
        assert restarted.get("/api/v1/uploads").status_code == 200


def test_actual_migration_scope_and_foreign_keys(client):
    db = client.app.state.database
    assert set(inspect(db.engine).get_table_names()) == {
        "alembic_version", "dialogue_upload", "case_record", "material_version", "rule_row", "kb_row", "operation_commit",
        "task", "runtime_slot", "task_case", "ordinary_task", "config_snapshot", "execution_item", "attempt",
        "evaluation_result", "gap", "final_error", "batch_summary", "qa", "export_event", "export_item", "qa_write_receipt", "supplement", "supplement_item", "effect_task", "generation_result", "sampling_run", "draw", "human_mark", "sampling_receipt"}
    columns = {column["name"]: column["type"] for column in inspect(db.engine).get_columns("case_record")}
    assert str(columns["H_json"]) == "TEXT"
    with db.engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0009_sampling"
    identifier = upload(client).json()["data"]["id"]
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            connection.execute(text("DELETE FROM dialogue_upload WHERE id=:id"), {"id": identifier})
    assert client.get(f"/api/v1/uploads/{identifier}").status_code == 200


def test_unknown_and_duplicate_form_fields_rejected(client):
    for extra in ({"unexpected": "value"}, {"kind": ["dialogues", "rules"]}):
        fields = {"kind": "dialogues", "operation_id": str(uuid4()), **extra}
        response = client.post("/api/v1/uploads", data=fields, files={"file": ("文件.csv", encode("dialogues", []), "text/csv")})
        assert response.status_code == 422
        assert response.json()["code"] == "REQUEST_INVALID"


def test_material_raw_order_and_pagination(client):
    raw = encode("knowledge", [["B", "  标题", '内容,\r\n"引号"'], ["A", "第二", "尾部\n"]], bom=True)
    identifier = upload(client, "knowledge", raw=raw).json()["data"]["id"]
    upload(client, "rules")
    detail = client.get(f"/api/v1/materials/{identifier}").json()["data"]
    assert [row["source_id"] for row in detail["rows"]] == ["B", "A"]
    assert detail["rows"][0]["content"] == '内容,\r\n"引号"'
    assert client.get(f"/api/v1/materials/{identifier}/file").content == raw
    assert len(client.get("/api/v1/materials?kind=knowledge").json()["items"]) == 1
    assert len(client.get("/api/v1/materials?offset=1&limit=1").json()["items"]) == 1
    assert client.get(f"/api/v1/uploads/{identifier}").status_code == 404
    assert client.patch(f"/api/v1/materials/{identifier}", json={}).status_code == 405


@pytest.mark.parametrize("kind", ["rules", "knowledge"])
def test_first_failed_material_import_has_no_available_version(client, kind):
    response = upload(client, kind, rows=[["1", "标题", ""]])
    assert response.status_code == 422
    assert client.get(f"/api/v1/materials?kind={kind}").json()["items"] == []


def test_missing_and_invalid_http_values_have_structured_errors(client):
    for response in (
        client.post("/api/v1/uploads", data={"kind": "rules"}),
        client.get("/api/v1/materials?offset=-1"),
        client.get("/api/v1/materials?kind=dialogues"),
        client.get("/api/v1/materials/not-a-uuid"),
    ):
        assert response.status_code == 422
        assert response.json()["code"] == "REQUEST_INVALID"
        assert response.json()["commit_state"] == "not_committed"


def test_database_query_failure_is_not_a_false_empty_list(client):
    db = client.app.state.database
    def fail_query(*args):
        raise OperationalError("SELECT", {}, OSError("模拟数据库不可读"))
    event.listen(db.engine, "before_cursor_execute", fail_query)
    try:
        response = client.get("/api/v1/uploads")
    finally:
        event.remove(db.engine, "before_cursor_execute", fail_query)
    assert response.status_code == 503
    assert response.json()["commit_state"] == "unknown"
    assert "items" not in response.json()


def test_startup_migration_failure_releases_directory_lock(tmp_path, monkeypatch):
    from app.db import database
    real_upgrade = database.command.upgrade
    def fail_upgrade(*args):
        raise RuntimeError("模拟迁移失败")
    monkeypatch.setattr(database.command, "upgrade", fail_upgrade)
    with pytest.raises(RuntimeError, match="迁移失败"):
        with TestClient(create_app(tmp_path)):
            pass
    monkeypatch.setattr(database.command, "upgrade", real_upgrade)
    with TestClient(create_app(tmp_path)) as restarted:
        assert restarted.get("/api/v1/materials").json()["items"] == []
