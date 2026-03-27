"""
RunHistory model - execution history records
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Float, Text, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class RunHistory(BaseModel):
    """RunHistory model for test execution records"""
    __tablename__ = 'run_history'

    task_id = Column(String(100), nullable=False, unique=True, comment='Task ID, unique')
    type = Column(
        Enum('testcase', 'suite', 'test_plan', name='run_type_enum'),
        nullable=False,
        comment='Run type: testcase, suite, or test_plan'
    )
    target_id = Column(Integer, nullable=True, comment='Target ID (testcase_id or suite_id, null for test_plan)')
    target_name = Column(String(200), nullable=True, comment='Target name (null for test_plan)')
    result = Column(
        Enum('pending', 'running', 'pass', 'fail', 'cancelled', 'timeout', 'error', name='run_result_enum_v2'),
        nullable=False,
        default='pending',
        comment='Execution result'
    )
    returncode = Column(Integer, nullable=True, comment='Process return code')
    duration = Column(Float, nullable=True, comment='Execution duration in seconds')
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True, comment='Profile ID used')
    profile_name = Column(String(100), nullable=True, comment='Profile name')
    device_serial = Column(String(100), nullable=True, comment='Device serial used')
    device_name = Column(String(100), nullable=True, comment='Device name')
    has_screenshots = Column(Integer, nullable=False, default=0, comment='Has screenshots flag')
    log_path = Column(String(500), nullable=True, comment='Log file path')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')
    test_plan_id = Column(Integer, ForeignKey('test_plans.id', ondelete='SET NULL'), nullable=True, comment='Test Plan ID (for test_plan runs)')

    # Suite execution statistics
    total_count = Column(Integer, nullable=False, default=0, comment='Total testcase count (for suites and test_plans)')
    success_count = Column(Integer, nullable=False, default=0, comment='Success count (for suites and test_plans)')
    failed_count = Column(Integer, nullable=False, default=0, comment='Failed count (for suites and test_plans)')
    skipped_count = Column(Integer, nullable=False, default=0, comment='Skipped count (for suites and test_plans)')

    started_at = Column(DateTime, nullable=True, comment='Start time')
    finished_at = Column(DateTime, nullable=True, comment='Finish time')

    # Relationships
    profile = relationship('Profile')

    def __repr__(self):
        return f"<RunHistory(task_id='{self.task_id}', type='{self.type}', result='{self.result}')>"
