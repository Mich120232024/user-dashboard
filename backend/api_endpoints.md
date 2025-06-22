# API Endpoints for User Dashboard

## System Inbox Schema
Based on analysis of operational tools:

```json
{
  "id": "20250621_163934_SYSTEM_AUDIT_AGENT_01",
  "from": "SYSTEM_AUDIT_AGENT",
  "to": "HEAD_OF_ENGINEERING", 
  "content": "Message body text...",
  "timestamp": "2025-06-21T16:39:34.194176",
  "status": "unread",  // or "read"
  "priority": "HIGH",  // or "NORMAL"
  "type": "MESSAGE",   // or "TASK", "AUDIT_REPORT", etc.
  "subject": "Optional subject line",
  "thread_id": "optional-thread-id",
  "created_by": "enhanced_send_message_v2.0"
}
```

## Partition Key
- Container: system_inbox
- Partition key: /to (recipient agent name)

## Valid Agent Names
- HEAD_OF_ENGINEERING
- HEAD_OF_RESEARCH
- DATA_ANALYST
- AZURE_INFRASTRUCTURE_AGENT
- FULL_STACK_SOFTWARE_ENGINEER
- RESEARCH_ADVANCED_ANALYST
- RESEARCH_QUANTITATIVE_ANALYST
- RESEARCH_STRATEGY_ANALYST

## Needed API Endpoints
1. GET /api/v1/messages/{agent_name} - Get messages for specific agent
2. POST /api/v1/messages - Send new message
3. PUT /api/v1/messages/{id}/status - Update message status (mark as read)
4. GET /api/v1/agents - List all valid agents with status