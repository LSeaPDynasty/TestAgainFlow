"""Tests for run results aggregation service."""
from __future__ import annotations

from datetime import datetime

from app.models.run_history import RunHistory
from app.models.run_log import RunLog
from app.models.screenshot import RunScreenshot
from app.services.run_results import build_run_results


def _create_run(db, task_id: str, result: str = "running") -> RunHistory:
    run = RunHistory(
        task_id=task_id,
        type="testcase",
        target_id=1,
        target_name="SmokeCase",
        result=result,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def test_build_run_results_with_logs_and_screenshots(db):
    task_id = "service_result_001"
    run = _create_run(db, task_id, result="pass")

    db.add(
        RunLog(
            task_id=task_id,
            level="INFO",
            message="step passed",
            timestamp=1.0,
            testcase_id=11,
            testcase_name="Case-A",
            testcase_result="passed",
        )
    )
    db.add(
        RunScreenshot(
            task_id=task_id,
            filename="a.png",
            filepath="/tmp/a.png",
            step_name="click login",
            timestamp="1.0",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()

    payload = build_run_results(db, run)
    assert "testcases" in payload
    assert "summary" in payload
    assert payload["summary"]["screenshots_count"] == 1
    assert payload["summary"]["total_testcases"] == 1
    assert payload["testcases"][0]["testcase_name"] == "Case-A"
    assert payload["testcases"][0]["result"] == "passed"


def test_build_run_results_without_logs_falls_back_to_run_target(db):
    task_id = "service_result_002"
    run = _create_run(db, task_id, result="fail")

    payload = build_run_results(db, run)
    assert payload["summary"]["total_testcases"] == 1
    assert payload["testcases"][0]["testcase_id"] == run.target_id
    assert payload["testcases"][0]["testcase_name"] == run.target_name
    assert payload["testcases"][0]["result"] == run.result

