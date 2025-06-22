"""
Async Redis caching service for FastAPI
High-performance caching with aioredis
"""

import os
import json
import logging
import asyncio
from typing import Any, Optional, Union
from datetime import timedelta
from functools import wraps

import aioredis
from aioredis import Redis

logger = logging.getLogger(__name__)


class AsyncCacheService:
    """Async Redis cache service"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_pool = None
        self._redis = None
        
    async def get_redis(self) -> Redis:
        """Get Redis connection with pooling"""
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True
                )
                # Test connection
                await self._redis.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                self._redis = None
                
        return self._redis
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            redis = await self.get_redis()
            if redis is None:
                return None
                
            value = await redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
        return None
        
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Union[int, timedelta] = 300
    ) -> bool:
        """Set value in cache with TTL"""
        try:
            redis = await self.get_redis()
            if redis is None:
                return False
                
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
                
            await redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.debug(f"Cache set error: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            redis = await self.get_redis()
            if redis is None:
                return False
                
            await redis.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error: {e}")
            return False
            
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        try:
            redis = await self.get_redis()
            if redis is None:
                return 0
                
            keys = await redis.keys(pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache clear error: {e}")
            return 0
            
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()


# Global cache service
_cache_service = None

async def get_cache_service() -> AsyncCacheService:
    """FastAPI dependency for cache service"""
    global _cache_service
    if _cache_service is None:
        _cache_service = AsyncCacheService()
    return _cache_service


def async_cached(ttl: int = 300, key_prefix: str = "api"):
    """Async caching decorator for FastAPI endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cache = await get_cache_service()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {cache_key}")
            
            return result
        return wrapper
    return decorator