"""
Tag model and association tables
"""
from sqlalchemy import String, Integer, ForeignKey, Table, Column
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


# Association tables for many-to-many relationships
step_tags = Table(
    'step_tags', Base.metadata,
    Column('step_id', Integer, ForeignKey('steps.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    comment='Step-Tag association table'
)

flow_tags = Table(
    'flow_tags', Base.metadata,
    Column('flow_id', Integer, ForeignKey('flows.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    comment='Flow-Tag association table'
)

testcase_tags = Table(
    'testcase_tags', Base.metadata,
    Column('testcase_id', Integer, ForeignKey('testcases.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    comment='Testcase-Tag association table'
)

profile_tags = Table(
    'profile_tags', Base.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    comment='Profile-Tag association table'
)


class Tag(BaseModel):
    """Tag model for categorization"""
    __tablename__ = 'tags'

    name = Column(String(50), nullable=False, unique=True, comment='Tag name, unique')
    color = Column(String(20), nullable=False, default='#3b82f6', comment='Tag color (hex)')

    # Relationships
    steps = relationship('Step', secondary=step_tags, back_populates='tags')
    flows = relationship('Flow', secondary=flow_tags, back_populates='tags')
    testcases = relationship('Testcase', secondary=testcase_tags, back_populates='tags')
    profiles = relationship('Profile', secondary=profile_tags, back_populates='tags')

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', color='{self.color}')>"
