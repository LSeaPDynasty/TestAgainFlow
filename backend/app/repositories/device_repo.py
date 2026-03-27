"""
Device repository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.device import Device
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    """Device repository"""

    def __init__(self, db: Session):
        super().__init__(Device, db)

    def get_by_serial(self, serial: str) -> Optional[Device]:
        """Get device by serial number"""
        return self.get_by_field('serial', serial)

    def list_all(self) -> List[Device]:
        """List all devices"""
        return self.list(limit=1000)
