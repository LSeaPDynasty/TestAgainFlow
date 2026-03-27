"""Runtime state helpers for run control endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set

from app.services.run_orchestrator import get_run_orchestrator


@dataclass
class RunTransitionResult:
    ok: bool
    current_status: str
    error_message: Optional[str] = None


def map_db_result_to_runtime_status(db_result: Optional[str]) -> str:
    mapping = {
        "pending": "queued",
        "running": "running",
        "pass": "success",
        "fail": "failed",
        "cancelled": "cancelled",
        "timeout": "failed",
    }
    return mapping.get(db_result or "", "queued")


def ensure_current_status(task_id: str, db_result: Optional[str]) -> str:
    orchestrator = get_run_orchestrator()
    current_status = orchestrator.get_status(task_id) or map_db_result_to_runtime_status(db_result)
    orchestrator.ensure_task(task_id, status=current_status)
    return orchestrator.get_status(task_id) or current_status


def transition_run_state(
    *,
    task_id: str,
    db_result: Optional[str],
    allowed_current: Set[str],
    target_status: str,
) -> RunTransitionResult:
    orchestrator = get_run_orchestrator()
    current_status = ensure_current_status(task_id, db_result)
    if current_status not in allowed_current:
        return RunTransitionResult(
            ok=False,
            current_status=current_status,
            error_message=f"Task cannot be transitioned from {current_status} to {target_status}",
        )
    if not orchestrator.transition(task_id, target_status):
        return RunTransitionResult(
            ok=False,
            current_status=current_status,
            error_message="Invalid status transition",
        )
    return RunTransitionResult(ok=True, current_status=target_status)
