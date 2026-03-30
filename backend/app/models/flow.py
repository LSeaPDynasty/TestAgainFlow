"""
Flow and FlowStep models - flow orchestration
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum, Index
import sqlalchemy
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class Flow(BaseModel):
    """Flow model representing a sequence of steps"""
    __tablename__ = 'flows'

    name = Column(String(200), nullable=False, unique=True, comment='Flow name, globally unique')
    description = Column(Text, nullable=True, comment='Description')
    flow_type = Column(
        Enum('standard', 'dsl', 'python', name='flow_type_enum'),
        nullable=False,
        default='standard',
        comment='Flow type: standard, dsl, python'
    )
    requires = Column(JSON, nullable=True, comment='Required parameter names')
    default_params = Column(JSON, nullable=True, comment='Default parameter values')
    dsl_content = Column(Text, nullable=True, comment='DSL text content')
    py_file = Column(String(500), nullable=True, comment='Python file relative path')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')

    # Relationships
    # 明确指定使用 flow_id 外键来建立关系
    flow_steps = relationship(
        'FlowStep',
        back_populates='flow',
        foreign_keys='FlowStep.flow_id',
        cascade='all, delete-orphan'
    )
    tags = relationship('Tag', secondary='flow_tags', back_populates='flows')

    # Indexes for query optimization
    __table_args__ = (
        Index('ix_flow_project_id', 'project_id'),
        Index('ix_flow_type', 'flow_type'),
    )

    def __repr__(self):
        return f"<Flow(id={self.id}, name='{self.name}', type='{self.flow_type}')>"


class FlowStep(BaseModel):
    """Flow-Step association table"""
    __tablename__ = 'flow_steps'

    flow_id = Column(Integer, ForeignKey('flows.id', ondelete='CASCADE'), nullable=False, comment='Flow ID')
    step_id = Column(Integer, ForeignKey('steps.id', ondelete='CASCADE'), nullable=True, comment='Step ID')
    sub_flow_id = Column(Integer, ForeignKey('flows.id', ondelete='CASCADE'), nullable=True, comment='Sub Flow ID (for nested flows)')
    order_index = Column(Integer, nullable=False, comment='Execution order')
    override_value = Column(Text, nullable=True, comment='Override action value')

    # Relationships
    # 主流程关系 - 使用 flow_id
    flow = relationship(
        'Flow',
        back_populates='flow_steps',
        foreign_keys=[flow_id]
    )
    # 步骤关系
    step = relationship('Step', foreign_keys=[step_id])
    # 子流程关系 - 使用 sub_flow_id
    sub_flow = relationship(
        'Flow',
        foreign_keys=[sub_flow_id],
        remote_side='Flow.id'
    )

    # Indexes for query optimization - composite indexes for common join patterns
    __table_args__ = (
        Index('ix_flow_step_flow_id', 'flow_id'),
        Index('ix_flow_step_step_id', 'step_id'),
        Index('ix_flow_step_flow_order', 'flow_id', 'order_index'),
    )

    def __repr__(self):
        if self.step_id:
            return f"<FlowStep(flow_id={self.flow_id}, step_id={self.step_id}, order={self.order_index})>"
        else:
            return f"<FlowStep(flow_id={self.flow_id}, sub_flow_id={self.sub_flow_id}, order={self.order_index})>"
