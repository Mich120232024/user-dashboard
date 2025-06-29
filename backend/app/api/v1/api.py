"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents, auth, messages, users, websocket, documents, cosmos,
    blob, memory, monitoring, graph, live_data, memory_layers, docs, agents_async, agents_simple, architecture, api_catalog
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
# Use simple agents router for system_inbox integration  
api_router.include_router(agents_simple.router, prefix="/agents", tags=["agents"])
api_router.include_router(agents_async.router, prefix="/agents-async", tags=["agents-async"])
api_router.include_router(agents.router, prefix="/agents-legacy", tags=["agents-legacy"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(cosmos.router, prefix="/cosmos", tags=["cosmos"])
api_router.include_router(blob.router, prefix="/blob", tags=["blob-storage"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory-layers"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph-explorer"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# New Flask-compatible endpoints
api_router.include_router(live_data.router, prefix="/live", tags=["live-data"])
api_router.include_router(memory_layers.router, prefix="/memory-layers", tags=["memory-layers-compat"])
api_router.include_router(docs.router, prefix="/docs", tags=["documentation"])
api_router.include_router(architecture.router, prefix="/architecture", tags=["architecture"])
api_router.include_router(api_catalog.router, prefix="/api-catalog", tags=["api-catalog"])