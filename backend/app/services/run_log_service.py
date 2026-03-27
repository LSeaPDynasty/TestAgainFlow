"""Service helpers for run logs endpoints."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.run_log import RunLog


def list_run_logs(db: Session, task_id: str) -> list[dict]:
    # For test plans, also fetch logs from sub-tasks (suite tasks)
    # Test plan sub-tasks have IDs like: plan_xxx_suite_1, plan_xxx_suite_2, etc.
    logs_query = db.query(RunLog).filter(RunLog.task_id == task_id)

    # If this is a test plan task (starts with "plan_"), also get sub-task logs
    if task_id.startswith("plan_"):
        # Match sub-task IDs: plan_xxx_suite_%, plan_xxx_tc_%, etc.
        sub_task_pattern = f"{task_id}_suite_%"
        logs_query = logs_query.union(
            db.query(RunLog).filter(RunLog.task_id.like(sub_task_pattern))
        )
        # Also get testcase logs from suite execution
        tc_pattern = f"{task_id}_suite_%_tc_%"
        logs_query = logs_query.union(
            db.query(RunLog).filter(RunLog.task_id.like(tc_pattern))
        )

    logs = logs_query.order_by(RunLog.created_at).all()
    return [
        {
            "level": log.level,
            "message": log.message,
            "timestamp": log.timestamp,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "task_id": log.task_id,  # Include task_id for grouping
        }
        for log in logs
    ]
