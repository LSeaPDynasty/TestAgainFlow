"""
Response utility functions
"""
from typing import Optional, Any, Generic, TypeVar
from app.schemas.common import ApiResponse, ErrorCode

T = TypeVar('T')


def ok(data: Optional[T] = None, message: str = "success") -> ApiResponse[T]:
    """Create success response"""
    return ApiResponse(code=ErrorCode.SUCCESS, message=message, data=data)


def error(code: int, message: str, data: Optional[Any] = None) -> ApiResponse:
    """Create error response"""
    return ApiResponse(code=code, message=message, data=data)
