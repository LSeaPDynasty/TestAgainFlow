"""Tests for task queue websocket state synchronization."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict

import pytest

from app.models.run_history import RunHistory
from app.routers import task_queue_ws
from app.services.run_orchestrator import get_run_orchestrator


def _create_run_history(db, task_id: str, result: str = "pending") -> RunHistory:
    run = RunHistory(
        task_id=task_id,
        type="testcase",
        target_id=1,
        target_name="DemoCase",
        result=result,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def test_sync_runtime_and_db_running(db, monkeypatch):
    task_id = "ws_sync_running_001"
    _create_run_history(db, task_id, result="pending")

    @contextmanager
    def _override_db_session():
        yield db

    monkeypatch.setattr(task_queue_ws, "_db_session", _override_db_session)

    task_queue_ws._sync_runtime_and_db(task_id, "running")

    updated = db.query(RunHistory).filter(RunHistory.task_id == task_id).one()
    assert updated.result == "running"

    orchestrator = get_run_orchestrator()
    assert orchestrator.get_status(task_id) == "running"


def test_sync_runtime_and_db_failed_sets_finished_at(db, monkeypatch):
    task_id = "ws_sync_failed_001"
    _create_run_history(db, task_id, result="running")

    @contextmanager
    def _override_db_session():
        yield db

    monkeypatch.setattr(task_queue_ws, "_db_session", _override_db_session)

    task_queue_ws._sync_runtime_and_db(task_id, "failed")

    updated = db.query(RunHistory).filter(RunHistory.task_id == task_id).one()
    assert updated.result == "fail"
    assert updated.finished_at is not None

    orchestrator = get_run_orchestrator()
    assert orchestrator.get_status(task_id) == "failed"


class _DummyWebSocket:
    def __init__(self):
        self.sent: list[Dict[str, Any]] = []

    async def send_json(self, payload: Dict[str, Any]) -> None:
        self.sent.append(payload)


class _DummyTaskQueue:
    def __init__(self):
        self.updates: list[tuple[str, str, Dict[str, Any]]] = []

    def update_task_status(self, task_id: str, status: str, **kwargs) -> None:
        self.updates.append((task_id, status, kwargs))

    def get_task_data(self, task_id: str):
        return {"task_id": task_id}


@pytest.mark.asyncio
async def test_handle_executor_message_unknown_type_returns_structured_error():
    ws = _DummyWebSocket()
    queue = _DummyTaskQueue()

    await task_queue_ws.handle_executor_message(
        "executor_1",
        {"type": "unknown"},
        queue,
        ws,
    )

    assert ws.sent
    assert ws.sent[0]["type"] == "error"
    assert ws.sent[0]["code"] == "unknown_message_type"


@pytest.mark.asyncio
async def test_handle_task_status_missing_required_field_returns_error(monkeypatch):
    ws = _DummyWebSocket()
    queue = _DummyTaskQueue()
    calls: list[tuple[str, str]] = []

    async def _noop_broadcast(message):
        return None

    monkeypatch.setattr(task_queue_ws, "_sync_runtime_and_db", lambda task_id, status: calls.append((task_id, status)))
    monkeypatch.setattr(task_queue_ws.manager, "broadcast", _noop_broadcast)

    await task_queue_ws._handle_task_status(
        "executor_1",
        {"type": "task_status", "task_id": "task_1"},
        queue,
        ws,
    )

    assert ws.sent
    assert ws.sent[0]["type"] == "error"
    assert ws.sent[0]["code"] == "missing_field"
    assert queue.updates == []
    assert calls == []
