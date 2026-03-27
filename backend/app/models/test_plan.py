"""
TestPlan model - test plan management for organizing and executing multiple test suites
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class TestPlan(BaseModel):
    """TestPlan model representing a collection of test suites with execution strategies"""
    __tablename__ = 'test_plans'

    name = Column(String(200), nullable=False, unique=True, comment='Test plan name, globally unique')
    description = Column(Text, nullable=True, comment='Test plan description')
    execution_strategy = Column(
        Enum('sequential', 'parallel', name='execution_strategy_enum'),
        nullable=False,
        default='sequential',
        comment='Execution strategy: sequential or parallel'
    )
    max_parallel_tasks = Column(Integer, nullable=False, default=1, comment='Max parallel tasks for parallel execution')
    enabled = Column(Boolean, nullable=False, default=True, comment='Enabled flag')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')

    # Relationships
    test_plan_suites = relationship('TestPlanSuite', back_populates='test_plan', cascade='all, delete-orphan')
    project = relationship('Project', back_populates='test_plans')

    def __repr__(self):
        return f"<TestPlan(id={self.id}, name='{self.name}', strategy='{self.execution_strategy}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'execution_strategy': self.execution_strategy,
            'max_parallel_tasks': self.max_parallel_tasks,
            'enabled': self.enabled,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class TestPlanSuite(BaseModel):
    """TestPlan-Suite association table with order and configuration"""
    __tablename__ = 'test_plan_suites'

    test_plan_id = Column(Integer, ForeignKey('test_plans.id', ondelete='CASCADE'), nullable=False, comment='Test plan ID')
    suite_id = Column(Integer, ForeignKey('suites.id', ondelete='CASCADE'), nullable=False, comment='Suite ID')
    order_index = Column(Integer, nullable=False, comment='Execution order in the test plan')
    enabled = Column(Boolean, nullable=False, default=True, comment='Enabled flag for this suite')
    execution_config = Column(Text, nullable=True, comment='JSON format execution configuration for this suite')

    # Relationships
    test_plan = relationship('TestPlan', back_populates='test_plan_suites')
    suite = relationship('Suite')
    testcase_orders = relationship('TestPlanTestcaseOrder', back_populates='test_plan_suite', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<TestPlanSuite(plan_id={self.test_plan_id}, suite_id={self.suite_id}, order={self.order_index})>"


class TestPlanTestcaseOrder(BaseModel):
    """TestPlan-Suite-Testcase custom order table"""
    __tablename__ = 'test_plan_testcase_orders'

    test_plan_suite_id = Column(Integer, ForeignKey('test_plan_suites.id', ondelete='CASCADE'), nullable=False, comment='Test plan suite association ID')
    testcase_id = Column(Integer, ForeignKey('testcases.id', ondelete='CASCADE'), nullable=False, comment='Testcase ID')
    order_index = Column(Integer, nullable=False, comment='Execution order within the suite')

    # Relationships
    test_plan_suite = relationship('TestPlanSuite', back_populates='testcase_orders')
    testcase = relationship('Testcase')

    def __repr__(self):
        return f"<TestPlanTestcaseOrder(plan_suite_id={self.test_plan_suite_id}, testcase_id={self.testcase_id}, order={self.order_index})>"
