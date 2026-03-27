"""
Base model and common fields for all ORM models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """
    Base model with common fields
    All models should inherit from this class
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, comment='Primary key')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='Creation time')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='Last update time')