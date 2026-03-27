"""
Device schemas
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DeviceCapabilitiesSchema(BaseModel):
    """Device capabilities"""
    biometric: bool = Field(False, description="Biometric support")
    nfc: bool = Field(False, description="NFC support")
    camera: bool = Field(False, description="Camera support")


class DeviceBase(BaseModel):
    """Base device fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Device name")
    serial: str = Field(..., min_length=1, max_length=100, description="Device serial number")
    model: Optional[str] = Field(None, max_length=100, description="Device model")
    os_version: Optional[str] = Field(None, max_length=50, description="OS version")
    connection_type: str = Field("usb", pattern="^(usb|tcp)$", description="Connection type")
    ip_port: Optional[str] = Field(None, max_length=50, description="IP:Port for TCP")
    capabilities: Optional[DeviceCapabilitiesSchema] = Field(None, description="Device capabilities")


class DeviceCreate(DeviceBase):
    """Device creation schema"""
    pass


class DeviceUpdate(BaseModel):
    """Device update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=50)
    connection_type: Optional[str] = Field(None, pattern="^(usb|tcp)$")
    ip_port: Optional[str] = Field(None, max_length=50)
    capabilities: Optional[DeviceCapabilitiesSchema] = None


class DeviceResponse(DeviceBase):
    """Device response schema"""
    id: int
    adb_status: str = Field(..., description="ADB status: online, offline, unauthorized")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
