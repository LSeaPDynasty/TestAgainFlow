"""
Element and Locator models - UI element definitions
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class Element(BaseModel):
    """Element model representing a UI element"""
    __tablename__ = 'elements'

    name = Column(String(100), nullable=False, comment='Element name')
    description = Column(Text, nullable=True, comment='Description')
    screen_id = Column(Integer, ForeignKey('screens.id', ondelete='CASCADE'), nullable=False, comment='Associated screen ID')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Project ID')

    # Relationships
    screen = relationship('Screen', back_populates='elements')
    locators = relationship('Locator', back_populates='element', cascade='all, delete-orphan')

    # Unique constraint: element name is unique within a screen
    __table_args__ = (
        UniqueConstraint('name', 'screen_id', name='uq_element_name_screen'),
    )

    def __repr__(self):
        return f"<Element(id={self.id}, name='{self.name}', screen_id={self.screen_id})>"


class Locator(BaseModel):
    """Locator model for multiple locator strategies"""
    __tablename__ = 'locators'

    element_id = Column(Integer, ForeignKey('elements.id', ondelete='CASCADE'), nullable=False, comment='Associated element ID')
    type = Column(String(50), nullable=False, comment='Locator type: resource-id, text, xpath, etc.')
    value = Column(Text, nullable=False, comment='Locator value')
    priority = Column(Integer, nullable=False, default=1, comment='Priority, 1 is highest')

    # Relationships
    element = relationship('Element', back_populates='locators')

    def __repr__(self):
        return f"<Locator(id={self.id}, type='{self.type}', priority={self.priority})>"
