"""Tests for reports summary endpoint and reporting service."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.models.run_history import RunHistory
from app.services.reporting import get_report_summary, resolve_report_range


def _create_run(db, *, task_id: str, result: str, days_ago: int = 0, run_type: str = "testcase", target_id: int = 1):
    started_at = datetime.utcnow() - timedelta(days=days_ago)
    run = RunHistory(
        task_id=task_id,
        type=run_type,
        target_id=target_id,
        target_name=f"target-{target_id}",
        result=result,
        started_at=started_at,
        duration=12.5,
    )
    db.add(run)
    db.commit()
    return run


def test_resolve_report_range_defaults():
    result = resolve_report_range(None, None)
    assert result.date_to >= result.date_from
    assert (result.date_to - result.date_from).days >= 6


def test_get_report_summary_counts(db):
    _create_run(db, task_id="rp_1", result="pass")
    _create_run(db, task_id="rp_2", result="fail")
    _create_run(db, task_id="rp_3", result="pass")

    stats = get_report_summary(db)
    assert stats.total_runs == 3
    assert stats.pass_count == 2
    assert stats.fail_count == 1
    assert stats.pass_rate == 66.7


def test_reports_summary_endpoint(client, db):
    _create_run(db, task_id="rp_ep_1", result="pass")
    _create_run(db, task_id="rp_ep_2", result="fail")

    response = client.get("/api/v1/reports/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["total_runs"] == 2
