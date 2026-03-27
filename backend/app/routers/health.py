"""Health check router."""
from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.system_health import collect_health_snapshot
from app.utils.response import ok

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse)
def health_check():
    """Health check endpoint."""
    snapshot = collect_health_snapshot()
    return ok(data=snapshot.to_dict())
