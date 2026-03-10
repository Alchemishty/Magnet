"""WebSocket route for real-time progress events."""

import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.repositories.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/briefs/{brief_id}/progress")
async def brief_progress(websocket: WebSocket, brief_id: UUID) -> None:
    await websocket.accept()

    try:
        client = get_redis_client()
    except ValueError as exc:
        await websocket.send_json({"error": str(exc)})
        await websocket.close(code=1011)
        return

    channel = f"progress:brief:{brief_id}"
    try:
        async for message in client.subscribe(channel):
            await websocket.send_text(message)
    except WebSocketDisconnect:
        logger.debug("Client disconnected from %s", channel)
    finally:
        client.close()
