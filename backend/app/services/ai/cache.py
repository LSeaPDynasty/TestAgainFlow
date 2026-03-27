"""
AI Request Caching Service
Provides caching decorator for AI requests
"""
import json
import hashlib
import functools
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.ai_config import AICache


class AICacheService:
    """AI Response caching service"""

    def __init__(self, db: Session, default_ttl: Optional[int] = None):
        """
        Initialize cache service

        Args:
            db: Database session
            default_ttl: Default TTL in seconds (uses config default if not specified)
        """
        from app.config import settings

        self.db = db
        self.default_ttl = default_ttl or settings.ai_cache_ttl

    def get(self, request_hash: str) -> Optional[Dict]:
        """
        Get cached response

        Args:
            request_hash: Hash of the request payload

        Returns:
            Cached response data or None
        """
        # Clean expired cache first
        self._clean_expired()

        # Get cache entry
        cache_entry = self.db.query(AICache).filter(
            AICache.request_hash == request_hash,
            AICache.expires_at > datetime.utcnow()
        ).first()

        if cache_entry:
            return cache_entry.response_data

        return None

    def set(self, request_hash: str, response_data: Dict, ttl: Optional[int] = None) -> None:
        """
        Set cached response

        Args:
            request_hash: Hash of the request payload
            response_data: Response data to cache
            ttl: Time to live in seconds (uses default if not specified)
        """
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)

        # Delete existing entry if any
        self.db.query(AICache).filter(AICache.request_hash == request_hash).delete()

        # Create new cache entry
        cache_entry = AICache(
            request_hash=request_hash,
            response_data=response_data,
            expires_at=expires_at
        )
        self.db.add(cache_entry)
        self.db.commit()

    def delete(self, request_hash: str) -> bool:
        """Delete cache entry"""
        result = self.db.query(AICache).filter(AICache.request_hash == request_hash).delete()
        self.db.commit()
        return result > 0

    def _clean_expired(self) -> int:
        """Clean expired cache entries"""
        result = self.db.query(AICache).filter(
            AICache.expires_at < datetime.utcnow()
        ).delete()
        self.db.commit()
        return result

    @staticmethod
    def generate_hash(data: Dict) -> str:
        """Generate hash from request data"""
        # Sort keys for consistent hashing
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()


def ai_cache(ttl_seconds: int = 3600, key_func=None):
    """
    Decorator for caching AI requests

    Args:
        ttl_seconds: Time to live in seconds
        key_func: Optional function to generate cache key

    Usage:
        @ai_cache(ttl_seconds=3600)
        async def my_ai_function(request_data):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get database session from self if available
            db = getattr(self, 'db', None)
            if not db:
                # No database, skip caching
                return await func(self, *args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash of args and kwargs
                cache_data = {
                    "args": str(args),
                    "kwargs": str(sorted(kwargs.items()))
                }
                cache_key = AICacheService.generate_hash(cache_data)

            # Try to get from cache
            cache_service = AICacheService(db, ttl_seconds)
            cached = cache_service.get(cache_key)
            if cached:
                return cached

            # Call function
            result = await func(self, *args, **kwargs)

            # Cache result
            if isinstance(result, dict):
                cache_service.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator
