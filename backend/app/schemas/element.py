"""
Element schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class LocatorSchema(BaseModel):
    """Locator schema"""
    id: Optional[int] = None
    type: str = Field(..., description="Locator type: resource-id, text, xpath, etc.")
    value: str = Field(..., description="Locator value")
    priority: int = Field(1, ge=1, description="Priority, 1 is highest")


class ElementBase(BaseModel):
    """Base element fields"""
    name: str = Field(..., max_length=100, description="Element name")
    description: Optional[str] = Field(None, description="Description")
    screen_id: int = Field(..., description="Associated screen ID")


class ElementCreate(ElementBase):
    """Element creation schema"""
    locators: List[LocatorSchema] = Field(..., description="Locator list, at least one")


class ElementUpdate(BaseModel):
    """Element update schema"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    screen_id: Optional[int] = None
    locators: Optional[List[LocatorSchema]] = None


class ElementResponse(ElementBase):
    """Element response schema"""
    id: int
    screen_name: str = Field(..., description="Screen name")
    locators: List[LocatorSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ElementTestRequest(BaseModel):
    """Element locator test request"""
    device_serial: str = Field(..., description="Device serial number")
    locator_index: int = Field(0, ge=0, description="Locator index to test")


class ElementTestResponse(BaseModel):
    """Element locator test response"""
    found: bool = Field(..., description="Whether element was found")
    locator_type: str = Field(..., description="Locator type used")
    locator_value: str = Field(..., description="Locator value used")
    bounds: Optional[dict] = Field(None, description="Element bounds: {left, top, right, bottom}")
    screenshot_url: Optional[str] = Field(None, description="Screenshot URL")
