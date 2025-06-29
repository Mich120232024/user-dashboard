"""API Catalog endpoints for exploring Cosmos DB data collections."""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from app.services.async_cosmos_db import get_cosmos_service
from app.schemas.api_catalog import APICatalogResponse, APICatalogMetrics, APICatalogFilter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/catalogs", response_model=List[APICatalogResponse])
async def get_api_catalogs(
    catalog_type: Optional[str] = Query(None, description="Filter by catalog type (fred, eurostat, world_bank)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get all API catalogs from the data-collection-db.
    
    Returns list of API catalogs with metadata and endpoint information.
    """
    try:
        # Access data-collection-db directly with proper credentials
        from azure.cosmos import CosmosClient, exceptions
        import os
        
        cosmos_client = CosmosClient(
            os.getenv('COSMOS_ENDPOINT'),
            os.getenv('COSMOS_KEY')
        )
        
        database = cosmos_client.get_database_client('data-collection-db')
        container = database.get_container_client('api_catalog')
        
        # Build query based on filters
        query = "SELECT * FROM c"
        parameters = []
        
        if catalog_type:
            query += " WHERE c.catalog_type = @catalog_type"
            parameters.append({"name": "@catalog_type", "value": catalog_type})
        
        query += f" OFFSET {skip} LIMIT {limit}"
        
        # Execute query
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Retrieved {len(items)} API catalog items")
        
        # Transform to response format
        catalogs = []
        for item in items:
            # Handle different catalog formats
            catalog_type = item.get('catalog_type', item.get('category', 'unknown'))
            name = item.get('name', item.get('apiName', item.get('id', 'Unknown')))
            # Get description - handle dict or string
            desc_field = item.get('description', item.get('descriptionUpdate', ''))
            if isinstance(desc_field, dict):
                description = desc_field.get('value', str(desc_field))
            else:
                description = str(desc_field) if desc_field else ''
            
            # Get base URL from first endpoint if not at top level
            base_url = item.get('base_url', '')
            endpoints = item.get('endpoints', [])
            if not base_url and endpoints and len(endpoints) > 0:
                base_url = endpoints[0].get('baseUrl', '')
            
            catalog = APICatalogResponse(
                id=item.get('id', ''),
                catalog_type=catalog_type,
                name=name,
                description=description,
                base_url=base_url,
                endpoints_count=len(endpoints),
                last_updated=str(item.get('last_updated', item.get('_ts', ''))),
                version=item.get('version', '1.0'),
                metadata=item.get('metadata', {}),
                endpoints=[]  # Endpoints available via detail endpoint
            )
            catalogs.append(catalog)
        
        return catalogs
        
    except Exception as e:
        logger.error(f"Error retrieving API catalogs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve API catalogs: {str(e)}")


@router.get("/catalogs/{catalog_id}")
async def get_api_catalog_detail(catalog_id: str):
    """
    Get detailed information about a specific API catalog including all endpoints.
    """
    try:
        cosmos_service = await get_cosmos_service()
        cosmos_client = await cosmos_service.get_client()
        database = cosmos_client.get_database_client('data-collection-db')
        container = database.get_container_client('api_catalog')
        
        # Get specific catalog
        item = container.read_item(item=catalog_id, partition_key=catalog_id)
        
        logger.info(f"Retrieved catalog detail for: {catalog_id}")
        
        return {
            "id": item.get('id', ''),
            "catalog_type": item.get('catalog_type', ''),
            "name": item.get('name', ''),
            "description": item.get('description', ''),
            "base_url": item.get('base_url', ''),
            "authentication": item.get('authentication', {}),
            "rate_limits": item.get('rate_limits', {}),
            "endpoints": item.get('endpoints', []),
            "metadata": item.get('metadata', {}),
            "last_updated": item.get('last_updated', ''),
            "version": item.get('version', ''),
            "documentation_url": item.get('documentation_url', ''),
            "contact": item.get('contact', {})
        }
        
    except Exception as e:
        logger.error(f"Error retrieving catalog {catalog_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve catalog: {str(e)}")


@router.get("/catalogs/metrics/summary")
async def get_api_catalog_metrics():
    """
    Get summary metrics about all API catalogs.
    """
    try:
        cosmos_service = await get_cosmos_service()
        cosmos_client = await cosmos_service.get_client()
        database = cosmos_client.get_database_client('data-collection-db')
        container = database.get_container_client('api_catalog')
        
        # Get all catalogs for metrics calculation
        items = list(container.query_items(
            query="SELECT * FROM c",
            enable_cross_partition_query=True
        ))
        
        # Calculate metrics
        total_catalogs = len(items)
        total_endpoints = sum(len(item.get('endpoints', [])) for item in items)
        
        catalog_types = {}
        endpoint_methods = {}
        
        for item in items:
            catalog_type = item.get('catalog_type', 'unknown')
            catalog_types[catalog_type] = catalog_types.get(catalog_type, 0) + 1
            
            for endpoint in item.get('endpoints', []):
                method = endpoint.get('method', 'GET')
                endpoint_methods[method] = endpoint_methods.get(method, 0) + 1
        
        metrics = APICatalogMetrics(
            total_catalogs=total_catalogs,
            total_endpoints=total_endpoints,
            catalog_types=catalog_types,
            endpoint_methods=endpoint_methods,
            avg_endpoints_per_catalog=round(total_endpoints / total_catalogs, 2) if total_catalogs > 0 else 0
        )
        
        logger.info(f"Generated metrics: {total_catalogs} catalogs, {total_endpoints} endpoints")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating catalog metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")


@router.get("/catalogs/search")
async def search_api_catalogs(
    q: str = Query(..., description="Search query"),
    field: str = Query("all", description="Field to search in (name, description, endpoint_path, all)"),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Search API catalogs and endpoints by query string.
    """
    try:
        cosmos_service = await get_cosmos_service()
        cosmos_client = await cosmos_service.get_client()
        database = cosmos_client.get_database_client('data-collection-db')
        container = database.get_container_client('api_catalog')
        
        # Build search query based on field
        if field == "name":
            query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.name), @search_term)"
        elif field == "description":
            query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.description), @search_term)"
        elif field == "endpoint_path":
            query = """
                SELECT c.id, c.name, c.catalog_type, 
                       ARRAY(SELECT VALUE e FROM e IN c.endpoints WHERE CONTAINS(LOWER(e.path), @search_term)) as matching_endpoints
                FROM c 
                WHERE EXISTS(SELECT VALUE e FROM e IN c.endpoints WHERE CONTAINS(LOWER(e.path), @search_term))
            """
        else:  # all fields
            query = """
                SELECT * FROM c 
                WHERE CONTAINS(LOWER(c.name), @search_term) 
                   OR CONTAINS(LOWER(c.description), @search_term)
                   OR EXISTS(SELECT VALUE e FROM e IN c.endpoints WHERE CONTAINS(LOWER(e.path), @search_term))
            """
        
        query += f" LIMIT {limit}"
        
        items = list(container.query_items(
            query=query,
            parameters=[{"name": "@search_term", "value": q.lower()}],
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Search for '{q}' returned {len(items)} results")
        
        return {
            "query": q,
            "field": field,
            "results_count": len(items),
            "results": items
        }
        
    except Exception as e:
        logger.error(f"Error searching catalogs: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/catalogs/types")
async def get_catalog_types():
    """
    Get all available catalog types.
    """
    try:
        cosmos_service = await get_cosmos_service()
        cosmos_client = await cosmos_service.get_client()
        database = cosmos_client.get_database_client('data-collection-db')
        container = database.get_container_client('api_catalog')
        
        # Get distinct catalog types
        items = list(container.query_items(
            query="SELECT DISTINCT VALUE c.catalog_type FROM c",
            enable_cross_partition_query=True
        ))
        
        return {
            "catalog_types": sorted(items),
            "count": len(items)
        }
        
    except Exception as e:
        logger.error(f"Error getting catalog types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get catalog types: {str(e)}")