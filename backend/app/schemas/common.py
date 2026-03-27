"""
Common schemas - shared response models and pagination
"""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    code: int = Field(0, description="Response code, 0 for success")
    message: str = Field("success", description="Response message")
    data: Optional[T] = Field(None, description="Response data")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T] = Field(default_factory=list, description="List of items")
    total: int = Field(0, description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Items per page")


class PageParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number, starts from 1")
    page_size: int = Field(20, ge=1, le=100, description="Items per page, max 100")
    search: Optional[str] = Field(None, description="Search keyword")
    order_by: str = Field("created_at", description="Sort field")
    order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order: asc or desc")


# Error codes
class ErrorCode:
    SUCCESS = 0
    VALIDATION_ERROR = 4001
    NOT_FOUND = 4004
    CONFLICT = 4009
    DEPENDENCY_ERROR = 4022
    INTERNAL_ERROR = 5000
    DATABASE_ERROR = 5001
    ENGINE_ERROR = 5002
