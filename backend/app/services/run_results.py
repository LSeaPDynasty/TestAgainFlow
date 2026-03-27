"""Run results aggregation service."""
from __future__ import annotations

from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.run_log import RunLog
from app.models.screenshot import RunScreenshot


def build_run_results(db: Session, run) -> Dict[str, object]:
    """Build normalized run results payload for API responses."""
    task_id = run.task_id

    logs = (
        db.query(RunLog)
        .filter(RunLog.task_id == task_id)
        .order_by(RunLog.created_at.asc())
        .all()
    )
    screenshots = (
        db.query(RunScreenshot)
        .filter(RunScreenshot.task_id == task_id)
        .order_by(RunScreenshot.created_at.asc())
        .all()
    )

    testcase_results: Dict[str, Dict[str, object]] = {}
    for log in logs:
        tc_name = log.testcase_name or run.target_name
        tc_key = str(log.testcase_id or run.target_id)
        if tc_key not in testcase_results:
            testcase_results[tc_key] = {
                "testcase_id": log.testcase_id or run.target_id,
                "testcase_name": tc_name,
                "result": log.testcase_result or "unknown",
                "logs": [],
            }
        testcase_results[tc_key]["logs"].append(
            {
                "level": log.level,
                "message": log.message,
                "timestamp": log.timestamp,
            }
        )
        if log.testcase_result:
            testcase_results[tc_key]["result"] = log.testcase_result

    if not testcase_results:
        testcase_results[str(run.target_id)] = {
            "testcase_id": run.target_id,
            "testcase_name": run.target_name,
            "result": run.result,
            "logs": [],
        }

    summary = {
        "task_id": task_id,
        "type": run.type,
        "status": run.result,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "duration": run.duration,
        "total_testcases": len(testcase_results),
        "screenshots_count": len(screenshots),
    }

    return {
        "testcases": list(testcase_results.values()),
        "summary": summary,
    }

