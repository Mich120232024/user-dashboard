"""Simple agents endpoint for system_inbox integration."""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Valid agents from operational tools
VALID_AGENTS = [
    {
        "name": "HEAD_OF_ENGINEERING",
        "role": "Engineering Manager", 
        "status": "active",
        "department": "Engineering"
    },
    {
        "name": "HEAD_OF_RESEARCH", 
        "role": "Research Manager",
        "status": "active", 
        "department": "Research"
    },
    {
        "name": "DATA_ANALYST",
        "role": "Data Analysis",
        "status": "active",
        "department": "Engineering" 
    },
    {
        "name": "AZURE_INFRASTRUCTURE_AGENT",
        "role": "Infrastructure",
        "status": "active",
        "department": "Engineering"
    },
    {
        "name": "FULL_STACK_SOFTWARE_ENGINEER", 
        "role": "Software Development",
        "status": "active",
        "department": "Engineering"
    },
    {
        "name": "RESEARCH_ADVANCED_ANALYST",
        "role": "Advanced Research", 
        "status": "active",
        "department": "Research"
    },
    {
        "name": "RESEARCH_QUANTITATIVE_ANALYST",
        "role": "Quantitative Analysis",
        "status": "idle",
        "department": "Research"
    },
    {
        "name": "RESEARCH_STRATEGY_ANALYST",
        "role": "Strategy Research", 
        "status": "idle",
        "department": "Research"
    }
]


@router.get("/")
async def list_agents() -> List[Dict[str, Any]]:
    """List all valid agents for the system."""
    try:
        return VALID_AGENTS
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/{agent_name}")
async def get_agent(agent_name: str) -> Dict[str, Any]:
    """Get specific agent information."""
    try:
        agent = next((a for a in VALID_AGENTS if a["name"] == agent_name), None)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Add some mock activity data
        return {
            **agent,
            "last_activity": "2025-06-22T10:00:00Z",
            "message_count": 0,  # Could query system_inbox for real count
            "tasks_completed": 42,
            "shell_files": [
                "memory_context.md",
                "journal.md", 
                "deep_context.md",
                "agent_notes/"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.get("/{agent_name}/messages/count")
async def get_agent_message_count(agent_name: str) -> Dict[str, Any]:
    """Get message count for specific agent from system_inbox."""
    try:
        # Import here to avoid circular dependencies
        from app.services.cosmos_db_manager import CosmosDBManager
        
        cosmos_manager = CosmosDBManager()
        system_inbox = cosmos_manager.database.get_container_client("system_inbox")
        
        # Query message counts by status
        queries = {
            "total": f'SELECT VALUE COUNT(1) FROM c WHERE c["to"] = "{agent_name}"',
            "unread": f'SELECT VALUE COUNT(1) FROM c WHERE c["to"] = "{agent_name}" AND c.status = "unread"',
            "read": f'SELECT VALUE COUNT(1) FROM c WHERE c["to"] = "{agent_name}" AND c.status = "read"'
        }
        
        counts = {}
        for status, query in queries.items():
            try:
                items = list(system_inbox.query_items(
                    query=query,
                    enable_cross_partition_query=False
                ))
                counts[status] = items[0] if items else 0
            except:
                counts[status] = 0
        
        return {
            "agent": agent_name,
            "message_counts": counts
        }
        
    except Exception as e:
        logger.error(f"Error getting message count for {agent_name}: {e}")
        # Return 0 counts on error rather than failing
        return {
            "agent": agent_name,
            "message_counts": {"total": 0, "unread": 0, "read": 0}
        }