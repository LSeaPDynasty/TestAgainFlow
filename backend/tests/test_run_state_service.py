"""Tests for run state transition service."""
from __future__ import annotations

from app.services.run_orchestrator import get_run_orchestrator
from app.services.run_state import map_db_result_to_runtime_status, transition_run_state


def test_map_db_result_to_runtime_status():
    assert map_db_result_to_runtime_status("pending") == "queued"
    assert map_db_result_to_runtime_status("pass") == "success"
    assert map_db_result_to_runtime_status("unknown") == "queued"


def test_transition_run_state_success():
    orchestrator = get_run_orchestrator()
    task_id = "run_state_service_success"
    orchestrator.create_task(task_id, targets=[])

    result = transition_run_state(
        task_id=task_id,
        db_result="pending",
        allowed_current={"queued", "running"},
        target_status="running",
    )
    assert result.ok is True
    assert orchestrator.get_status(task_id) == "running"


def test_transition_run_state_blocked():
    orchestrator = get_run_orchestrator()
    task_id = "run_state_service_blocked"
    orchestrator.create_task(task_id, targets=[])
    orchestrator.transition(task_id, "running")

    result = transition_run_state(
        task_id=task_id,
        db_result="running",
        allowed_current={"paused"},
        target_status="cancelled",
    )
    assert result.ok is False
    assert "cannot be transitioned" in (result.error_message or "")
