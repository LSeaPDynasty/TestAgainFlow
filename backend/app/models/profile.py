"""
Profile model - environment configurations
"""
from sqlalchemy import Column, String, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class Profile(BaseModel):
    """Profile model representing an environment configuration"""
    __tablename__ = 'profiles'

    name = Column(String(100), nullable=False, unique=True, comment='Profile name, unique')
    description = Column(Text, nullable=True, comment='Description')
    variables = Column(JSON, nullable=True, comment='Environment variables as key-value pairs')
    ai_config_id = Column(Integer, ForeignKey('ai_configs.id', ondelete='SET NULL'), nullable=True, comment='Associated AI configuration ID')

    # Relationships
    tags = relationship('Tag', secondary='profile_tags', back_populates='profiles')

    def __repr__(self):
        return f"<Profile(id={self.id}, name='{self.name}')>"
