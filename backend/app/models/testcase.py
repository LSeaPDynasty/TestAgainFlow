"""
Testcase model - complete test scenarios
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class Testcase(BaseModel):
    """Testcase model representing a complete test scenario"""
    __tablename__ = 'testcases'

    name = Column(String(200), nullable=False, unique=True, comment='Testcase name, globally unique')
    description = Column(Text, nullable=True, comment='Description')
    priority = Column(
        Enum('P0', 'P1', 'P2', 'P3', name='priority_enum'),
        nullable=False,
        default='P2',
        comment='Priority: P0, P1, P2, P3'
    )
    timeout = Column(Integer, nullable=False, default=120, comment='Timeout in seconds')
    params = Column(JSON, nullable=True, comment='Testcase-level parameters')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')

    # Relationships
    testcase_flows = relationship('TestcaseFlow', back_populates='testcase', cascade='all, delete-orphan')
    inline_steps = relationship('TestcaseInlineStep', back_populates='testcase', cascade='all, delete-orphan')
    testcase_items = relationship('TestcaseItem', back_populates='testcase', cascade='all, delete-orphan')
    tags = relationship('Tag', secondary='testcase_tags', back_populates='testcases')

    def __repr__(self):
        return f"<Testcase(id={self.id}, name='{self.name}', priority='{self.priority}')>"


class TestcaseFlow(BaseModel):
    """Testcase-Flow association table"""
    __tablename__ = 'testcase_flows'

    testcase_id = Column(Integer, ForeignKey('testcases.id', ondelete='CASCADE'), nullable=False, comment='Testcase ID')
    flow_id = Column(Integer, ForeignKey('flows.id', ondelete='CASCADE'), nullable=False, comment='Flow ID')
    flow_role = Column(
        Enum('setup', 'main', 'teardown', name='flow_role_enum'),
        nullable=False,
        comment='Flow role: setup, main, teardown'
    )
    order_index = Column(Integer, nullable=False, comment='Execution order')
    enabled = Column(Boolean, nullable=False, default=True, comment='Enabled flag')
    params = Column(JSON, nullable=True, comment='Override parameters')

    # Relationships
    testcase = relationship('Testcase', back_populates='testcase_flows')
    flow = relationship('Flow')

    def __repr__(self):
        return f"<TestcaseFlow(testcase_id={self.testcase_id}, flow_id={self.flow_id}, role='{self.flow_role}')>"


class TestcaseInlineStep(BaseModel):
    """Testcase inline steps association"""
    __tablename__ = 'testcase_inline_steps'

    testcase_id = Column(Integer, ForeignKey('testcases.id', ondelete='CASCADE'), nullable=False, comment='Testcase ID')
    step_id = Column(Integer, ForeignKey('steps.id', ondelete='CASCADE'), nullable=False, comment='Step ID')
    order_index = Column(Integer, nullable=False, comment='Execution order')
    override_value = Column(Text, nullable=True, comment='Override action_value')

    # Relationships
    testcase = relationship('Testcase', back_populates='inline_steps')
    step = relationship('Step')

    def __repr__(self):
        return f"<TestcaseInlineStep(testcase_id={self.testcase_id}, step_id={self.step_id}, order={self.order_index})>"
