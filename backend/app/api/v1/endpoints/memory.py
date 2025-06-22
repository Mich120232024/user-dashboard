"""Memory layers API endpoints for FastAPI backend."""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

# Import Cosmos DB dependency
from .cosmos import get_cosmos_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class MemoryLayer(BaseModel):
    id: str
    name: str
    type: str
    description: str
    agent_name: Optional[str] = None
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    size_bytes: int
    version: int

class MemoryQuery(BaseModel):
    layer_type: Optional[str] = None
    agent_name: Optional[str] = None
    search_term: Optional[str] = None
    limit: int = 50

class MemoryCreateRequest(BaseModel):
    name: str
    type: str
    description: str
    agent_name: Optional[str] = None
    data: Dict[str, Any]

# Memory layer types
MEMORY_LAYER_TYPES = {
    'constitutional': 'Constitutional Identity',
    'compliance': 'Compliance Dynamics', 
    'operational': 'Operational Context',
    'analysis': 'Log Analysis'
}

@router.get("/layers")
async def get_memory_layers(
    layer_type: Optional[str] = Query(None),
    agent_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    db=Depends(get_cosmos_db)
):
    """Get memory layers with optional filtering."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Try to get memory layers from multiple possible containers
        containers_to_check = ['memory_contexts', 'memory_layers', 'agent_memory', 'working_contexts']
        
        all_layers = []
        
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                
                # Build query based on filters
                query_parts = ["SELECT * FROM c"]
                parameters = []
                conditions = []
                
                if layer_type:
                    conditions.append("c.type = @type")
                    parameters.append({"name": "@type", "value": layer_type})
                
                if agent_name:
                    conditions.append("c.agent_name = @agent_name")
                    parameters.append({"name": "@agent_name", "value": agent_name})
                
                if conditions:
                    query_parts.append("WHERE " + " AND ".join(conditions))
                
                query_parts.append("ORDER BY c._ts DESC")
                query_parts.append(f"OFFSET 0 LIMIT {limit}")
                
                query = " ".join(query_parts)
                
                layers = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                # Add container source to each layer
                for layer in layers:
                    layer['_container'] = container_name
                    
                all_layers.extend(layers)
                
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        # Remove duplicates and sort by timestamp
        unique_layers = {}
        for layer in all_layers:
            layer_id = layer.get('id', layer.get('_rid'))
            if layer_id not in unique_layers:
                unique_layers[layer_id] = layer
        
        sorted_layers = sorted(unique_layers.values(), key=lambda x: x.get('_ts', 0), reverse=True)
        
        return {
            'success': True,
            'layers': sorted_layers[:limit],
            'count': len(sorted_layers),
            'layer_types': MEMORY_LAYER_TYPES,
            'filters': {
                'layer_type': layer_type,
                'agent_name': agent_name,
                'limit': limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting memory layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/layers/{layer_id}")
async def get_memory_layer(layer_id: str, db=Depends(get_cosmos_db)):
    """Get a specific memory layer by ID."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Search across all possible memory containers
        containers_to_check = ['memory_contexts', 'memory_layers', 'agent_memory', 'working_contexts']
        
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                
                query = "SELECT * FROM c WHERE c.id = @id"
                parameters = [{"name": "@id", "value": layer_id}]
                
                layers = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if layers:
                    layer = layers[0]
                    layer['_container'] = container_name
                    
                    return {
                        'success': True,
                        'layer': layer
                    }
                    
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        raise HTTPException(status_code=404, detail=f"Memory layer {layer_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory layer {layer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/layers")
async def create_memory_layer(request: MemoryCreateRequest, db=Depends(get_cosmos_db)):
    """Create a new memory layer."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Use memory_contexts container by default
        container_name = 'memory_contexts'
        try:
            container = database.get_container_client(container_name)
        except:
            # Try to create the container if it doesn't exist
            try:
                database.create_container_if_not_exists(
                    id=container_name,
                    partition_key={'paths': ['/agent_name'], 'kind': 'Hash'}
                )
                container = database.get_container_client(container_name)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Cannot access or create memory container: {e}")
        
        # Create memory layer document
        timestamp = datetime.utcnow()
        layer_id = f"memory_{request.type}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Calculate data size
        data_json = json.dumps(request.data)
        size_bytes = len(data_json.encode('utf-8'))
        
        layer_doc = {
            'id': layer_id,
            'name': request.name,
            'type': request.type,
            'description': request.description,
            'agent_name': request.agent_name or 'system',
            'data': request.data,
            'created_at': timestamp.isoformat() + 'Z',
            'updated_at': timestamp.isoformat() + 'Z',
            'size_bytes': size_bytes,
            'version': 1,
            'memory_layer_type': MEMORY_LAYER_TYPES.get(request.type, 'Unknown'),
            'partitionKey': request.agent_name or 'system'
        }
        
        result = container.create_item(layer_doc)
        
        return {
            'success': True,
            'message': 'Memory layer created successfully',
            'layer_id': result['id'],
            'container': container_name
        }
        
    except Exception as e:
        logger.error(f"Error creating memory layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/layers/{layer_id}")
async def update_memory_layer(layer_id: str, request: MemoryCreateRequest, db=Depends(get_cosmos_db)):
    """Update an existing memory layer."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Find the layer first
        containers_to_check = ['memory_contexts', 'memory_layers', 'agent_memory', 'working_contexts']
        layer = None
        container = None
        
        for container_name in containers_to_check:
            try:
                test_container = database.get_container_client(container_name)
                
                query = "SELECT * FROM c WHERE c.id = @id"
                parameters = [{"name": "@id", "value": layer_id}]
                
                layers = list(test_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if layers:
                    layer = layers[0]
                    container = test_container
                    break
                    
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        if not layer or not container:
            raise HTTPException(status_code=404, detail=f"Memory layer {layer_id} not found")
        
        # Update the layer
        timestamp = datetime.utcnow()
        data_json = json.dumps(request.data)
        size_bytes = len(data_json.encode('utf-8'))
        
        layer.update({
            'name': request.name,
            'type': request.type,
            'description': request.description,
            'agent_name': request.agent_name or layer.get('agent_name', 'system'),
            'data': request.data,
            'updated_at': timestamp.isoformat() + 'Z',
            'size_bytes': size_bytes,
            'version': layer.get('version', 1) + 1,
            'memory_layer_type': MEMORY_LAYER_TYPES.get(request.type, 'Unknown')
        })
        
        result = container.upsert_item(layer)
        
        return {
            'success': True,
            'message': 'Memory layer updated successfully',
            'layer_id': result['id'],
            'version': result['version']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory layer {layer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/layers/{layer_id}")
async def delete_memory_layer(layer_id: str, db=Depends(get_cosmos_db)):
    """Delete a memory layer."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Find the layer first
        containers_to_check = ['memory_contexts', 'memory_layers', 'agent_memory', 'working_contexts']
        layer = None
        container = None
        
        for container_name in containers_to_check:
            try:
                test_container = database.get_container_client(container_name)
                
                query = "SELECT * FROM c WHERE c.id = @id"
                parameters = [{"name": "@id", "value": layer_id}]
                
                layers = list(test_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if layers:
                    layer = layers[0]
                    container = test_container
                    break
                    
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        if not layer or not container:
            raise HTTPException(status_code=404, detail=f"Memory layer {layer_id} not found")
        
        # Delete the layer
        partition_key = layer.get('partitionKey', layer.get('agent_name', 'system'))
        container.delete_item(item=layer_id, partition_key=partition_key)
        
        return {
            'success': True,
            'message': f'Memory layer {layer_id} deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory layer {layer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_memory_stats(db=Depends(get_cosmos_db)):
    """Get memory layer statistics."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        stats = {
            'total_layers': 0,
            'layers_by_type': {},
            'layers_by_agent': {},
            'total_size_bytes': 0,
            'containers': {}
        }
        
        containers_to_check = ['memory_contexts', 'memory_layers', 'agent_memory', 'working_contexts']
        
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                
                # Get all layers from this container
                query = "SELECT * FROM c"
                layers = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                container_stats = {
                    'count': len(layers),
                    'size_bytes': 0,
                    'types': {},
                    'agents': {}
                }
                
                for layer in layers:
                    # Update totals
                    stats['total_layers'] += 1
                    
                    # Size
                    size = layer.get('size_bytes', 0)
                    stats['total_size_bytes'] += size
                    container_stats['size_bytes'] += size
                    
                    # Type stats
                    layer_type = layer.get('type', 'unknown')
                    stats['layers_by_type'][layer_type] = stats['layers_by_type'].get(layer_type, 0) + 1
                    container_stats['types'][layer_type] = container_stats['types'].get(layer_type, 0) + 1
                    
                    # Agent stats
                    agent = layer.get('agent_name', 'unknown')
                    stats['layers_by_agent'][agent] = stats['layers_by_agent'].get(agent, 0) + 1
                    container_stats['agents'][agent] = container_stats['agents'].get(agent, 0) + 1
                
                stats['containers'][container_name] = container_stats
                
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                stats['containers'][container_name] = {
                    'count': 0,
                    'size_bytes': 0,
                    'types': {},
                    'agents': {},
                    'error': str(e)
                }
        
        return {
            'success': True,
            'stats': stats,
            'layer_types_available': MEMORY_LAYER_TYPES
        }
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_memory_layers(query: MemoryQuery, db=Depends(get_cosmos_db)):
    """Search memory layers by content."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        results = []
        containers_to_check = ['memory_contexts', 'memory_layers', 'agent_memory', 'working_contexts']
        
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                
                # Build search query
                query_parts = ["SELECT * FROM c"]
                parameters = []
                conditions = []
                
                if query.layer_type:
                    conditions.append("c.type = @type")
                    parameters.append({"name": "@type", "value": query.layer_type})
                
                if query.agent_name:
                    conditions.append("c.agent_name = @agent_name")
                    parameters.append({"name": "@agent_name", "value": query.agent_name})
                
                if query.search_term:
                    search_conditions = [
                        "CONTAINS(LOWER(c.name), LOWER(@search))",
                        "CONTAINS(LOWER(c.description), LOWER(@search))",
                        "CONTAINS(LOWER(c.data), LOWER(@search))"
                    ]
                    conditions.append(f"({' OR '.join(search_conditions)})")
                    parameters.append({"name": "@search", "value": query.search_term})
                
                if conditions:
                    query_parts.append("WHERE " + " AND ".join(conditions))
                
                query_parts.append("ORDER BY c._ts DESC")
                query_parts.append(f"OFFSET 0 LIMIT {query.limit}")
                
                search_query = " ".join(query_parts)
                
                layers = list(container.query_items(
                    query=search_query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                # Add search context
                for layer in layers:
                    layer['_container'] = container_name
                    if query.search_term:
                        # Add search highlights (simplified)
                        layer['_search_highlights'] = []
                        search_lower = query.search_term.lower()
                        
                        if search_lower in layer.get('name', '').lower():
                            layer['_search_highlights'].append({'field': 'name', 'value': layer['name']})
                        if search_lower in layer.get('description', '').lower():
                            layer['_search_highlights'].append({'field': 'description', 'value': layer['description']})
                
                results.extend(layers)
                
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        # Remove duplicates and sort
        unique_results = {}
        for result in results:
            result_id = result.get('id', result.get('_rid'))
            if result_id not in unique_results:
                unique_results[result_id] = result
        
        final_results = sorted(unique_results.values(), key=lambda x: x.get('_ts', 0), reverse=True)
        
        return {
            'success': True,
            'results': final_results[:query.limit],
            'count': len(final_results),
            'query': query.dict(),
            'containers_searched': len([c for c in containers_to_check if c in [r.get('_container') for r in results]])
        }
        
    except Exception as e:
        logger.error(f"Error searching memory layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/architecture")
async def get_memory_architecture():
    """Get the memory architecture overview."""
    return {
        'success': True,
        'architecture': {
            'layers': [
                {
                    'id': 'constitutional',
                    'name': 'Constitutional Identity',
                    'description': 'Who I am (immutable)',
                    'characteristics': ['Core identity', 'Immutable principles', 'Base behavior patterns'],
                    'managed_by': 'System',
                    'update_frequency': 'Never'
                },
                {
                    'id': 'compliance',
                    'name': 'Compliance Dynamics',
                    'description': 'Current rules (COMPLIANCE_MANAGER controlled)',
                    'characteristics': ['Active governance rules', 'Security policies', 'Operational constraints'],
                    'managed_by': 'COMPLIANCE_MANAGER',
                    'update_frequency': 'As needed'
                },
                {
                    'id': 'operational',
                    'name': 'Operational Context',
                    'description': 'Active work (self-managed)',
                    'characteristics': ['Current projects', 'Task context', 'Working memory'],
                    'managed_by': 'Agent',
                    'update_frequency': 'Continuously'
                },
                {
                    'id': 'analysis',
                    'name': 'Log Analysis',
                    'description': 'Performance insights (auto-generated)',
                    'characteristics': ['Performance metrics', 'Error patterns', 'Optimization insights'],
                    'managed_by': 'System',
                    'update_frequency': 'Periodic'
                }
            ],
            'data_flow': [
                'Constitutional Identity → Base behavior',
                'Compliance Dynamics → Rule enforcement',
                'Operational Context → Task execution',
                'Log Analysis → Performance feedback'
            ],
            'integration_points': [
                'Cosmos DB containers for persistence',
                'Azure Blob Storage for large contexts',
                'Real-time updates during agent execution',
                'Cross-session context preservation'
            ]
        }
    }