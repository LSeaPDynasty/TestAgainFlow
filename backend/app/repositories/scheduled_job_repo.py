"""
Scheduled Job repository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.models.scheduled_job import ScheduledJob, JobStatus
from app.repositories.base import BaseRepository


class ScheduledJobRepository(BaseRepository[ScheduledJob]):
    """Scheduled Job repository"""

    def __init__(self, db: Session):
        super().__init__(ScheduledJob, db)

    def get_by_name(self, name: str) -> Optional[ScheduledJob]:
        """Get job by name"""
        return self.get_by_field('name', name)

    def list_enabled(self) -> List[ScheduledJob]:
        """List all enabled jobs"""
        stmt = select(ScheduledJob).where(
            and_(
                ScheduledJob.enabled == True,
                ScheduledJob.status != JobStatus.DISABLED
            )
        ).order_by(ScheduledJob.created_at.desc())
        return self.db.execute(stmt).scalars().all()

    def list_with_details(
        self,
        skip: int = 0,
        limit: int = 20,
        enabled_only: bool = False,
        project_id: Optional[int] = None
    ) -> tuple[List[dict], int]:
        """List jobs with details"""
        # Build query
        stmt = select(ScheduledJob)

        # Apply filters
        filters = []
        if enabled_only:
            filters.append(ScheduledJob.enabled == True)
        if project_id is not None:
            filters.append(ScheduledJob.project_id == project_id)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(ScheduledJob.__table__.c.id)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        if project_id is not None:
            count_stmt = count_stmt.where(ScheduledJob.project_id == project_id)
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(ScheduledJob.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        results = []
        for job in self.db.execute(stmt).scalars():
            # Get target name
            target_name = ""
            if job.job_type == "testcase":
                from app.models.testcase import Testcase
                testcase = self.db.execute(
                    select(Testcase).where(Testcase.id == job.target_id)
                ).scalar_one_or_none()
                target_name = testcase.name if testcase else f"Unknown Testcase({job.target_id})"
            else:  # suite
                from app.models.suite import Suite
                suite = self.db.execute(
                    select(Suite).where(Suite.id == job.target_id)
                ).scalar_one_or_none()
                target_name = suite.name if suite else f"Unknown Suite({job.target_id})"

            results.append({
                'id': job.id,
                'name': job.name,
                'description': job.description,
                'job_type': job.job_type,
                'target_id': job.target_id,
                'target_name': target_name,
                'cron_expression': job.cron_expression,
                'device_serial': job.device_serial,
                'enabled': job.enabled,
                'status': job.status.value,
                'last_run_time': job.last_run_time,
                'next_run_time': job.next_run_time,
                'last_run_status': job.last_run_status,
                'last_run_message': job.last_run_message,
                'created_at': job.created_at,
                'updated_at': job.updated_at
            })

        return results, total

    def update_status(self, job_id: int, status: JobStatus,
                      last_run_status: Optional[str] = None,
                      last_run_message: Optional[str] = None) -> Optional[ScheduledJob]:
        """Update job status and run info"""
        job = self.get(job_id)
        if job:
            job.status = status
            if last_run_status:
                job.last_run_status = last_run_status
            if last_run_message:
                job.last_run_message = last_run_message
            self.db.commit()
            self.db.refresh(job)
        return job

    def update_last_run(self, job_id: int, success: bool, message: str = "") -> Optional[ScheduledJob]:
        """Update last run info"""
        from datetime import datetime
        job = self.get(job_id)
        if job:
            job.last_run_time = datetime.utcnow()
            job.last_run_status = "success" if success else "failed"
            job.last_run_message = message
            if success:
                job.status = JobStatus.PENDING
            self.db.commit()
            self.db.refresh(job)
        return job
