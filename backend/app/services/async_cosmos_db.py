"""
Async Azure Cosmos DB service with proper FastAPI patterns
Uses aiohttp connector for true async operations
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta

import aiohttp
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

logger = logging.getLogger(__name__)


class AsyncCosmosDBService:
    """Async Cosmos DB service optimized for FastAPI"""
    
    def __init__(self):
        self.endpoint = os.getenv('COSMOS_ENDPOINT')
        self.key = os.getenv('COSMOS_KEY') 
        self.database_name = os.getenv('COSMOS_DATABASE', 'research-analytics-db')
        
        if not self.endpoint or not self.key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set")
            
        # Use async client with connection pooling
        self._client = None
        self._database = None
        
    async def get_client(self) -> CosmosClient:
        """Get async Cosmos client with connection pooling"""
        if self._client is None:
            # Create connector with connection pooling
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=20,  # Per-host connection limit
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self._client = CosmosClient(
                self.endpoint, 
                self.key,
                connection_policy={
                    'connection_mode': 'Direct',
                    'request_timeout': 30
                }
            )
            
        return self._client
        
    async def get_database(self):
        """Get database client"""
        if self._database is None:
            client = await self.get_client()
            self._database = client.get_database_client(self.database_name)
        return self._database
        
    async def query_items_async(
        self, 
        container_name: str, 
        query: str, 
        parameters: Optional[List[Dict]] = None,
        max_items: int = 100
    ) -> List[Dict]:
        """Execute async query with proper streaming"""
        try:
            database = await self.get_database()
            container = database.get_container_client(container_name)
            
            # Use async generator for memory efficiency
            items = []
            item_count = 0
            
            async for item in container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            ):
                items.append(item)
                item_count += 1
                if item_count >= max_items:
                    break
                    
            logger.debug(f"Query returned {len(items)} items from {container_name}")
            return items
            
        except Exception as e:
            logger.error(f"Query failed for {container_name}: {e}")
            return []
            
    async def query_items_stream(
        self, 
        container_name: str, 
        query: str, 
        parameters: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict, None]:
        """Stream query results for large datasets"""
        try:
            database = await self.get_database()
            container = database.get_container_client(container_name)
            
            async for item in container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            ):
                yield item
                
        except Exception as e:
            logger.error(f"Stream query failed for {container_name}: {e}")
            return
            
    async def get_container_count(self, container_name: str) -> int:
        """Get document count efficiently"""
        try:
            items = await self.query_items_async(
                container_name,
                "SELECT VALUE COUNT(1) FROM c",
                max_items=1
            )
            return items[0] if items else 0
        except Exception as e:
            logger.error(f"Count query failed for {container_name}: {e}")
            return 0
            
    async def batch_query(self, queries: List[Dict]) -> List[List[Dict]]:
        """Execute multiple queries concurrently"""
        tasks = []
        for query_info in queries:
            task = self.query_items_async(
                query_info['container'],
                query_info['query'],
                query_info.get('parameters'),
                query_info.get('max_items', 100)
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        clean_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch query failed: {result}")
                clean_results.append([])
            else:
                clean_results.append(result)
                
        return clean_results
        
    async def close(self):
        """Cleanup connections"""
        if self._client:
            await self._client.close()


# Global service instance
_cosmos_service = None

async def get_cosmos_service() -> AsyncCosmosDBService:
    """FastAPI dependency for async Cosmos DB service"""
    global _cosmos_service
    if _cosmos_service is None:
        _cosmos_service = AsyncCosmosDBService()
    return _cosmos_service