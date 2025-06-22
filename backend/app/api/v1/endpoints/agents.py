"""Agent management API endpoints for FastAPI backend."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

# Import Cosmos DB dependency
from .cosmos import get_cosmos_db

# Import optimization utilities
try:
    from app.core.cosmos_optimization import optimize_query
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False
    
logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory cache for expensive operations
_agent_cache = {}
AGENT_CACHE_TTL = 30  # 30 seconds cache for agent data

@router.get("/status")
async def get_agents_overview(db=Depends(get_cosmos_db)):
    """Get overview of agents with their concrete information."""
    # Check cache first
    cache_key = "agents_status"
    now = time.time()
    
    if cache_key in _agent_cache:
        cached_data, cached_time = _agent_cache[cache_key]
        if now - cached_time < AGENT_CACHE_TTL:
            logger.info("Returning cached agents status")
            return cached_data
    
    try:
        database = db.client.get_database_client(db.database_name)
        
        agents_info = []
        
        # Real containers from your Cosmos DB
        containers_to_check = [
            'agent_logs', 'agent_session_logs', 'working_contexts', 
            'memory_contexts', 'journal_entries', 'agent_status'
        ]
        
        agent_names = set()
        
        # First, find all unique agent names from recent activity
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                query = """SELECT DISTINCT c.agent_name 
                          FROM c 
                          WHERE c.agent_name != null
                          AND c._ts > @recent_ts"""
                
                # Optimize query if possible
                if OPTIMIZATION_AVAILABLE:
                    query, partition_value = optimize_query(query, container_name)
                    
                recent_ts = (datetime.utcnow() - timedelta(days=7)).timestamp()
                parameters = [{"name": "@recent_ts", "value": recent_ts}]
                
                if OPTIMIZATION_AVAILABLE and partition_value:
                    parameters.append({"name": "@partitionKey", "value": partition_value})
                
                results = []
                async for item in container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                    max_item_count=50
                ):
                    results.append(item)
                
                for result in results:
                    name = result.get('agent_name')
                    if name and name.strip():
                        agent_names.add(name.strip())
                        if len(agent_names) >= 10:  # Limit to 10 agents for performance
                            break
                        
            except Exception as e:
                logger.debug(f"Could not query {container_name}: {e}")
                continue
        
        # If no agents found, return sample data
        if not agent_names:
            agents_info = [
                {
                    'agent_name': 'No agents found in recent activity',
                    'current_activity': 'Check agent_logs, working_contexts containers',
                    'current_task': 'No recent agent activity detected',
                    'todos_count': 0,
                    'completed_tasks_count': 0,
                    'last_seen': None,
                    'recent_messages': [],
                    'status': 'unknown'
                }
            ]
        else:
            # Get concrete info for each agent
            for agent_name in list(agent_names)[:10]:  # Limit to first 10
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
                
                # Get latest activity from agent_logs
                try:
                    container = database.get_container_client('agent_logs')
                    query = """SELECT TOP 5 * FROM c 
                              WHERE c.agent_name = @agent_name
                              ORDER BY c._ts DESC"""
                    
                    logs = []
                    async for item in container.query_items(
                        query=query,
                        parameters=[{"name": "@agent_name", "value": agent_name}],
                        enable_cross_partition_query=True
                    ):
                        logs.append(item)
                    
                    if logs:
                        latest = logs[0]
                        agent_info['last_seen'] = datetime.fromtimestamp(latest.get('_ts', 0)).isoformat()
                        agent_info['current_activity'] = latest.get('action') or latest.get('message', 'Active')
                        
                        # Determine if active (last 2 hours)
                        if latest.get('_ts', 0) > (datetime.utcnow() - timedelta(hours=2)).timestamp():
                            agent_info['status'] = 'active'
                        elif latest.get('_ts', 0) > (datetime.utcnow() - timedelta(days=1)).timestamp():
                            agent_info['status'] = 'idle'
                        else:
                            agent_info['status'] = 'offline'
                            
                except Exception as e:
                    logger.debug(f"Could not get agent logs for {agent_name}: {e}")
                
                # Get working contexts (todos) count
                try:
                    container = database.get_container_client('working_contexts')
                    query = """SELECT VALUE COUNT(1) FROM c 
                              WHERE c.agent_name = @agent_name
                              AND (c.status = 'pending' OR c.status = 'active' OR c.status IS NULL)"""
                    
                    todos_items = []
                    async for item in container.query_items(
                        query=query,
                        parameters=[{"name": "@agent_name", "value": agent_name}],
                        enable_cross_partition_query=True
                    ):
                        todos_items.append(item)
                    todos_count = todos_items
                    
                    agent_info['todos_count'] = todos_count[0] if todos_count else 0
                    
                    # Get current task from most recent working context
                    if agent_info['todos_count'] > 0:
                        task_query = """SELECT TOP 1 * FROM c 
                                       WHERE c.agent_name = @agent_name
                                       ORDER BY c._ts DESC"""
                        
                        tasks = []
                        async for item in container.query_items(
                            query=task_query,
                            parameters=[{"name": "@agent_name", "value": agent_name}],
                            enable_cross_partition_query=True
                        ):
                            tasks.append(item)
                        
                        if tasks:
                            agent_info['current_task'] = tasks[0].get('context', 'Working on task')
                        
                except Exception as e:
                    logger.debug(f"Could not get working contexts for {agent_name}: {e}")
                
                # Get completed tasks count from agent_session_logs
                try:
                    container = database.get_container_client('agent_session_logs')
                    query = """SELECT VALUE COUNT(1) FROM c 
                              WHERE c.agent_name = @agent_name
                              AND (c.status = 'completed' OR c.status = 'success')"""
                    
                    completed = list(container.query_items(
                        query=query,
                        parameters=[{"name": "@agent_name", "value": agent_name}],
                        enable_cross_partition_query=True
                    ))
                    
                    agent_info['completed_tasks_count'] = completed[0] if completed else 0
                    
                except Exception as e:
                    logger.debug(f"Could not get completed tasks for {agent_name}: {e}")
                
                # Get recent journal entries as messages
                try:
                    container = database.get_container_client('journal_entries')
                    query = """SELECT TOP 3 c.entry, c._ts FROM c 
                              WHERE c.agent_name = @agent_name
                              ORDER BY c._ts DESC"""
                    
                    entries = list(container.query_items(
                        query=query,
                        parameters=[{"name": "@agent_name", "value": agent_name}],
                        enable_cross_partition_query=True
                    ))
                    
                    for entry in entries:
                        content = entry.get('entry', '')
                        agent_info['recent_messages'].append({
                            'content': content[:100] + '...' if len(content) > 100 else content,
                            'timestamp': datetime.fromtimestamp(entry.get('_ts', 0)).isoformat()
                        })
                        
                except Exception as e:
                    logger.debug(f"Could not get journal entries for {agent_name}: {e}")
                
                agents_info.append(agent_info)
        
        # Sort by last seen (most recent first)
        agents_info.sort(key=lambda x: x['last_seen'] or '1970-01-01', reverse=True)
        
        result = {
            'success': True,
            'agents': agents_info,
            'summary': {
                'total_agents': len(agents_info),
                'active_agents': len([a for a in agents_info if a['status'] == 'active']),
                'idle_agents': len([a for a in agents_info if a['status'] == 'idle']),
                'offline_agents': len([a for a in agents_info if a['status'] == 'offline']),
            }
        }
        
        # Cache the result
        _agent_cache[cache_key] = (result, time.time())
        logger.info(f"Cached agents status for {len(agents_info)} agents")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting agent overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/{agent_name}/details")
async def get_agent_details(agent_name: str, db=Depends(get_cosmos_db)):
    """Get detailed concrete information for a specific agent."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        agent_details = {
            'agent_name': agent_name,
            'current_activity': [],
            'agenda': [],
            'todos': [],
            'completed_tasks': [],
            'conversations': [],
            'recent_actions': [],
            'journal_entries': [],
            'memory_contexts': [],
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # 1. Get current activity and recent actions from agent_logs
        try:
            container = database.get_container_client('agent_logs')
            query = """SELECT TOP 10 * FROM c 
                      WHERE c.agent_name = @agent_name
                      ORDER BY c._ts DESC"""
            
            logs = list(container.query_items(
                query=query,
                parameters=[{"name": "@agent_name", "value": agent_name}],
                enable_cross_partition_query=True
            ))
            
            for log in logs:
                action_info = {
                    'action': log.get('action') or log.get('message', 'Activity'),
                    'details': log.get('details') or log.get('context', ''),
                    'timestamp': datetime.fromtimestamp(log.get('_ts', 0)).isoformat(),
                    'status': log.get('status', 'info')
                }
                
                if len(agent_details['current_activity']) == 0:
                    agent_details['current_activity'].append(action_info)
                
                agent_details['recent_actions'].append(action_info)
                
        except Exception as e:
            logger.debug(f"Could not get agent logs: {e}")
        
        # 2. Get todos from working_contexts
        try:
            container = database.get_container_client('working_contexts')
            query = """SELECT * FROM c 
                      WHERE c.agent_name = @agent_name
                      ORDER BY c._ts DESC"""
            
            todos = list(container.query_items(
                query=query,
                parameters=[{"name": "@agent_name", "value": agent_name}],
                enable_cross_partition_query=True
            ))
            
            for todo in todos[:20]:
                agent_details['todos'].append({
                    'id': todo.get('id'),
                    'task': todo.get('context') or todo.get('task', 'Task'),
                    'status': todo.get('status', 'pending'),
                    'priority': todo.get('priority', 'normal'),
                    'created': datetime.fromtimestamp(todo.get('_ts', 0)).isoformat(),
                    'details': todo.get('details', '')
                })
                
        except Exception as e:
            logger.debug(f"Could not get working contexts: {e}")
        
        # 3. Get journal entries (agenda/plans)
        try:
            container = database.get_container_client('journal_entries')
            query = """SELECT * FROM c 
                      WHERE c.agent_name = @agent_name
                      ORDER BY c._ts DESC
                      OFFSET 0 LIMIT 15"""
            
            entries = list(container.query_items(
                query=query,
                parameters=[{"name": "@agent_name", "value": agent_name}],
                enable_cross_partition_query=True
            ))
            
            for entry in entries:
                journal_entry = {
                    'content': entry.get('entry', ''),
                    'type': entry.get('entry_type', 'journal'),
                    'timestamp': datetime.fromtimestamp(entry.get('_ts', 0)).isoformat(),
                    'session_id': entry.get('session_id', '')
                }
                
                agent_details['journal_entries'].append(journal_entry)
                
                # If entry contains planning keywords, add to agenda
                content = entry.get('entry', '').lower()
                if any(keyword in content for keyword in ['plan', 'agenda', 'next', 'will', 'goal', 'objective']):
                    agent_details['agenda'].append({
                        'content': entry.get('entry', ''),
                        'type': 'plan',
                        'timestamp': datetime.fromtimestamp(entry.get('_ts', 0)).isoformat()
                    })
                
        except Exception as e:
            logger.debug(f"Could not get journal entries: {e}")
        
        # 4. Get completed tasks from agent_session_logs
        try:
            container = database.get_container_client('agent_session_logs')
            query = """SELECT * FROM c 
                      WHERE c.agent_name = @agent_name
                      AND (c.status = 'completed' OR c.status = 'success')
                      ORDER BY c._ts DESC
                      OFFSET 0 LIMIT 20"""
            
            completed = list(container.query_items(
                query=query,
                parameters=[{"name": "@agent_name", "value": agent_name}],
                enable_cross_partition_query=True
            ))
            
            for task in completed:
                agent_details['completed_tasks'].append({
                    'task': task.get('action') or task.get('task', 'Completed task'),
                    'completed_at': datetime.fromtimestamp(task.get('_ts', 0)).isoformat(),
                    'duration': task.get('duration'),
                    'result': task.get('result') or task.get('outcome', 'Success'),
                    'session_id': task.get('session_id', '')
                })
                
        except Exception as e:
            logger.debug(f"Could not get session logs: {e}")
        
        # 5. Get memory contexts
        try:
            container = database.get_container_client('memory_contexts')
            query = """SELECT TOP 10 * FROM c 
                      WHERE c.agent_name = @agent_name
                      ORDER BY c._ts DESC"""
            
            memories = list(container.query_items(
                query=query,
                parameters=[{"name": "@agent_name", "value": agent_name}],
                enable_cross_partition_query=True
            ))
            
            for memory in memories:
                agent_details['memory_contexts'].append({
                    'id': memory.get('id'),
                    'context_type': memory.get('context_type', 'memory'),
                    'content': memory.get('context', ''),
                    'timestamp': datetime.fromtimestamp(memory.get('_ts', 0)).isoformat(),
                    'importance': memory.get('importance', 'normal')
                })
                
        except Exception as e:
            logger.debug(f"Could not get memory contexts: {e}")
        
        # 6. Get system inbox conversations
        try:
            container = database.get_container_client('system_inbox')
            query = """SELECT TOP 5 * FROM c 
                      WHERE c.to = @agent_name OR c.from = @agent_name
                      ORDER BY c._ts DESC"""
            
            conversations = list(container.query_items(
                query=query,
                parameters=[{"name": "@agent_name", "value": agent_name}],
                enable_cross_partition_query=True
            ))
            
            for conv in conversations:
                agent_details['conversations'].append({
                    'id': conv.get('id'),
                    'topic': conv.get('subject', 'Conversation'),
                    'last_message': conv.get('message', ''),
                    'timestamp': datetime.fromtimestamp(conv.get('_ts', 0)).isoformat(),
                    'from': conv.get('from', ''),
                    'to': conv.get('to', '')
                })
                
        except Exception as e:
            logger.debug(f"Could not get system inbox: {e}")
        
        return {
            'success': True,
            'details': agent_details
        }
        
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_agent_health(db=Depends(get_cosmos_db)):
    """Get simple agent health overview."""
    try:
        status_response = await get_agents_overview(db=db)
        
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