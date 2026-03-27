"""
RunHistory repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, cast, Date
from datetime import datetime, timedelta
from app.models.run_history import RunHistory
from app.repositories.base import BaseRepository


class RunHistoryRepository(BaseRepository[RunHistory]):
    """RunHistory repository"""

    def __init__(self, db: Session):
        super().__init__(RunHistory, db)

    def get_by_task_id(self, task_id: str) -> Optional[RunHistory]:
        """Get run by task ID"""
        return self.get_by_field('task_id', task_id)

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 20,
        result: Optional[str] = None,
        testcase_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List runs with filters"""
        stmt = select(RunHistory)

        # Apply filters
        filters = []
        if result:
            filters.append(RunHistory.result == result)
        if testcase_name:
            filters.append(RunHistory.target_name.ilike(f'%{testcase_name}%'))
        if date_from:
            filters.append(RunHistory.started_at >= date_from)
        if date_to:
            filters.append(RunHistory.started_at <= date_to)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count(RunHistory.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(RunHistory.started_at.desc()).offset(skip).limit(limit)

        # Execute query
        results = []
        rows = self.db.execute(stmt).scalars().all()
        for row in rows:
            results.append({
                'id': row.id,
                'task_id': row.task_id,
                'testcase_id': row.target_id,
                'testcase_name': row.target_name,
                'result': row.result,
                'returncode': row.returncode,
                'duration': row.duration,
                'profile_id': row.profile_id,
                'profile_name': row.profile_name,
                'device_serial': row.device_serial,
                'device_name': row.device_name,
                'has_screenshots': bool(row.has_screenshots),
                'started_at': row.started_at,
                'finished_at': row.finished_at
            })

        return results, total

    def list_with_details(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        device_serial: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List runs with details and filters"""
        stmt = select(RunHistory)

        # Apply filters
        filters = []
        if status:
            filters.append(RunHistory.result == status)
        if device_serial:
            filters.append(RunHistory.device_serial == device_serial)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count(RunHistory.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(RunHistory.started_at.desc()).offset(skip).limit(limit)

        # Execute query
        results = []
        rows = self.db.execute(stmt).scalars().all()
        for row in rows:
            results.append({
                'id': row.id,
                'task_id': row.task_id,
                'type': row.type,
                'target_id': row.target_id,
                'target_name': row.target_name,
                'result': row.result,
                'returncode': row.returncode,
                'duration': row.duration,
                'profile_id': row.profile_id,
                'profile_name': row.profile_name,
                'device_serial': row.device_serial,
                'device_name': row.device_name,
                'has_screenshots': bool(row.has_screenshots),
                'started_at': row.started_at,
                'finished_at': row.finished_at
            })

        return results, total

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get run statistics for the last N days"""
        from sqlalchemy import cast, Date

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Total runs
        total_stmt = select(func.count(RunHistory.id)).where(RunHistory.started_at >= cutoff_date)
        total_runs = self.db.execute(total_stmt).scalar() or 0

        # Pass/fail counts
        pass_stmt = select(func.count(RunHistory.id)).where(
            and_(RunHistory.started_at >= cutoff_date, RunHistory.result == 'pass')
        )
        pass_count = self.db.execute(pass_stmt).scalar() or 0

        fail_stmt = select(func.count(RunHistory.id)).where(
            and_(RunHistory.started_at >= cutoff_date, RunHistory.result == 'fail')
        )
        fail_count = self.db.execute(fail_stmt).scalar() or 0

        # Average duration
        avg_stmt = select(func.avg(RunHistory.duration)).where(
            and_(RunHistory.started_at >= cutoff_date, RunHistory.duration.isnot(None))
        )
        avg_duration = self.db.execute(avg_stmt).scalar()

        # Daily trend
        trend_stmt = select(
            cast(RunHistory.started_at, Date).label('date'),
            func.sum(func.case((RunHistory.result == 'pass', 1), else_=0)).label('pass'),
            func.sum(func.case((RunHistory.result == 'fail', 1), else_=0)).label('fail')
        ).where(RunHistory.started_at >= cutoff_date).group_by('date').order_by('date')

        daily_trend = []
        for row in self.db.execute(trend_stmt):
            daily_trend.append({
                'date': row.date.isoformat() if row.date else '',
                'pass': int(getattr(row, 'pass') or 0),
                'fail': int(row.fail or 0)
            })

        # Top failed testcases
        top_failed_stmt = select(
            RunHistory.target_id,
            RunHistory.target_name,
            func.count(RunHistory.id).label('fail_count')
        ).where(
            and_(RunHistory.started_at >= cutoff_date, RunHistory.result == 'fail')
        ).group_by(
            RunHistory.target_id, RunHistory.target_name
        ).order_by('fail_count DESC').limit(10)

        top_failed = []
        for row in self.db.execute(top_failed_stmt):
            top_failed.append({
                'testcase_id': row.target_id,
                'testcase_name': row.target_name,
                'fail_count': row.fail_count
            })

        return {
            'total_runs': total_runs,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'pass_rate': round(pass_count / total_runs * 100, 1) if total_runs > 0 else 0,
            'avg_duration': round(avg_duration, 1) if avg_duration else None,
            'daily_trend': daily_trend,
            'top_failed': top_failed
        }
