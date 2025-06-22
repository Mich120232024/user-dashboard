"""Cosmos DB content viewer for dashboard."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

logger = logging.getLogger(__name__)


class CosmosDBViewer:
    """Read-only viewer for Cosmos DB content."""
    
    def __init__(self, endpoint: str, key: str, database_name: str):
        """Initialize Cosmos DB viewer."""
        self.client = CosmosClient(endpoint, key)
        self.database = self.client.get_database_client(database_name)
        logger.info(f"Cosmos DB Viewer initialized for database: {database_name}")
    
    def list_containers(self) -> List[Dict[str, Any]]:
        """List all containers in the database."""
        containers = []
        for container in self.database.list_containers():
            containers.append({
                "id": container["id"],
                "partition_key": container.get("partitionKey", {}).get("paths", []),
                "indexing_policy": container.get("indexingPolicy", {})
            })
        return containers
    
    def query_container(self, container_id: str, query: str = "SELECT * FROM c", 
                       max_items: int = 100) -> List[Dict[str, Any]]:
        """Query a container with safety limits."""
        try:
            container = self.database.get_container_client(container_id)
            
            # Add safety limit to query if not present
            if "TOP" not in query.upper() and "OFFSET" not in query.upper():
                query = query.replace("SELECT", f"SELECT TOP {max_items}", 1)
            
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items
        except CosmosResourceNotFoundError:
            logger.error(f"Container not found: {container_id}")
            return []
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return []
    
    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get statistics for a container."""
        try:
            container = self.database.get_container_client(container_id)
            
            # Count total items
            count_query = "SELECT VALUE COUNT(1) FROM c"
            count_result = list(container.query_items(
                query=count_query,
                enable_cross_partition_query=True
            ))
            total_count = count_result[0] if count_result else 0
            
            # Get sample of recent items
            recent_query = "SELECT TOP 5 * FROM c ORDER BY c._ts DESC"
            recent_items = list(container.query_items(
                query=recent_query,
                enable_cross_partition_query=True
            ))
            
            # Get partition distribution (simplified)
            partition_query = "SELECT c.partitionKey, COUNT(1) as count FROM c GROUP BY c.partitionKey"
            try:
                partition_dist = list(container.query_items(
                    query=partition_query,
                    enable_cross_partition_query=True
                ))
            except:
                partition_dist = []
            
            return {
                "container_id": container_id,
                "total_items": total_count,
                "recent_items": recent_items,
                "partition_distribution": partition_dist
            }
        except Exception as e:
            logger.error(f"Error getting container stats: {str(e)}")
            return {
                "container_id": container_id,
                "error": str(e)
            }
    
    def search_content(self, search_term: str, containers: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Search across containers for content."""
        results = {}
        
        if containers is None:
            # Search all containers
            containers = [c["id"] for c in self.list_containers()]
        
        for container_id in containers:
            # Basic search query - can be enhanced based on schema
            search_query = f"""
            SELECT * FROM c 
            WHERE CONTAINS(LOWER(c.content), LOWER('{search_term}'))
               OR CONTAINS(LOWER(c.subject), LOWER('{search_term}'))
               OR CONTAINS(LOWER(c.body), LOWER('{search_term}'))
               OR CONTAINS(LOWER(c.title), LOWER('{search_term}'))
            """
            
            container_results = self.query_container(container_id, search_query, max_items=50)
            if container_results:
                results[container_id] = container_results
        
        return results
    
    def export_container_data(self, container_id: str, format: str = "json") -> str:
        """Export container data for backup or analysis."""
        items = self.query_container(container_id, "SELECT * FROM c", max_items=1000)
        
        if format == "json":
            return json.dumps(items, indent=2, default=str)
        elif format == "csv":
            # Simple CSV export - can be enhanced
            if not items:
                return ""
            
            import csv
            import io
            
            output = io.StringIO()
            if items:
                fieldnames = list(items[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(items)
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")