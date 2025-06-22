"""Caching service for Cosmos DB operations."""

import json
import logging
import time
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

# In-memory cache implementation
# In production, use Redis or Azure Cache
class CosmosCache:
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        
    def _generate_key(self, container: str, operation: str, params: Optional[Dict] = None) -> str:
        """Generate a unique cache key."""
        key_parts = [container, operation]
        if params:
            # Sort params for consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            key_parts.append(hashlib.md5(sorted_params.encode()).hexdigest()[:8])
        return ":".join(key_parts)
    
    def get(self, container: str, operation: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Get cached data if available and not expired."""
        key = self._generate_key(container, operation, params)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires_at']:
                logger.debug(f"Cache hit for {key}")
                return entry['data']
            else:
                # Remove expired entry
                del self.cache[key]
                logger.debug(f"Cache expired for {key}")
        
        return None
    
    def set(self, container: str, operation: str, data: Any, params: Optional[Dict] = None, ttl: Optional[int] = None):
        """Cache data with expiration."""
        key = self._generate_key(container, operation, params)
        ttl = ttl or self.ttl_seconds
        
        self.cache[key] = {
            'data': data,
            'expires_at': time.time() + ttl,
            'cached_at': time.time()
        }
        logger.debug(f"Cached {key} for {ttl} seconds")
    
    def invalidate(self, container: Optional[str] = None):
        """Invalidate cache entries."""
        if container:
            # Invalidate specific container
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{container}:")]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries for container {container}")
        else:
            # Clear all cache
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared entire cache ({count} entries)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_keys = len(self.cache)
        expired_keys = 0
        current_time = time.time()
        
        # Count by container
        container_counts = {}
        for key in self.cache.keys():
            container = key.split(':')[0]
            if container not in container_counts:
                container_counts[container] = 0
            container_counts[container] += 1
            
            # Check if expired
            if self.cache[key]['expires_at'] < current_time:
                expired_keys += 1
        
        # Calculate memory usage (approximate)
        memory_bytes = sum(
            len(json.dumps(entry['data'])) if isinstance(entry['data'], (dict, list)) else len(str(entry['data']))
            for entry in self.cache.values()
        )
        
        return {
            'total_keys': total_keys,
            'expired_keys': expired_keys,
            'active_keys': total_keys - expired_keys,
            'memory_used': f"{memory_bytes / 1024:.2f} KB",
            'key_types': container_counts,
            'ttl_seconds': self.ttl_seconds
        }

# Global cache instance
cosmos_cache = CosmosCache()

class CacheableQuery:
    """Decorator for cacheable Cosmos DB queries."""
    
    def __init__(self, container: str, operation: str, ttl: Optional[int] = None):
        self.container = container
        self.operation = operation
        self.ttl = ttl
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # Extract parameters for cache key
            params = {
                'args': args[1:] if args else [],  # Skip 'self'
                'kwargs': kwargs
            }
            
            # Check cache first
            cached_data = cosmos_cache.get(self.container, self.operation, params)
            if cached_data is not None:
                return cached_data
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cosmos_cache.set(self.container, self.operation, result, params, self.ttl)
            
            return result
        
        return wrapper

# Query filters for optimized Cosmos DB queries
class QueryFilter:
    """Build optimized Cosmos DB queries with filters."""
    
    def __init__(self):
        self.filters = []
        self.parameters = []
        
    def add_date_range(self, field: str, start: Optional[datetime] = None, end: Optional[datetime] = None):
        """Add date range filter."""
        if start:
            self.filters.append(f"c.{field} >= @start_date")
            self.parameters.append({"name": "@start_date", "value": int(start.timestamp())})
        if end:
            self.filters.append(f"c.{field} <= @end_date")
            self.parameters.append({"name": "@end_date", "value": int(end.timestamp())})
        return self
    
    def add_category(self, field: str, value: str):
        """Add category filter."""
        if value:
            self.filters.append(f"c.{field} = @category")
            self.parameters.append({"name": "@category", "value": value})
        return self
    
    def add_status(self, field: str, value: str):
        """Add status filter."""
        if value:
            self.filters.append(f"c.{field} = @status")
            self.parameters.append({"name": "@status", "value": value})
        return self
    
    def add_agent(self, field: str, value: str):
        """Add agent filter."""
        if value:
            self.filters.append(f"c.{field} = @agent")
            self.parameters.append({"name": "@agent", "value": value})
        return self
    
    def add_type(self, field: str, value: str):
        """Add type filter."""
        if value:
            self.filters.append(f"c.{field} = @type")
            self.parameters.append({"name": "@type", "value": value})
        return self
    
    def add_text_search(self, fields: List[str], search_term: str):
        """Add text search across multiple fields."""
        if search_term and fields:
            conditions = [f"CONTAINS(LOWER(c.{field}), LOWER(@search))" for field in fields]
            self.filters.append(f"({' OR '.join(conditions)})")
            self.parameters.append({"name": "@search", "value": search_term})
        return self
    
    def build_query(self, base_query: str = "SELECT * FROM c") -> Dict[str, Any]:
        """Build the complete query with filters."""
        if self.filters:
            query = f"{base_query} WHERE {' AND '.join(self.filters)}"
        else:
            query = base_query
            
        return {
            "query": query,
            "parameters": self.parameters
        }

# Container-specific filter configurations
CONTAINER_FILTERS = {
    "system-inbox": {
        "fields": ["subject", "from", "body", "category", "status", "_ts"],
        "filters": ["date", "category", "status"]
    },
    "user-content": {
        "fields": ["title", "content", "tags", "author", "created_at"],
        "filters": ["date", "author", "tags"]
    },
    "agent-logs": {
        "fields": ["agent_name", "action", "status", "timestamp", "error"],
        "filters": ["date", "agent", "status", "type"]
    },
    "memory-store": {
        "fields": ["layer", "key", "value", "updated_at", "agent_id"],
        "filters": ["date", "agent", "layer"]
    }
}

def get_container_filters(container_name: str) -> Dict[str, Any]:
    """Get filter configuration for a specific container."""
    return CONTAINER_FILTERS.get(container_name, {
        "fields": ["id", "content", "_ts"],
        "filters": ["date"]
    })