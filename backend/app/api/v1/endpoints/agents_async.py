"""Agent management API endpoints with proper async patterns"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends

from app.services.async_cosmos_db import get_cosmos_service, AsyncCosmosDBService
from app.services.async_cache import async_cached

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
@async_cached(ttl=30, key_prefix="agents")
async def get_agents_overview(
    cosmos: AsyncCosmosDBService = Depends(get_cosmos_service)
):
    """Get overview of agents with optimized async queries"""
    try:
        # Define containers to check
        containers_to_check = [
            'agent_logs', 'agent_session_logs', 'working_contexts', 
            'memory_contexts', 'journal_entries', 'agent_status'
        ]
        
        # Get agent names from recent activity (parallel queries)
        recent_ts = (datetime.utcnow() - timedelta(days=7)).timestamp()
        
        queries = []
        for container_name in containers_to_check:
            queries.append({
                'container': container_name,
                'query': """SELECT DISTINCT c.agent_name 
                           FROM c 
                           WHERE c.agent_name != null
                           AND c._ts > @recent_ts""",
                'parameters': [{"name": "@recent_ts", "value": recent_ts}],
                'max_items': 20
            })
        
        # Execute all queries concurrently
        results = await cosmos.batch_query(queries)
        
        # Collect unique agent names
        agent_names = set()
        for result_list in results:
            for result in result_list:
                name = result.get('agent_name')
                if name and name.strip():
                    agent_names.add(name.strip())
                    if len(agent_names) >= 10:
                        break
                        
        if not agent_names:
            return {
                'success': True,
                'agents': [{
                    'agent_name': 'No agents found in recent activity',
                    'current_activity': 'Check agent_logs, working_contexts containers',
                    'current_task': 'No recent agent activity detected',
                    'todos_count': 0,
                    'completed_tasks_count': 0,
                    'last_seen': None,
                    'recent_messages': [],
                    'status': 'unknown'
                }],
                'summary': {
                    'total_agents': 0,
                    'active_agents': 0,
                    'idle_agents': 0,
                    'offline_agents': 0,
                }
            }
        
        # Get detailed info for each agent (parallel queries)
        agent_detail_tasks = []
        for agent_name in list(agent_names)[:10]:
            agent_detail_tasks.append(
                get_agent_details_async(cosmos, agent_name)
            )
            
        agents_info = await asyncio.gather(*agent_detail_tasks)
        
        # Sort by last seen
        agents_info.sort(key=lambda x: x['last_seen'] or '1970-01-01', reverse=True)
        
        return {
            'success': True,
            'agents': agents_info,
            'summary': {
                'total_agents': len(agents_info),
                'active_agents': len([a for a in agents_info if a['status'] == 'active']),
                'idle_agents': len([a for a in agents_info if a['status'] == 'idle']),
                'offline_agents': len([a for a in agents_info if a['status'] == 'offline']),
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting agent overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_agent_details_async(
    cosmos: AsyncCosmosDBService, 
    agent_name: str
) -> Dict[str, Any]:
    """Get agent details with concurrent queries"""
    
    agent_info = {
        'agent_name': agent_name,
        'current_activity': 'No recent activity',
        'current_task': 'No active task',
        'todos_count': 0,
        'completed_tasks_count': 0,
        'last_seen': None,
        'recent_messages': [],
        'status': 'unknown'
    }
    
    # Prepare concurrent queries for this agent
    agent_queries = [
        {
            'name': 'logs',
            'container': 'agent_logs',
            'query': """SELECT TOP 5 * FROM c 
                       WHERE c.agent_name = @agent_name
                       ORDER BY c._ts DESC""",
            'parameters': [{"name": "@agent_name", "value": agent_name}],
            'max_items': 5
        },
        {
            'name': 'todos',
            'container': 'working_contexts',
            'query': """SELECT VALUE COUNT(1) FROM c 
                       WHERE c.agent_name = @agent_name
                       AND (c.status = 'pending' OR c.status = 'active' OR c.status IS NULL)""",
            'parameters': [{"name": "@agent_name", "value": agent_name}],
            'max_items': 1
        },
        {
            'name': 'completed',
            'container': 'agent_session_logs',
            'query': """SELECT VALUE COUNT(1) FROM c 
                       WHERE c.agent_name = @agent_name
                       AND (c.status = 'completed' OR c.status = 'success')""",
            'parameters': [{"name": "@agent_name", "value": agent_name}],
            'max_items': 1
        },
        {
            'name': 'journal',
            'container': 'journal_entries',
            'query': """SELECT TOP 3 c.entry, c._ts FROM c 
                       WHERE c.agent_name = @agent_name
                       ORDER BY c._ts DESC""",
            'parameters': [{"name": "@agent_name", "value": agent_name}],
            'max_items': 3
        }
    ]
    
    try:
        # Execute all queries concurrently
        query_list = [{k: v for k, v in q.items() if k != 'name'} for q in agent_queries]
        results = await cosmos.batch_query(query_list)
        
        # Process results
        logs, todos_result, completed_result, journal_entries = results
        
        # Process logs
        if logs:
            latest = logs[0]
            agent_info['last_seen'] = datetime.fromtimestamp(latest.get('_ts', 0)).isoformat()
            agent_info['current_activity'] = latest.get('action') or latest.get('message', 'Active')
            
            # Determine status
            if latest.get('_ts', 0) > (datetime.utcnow() - timedelta(hours=2)).timestamp():
                agent_info['status'] = 'active'
            elif latest.get('_ts', 0) > (datetime.utcnow() - timedelta(days=1)).timestamp():
                agent_info['status'] = 'idle'
            else:
                agent_info['status'] = 'offline'
        
        # Process todos count
        agent_info['todos_count'] = todos_result[0] if todos_result else 0
        
        # Process completed count
        agent_info['completed_tasks_count'] = completed_result[0] if completed_result else 0
        
        # Process journal entries
        for entry in journal_entries:
            content = entry.get('entry', '')
            agent_info['recent_messages'].append({
                'content': content[:100] + '...' if len(content) > 100 else content,
                'timestamp': datetime.fromtimestamp(entry.get('_ts', 0)).isoformat()
            })
            
    except Exception as e:
        logger.debug(f"Could not get details for {agent_name}: {e}")
    
    return agent_info


@router.get("/agent/{agent_name}/details")
@async_cached(ttl=60, key_prefix="agent_details")
async def get_agent_details(
    agent_name: str,
    cosmos: AsyncCosmosDBService = Depends(get_cosmos_service)
):
    """Get detailed information for a specific agent"""
    try:
        # Use the async helper function
        details = await get_agent_details_async(cosmos, agent_name)
        
        return {
            'success': True,
            'details': details
        }
        
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
@async_cached(ttl=30, key_prefix="agent_health")
async def get_agent_health(
    cosmos: AsyncCosmosDBService = Depends(get_cosmos_service)
):
    """Get simple agent health overview"""
    try:
        status_response = await get_agents_overview(cosmos=cosmos)
        
        if not status_response['success']:
            raise HTTPException(status_code=500, detail="Could not get agent status")
        
        summary = status_response['summary']
        
        health = {
            'system_status': 'healthy' if summary['active_agents'] > 0 else 'idle',
            'health_score': 100.0 if summary['active_agents'] > 0 else 50.0,
            'total_agents': summary['total_agents'],
            'active_agents': summary['active_agents'],
            'idle_agents': summary['idle_agents'],
            'offline_agents': summary['offline_agents'],
            'average_success_rate': 100.0,
            'last_updated': datetime.utcnow().isoformat(),
            'recommendations': [
                "Focus on concrete agent activities and tasks",
                "Monitor agent todos and completion rates", 
                "Review agent conversations for context"
            ]
        }
        
        return {
            'success': True,
            'health': health
        }
        
    except Exception as e:
        logger.error(f"Error getting agent health: {e}")
        raise HTTPException(status_code=500, detail=str(e))