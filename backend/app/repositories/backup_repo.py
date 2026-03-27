"""
Backup repository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.backup import Backup
from app.repositories.base import BaseRepository


class BackupRepository(BaseRepository[Backup]):
    """Backup repository"""

    def __init__(self, db: Session):
        super().__init__(Backup, db)

    def list_by_resource(self, resource: Optional[str] = None) -> List[Backup]:
        """List backups by resource type"""
        if resource:
            return self.list(filters={'resource': resource}, limit=1000, order_by='created_at', order='desc')
        return self.list(limit=1000, order_by='created_at', order='desc')
