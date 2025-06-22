"""Cosmos DB endpoints for FastAPI backend."""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from hashlib import md5
from collections import defaultdict
import json
import time

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from redis import Redis
import redis.exceptions

logger = logging.getLogger(__name__)

# Import caching service
try:
    from app.services.cache import cosmos_cache, CacheableQuery, QueryFilter, get_container_filters
    CACHE_AVAILABLE = True
except ImportError:
    logger.warning("Cache service not available")
    CACHE_AVAILABLE = False

# Import cosmos_db_manager from services
try:
    from app.services.cosmos_db_manager import get_db_manager
    logger.info("Successfully imported get_db_manager from services")
except ImportError as e:
    logger.error(f"Failed to import cosmos_db_manager: {e}")
    # Try alternate import path
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / 'scripts'))
        from cosmos_db_manager import get_db_manager
        logger.info("Successfully imported get_db_manager from scripts")
    except ImportError:
        logger.error("Failed to import cosmos_db_manager from both locations")
        get_db_manager = None

router = APIRouter()

# Import query optimization utilities
try:
    from app.core.cosmos_optimization import optimize_query, limit_fields
    OPTIMIZATION_AVAILABLE = True
    logger.info("Query optimization utilities loaded")
except ImportError:
    logger.warning("Query optimization not available")
    OPTIMIZATION_AVAILABLE = False

# Pydantic models
class MessageRequest(BaseModel):
    to: str
    subject: str
    content: str
    from_: Optional[str] = "USER_DASHBOARD"
    type: Optional[str] = "USER_MESSAGE"
    priority: Optional[str] = "medium"
    requiresResponse: Optional[bool] = False
    tags: Optional[List[str]] = []

class DocumentRequest(BaseModel):
    data: Dict[str, Any]
    
class RemoveDuplicatesRequest(BaseModel):
    duplicate_ids: List[str]

# Database manager singleton
db_manager = None

# Cache configuration
CACHE_TTL = 300  # 5 minutes for container lists
DOCUMENT_CACHE_TTL = 60  # 1 minute for documents
redis_client = None

