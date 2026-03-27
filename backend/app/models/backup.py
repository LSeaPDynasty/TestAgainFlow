"""
Backup model - backup and restore records
"""
from sqlalchemy import Column, String, BigInteger
from .base import BaseModel, Base


class Backup(BaseModel):
    """Backup model for data backup records"""
    __tablename__ = 'backups'

    id = Column(String(100), primary_key=True, comment='Backup ID (timestamp based)')
    resource = Column(String(50), nullable=False, comment='Resource type: all, elements, flows, etc.')
    description = Column(String(500), nullable=True, comment='Backup description')
    size_bytes = Column(BigInteger, nullable=True, comment='Backup file size in bytes')

    def __repr__(self):
        return f"<Backup(id='{self.id}', resource='{self.resource}')>"
