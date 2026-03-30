"""
Suite model - test case collections
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, Boolean, Index
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class Suite(BaseModel):
    """Suite model representing a collection of testcases"""
    __tablename__ = 'suites'

    name = Column(String(200), nullable=False, unique=True, comment='Suite name, globally unique')
    description = Column(Text, nullable=True, comment='Description')
    priority = Column(
        Enum('P0', 'P1', 'P2', 'P3', name='suite_priority_enum'),
        nullable=False,
        default='P1',
        comment='Priority: P0, P1, P2, P3'
    )
    enabled = Column(Boolean, nullable=False, default=True, comment='Enabled flag')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')

    # Relationships
    suite_testcases = relationship('SuiteTestcase', back_populates='suite', cascade='all, delete-orphan')
    test_plan_entries = relationship('TestPlanSuite', back_populates='suite')

    # Indexes for query optimization
    __table_args__ = (
        Index('ix_suite_project_id', 'project_id'),
        Index('ix_suite_enabled', 'enabled'),
    )

    def __repr__(self):
        return f"<Suite(id={self.id}, name='{self.name}', priority='{self.priority}')>"


class SuiteTestcase(BaseModel):
    """Suite-Testcase association table"""
    __tablename__ = 'suite_testcases'

    suite_id = Column(Integer, ForeignKey('suites.id', ondelete='CASCADE'), nullable=False, comment='Suite ID')
    testcase_id = Column(Integer, ForeignKey('testcases.id', ondelete='CASCADE'), nullable=False, comment='Testcase ID')
    order_index = Column(Integer, nullable=False, comment='Execution order')
    enabled = Column(Boolean, nullable=False, default=True, comment='Enabled flag')

    # Relationships
    suite = relationship('Suite', back_populates='suite_testcases')
    testcase = relationship('Testcase')

    # Indexes for query optimization - composite indexes for common join patterns
    __table_args__ = (
        Index('ix_suite_testcase_suite_id', 'suite_id'),
        Index('ix_suite_testcase_testcase_id', 'testcase_id'),
        Index('ix_suite_testcase_suite_order', 'suite_id', 'order_index'),
        Index('ix_suite_testcase_enabled', 'enabled'),
    )

    def __repr__(self):
        return f"<SuiteTestcase(suite_id={self.suite_id}, testcase_id={self.testcase_id}, order={self.order_index})>"
