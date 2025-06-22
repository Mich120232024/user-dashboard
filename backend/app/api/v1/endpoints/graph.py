"""Graph explorer API endpoints for FastAPI backend."""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

# Import Cosmos DB dependency
from .cosmos import get_cosmos_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any]
    size: Optional[float] = 1.0
    color: Optional[str] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    type: str
    properties: Dict[str, Any]
    weight: Optional[float] = 1.0

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any]

class GraphQuery(BaseModel):
    node_types: Optional[List[str]] = None
    edge_types: Optional[List[str]] = None
    search_term: Optional[str] = None
    max_depth: int = 3
    max_nodes: int = 100

@router.get("/nodes")
async def get_graph_nodes(
    node_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_cosmos_db)
):
    """Get graph nodes from the database."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        nodes = []
        containers_to_check = [
            'agent_session_logs', 'system_inbox', 'identity_cards',
            'working_contexts', 'journal_entries', 'memory_contexts'
        ]
        
        node_colors = {
            'agent': '#3b82f6',      # Blue
            'session': '#10b981',    # Green
            'message': '#f59e0b',    # Amber
            'context': '#8b5cf6',    # Purple
            'memory': '#ef4444',     # Red
            'document': '#6b7280'    # Gray
        }
        
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                
                # Build query
                query_parts = ["SELECT * FROM c"]
                parameters = []
                conditions = []
                
                if search:
                    search_conditions = [
                        "CONTAINS(LOWER(c.id), LOWER(@search))",
                        "CONTAINS(LOWER(c.subject), LOWER(@search))",
                        "CONTAINS(LOWER(c.content), LOWER(@search))",
                        "CONTAINS(LOWER(c.agentName), LOWER(@search))",
                        "CONTAINS(LOWER(c.agent_name), LOWER(@search))"
                    ]
                    conditions.append(f"({' OR '.join(search_conditions)})")
                    parameters.append({"name": "@search", "value": search})
                
                if conditions:
                    query_parts.append("WHERE " + " AND ".join(conditions))
                
                query_parts.append("ORDER BY c._ts DESC")
                query_parts.append(f"OFFSET 0 LIMIT {limit // len(containers_to_check) + 10}")
                
                query = " ".join(query_parts)
                
                docs = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                # Convert documents to graph nodes
                for doc in docs:
                    node_id = doc.get('id', doc.get('_rid', ''))
                    if not node_id:
                        continue
                    
                    # Determine node type based on container and content
                    if container_name == 'agent_session_logs':
                        if doc.get('agentName') or doc.get('agent_name'):
                            node_type_detected = 'agent'
                        else:
                            node_type_detected = 'session'
                    elif container_name == 'system_inbox':
                        node_type_detected = 'message'
                    elif 'context' in container_name:
                        node_type_detected = 'context'
                    elif 'memory' in container_name:
                        node_type_detected = 'memory'
                    else:
                        node_type_detected = 'document'
                    
                    # Skip if filtering by type
                    if node_type and node_type != node_type_detected:
                        continue
                    
                    # Create node label
                    label = doc.get('subject') or doc.get('name') or doc.get('agentName') or doc.get('agent_name') or node_id[:20]
                    
                    # Calculate node size based on content or connections
                    size = 1.0
                    if doc.get('content'):
                        size = min(5.0, len(str(doc['content'])) / 1000 + 1)
                    
                    # Extract relevant properties
                    properties = {}
                    for key in ['agentName', 'agent_name', 'sessionId', 'session_id', 'subject', 'from', 'to', 'timestamp', '_ts']:
                        if key in doc:
                            properties[key] = doc[key]
                    
                    # Add creation time
                    if doc.get('_ts'):
                        properties['created'] = datetime.fromtimestamp(doc['_ts']).isoformat()
                    
                    nodes.append(GraphNode(
                        id=node_id,
                        label=label,
                        type=node_type_detected,
                        properties=properties,
                        size=size,
                        color=node_colors.get(node_type_detected, '#6b7280')
                    ))
                
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        # Remove duplicates and limit
        unique_nodes = {}
        for node in nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
        
        final_nodes = list(unique_nodes.values())[:limit]
        
        return {
            'success': True,
            'nodes': [node.dict() for node in final_nodes],
            'count': len(final_nodes),
            'node_types': list(set(node.type for node in final_nodes))
        }
        
    except Exception as e:
        logger.error(f"Error getting graph nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/edges")
async def get_graph_edges(
    source_id: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    edge_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_cosmos_db)
):
    """Get graph edges (relationships) from the database."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        edges = []
        edge_id_counter = 0
        
        # Get all documents to find relationships
        containers_to_check = [
            'agent_session_logs', 'system_inbox', 'identity_cards',
            'working_contexts', 'journal_entries', 'memory_contexts'
        ]
        
        all_docs = {}
        
        # First pass: collect all documents
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                
                query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 200"
                docs = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                for doc in docs:
                    doc_id = doc.get('id', doc.get('_rid', ''))
                    if doc_id:
                        all_docs[doc_id] = doc
                
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        # Second pass: find relationships
        for doc_id, doc in all_docs.items():
            # Filter by source if specified
            if source_id and doc_id != source_id:
                continue
            
            # Agent to Session relationships
            session_id = doc.get('sessionId') or doc.get('session_id')
            agent_name = doc.get('agentName') or doc.get('agent_name')
            
            if session_id and agent_name:
                # Create agent-session edge
                edge_id = f"edge_{edge_id_counter}"
                edge_id_counter += 1
                
                if not edge_type or edge_type == 'participates':
                    edges.append(GraphEdge(
                        id=edge_id,
                        source=agent_name,
                        target=session_id,
                        label="participates in",
                        type="participates",
                        properties={"created": doc.get('_ts', 0)},
                        weight=1.0
                    ))
            
            # Message relationships (from/to)
            from_field = doc.get('from')
            to_field = doc.get('to')
            
            if from_field and to_field:
                edge_id = f"edge_{edge_id_counter}"
                edge_id_counter += 1
                
                if not edge_type or edge_type == 'sends_to':
                    edges.append(GraphEdge(
                        id=edge_id,
                        source=from_field,
                        target=to_field,
                        label="sends message to",
                        type="sends_to",
                        properties={
                            "message_id": doc_id,
                            "subject": doc.get('subject', ''),
                            "created": doc.get('_ts', 0)
                        },
                        weight=1.0
                    ))
            
            # Context relationships (agent to context)
            if agent_name and 'context' in str(doc).lower():
                edge_id = f"edge_{edge_id_counter}"
                edge_id_counter += 1
                
                if not edge_type or edge_type == 'has_context':
                    edges.append(GraphEdge(
                        id=edge_id,
                        source=agent_name,
                        target=doc_id,
                        label="has context",
                        type="has_context",
                        properties={"created": doc.get('_ts', 0)},
                        weight=1.0
                    ))
            
            # Memory relationships
            if agent_name and 'memory' in str(doc).lower():
                edge_id = f"edge_{edge_id_counter}"
                edge_id_counter += 1
                
                if not edge_type or edge_type == 'remembers':
                    edges.append(GraphEdge(
                        id=edge_id,
                        source=agent_name,
                        target=doc_id,
                        label="remembers",
                        type="remembers",
                        properties={"created": doc.get('_ts', 0)},
                        weight=1.0
                    ))
        
        # Filter by target if specified
        if target_id:
            edges = [edge for edge in edges if edge.target == target_id]
        
        # Remove duplicates and limit
        unique_edges = {}
        for edge in edges:
            edge_key = f"{edge.source}-{edge.target}-{edge.type}"
            if edge_key not in unique_edges:
                unique_edges[edge_key] = edge
        
        final_edges = list(unique_edges.values())[:limit]
        
        return {
            'success': True,
            'edges': [edge.dict() for edge in final_edges],
            'count': len(final_edges),
            'edge_types': list(set(edge.type for edge in final_edges))
        }
        
    except Exception as e:
        logger.error(f"Error getting graph edges: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph")
