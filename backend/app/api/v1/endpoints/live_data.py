"""Live data API endpoints matching Flask dashboard functionality."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

# Import Cosmos DB dependency
from .cosmos import get_cosmos_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory cache for expensive operations
_cache = {}
CACHE_TTL = 60  # 60 seconds cache for health check

@router.get("/agents")
async def get_live_agents(db=Depends(get_cosmos_db)):
    """Get live agent data matching Flask /api/live/agents."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Get recent agent activity from multiple containers
        containers = ['agent_logs', 'agent_session_logs', 'journal_entries']
        agents_data = {}
        
        for container_name in containers:
            try:
                container = database.get_container_client(container_name)
                query = """SELECT * FROM c 
                          WHERE c.agent_name != null 
                          AND c._ts > @recent_ts
                          ORDER BY c._ts DESC"""
                
                recent_ts = (datetime.utcnow() - timedelta(hours=24)).timestamp()
                results = []
                async for item in container.query_items(
                    query=query,
                    parameters=[{"name": "@recent_ts", "value": recent_ts}],
                    enable_cross_partition_query=True,
                    max_item_count=100
                ):
                    results.append(item)
                
                for item in results:
                    agent_name = item.get('agent_name')
                    if agent_name:
                        if agent_name not in agents_data:
                            agents_data[agent_name] = {
                                'agent_name': agent_name,
                                'status': 'active',
                                'last_activity': item.get('_ts', 0),
                                'actions': [],
                                'sessions': [],
                                'journals': []
                            }
                        
                        # Categorize by container type
                        if container_name == 'agent_logs':
                            agents_data[agent_name]['actions'].append(item)
                        elif container_name == 'agent_session_logs':
                            agents_data[agent_name]['sessions'].append(item)
                        elif container_name == 'journal_entries':
                            agents_data[agent_name]['journals'].append(item)
                        
                        # Update last activity
                        if item.get('_ts', 0) > agents_data[agent_name]['last_activity']:
                            agents_data[agent_name]['last_activity'] = item.get('_ts', 0)
                            
            except Exception as e:
                logger.debug(f"Could not query {container_name}: {e}")
                continue
        
        # Convert to list and add computed fields
        agents_list = []
        for agent_name, data in agents_data.items():
            # Determine status based on last activity
            last_ts = data['last_activity']
            now_ts = datetime.utcnow().timestamp()
            
            if last_ts > (now_ts - 3600):  # 1 hour
                status = 'active'
            elif last_ts > (now_ts - 86400):  # 24 hours
                status = 'idle'
            else:
                status = 'offline'
            
            agents_list.append({
                'agent_name': agent_name,
                'status': status,
                'last_activity': datetime.fromtimestamp(last_ts).isoformat(),
                'action_count': len(data['actions']),
                'session_count': len(data['sessions']),
                'journal_count': len(data['journals']),
                'recent_action': data['actions'][0].get('action', 'No recent action') if data['actions'] else 'No recent action'
            })
        
        # Sort by last activity
        agents_list.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return {
            'success': True,
            'agents': agents_list,
            'total_count': len(agents_list),
            'active_count': len([a for a in agents_list if a['status'] == 'active']),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting live agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/core-documents")
async def get_core_documents(db=Depends(get_cosmos_db)):
    """Get core documents matching Flask /api/live/core-documents."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Get core documents from key containers
        core_containers = ['documents', 'processed_documents', 'institutional-data-center']
        documents = []
        
        for container_name in core_containers:
            try:
                container = database.get_container_client(container_name)
                query = """SELECT TOP 20 * FROM c ORDER BY c._ts DESC"""
                
                results = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                for doc in results:
                    documents.append({
                        'id': doc.get('id'),
                        'container': container_name,
                        'title': doc.get('title') or doc.get('name') or doc.get('id', 'Untitled'),
                        'content_preview': str(doc.get('content', ''))[:200] + '...' if doc.get('content') else 'No content',
                        'timestamp': datetime.fromtimestamp(doc.get('_ts', 0)).isoformat(),
                        'size': len(str(doc)),
                        'type': doc.get('type', 'document')
                    })
                    
            except Exception as e:
                logger.debug(f"Could not query {container_name}: {e}")
                continue
        
        # Sort by timestamp
        documents.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'success': True,
            'documents': documents[:50],  # Limit to 50 most recent
            'total_count': len(documents),
            'containers_checked': core_containers,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting core documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-health")
async def get_system_health(db=Depends(get_cosmos_db)):
    """Get system health matching Flask /api/live/system-health."""
    # Check cache first
    cache_key = "system_health"
    now = time.time()
    
    if cache_key in _cache:
        cached_data, cached_time = _cache[cache_key]
        if now - cached_time < CACHE_TTL:
            logger.info("Returning cached system health data")
            return cached_data
    
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Check container health
        container_health = {}
        total_containers = 0
        healthy_containers = 0
        
        try:
            containers = list(database.list_containers())
            total_containers = len(containers)
            
            # Sample only 5 containers for performance (adjust health calculation accordingly)
            import random
            sample_size = min(5, len(containers))
            containers_to_check = random.sample(containers, sample_size) if len(containers) > 5 else containers
            
            for container_info in containers_to_check:
                container_id = container_info['id']
                try:
                    container = database.get_container_client(container_id)
                    # Simple health check - try to query one document
                    list(container.query_items(
                        query="SELECT TOP 1 * FROM c",
                        enable_cross_partition_query=True
                    ))
                    container_health[container_id] = 'healthy'
                    healthy_containers += 1
                except:
                    container_health[container_id] = 'unhealthy'
                    
        except Exception as e:
            logger.debug(f"Error checking container health: {e}")
        
        # Calculate health score based on sample
        # Extrapolate from sample to estimate total health
        sample_health_rate = (healthy_containers / sample_size * 100) if sample_size > 0 else 0
        health_score = sample_health_rate  # Use sample rate as overall health estimate
        
        # Determine system status
        if health_score >= 90:
            system_status = 'excellent'
        elif health_score >= 70:
            system_status = 'good'
        elif health_score >= 50:
            system_status = 'fair'
        else:
            system_status = 'poor'
        
        # Get recent activity count
        activity_count = 0
        try:
            container = database.get_container_client('logs')
            recent_ts = (datetime.utcnow() - timedelta(hours=1)).timestamp()
            results = list(container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c._ts > @recent_ts",
                parameters=[{"name": "@recent_ts", "value": recent_ts}],
                enable_cross_partition_query=True
            ))
            activity_count = results[0] if results else 0
        except:
            activity_count = 0
        
        result = {
            'success': True,
            'system_status': system_status,
            'health_score': round(health_score, 2),
            'total_containers': total_containers,
            'healthy_containers': healthy_containers,
            'unhealthy_containers': total_containers - healthy_containers,
            'recent_activity_count': activity_count,
            'container_health': container_health,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': '24h 15m',  # Placeholder - would need actual uptime tracking
            'memory_usage': '45%',  # Placeholder - would need actual memory monitoring
            'cpu_usage': '12%'  # Placeholder - would need actual CPU monitoring
        }
        
        # Cache the result
        _cache[cache_key] = (result, time.time())
        logger.info(f"Cached system health data (sampled {sample_size} of {total_containers} containers)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))