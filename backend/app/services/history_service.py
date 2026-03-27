"""Service helpers for history endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.run_history_repo import RunHistoryRepository
from app.schemas.history import HistoryStats
from app.services.reporting import get_report_summary


@dataclass
class ParsedHistoryFilters:
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    error_message: Optional[str] = None


def parse_history_date_filters(date_from: Optional[str], date_to: Optional[str]) -> ParsedHistoryFilters:
    parsed_from = None
    parsed_to = None

    if date_from:
        try:
            parsed_from = datetime.fromisoformat(date_from)
        except ValueError:
            return ParsedHistoryFilters(None, None, "Invalid date_from format")

    if date_to:
        try:
            parsed_to = datetime.fromisoformat(date_to)
        except ValueError:
            return ParsedHistoryFilters(None, None, "Invalid date_to format")

    return ParsedHistoryFilters(parsed_from, parsed_to, None)


def get_history_statistics(db: Session, days: int = 7) -> HistoryStats:
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return get_report_summary(
        db,
        date_from=start.isoformat(),
        date_to=end.isoformat(),
        suite_id=None,
    )


def list_history_records(
    db: Session,
    *,
    skip: int,
    limit: int,
    result: Optional[str],
    testcase_name: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
):
    repo = RunHistoryRepository(db)
    return repo.list_with_filters(
        skip=skip,
        limit=limit,
        result=result,
        testcase_name=testcase_name,
        date_from=date_from,
        date_to=date_to,
    )