async def get_full_graph(
    max_nodes: int = Query(50, ge=10, le=200),
    max_depth: int = Query(2, ge=1, le=5),
    center_node: Optional[str] = Query(None),
    db=Depends(get_cosmos_db)
):
    """Get a complete graph with nodes and edges."""
    try:
        # Get nodes
        nodes_response = await get_graph_nodes(limit=max_nodes, db=db)
        if not nodes_response['success']:
            raise HTTPException(status_code=500, detail="Failed to get nodes")
        
        # Get edges
        edges_response = await get_graph_edges(limit=max_nodes * 2, db=db)
        if not edges_response['success']:
            raise HTTPException(status_code=500, detail="Failed to get edges")
        
        nodes = [GraphNode(**node) for node in nodes_response['nodes']]
        edges = [GraphEdge(**edge) for edge in edges_response['edges']]
        
        # If center_node specified, filter to only connected nodes
        if center_node:
            connected_nodes = set([center_node])
            
            # BFS to find connected nodes within max_depth
            queue = deque([(center_node, 0)])
            
            while queue:
                current_node, depth = queue.popleft()
                
                if depth >= max_depth:
                    continue
                
                # Find connected nodes
                for edge in edges:
                    if edge.source == current_node and edge.target not in connected_nodes:
                        connected_nodes.add(edge.target)
                        queue.append((edge.target, depth + 1))
                    elif edge.target == current_node and edge.source not in connected_nodes:
                        connected_nodes.add(edge.source)
                        queue.append((edge.source, depth + 1))
            
            # Filter nodes and edges
            nodes = [node for node in nodes if node.id in connected_nodes]
            edges = [edge for edge in edges if edge.source in connected_nodes and edge.target in connected_nodes]
        
        # Calculate graph statistics
        node_types = defaultdict(int)
        edge_types = defaultdict(int)
        
        for node in nodes:
            node_types[node.type] += 1
        
        for edge in edges:
            edge_types[edge.type] += 1
        
        # Calculate centrality (simplified - just connection count)
        node_connections = defaultdict(int)
        for edge in edges:
            node_connections[edge.source] += 1
            node_connections[edge.target] += 1
        
        # Update node sizes based on connections
        for node in nodes:
            connections = node_connections.get(node.id, 0)
            node.size = max(1.0, min(10.0, connections / 2 + 1))
        
        metadata = {
            'node_count': len(nodes),
            'edge_count': len(edges),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'center_node': center_node,
            'max_depth': max_depth,
            'generated_at': datetime.utcnow().isoformat(),
            'most_connected_nodes': sorted(
                [(node_id, count) for node_id, count in node_connections.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        graph_data = GraphData(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )
        
        return {
            'success': True,
            'graph': graph_data.dict()
        }
        
    except Exception as e:
        logger.error(f"Error getting full graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_graph(
    q: str = Query(..., min_length=1),
    max_results: int = Query(20, ge=1, le=100),
    db=Depends(get_cosmos_db)
):
    """Search for nodes in the graph."""
    try:
        # Get nodes with search filter
        nodes_response = await get_graph_nodes(search=q, limit=max_results, db=db)
        
        if not nodes_response['success']:
            raise HTTPException(status_code=500, detail="Failed to search nodes")
        
        nodes = nodes_response['nodes']
        
        # For each found node, get its immediate connections
        connected_edges = []
        node_ids = [node['id'] for node in nodes]
        
        for node_id in node_ids:
            # Get edges for this node (limit to avoid too many results)
            edges_response = await get_graph_edges(source_id=node_id, limit=10, db=db)
            if edges_response['success']:
                connected_edges.extend(edges_response['edges'])
            
            # Also get edges where this node is the target
            edges_response = await get_graph_edges(target_id=node_id, limit=10, db=db)
            if edges_response['success']:
                connected_edges.extend(edges_response['edges'])
        
        # Remove duplicate edges
        unique_edges = {}
        for edge in connected_edges:
            edge_key = f"{edge['source']}-{edge['target']}-{edge['type']}"
            if edge_key not in unique_edges:
                unique_edges[edge_key] = edge
        
        # Get connected nodes that aren't in the search results
        connected_node_ids = set()
        for edge in unique_edges.values():
            connected_node_ids.add(edge['source'])
            connected_node_ids.add(edge['target'])
        
        # Remove nodes already in search results
        search_node_ids = set(node_ids)
        new_node_ids = connected_node_ids - search_node_ids
        
        # Get data for connected nodes (limit to avoid too many results)
        additional_nodes = []
        if new_node_ids:
            # This is simplified - in a real implementation, you'd query for these specific nodes
            all_nodes_response = await get_graph_nodes(limit=100, db=db)
            if all_nodes_response['success']:
                additional_nodes = [
                    node for node in all_nodes_response['nodes']
                    if node['id'] in new_node_ids
                ][:20]  # Limit additional nodes
        
        return {
            'success': True,
            'search_term': q,
            'nodes': nodes + additional_nodes,
            'edges': list(unique_edges.values()),
            'counts': {
                'search_results': len(nodes),
                'connected_nodes': len(additional_nodes),
                'total_nodes': len(nodes) + len(additional_nodes),
                'edges': len(unique_edges)
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_graph_stats(db=Depends(get_cosmos_db)):
    """Get graph statistics and metrics."""
    try:
        # Get basic counts
        nodes_response = await get_graph_nodes(limit=1000, db=db)
        edges_response = await get_graph_edges(limit=2000, db=db)
        
        if not nodes_response['success'] or not edges_response['success']:
            raise HTTPException(status_code=500, detail="Failed to get graph data")
        
        nodes = nodes_response['nodes']
        edges = edges_response['edges']
        
        # Calculate statistics
        node_types = defaultdict(int)
        edge_types = defaultdict(int)
        node_connections = defaultdict(int)
        
        for node in nodes:
            node_types[node['type']] += 1
        
        for edge in edges:
            edge_types[edge['type']] += 1
            node_connections[edge['source']] += 1
            node_connections[edge['target']] += 1
        
        # Find most connected nodes
        most_connected = sorted(
            node_connections.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Calculate density (edges / possible edges)
        n = len(nodes)
        max_possible_edges = n * (n - 1) / 2 if n > 1 else 0
        density = len(edges) / max_possible_edges if max_possible_edges > 0 else 0
        
        # Find isolated nodes (no connections)
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge['source'])
            connected_nodes.add(edge['target'])
        
        isolated_nodes = [node['id'] for node in nodes if node['id'] not in connected_nodes]
        
        stats = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'density': round(density, 4),
            'average_connections': round(sum(node_connections.values()) / len(nodes), 2) if nodes else 0,
            'most_connected_nodes': most_connected,
            'isolated_nodes_count': len(isolated_nodes),
            'isolated_nodes': isolated_nodes[:10],  # Show first 10
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))