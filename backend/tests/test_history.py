"""Tests for history endpoints."""
from __future__ import annotations

from datetime import datetime

from app.models.run_history import RunHistory


def _create_history(db, *, task_id: str, result: str):
    run = RunHistory(
        task_id=task_id,
        type="testcase",
        target_id=1,
        target_name="DemoCase",
        result=result,
        started_at=datetime.utcnow(),
        duration=10.0,
    )
    db.add(run)
    db.commit()


def test_list_history_with_invalid_date_returns_validation_error(client):
    response = client.get("/api/v1/history?date_from=invalid-date")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 4001


def test_list_history_success(client, db):
    _create_history(db, task_id="hist_1", result="pass")
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["total"] >= 1


def test_history_stats_success(client, db):
    _create_history(db, task_id="hist_2", result="pass")
    _create_history(db, task_id="hist_3", result="fail")
    response = client.get("/api/v1/history/stats?days=7")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["total_runs"] >= 2
