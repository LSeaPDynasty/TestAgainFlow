"""
内存缓存工具 - 替代Redis的轻量级缓存解决方案
"""
import time
import threading
from typing import Any, Optional, Dict, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class MemoryCache:
    """线程安全的内存缓存，支持TTL和缓存统计"""

    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._max_size = max_size  # 最大缓存条目数
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,  # 驱逐统计
        }

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                # 检查是否过期
                if item['expires_at'] is None or item['expires_at'] > time.time():
                    self._stats['hits'] += 1
                    return item['value']
                else:
                    # 过期，删除
                    del self._cache[key]
                    self._stats['misses'] += 1
                    return None
            self._stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示永不过期
        """
        with self._lock:
            # 如果缓存已满，先删除最旧的条目（LRU策略）
            if len(self._cache) >= self._max_size and key not in self._cache:
                # 找到创建时间最早的条目
                oldest_key = min(self._cache.items(), key=lambda x: x[1]['created_at'])[0]
                del self._cache[oldest_key]
                self._stats['evictions'] += 1
                logger.debug(f"Cache evicted oldest entry: {oldest_key}")

            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl

            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time(),
            }
            self._stats['sets'] += 1

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def clear_pattern(self, pattern: str) -> int:
        """按模式清空缓存

        Args:
            pattern: 缓存键模式（支持简单的 * 通配符）

        Returns:
            清除的缓存数量
        """
        with self._lock:
            keys_to_delete = []
            for key in self._cache.keys():
                if self._match_pattern(key, pattern):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

            if keys_to_delete:
                logger.info(f"Cleared {len(keys_to_delete)} cache entries matching pattern: {pattern}")
            return len(keys_to_delete)

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """简单的模式匹配"""
        import re
        # 将 * 转换为正则表达式
        regex_pattern = pattern.replace('*', '.*')
        return re.match(f'^{regex_pattern}$', key) is not None

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0

            return {
                **self._stats,
                'size': len(self._cache),
                'hit_rate': f"{hit_rate:.2%}",
                'total_requests': total_requests,
            }

    def cleanup_expired(self) -> int:
        """清理过期的缓存项"""
        with self._lock:
            current_time = time.time()
            keys_to_delete = []

            for key, item in self._cache.items():
                if item['expires_at'] is not None and item['expires_at'] <= current_time:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

            if keys_to_delete:
                logger.debug(f"Cleaned up {len(keys_to_delete)} expired cache entries")
            return len(keys_to_delete)


# 全局缓存实例
cache = MemoryCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """缓存装饰器

    Args:
        ttl: 缓存过期时间（秒），默认300秒（5分钟）
        key_prefix: 缓存键前缀

    Usage:
        @cached(ttl=60, key_prefix="user")
        def get_user(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 缓存未命中，执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """缓存函数结果的装饰器，支持自定义键生成

    Args:
        ttl: 缓存过期时间（秒）
        key_func: 自定义缓存键生成函数

    Usage:
        @cache_result(ttl=120, key_func=lambda x: f"user:{x}")
        def get_user_profile(user_id: int):
            return fetch_user_from_db(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{args}:{kwargs}"

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 缓存未命中，执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator