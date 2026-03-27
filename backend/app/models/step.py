"""
Step model - reusable atomic operations
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class Step(BaseModel):
    """Step model representing a reusable atomic operation"""
    __tablename__ = 'steps'

    name = Column(String(200), nullable=False, comment='Step name')
    description = Column(Text, nullable=True, comment='Description')
    screen_id = Column(Integer, ForeignKey('screens.id', ondelete='CASCADE'), nullable=False, comment='Associated screen ID')
    action_type = Column(String(50), nullable=False, comment='Action type: click, input, assert_text, etc.')
    element_id = Column(Integer, ForeignKey('elements.id', ondelete='SET NULL'), nullable=True, comment='Target element ID')
    flow_id = Column(Integer, ForeignKey('flows.id', ondelete='SET NULL'), nullable=True, comment='Target flow ID (for call action type)')
    action_value = Column(Text, nullable=True, comment='Action value, supports {{variable}}')
    assert_config = Column(JSON, nullable=True, comment='Assertion config: {type, expected, on_fail}')
    wait_after_ms = Column(Integer, nullable=False, default=0, comment='Wait time after step (ms)')
    continue_on_error = Column(Integer, nullable=False, default=0, comment='Continue execution on error (1=continue, 0=stop)')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')

    # Relationships
    screen = relationship('Screen')
    element = relationship('Element')
    flow = relationship('Flow', foreign_keys=[flow_id])
    tags = relationship('Tag', secondary='step_tags', back_populates='steps')

    def __repr__(self):
        return f"<Step(id={self.id}, name='{self.name}', action_type='{self.action_type}')>"
