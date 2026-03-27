"""
DataStore model - global data warehouse
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class DataStore(BaseModel):
    """DataStore model for global environment data"""
    __tablename__ = 'data_store'

    env = Column(String(100), nullable=False, comment='Environment name (dev, staging, prod)')
    key_name = Column(String(200), nullable=False, comment='Key name')
    value = Column(Text, nullable=True, comment='Value')
    updated_at = Column(DateTime, nullable=False, comment='Last update time')

    # Unique constraint: env + key_name combination is unique
    __table_args__ = (
        UniqueConstraint('env', 'key_name', name='uq_env_key'),
    )

    def __repr__(self):
        return f"<DataStore(env='{self.env}', key='{self.key_name}')>"
