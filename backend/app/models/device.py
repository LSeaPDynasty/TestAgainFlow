"""
Device model - mobile device management
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, JSON
from .base import BaseModel, Base


class Device(BaseModel):
    """Device model representing a mobile device"""
    __tablename__ = 'devices'

    name = Column(String(100), nullable=False, comment='Device name')
    serial = Column(String(100), nullable=False, unique=True, comment='Device serial number, unique')
    model = Column(String(100), nullable=True, comment='Device model')
    os_version = Column(String(50), nullable=True, comment='OS version')
    connection_type = Column(
        Enum('usb', 'tcp', name='connection_type_enum'),
        nullable=False,
        default='usb',
        comment='Connection type: usb or tcp'
    )
    ip_port = Column(String(50), nullable=True, comment='IP:Port for TCP connection')
    capabilities = Column(JSON, nullable=True, comment='Device capabilities: {biometric, nfc, camera}')

    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.name}', serial='{self.serial}')>"
