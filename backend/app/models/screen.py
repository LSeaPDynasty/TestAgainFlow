"""
Screen model - represents a mobile app screen/page
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class Screen(BaseModel):
    """Screen model representing a mobile app screen/page"""
    __tablename__ = 'screens'

    name = Column(String(100), nullable=False, unique=True, comment='Screen name, unique')
    activity = Column(String(255), nullable=True, comment='Activity path, e.g. com.example.app.LoginActivity')
    description = Column(Text, nullable=True, comment='Description')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')

    # Relationships
    elements = relationship('Element', back_populates='screen', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Screen(id={self.id}, name='{self.name}')>"
