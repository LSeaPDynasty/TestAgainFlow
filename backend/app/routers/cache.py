"""
缓存管理API - 提供缓存统计和管理功能
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.services.permission_service import PermissionService
from app.utils.cache import cache
from app.utils import ok

router = APIRouter()


class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    hits: int
    misses: int
    sets: int
    deletes: int
    size: int
    hit_rate: str
    total_requests: int


class CacheClearRequest(BaseModel):
    """缓存清除请求"""
    pattern: str = "*"  # 默认清除所有缓存


@router.get("/stats", response_model=CacheStatsResponse)
def get_cache_stats(db: Session = Depends(get_db), user_id: int = 1):
    """
    获取缓存统计信息

    需要系统管理员权限
    """
    # 检查系统管理员权限 - 现在会自动抛出ForbiddenException
    PermissionService.check_system_admin(db, user_id)

    stats = cache.get_stats()
    return ok(data=stats)


@router.post("/clear")
def clear_cache(request: CacheClearRequest, db: Session = Depends(get_db), user_id: int = 1):
    """
    清除缓存

    需要系统管理员权限
    支持模式匹配清除，如 "project_*" 只清除项目相关缓存
    """
    # 检查系统管理员权限 - 现在会自动抛出ForbiddenException
    PermissionService.check_system_admin(db, user_id)

    if request.pattern == "*":
        cache.clear()
        return ok(message="缓存已清空")
    else:
        count = cache.clear_pattern(request.pattern)
        return ok(message=f"已清除 {count} 个缓存项")


@router.post("/cleanup")
def cleanup_expired_cache(db: Session = Depends(get_db), user_id: int = 1):
    """
    清理过期的缓存项

    需要系统管理员权限
    """
    # 检查系统管理员权限 - 现在会自动抛出ForbiddenException
    PermissionService.check_system_admin(db, user_id)

    count = cache.cleanup_expired()
    return ok(message=f"已清理 {count} 个过期缓存项")