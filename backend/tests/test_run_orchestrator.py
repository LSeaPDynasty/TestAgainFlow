"""Tests for run orchestrator state machine and cleanup."""
from __future__ import annotations

from app.services.run_orchestrator import (
    RUN_STATUS_CANCELLED,
    RUN_STATUS_FAILED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_STOPPED,
    RUN_STATUS_SUCCESS,
    RunOrchestrator,
)


def test_transition_respects_state_machine():
    orchestrator = RunOrchestrator()
    orchestrator.create_task("t1", [{"id": 1, "name": "case"}])

    assert orchestrator.transition("t1", RUN_STATUS_RUNNING) is True
    assert orchestrator.transition("t1", RUN_STATUS_STOPPED) is True
    assert orchestrator.transition("t1", RUN_STATUS_RUNNING) is False


def test_cleanup_expired_only_removes_final_tasks():
    orchestrator = RunOrchestrator()
    orchestrator.create_task("running_task", [{"id": 1, "name": "a"}])
    orchestrator.create_task("final_task", [{"id": 2, "name": "b"}])

    orchestrator.transition("running_task", RUN_STATUS_RUNNING)
    orchestrator.transition("final_task", RUN_STATUS_FAILED)

    # Mark final task as stale.
    orchestrator._tasks["final_task"].updated_at = 0
    orchestrator._tasks["running_task"].updated_at = 0

    removed = orchestrator.cleanup_expired(ttl_seconds=1)
    assert removed == 1
    assert orchestrator.get_status("final_task") is None
    assert orchestrator.get_status("running_task") == RUN_STATUS_RUNNING


def test_cleanup_expired_handles_multiple_final_statuses():
    orchestrator = RunOrchestrator()
    for task_id, status in {
        "s1": RUN_STATUS_SUCCESS,
        "s2": RUN_STATUS_CANCELLED,
        "s3": RUN_STATUS_STOPPED,
    }.items():
        orchestrator.ensure_task(task_id, status=status)
        orchestrator._tasks[task_id].updated_at = 0

    removed = orchestrator.cleanup_expired(ttl_seconds=1)
    assert removed == 3

