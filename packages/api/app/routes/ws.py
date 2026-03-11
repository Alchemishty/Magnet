"""WebSocket route for real-time progress events."""

import asyncio
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

    async def forward_messages() -> None:
        async for message in client.subscribe(channel):
            await websocket.send_text(message)

    async def wait_for_disconnect() -> None:
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    forward_task = asyncio.create_task(forward_messages())
    disconnect_task = asyncio.create_task(wait_for_disconnect())

    try:
        done, pending = await asyncio.wait(
            {forward_task, disconnect_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        client.close()
