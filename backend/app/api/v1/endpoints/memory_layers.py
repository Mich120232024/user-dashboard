"""Memory layers API endpoints matching Flask dashboard functionality."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

# Import Cosmos DB dependency
from .cosmos import get_cosmos_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/layers")
async def get_memory_layers(db=Depends(get_cosmos_db)):
    """Get memory layers matching Flask /api/memory/layers."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Memory layer structure from Flask dashboard
        layers = {
            'layer_1': {
                'name': 'Constitutional Identity',
                'description': 'Immutable core identity and principles',
                'container': 'identity_cards',
                'status': 'active',
                'item_count': 0,
                'last_updated': None,
                'items': []
            },
            'layer_2': {
                'name': 'Compliance Dynamics',
                'description': 'Dynamic compliance and governance rules',
                'container': 'processes',
                'status': 'active',
                'item_count': 0,
                'last_updated': None,
                'items': []
            },
            'layer_3': {
                'name': 'Operational Context',
                'description': 'Current operational context and working memory',
                'container': 'memory_contexts',
                'status': 'active',
                'item_count': 0,
                'last_updated': None,
                'items': []
            },
            'layer_4': {
                'name': 'Log Analysis',
                'description': 'Historical logs and performance analysis',
                'container': 'logs',
                'status': 'active',
                'item_count': 0,
                'last_updated': None,
                'items': []
            }
        }
        
        # Populate each layer with actual data
        for layer_key, layer_info in layers.items():
            container_name = layer_info['container']
            try:
                container = database.get_container_client(container_name)
                
                # Get count
                count_query = "SELECT VALUE COUNT(1) FROM c"
                count_result = list(container.query_items(
                    query=count_query,
                    enable_cross_partition_query=True
                ))
                layer_info['item_count'] = count_result[0] if count_result else 0
                
                # Get recent items
                items_query = "SELECT TOP 10 * FROM c ORDER BY c._ts DESC"
                items = list(container.query_items(
                    query=items_query,
                    enable_cross_partition_query=True
                ))
                
                layer_info['items'] = []
                for item in items:
                    layer_info['items'].append({
                        'id': item.get('id'),
                        'content': str(item.get('content', item.get('context', item.get('message', 'No content'))))[:200] + '...',
                        'timestamp': datetime.fromtimestamp(item.get('_ts', 0)).isoformat(),
                        'agent_name': item.get('agent_name'),
                        'type': item.get('type', 'unknown')
                    })
                
                # Set last updated
                if items:
                    layer_info['last_updated'] = datetime.fromtimestamp(items[0].get('_ts', 0)).isoformat()
                
            except Exception as e:
                logger.debug(f"Could not query {container_name} for {layer_key}: {e}")
                layer_info['status'] = 'error'
                layer_info['error'] = str(e)
        
        # Calculate overall memory system health
        active_layers = len([l for l in layers.values() if l['status'] == 'active'])
        total_items = sum(l['item_count'] for l in layers.values())
        
        return {
            'success': True,
            'layers': layers,
            'summary': {
                'total_layers': len(layers),
                'active_layers': active_layers,
                'total_items': total_items,
                'system_status': 'healthy' if active_layers == len(layers) else 'degraded'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting memory layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/layer/{layer_id}")
async def get_memory_layer_details(layer_id: str, db=Depends(get_cosmos_db)):
    """Get detailed information for a specific memory layer."""
    try:
        # Map layer IDs to containers
        layer_mapping = {
            'layer_1': 'identity_cards',
            'layer_2': 'processes', 
            'layer_3': 'memory_contexts',
            'layer_4': 'logs'
        }
        
        if layer_id not in layer_mapping:
            raise HTTPException(status_code=404, detail="Layer not found")
        
        database = db.client.get_database_client(db.database_name)
        container_name = layer_mapping[layer_id]
        
        try:
            container = database.get_container_client(container_name)
            
            # Get all items with pagination
            query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 50"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Process items for display
            processed_items = []
            for item in items:
                processed_items.append({
                    'id': item.get('id'),
                    'content': item.get('content') or item.get('context') or item.get('message', 'No content'),
                    'timestamp': datetime.fromtimestamp(item.get('_ts', 0)).isoformat(),
                    'agent_name': item.get('agent_name'),
                    'type': item.get('type', 'unknown'),
                    'raw_data': item  # Include full item for debugging
                })
            
            return {
                'success': True,
                'layer_id': layer_id,
                'container': container_name,
                'items': processed_items,
                'total_count': len(processed_items),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error querying container {container_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Error accessing layer data: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory layer details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/layer/{layer_id}/add")
async def add_memory_item(layer_id: str, item_data: dict, db=Depends(get_cosmos_db)):
    """Add item to memory layer."""
    try:
        layer_mapping = {
            'layer_1': 'identity_cards',
            'layer_2': 'processes',
            'layer_3': 'memory_contexts', 
            'layer_4': 'logs'
        }
        
        if layer_id not in layer_mapping:
            raise HTTPException(status_code=404, detail="Layer not found")
        
        database = db.client.get_database_client(db.database_name)
        container_name = layer_mapping[layer_id]
        container = database.get_container_client(container_name)
        
        # Prepare item with timestamp
        new_item = {
            'id': f"{layer_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.utcnow().isoformat(),
            '_ts': datetime.utcnow().timestamp(),
            **item_data
        }
        
        # Insert item
        result = container.create_item(new_item)
        
        return {
            'success': True,
            'layer_id': layer_id,
            'item_id': result['id'],
            'message': f"Item added to {layer_id}"
        }
        
    except Exception as e:
        logger.error(f"Error adding memory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))