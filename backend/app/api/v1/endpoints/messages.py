"""Message endpoints for system_inbox."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from app.services.cosmos_db_manager import CosmosDBManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class MessageResponse(BaseModel):
    id: str
    from_agent: str = None
    to: str
    content: str
    timestamp: str
    status: str
    priority: str = "NORMAL"
    type: str = "MESSAGE"
    subject: Optional[str] = None
    thread_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    from_agent: str
    to: str
    content: str
    priority: str = "NORMAL"
    message_type: str = "MESSAGE"
    subject: Optional[str] = None
    thread_id: Optional[str] = None


@router.get("/")
async def list_messages(
    agent: Optional[str] = Query(None, description="Filter messages for specific agent"),
    status: Optional[str] = Query(None, description="Filter by status (read/unread)"),
    limit: Optional[int] = Query(50, description="Maximum number of messages")
):
    """List messages from system_inbox."""
    try:
        # Get system_inbox container
        cosmos_manager = CosmosDBManager()
        system_inbox = cosmos_manager.database.get_container_client("system_inbox")
        
        # Build query
        if agent:
            query = f'SELECT * FROM c WHERE c["to"] = "{agent}"'
        else:
            query = "SELECT * FROM c"
            
        if status:
            if "WHERE" in query:
                query += f' AND c.status = "{status}"'
            else:
                query += f' WHERE c.status = "{status}"'
                
        query += " ORDER BY c.timestamp DESC"
        
        if limit:
            query += f" OFFSET 0 LIMIT {limit}"
        
        logger.info(f"Querying system_inbox: {query}")
        
        # Query system_inbox container
        items = list(system_inbox.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Convert to response format
        messages = []
        for item in items:
            messages.append({
                "id": item.get("id"),
                "from": item.get("from"),
                "to": item.get("to"),
                "content": item.get("content"),
                "timestamp": item.get("timestamp"),
                "status": item.get("status", "unknown"),
                "priority": item.get("priority", "NORMAL"),
                "type": item.get("type", "MESSAGE"),
                "subject": item.get("subject"),
                "thread_id": item.get("thread_id")
            })
        
        return messages
        
    except Exception as e:
        logger.error(f"Error querying messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.get("/{agent_name}")
async def get_agent_messages(
    agent_name: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(50, description="Maximum number of messages")
):
    """Get messages for a specific agent from system_inbox."""
    try:
        # Get system_inbox container
        cosmos_manager = CosmosDBManager()
        system_inbox = cosmos_manager.database.get_container_client("system_inbox")
        
        # Query messages for specific agent
        query = f'SELECT * FROM c WHERE c["to"] = "{agent_name}"'
        
        if status:
            query += f' AND c.status = "{status}"'
            
        query += " ORDER BY c.timestamp DESC"
        
        if limit:
            query += f" OFFSET 0 LIMIT {limit}"
        
        logger.info(f"Querying messages for {agent_name}: {query}")
        
        items = list(system_inbox.query_items(
            query=query,
            enable_cross_partition_query=False  # Using partition key /to
        ))
        
        # Convert and return
        messages = []
        for item in items:
            messages.append({
                "id": item.get("id"),
                "from": item.get("from"),
                "to": item.get("to"),
                "content": item.get("content"),
                "timestamp": item.get("timestamp"),
                "status": item.get("status", "unknown"),
                "priority": item.get("priority", "NORMAL"),
                "type": item.get("type", "MESSAGE"),
                "subject": item.get("subject"),
                "thread_id": item.get("thread_id")
            })
        
        return {
            "agent": agent_name,
            "total": len(messages),
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"Error querying messages for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.post("/")
async def send_message(message: SendMessageRequest):
    """Send a new message to system_inbox."""
    try:
        # Get system_inbox container
        cosmos_manager = CosmosDBManager()
        system_inbox = cosmos_manager.database.get_container_client("system_inbox")
        
        # Generate unique ID
        from datetime import datetime
        timestamp = datetime.now()
        message_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{message.from_agent}_01"
        
        # Create message document
        message_doc = {
            "id": message_id,
            "from": message.from_agent,
            "to": message.to,
            "content": message.content,
            "timestamp": timestamp.isoformat(),
            "status": "unread",
            "priority": message.priority,
            "type": message.message_type,
            "created_by": "dashboard_api"
        }
        
        if message.subject:
            message_doc["subject"] = message.subject
        if message.thread_id:
            message_doc["thread_id"] = message.thread_id
        
        # Insert into system_inbox
        result = system_inbox.create_item(body=message_doc)
        
        return {
            "success": True,
            "message_id": message_id,
            "timestamp": timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.put("/{message_id}/status")
async def update_message_status(message_id: str, status: str):
    """Update message status (mark as read/unread)."""
    try:
        # Get system_inbox container
        cosmos_manager = CosmosDBManager()
        system_inbox = cosmos_manager.database.get_container_client("system_inbox")
        
        # Get the message first to get partition key
        try:
            item = system_inbox.read_item(item=message_id, partition_key=message_id)
        except:
            # If that fails, query to find it
            query = f'SELECT * FROM c WHERE c.id = "{message_id}"'
            items = list(system_inbox.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            if not items:
                raise HTTPException(status_code=404, detail="Message not found")
            item = items[0]
        
        # Update status
        item["status"] = status
        
        # Update in database
        system_inbox.replace_item(item=item, body=item)
        
        return {
            "success": True,
            "message_id": message_id,
            "new_status": status
        }
        
    except Exception as e:
        logger.error(f"Error updating message status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")