"""Tests for system health snapshot service."""
from __future__ import annotations

from app.services import system_health


class _DummyOrchestrator:
    def list_statuses(self):
        return {"a": "running", "b": "failed", "c": "running"}


def test_collect_health_snapshot(monkeypatch):
    monkeypatch.setattr(system_health, "_check_db_connected", lambda: True)
    monkeypatch.setattr(system_health, "_check_adb_available", lambda: False)
    monkeypatch.setattr(system_health, "get_run_orchestrator", lambda: _DummyOrchestrator())

    snapshot = system_health.collect_health_snapshot()
    data = snapshot.to_dict()

    assert data["status"] == "ok"
    assert data["db_connected"] is True
    assert data["adb_available"] is False
    assert data["running_tasks"] == 2
    assert isinstance(data["uptime_seconds"], int)
