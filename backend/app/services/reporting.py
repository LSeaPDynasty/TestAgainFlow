"""Reporting service for run history analytics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.run_history import RunHistory
from app.schemas.history import HistoryStats


@dataclass
class ReportRange:
    date_from: datetime
    date_to: datetime


def resolve_report_range(date_from: Optional[str], date_to: Optional[str]) -> ReportRange:
    if not date_from:
        from_dt = datetime.utcnow() - timedelta(days=7)
    else:
        from_dt = datetime.fromisoformat(date_from)
    if not date_to:
        to_dt = datetime.utcnow()
    else:
        to_dt = datetime.fromisoformat(date_to)
    return ReportRange(date_from=from_dt, date_to=to_dt)


def _base_filters(*, report_range: ReportRange, suite_id: Optional[int]) -> list:
    filters = [RunHistory.started_at >= report_range.date_from, RunHistory.started_at <= report_range.date_to]
    if suite_id is not None:
        filters.extend([RunHistory.type == "suite", RunHistory.target_id == suite_id])
    return filters


def get_report_summary(
    db: Session,
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    suite_id: Optional[int] = None,
) -> HistoryStats:
    report_range = resolve_report_range(date_from, date_to)
    filters = _base_filters(report_range=report_range, suite_id=suite_id)

    total_runs = db.execute(select(func.count(RunHistory.id)).where(and_(*filters))).scalar() or 0
    pass_count = (
        db.execute(
            select(func.count(RunHistory.id)).where(and_(*filters, RunHistory.result == "pass"))
        ).scalar()
        or 0
    )
    fail_count = (
        db.execute(
            select(func.count(RunHistory.id)).where(and_(*filters, RunHistory.result == "fail"))
        ).scalar()
        or 0
    )
    avg_duration = (
        db.execute(
            select(func.avg(RunHistory.duration)).where(and_(*filters, RunHistory.duration.isnot(None)))
        ).scalar()
        or None
    )

    trend_rows = db.execute(
        select(RunHistory.started_at, RunHistory.result).where(and_(*filters))
    ).all()
    trend_map: dict[str, dict[str, int]] = {}
    for row in trend_rows:
        day = row.started_at.date().isoformat() if row.started_at else ""
        if day not in trend_map:
            trend_map[day] = {"pass_count": 0, "fail": 0}
        if row.result == "pass":
            trend_map[day]["pass_count"] += 1
        elif row.result == "fail":
            trend_map[day]["fail"] += 1
    daily_trend = [
        {"date": day, "pass_count": values["pass_count"], "fail": values["fail"]}
        for day, values in sorted(trend_map.items(), key=lambda item: item[0])
    ]

    top_failed_stmt = (
        select(
            RunHistory.target_id.label("testcase_id"),
            RunHistory.target_name.label("testcase_name"),
            func.count(RunHistory.id).label("fail_count"),
        )
        .where(and_(*filters, RunHistory.result == "fail"))
        .group_by(RunHistory.target_id, RunHistory.target_name)
        .order_by(func.count(RunHistory.id).desc())
        .limit(10)
    )
    top_failed = [
        {"testcase_id": row.testcase_id, "testcase_name": row.testcase_name, "fail_count": int(row.fail_count or 0)}
        for row in db.execute(top_failed_stmt)
    ]

    return HistoryStats(
        total_runs=int(total_runs),
        pass_count=int(pass_count),
        fail_count=int(fail_count),
        pass_rate=round((pass_count / total_runs) * 100, 1) if total_runs else 0.0,
        avg_duration=round(avg_duration, 1) if avg_duration is not None else None,
        daily_trend=daily_trend,
        top_failed=top_failed,
    )