def get_redis_client():
    """Get Redis client for caching."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True
            )
            # Test connection
            redis_client.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            logger.warning("Redis not available, caching disabled")
            redis_client = None
    return redis_client

def get_cosmos_db():
    """Get Cosmos DB manager instance."""
    global db_manager
    logger.info(f"get_cosmos_db called, db_manager is None: {db_manager is None}, get_db_manager available: {get_db_manager is not None}")
    
    if db_manager is None and get_db_manager is not None:
        try:
            # Set COSMOS_DATABASE from COSMOS_DATABASE_NAME for compatibility
            if os.getenv('COSMOS_DATABASE_NAME') and not os.getenv('COSMOS_DATABASE'):
                os.environ['COSMOS_DATABASE'] = os.getenv('COSMOS_DATABASE_NAME')
                logger.info(f"Set COSMOS_DATABASE to: {os.getenv('COSMOS_DATABASE')}")
            
            logger.info("Attempting to initialize Cosmos DB manager...")
            db_manager = get_db_manager()
            logger.info("Cosmos DB manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")
    
    if db_manager is None:
        logger.error("Cosmos DB manager is None after initialization attempt")
        raise HTTPException(status_code=500, detail="Cosmos DB not available")
    
    return db_manager

def cache_key(key_type: str, *args) -> str:
    """Generate cache key."""
    return f"cosmos:{key_type}:{':'.join(str(arg) for arg in args)}"

def get_cached_data(key: str, cache_client: Optional[Redis] = None):
    """Get data from cache."""
    if not cache_client:
        return None
    try:
        data = cache_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.debug(f"Cache get error: {e}")
    return None

def set_cached_data(key: str, data: Any, ttl: int = CACHE_TTL, cache_client: Optional[Redis] = None):
    """Set data in cache."""
    if not cache_client:
        return
    try:
        cache_client.setex(key, ttl, json.dumps(data))
    except Exception as e:
        logger.debug(f"Cache set error: {e}")

@router.get("/containers")
async def get_containers(
    use_cache: bool = Query(True, description="Enable caching"),
    count_docs: bool = Query(False, description="Include document counts (slower)"),
    db=Depends(get_cosmos_db)
):
    """Get all containers with optional document counts."""
    # Try in-memory cache first
    cache_key_suffix = "with_counts" if count_docs else "no_counts"
    if CACHE_AVAILABLE and use_cache:
        cached_data = cosmos_cache.get("all", f"containers_{cache_key_suffix}")
        if cached_data:
            logger.debug(f"Returning in-memory cached container list ({cache_key_suffix})")
            return {
                'success': True,
                'containers': cached_data,
                'cached': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    # Fallback to Redis cache
    cache_client = get_redis_client() if use_cache else None
    cache_key_str = cache_key("containers", db.database_name, cache_key_suffix)
    
    if cache_client and use_cache:
        cached = get_cached_data(cache_key_str, cache_client)
        if cached:
            logger.debug(f"Returning redis cached container list ({cache_key_suffix})")
            return cached
    
    try:
        database = db.client.get_database_client(db.database_name)
        containers = []
        
        for container in database.list_containers():
            container_info = {
                'id': container['id'],
                'partitionKey': container.get('partitionKey', {}).get('paths', [''])[0]
            }
            
            if count_docs:
                # Only count documents if requested
                container_client = database.get_container_client(container['id'])
                
                # Get document count with caching
                count_cache_key = cache_key("count", db.database_name, container['id'])
                count = None
                
                if cache_client and use_cache:
                    count = get_cached_data(count_cache_key, cache_client)
                
                if count is None:
                    count_query = "SELECT VALUE COUNT(1) FROM c"
                    count_items = list(container_client.query_items(
                        query=count_query,
                        enable_cross_partition_query=True
                    ))
                    count = count_items[0]
                    
                    if cache_client:
                        set_cached_data(count_cache_key, count, ttl=CACHE_TTL, cache_client=cache_client)
                
                container_info['count'] = count
            else:
                # Use placeholder for faster loading
                container_info['count'] = -1  # Indicates count not loaded
            
            containers.append(container_info)
        
        # Only sort by count if we have counts
        if count_docs:
            sorted_containers = sorted(containers, key=lambda x: x['count'], reverse=True)
        else:
            sorted_containers = sorted(containers, key=lambda x: x['id'])
        
        result = {
            'success': True,
            'containers': sorted_containers,
            'cached': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Cache in memory first
        if CACHE_AVAILABLE and use_cache:
            cosmos_cache.set("all", f"containers_{cache_key_suffix}", sorted_containers)
        
        # Also cache in Redis if available
        if cache_client:
            set_cached_data(cache_key_str, result, cache_client=cache_client)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers/{container_id}/documents")
async def get_documents(
    container_id: str,
    limit: int = Query(20, ge=1, le=100, description="Limit results per page"),
    offset: int = Query(0, ge=0),
    filter_field: Optional[str] = Query(None, description="Field to filter on"),
    filter_value: Optional[str] = Query(None, description="Value to filter by"),
    date_range: Optional[str] = Query(None, description="Date range filter (today, week, month, quarter)"),
    category: Optional[str] = Query(None, description="Category filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    agent: Optional[str] = Query(None, description="Agent filter"),
    doc_type: Optional[str] = Query(None, description="Document type filter"),
    use_cache: bool = Query(True, description="Enable caching"),
    db=Depends(get_cosmos_db)
):
    """Get documents from a specific container with filtering and caching."""
    cache_client = get_redis_client() if use_cache else None
    cache_key_str = cache_key("documents", container_id, limit, offset, filter_field or '', filter_value or '')
    
    # Try cache first for small result sets
    if cache_client and use_cache and limit <= 50:
        cached = get_cached_data(cache_key_str, cache_client)
        if cached:
            cached['cached'] = True
            return cached
    
    try:
        database = db.client.get_database_client(db.database_name)
        container = database.get_container_client(container_id)
        
        # Simplified query building for now - bypass complex filtering
        # TODO: Re-enable advanced filtering once cache service is fully working
        if filter_field and filter_value:
            if container_id == "system_inbox":
                query = f"SELECT * FROM c WHERE c.{filter_field} = @filterValue ORDER BY c.timestamp DESC OFFSET {offset} LIMIT {limit}"
            else:
                query = f"SELECT * FROM c WHERE c.{filter_field} = @filterValue ORDER BY c._ts DESC OFFSET {offset} LIMIT {limit}"
            parameters = [{"name": "@filterValue", "value": filter_value}]
        else:
            if container_id == "system_inbox":
                query = f"SELECT * FROM c ORDER BY c.timestamp DESC OFFSET {offset} LIMIT {limit}"
            else:
                query = f"SELECT * FROM c ORDER BY c._ts DESC OFFSET {offset} LIMIT {limit}"
            parameters = []
        
        documents = []
        for item in container.query_items(
            query=query,
            parameters=parameters if parameters else None,
            enable_cross_partition_query=True
        ):
            documents.append(item)
        
        result = {
            'success': True,
            'container': container_id,
            'documents': documents,
            'count': len(documents),
            'offset': offset,
            'limit': limit,
            'filters': {
                'field': filter_field,
                'value': filter_value,
                'date_range': date_range,
                'category': category,
                'status': status,
                'agent': agent,
                'type': doc_type
            },
            'cached': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Cache small result sets
        if cache_client and len(documents) <= 50:
            set_cached_data(cache_key_str, result, ttl=DOCUMENT_CACHE_TTL, cache_client=cache_client)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting documents from {container_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers/{container_id}/documents/{document_id}")
async def get_document(
    container_id: str,
    document_id: str,
    db=Depends(get_cosmos_db)
):
    """Get a specific document."""
    try:
        database = db.client.get_database_client(db.database_name)
        container = database.get_container_client(container_id)
        
        # Try to find document
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": document_id}]
        
        documents = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if documents:
            return {
                'success': True,
                'document': documents[0]
            }
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id} from {container_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    containers: Optional[List[str]] = Query(None, description="Limit search to specific containers"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    use_cache: bool = Query(True, description="Enable caching"),
    db=Depends(get_cosmos_db)
):
    """Search across containers with filtering and caching."""
    cache_client = get_redis_client() if use_cache else None
    containers_str = ','.join(containers) if containers else 'all'
    cache_key_str = cache_key("search", q, containers_str, limit)
    
    # Try cache first
    if cache_client and use_cache:
        cached = get_cached_data(cache_key_str, cache_client)
        if cached:
            cached['cached'] = True
            return cached
    
    try:
        results = []
        database = db.client.get_database_client(db.database_name)
        searched_containers = 0
        
        # Get containers to search
        all_containers = list(database.list_containers())
        if containers:
            # Filter to requested containers
            containers_to_search = [c for c in all_containers if c['id'] in containers]
        else:
            containers_to_search = all_containers
        
        # Search in each container
        for container_info in containers_to_search:
            if len(results) >= limit:
                break
                
            container = database.get_container_client(container_info['id'])
            searched_containers += 1
            
            # Search in common text fields
            query = """
            SELECT TOP @limit * FROM c 
            WHERE CONTAINS(LOWER(c.content), LOWER(@search))
               OR CONTAINS(LOWER(c.subject), LOWER(@search))
               OR CONTAINS(LOWER(c.action), LOWER(@search))
               OR CONTAINS(LOWER(c.id), LOWER(@search))
               OR CONTAINS(LOWER(c.agentName), LOWER(@search))
               OR CONTAINS(LOWER(c.from), LOWER(@search))
            ORDER BY c._ts DESC
            """
            
            parameters = [
                {"name": "@search", "value": q},
                {"name": "@limit", "value": limit - len(results)}
            ]
            
            try:
                docs = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                for doc in docs:
                    results.append({
                        'container': container_info['id'],
                        'document': doc,
                        'score': 1.0  # Cosmos DB doesn't provide relevance scores
                    })
                    
            except Exception as e:
                # Log but continue searching other containers
                logger.debug(f"Search failed in container {container_info['id']}: {e}")
                pass
        
        result = {
            'success': True,
            'results': results,
            'count': len(results),
            'search_term': q,
            'containers_searched': searched_containers,
            'cached': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Cache the result
        if cache_client and len(results) <= 50:
            set_cached_data(cache_key_str, result, ttl=DOCUMENT_CACHE_TTL * 2, cache_client=cache_client)
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(
    use_cache: bool = Query(True, description="Enable caching"),
    db=Depends(get_cosmos_db)
):
    """Get database statistics with caching."""
    cache_client = get_redis_client() if use_cache else None
    cache_key_str = cache_key("stats", db.database_name)
    
    # Try cache first
    if cache_client and use_cache:
        cached = get_cached_data(cache_key_str, cache_client)
        if cached:
            cached['cached'] = True
            return cached
    
    try:
        database = db.client.get_database_client(db.database_name)
        stats = {
            'database': db.database_name,
            'endpoint': db.endpoint,
            'containers': {},
            'totalDocuments': 0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'cacheEnabled': cache_client is not None
        }
        
        for container_info in database.list_containers():
            container = database.get_container_client(container_info['id'])
            
            # Try to get count from cache first
            count_cache_key = cache_key("count", db.database_name, container_info['id'])
            count = None
            
            if cache_client and use_cache:
                count = get_cached_data(count_cache_key, cache_client)
            
            if count is None:
                count_query = "SELECT VALUE COUNT(1) FROM c"
                count = list(container.query_items(
                    query=count_query,
                    enable_cross_partition_query=True
                ))[0]
                
                if cache_client:
                    set_cached_data(count_cache_key, count, ttl=CACHE_TTL, cache_client=cache_client)
            
            stats['containers'][container_info['id']] = count
            stats['totalDocuments'] += count
        
        result = {
            'success': True,
            'stats': stats,
            'cached': False
        }
        
        # Cache the result
        if cache_client:
            set_cached_data(cache_key_str, result, ttl=CACHE_TTL, cache_client=cache_client)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/info")
async def get_cache_info():
    """Get cache statistics and information."""
    if not CACHE_AVAILABLE:
        return {
            'success': True,
            'enabled': False,
            'message': 'Cache service not available'
        }
    
    stats = cosmos_cache.get_stats()
    return {
        'success': True,
        'enabled': True,
        'stats': stats
    }

@router.post("/cache/clear")
async def clear_cache(container: Optional[str] = Query(None, description="Clear specific container cache")):
    """Clear cache - optionally for a specific container."""
    if not CACHE_AVAILABLE:
        return {
            'success': False,
            'message': 'Cache service not available'
        }
    
    cosmos_cache.invalidate(container)
    
    if container:
        message = f"Cleared cache for container: {container}"
    else:
        message = "Cleared all cache entries"
    
    return {
        'success': True,
        'message': message
    }

@router.get("/containers/{container_id}/filters")
async def get_container_filters(container_id: str):
    """Get available filters for a container."""
    filters = get_container_filters(container_id)
    return {
        'success': True,
        'container': container_id,
        'filters': filters
    }

@router.get("/user-content")
async def get_user_content(db=Depends(get_cosmos_db)):
    """Get recent user content from system_inbox."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Try to get from system_inbox container
        try:
            container = database.get_container_client('system_inbox')
            query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 10"
            messages = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return {
                'success': True,
                'messages': messages,
                'container': 'system_inbox'
            }
            
        except:
            # Fallback to any container with messages
            for container_info in database.list_containers():
                if 'message' in container_info['id'].lower() or 'inbox' in container_info['id'].lower():
                    container = database.get_container_client(container_info['id'])
                    query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 5"
                    messages = list(container.query_items(
                        query=query,
                        enable_cross_partition_query=True
                    ))
                    
                    return {
                        'success': True,
                        'messages': messages,
                        'container': container_info['id']
                    }
            
            # No messages found
            return {
                'success': True,
                'messages': [],
                'container': None
            }
        
    except Exception as e:
        logger.error(f"Error getting user content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def send_message(message: MessageRequest, db=Depends(get_cosmos_db)):
    """Send a new message to the database."""
    try:
        # Create message document
        timestamp = datetime.utcnow().isoformat() + 'Z'
        message_id = f"msg_{timestamp.replace(':', '').replace('-', '').replace('.', '_')}"
        
        message_doc = {
            'id': message_id,
            'from': message.from_,
            'to': message.to,
            'subject': message.subject,
            'content': message.content,
            'type': message.type,
            'priority': message.priority,
            'timestamp': timestamp,
            'partitionKey': timestamp[:7],  # YYYY-MM format
            'requiresResponse': message.requiresResponse,
            'status': 'sent',
            'tags': message.tags
        }
        
        # Store in messages container
        database = db.client.get_database_client(db.database_name)
        container = database.get_container_client('system_inbox')
        
        result = container.create_item(message_doc)
        
        return {
            'success': True,
            'message': 'Message sent successfully',
            'document_id': result['id'],
            'timestamp': timestamp
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_name}/documents")
async def create_document(
    container_name: str,
    document: DocumentRequest,
    db=Depends(get_cosmos_db)
):
    """Create a new document in specified container."""
    try:
        # Validate container exists
        database = db.client.get_database_client(db.database_name)
        containers = [c['id'] for c in database.list_containers()]
        if container_name not in containers:
            raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
        
        container = database.get_container_client(container_name)
        data = document.data
        
        # Ensure required fields
        if 'id' not in data:
            data['id'] = f"{container_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat() + 'Z'
        
        # Create item
        result = container.create_item(body=data)
        
        return {
            'success': True,
            'document_id': result['id'],
            'container': container_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document in {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_log_hash(log):
    """Create hash from log content to identify duplicates."""
    key_fields = []
    
    if 'conversation_flow' in log:
        key_fields.append(log.get('session_metadata', {}).get('session_id', ''))
        key_fields.append(str(log.get('conversation_flow', [])))
    elif log.get('agentName'):
        key_fields.append(log.get('agentName', ''))
        key_fields.append(log.get('action', ''))
        key_fields.append(log.get('timestamp', ''))
    else:
        key_fields.append(str(log.get('content', '')))
        key_fields.append(str(log.get('complete_conversation_flow', '')))
        
    content = '|'.join(key_fields)
    return md5(content.encode()).hexdigest()

@router.get("/logs/analyze")
async def analyze_logs(db=Depends(get_cosmos_db)):
    """Analyze logs for duplicates and terminal history."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Try to get logs container
        try:
            container = database.get_container_client('logs')
        except:
            # Try alternative container names
            for alt_name in ['agent_logs', 'system_logs', 'agent_session_logs']:
                try:
                    container = database.get_container_client(alt_name)
                    break
                except:
                    continue
            else:
                raise HTTPException(status_code=404, detail="No logs container found")
        
        query = "SELECT * FROM c"
        all_logs = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Analyze duplicates
        seen_hashes = {}
        duplicates = []
        terminal_logs = []
        agent_logs = []
        log_stats = defaultdict(int)
        
        for log in all_logs:
            # Create hash
            content_hash = create_log_hash(log)
            
            if content_hash in seen_hashes:
                duplicates.append({
                    'original_id': seen_hashes[content_hash]['id'],
                    'duplicate_id': log.get('id', 'unknown'),
                    'type': log.get('logType', log.get('type', 'unknown'))
                })
            else:
                seen_hashes[content_hash] = log
            
            # Categorize
            if 'terminal' in str(log).lower() or 'conversation_flow' in log:
                terminal_logs.append(log)
            elif log.get('agentName'):
                agent_logs.append(log)
            
            # Stats
            log_type = log.get('logType', log.get('type', 'unknown'))
            log_stats[log_type] += 1
        
        # Verify terminal logs
        valid_terminal = 0
        for log in terminal_logs:
            if 'conversation_flow' in log:
                flow = log['conversation_flow']
                has_user = any(item.get('type') == 'user_input' for item in flow)
                has_claude = any(item.get('type') == 'claude_response' for item in flow)
                if has_user and has_claude:
                    valid_terminal += 1
            elif 'capture_completeness' in log:
                valid_terminal += 1
        
        return {
            'success': True,
            'analysis': {
                'total_logs': len(all_logs),
                'duplicates': len(duplicates),
                'duplicate_details': duplicates[:10],  # First 10
                'terminal_logs': len(terminal_logs),
                'valid_terminal_logs': valid_terminal,
                'agent_logs': len(agent_logs),
                'log_types': dict(log_stats)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/analyze")
async def analyze_messages(db=Depends(get_cosmos_db)):
    """Analyze messages for duplicates."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Try to get messages container
        try:
            container = database.get_container_client('system_inbox')
        except:
            # Try alternative container names
            for alt_name in ['system_inbox', 'user_messages', 'inbox']:
                try:
                    container = database.get_container_client(alt_name)
                    break
                except:
                    continue
            else:
                raise HTTPException(status_code=404, detail="No messages container found")
        
        query = "SELECT * FROM c"
        all_messages = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Group by content hash
        content_groups = defaultdict(list)
        
        for msg in all_messages:
            key_content = f"{msg.get('subject', '')}-{msg.get('content', '')}-{msg.get('from', '')}-{msg.get('to', '')}"
            content_hash = md5(key_content.encode()).hexdigest()
            content_groups[content_hash].append(msg)
        
        # Find duplicates
        duplicates = []
        total_duplicates = 0
        
        for group in content_groups.values():
            if len(group) > 1:
                total_duplicates += len(group) - 1
                duplicates.append({
                    'subject': group[0].get('subject', 'No subject'),
                    'copies': len(group),
                    'duplicate_ids': [msg['id'] for msg in group[1:]]  # All except first
                })
        
        return {
            'success': True,
            'analysis': {
                'total_messages': len(all_messages),
                'duplicate_groups': len(duplicates),
                'total_duplicates': total_duplicates,
                'duplicate_details': duplicates[:10]  # First 10 groups
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logs/remove-duplicates")
async def remove_duplicate_logs(
    request: RemoveDuplicatesRequest,
    db=Depends(get_cosmos_db)
):
    """Remove duplicate logs from database."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Try to get logs container
        try:
            container = database.get_container_client('logs')
        except:
            # Try alternative container names
            for alt_name in ['agent_logs', 'system_logs', 'agent_session_logs']:
                try:
                    container = database.get_container_client(alt_name)
                    break
                except:
                    continue
            else:
                raise HTTPException(status_code=404, detail="No logs container found")
        
        duplicate_ids = request.duplicate_ids
        
        if not duplicate_ids:
            raise HTTPException(status_code=400, detail="No duplicate IDs provided")
        
        removed = 0
        errors = []
        
        for dup_id in duplicate_ids:
            try:
                # First get the log to find its partition key
                log_query = f"SELECT * FROM c WHERE c.id = '{dup_id}'"
                log_results = list(container.query_items(query=log_query, enable_cross_partition_query=True))
                
                if log_results:
                    log = log_results[0]
                    partition_key = log.get('partitionKey', log.get('agentName', 'unknown'))
                    container.delete_item(item=dup_id, partition_key=partition_key)
                    removed += 1
                else:
                    errors.append({'id': dup_id, 'error': 'Log not found'})
            except Exception as e:
                errors.append({'id': dup_id, 'error': str(e)})
        
        return {
            'success': True,
            'removed': removed,
            'errors': errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing duplicate logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/remove-duplicates")
async def remove_duplicate_messages(
    request: RemoveDuplicatesRequest,
    db=Depends(get_cosmos_db)
):
    """Remove duplicate messages."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Try to get messages container
        try:
            container = database.get_container_client('system_inbox')
        except:
            # Try alternative container names
            for alt_name in ['system_inbox', 'user_messages', 'inbox']:
                try:
                    container = database.get_container_client(alt_name)
                    break
                except:
                    continue
            else:
                raise HTTPException(status_code=404, detail="No messages container found")
        
        duplicate_ids = request.duplicate_ids
        
        if not duplicate_ids:
            raise HTTPException(status_code=400, detail="No duplicate IDs provided")
        
        removed = 0
        errors = []
        
        # Get the actual partition key values for each message
        for msg_id in duplicate_ids:
            try:
                # First get the message to find its partition key
                msg_query = f"SELECT * FROM c WHERE c.id = '{msg_id}'"
                msg_results = list(container.query_items(query=msg_query, enable_cross_partition_query=True))
                
                if msg_results:
                    msg = msg_results[0]
                    partition_key = msg.get('partitionKey', '2025-06')  # Default fallback
                    container.delete_item(item=msg_id, partition_key=partition_key)
                    removed += 1
                else:
                    errors.append({'id': msg_id, 'error': 'Message not found'})
            except Exception as e:
                errors.append({'id': msg_id, 'error': str(e)})
        
        return {
            'success': True,
            'removed': removed,
            'errors': errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing duplicate messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Clear only keys matching pattern")
):
    """Clear cache entries."""
    cache_client = get_redis_client()
    if not cache_client:
        return {
            'success': False,
            'message': 'Cache not available'
        }
    
    try:
        cleared = 0
        if pattern:
            # Clear specific pattern
            keys = cache_client.keys(f"cosmos:{pattern}*")
            if keys:
                cleared = cache_client.delete(*keys)
        else:
            # Clear all cosmos cache
            keys = cache_client.keys("cosmos:*")
            if keys:
                cleared = cache_client.delete(*keys)
        
        return {
            'success': True,
            'cleared': cleared,
            'message': f'Cleared {cleared} cache entries'
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/info")
async def get_cache_info():
    """Get cache information."""
    cache_client = get_redis_client()
    if not cache_client:
        return {
            'success': False,
            'enabled': False,
            'message': 'Cache not available'
        }
    
    try:
        # Get cache stats
        info = cache_client.info()
        cosmos_keys = cache_client.keys("cosmos:*")
        
        # Group keys by type
        key_types = defaultdict(int)
        for key in cosmos_keys:
            parts = key.split(":")
            if len(parts) >= 2:
                key_types[parts[1]] += 1
        
        return {
            'success': True,
            'enabled': True,
            'stats': {
                'total_keys': len(cosmos_keys),
                'key_types': dict(key_types),
                'memory_used': info.get('used_memory_human', 'unknown'),
                'uptime': info.get('uptime_in_seconds', 0),
                'connected_clients': info.get('connected_clients', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return {
            'success': False,
            'enabled': True,
            'message': str(e)
        }