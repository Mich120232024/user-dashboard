"""WebSocket endpoints."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection endpoint."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")