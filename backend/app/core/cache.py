"""Redis caching utilities for performance optimization."""

import json
import logging
from functools import wraps
from typing import Any, Optional, Callable
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    CACHE_ENABLED = True
    logger.info("Redis cache connected successfully")
except Exception as e:
    logger.warning(f"Redis cache not available: {e}")
    redis_client = None
    CACHE_ENABLED = False


def cache_key_wrapper(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def cached_result(prefix: str, ttl: int = 300):
    """
    Decorator to cache function results in Redis.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default: 5 minutes)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if disabled or Redis not available
            # Fall back to in-memory cache if Redis is not available
            if not CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache_key_wrapper(prefix, *args, **kwargs)
            
            try:
                # Try to get from cache
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                
                # Store in cache
                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache error: {e}, falling back to direct execution")
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern."""
    if not CACHE_ENABLED or not redis_client:
        return
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries matching: {pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")


def get_cache_stats() -> dict:
    """Get Redis cache statistics."""
    if not CACHE_ENABLED or not redis_client:
        return {"enabled": False, "message": "Cache not available"}
    
    try:
        info = redis_client.info()
        memory = redis_client.info("memory")
        
        return {
            "enabled": True,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": memory.get("used_memory_human", "0B"),
            "total_keys": redis_client.dbsize(),
            "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1) * 100
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"enabled": True, "error": str(e)}