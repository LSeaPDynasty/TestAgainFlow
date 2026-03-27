"""
Scheduled Job model - automated test execution
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base import BaseModel, Base
import enum


class JobStatus(enum.Enum):
    """Scheduled job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class ScheduledJob(BaseModel):
    """Scheduled Job model for automated test execution"""
    __tablename__ = 'scheduled_jobs'

    name = Column(String(200), nullable=False, unique=True, comment='Job name')
    description = Column(Text, nullable=True, comment='Job description')
    job_type = Column(String(50), nullable=False, comment='Job type: testcase, suite')
    target_id = Column(Integer, nullable=False, comment='Target testcase or suite ID')
    cron_expression = Column(String(100), nullable=False, comment='Cron expression')
    device_serial = Column(String(100), nullable=True, comment='Device serial for execution')
    enabled = Column(Boolean, nullable=False, default=True, comment='Job enabled flag')
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, comment='Job status')
    last_run_time = Column(DateTime, nullable=True, comment='Last execution time')
    next_run_time = Column(DateTime, nullable=True, comment='Next scheduled run time')
    last_run_status = Column(String(20), nullable=True, comment='Last run status: success, failed')
    last_run_message = Column(Text, nullable=True, comment='Last run message')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')
    created_by = Column(Integer, nullable=True, comment='Creator user ID')

    # Relationships
    project = relationship('Project')

    def __repr__(self):
        return f"<ScheduledJob(id={self.id}, name='{self.name}', type='{self.job_type}', cron='{self.cron_expression}')>"
