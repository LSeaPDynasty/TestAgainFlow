"""
Pagination utility
"""
from typing import Tuple
from fastapi import Query
from app.schemas.common import PageParams


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    search: str = Query(None, description="Search keyword"),
    order_by: str = Query("created_at", description="Order by field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Order direction")
) -> PageParams:
    """Get pagination parameters from query"""
    return PageParams(
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order=order
    )


def calculate_offset(page: int, page_size: int) -> int:
    """Calculate offset for pagination"""
    return (page - 1) * page_size
