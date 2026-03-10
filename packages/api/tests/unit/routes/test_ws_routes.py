"""Tests for WebSocket progress route."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.routes.ws import router

app = FastAPI()
app.include_router(router)


class TestWebSocketProgress:
    @patch("app.routes.ws.get_redis_client")
    def test_receives_progress_messages(self, mock_get_redis):
        brief_id = uuid4()
        messages = ['{"status": "rendering"}', '{"status": "done"}']
        msg_iter = iter(messages)

        async def fake_subscribe(*channels):
            for msg in msg_iter:
                yield msg

        mock_client = MagicMock()
        mock_client.subscribe = fake_subscribe
        mock_get_redis.return_value = mock_client

        client = TestClient(app)
        with client.websocket_connect(
            f"/ws/briefs/{brief_id}/progress"
        ) as ws:
            data1 = ws.receive_text()
            data2 = ws.receive_text()

        assert data1 == '{"status": "rendering"}'
        assert data2 == '{"status": "done"}'
        mock_client.close.assert_called_once()

    @patch("app.routes.ws.get_redis_client")
    def test_subscribes_to_correct_channel(self, mock_get_redis):
        brief_id = uuid4()
        subscribed_channels = []

        async def fake_subscribe(*channels):
            subscribed_channels.extend(channels)
            return
            yield

        mock_client = MagicMock()
        mock_client.subscribe = fake_subscribe
        mock_get_redis.return_value = mock_client

        client = TestClient(app)
        with client.websocket_connect(
            f"/ws/briefs/{brief_id}/progress"
        ):
            pass

        assert f"progress:brief:{brief_id}" in subscribed_channels

    @patch("app.routes.ws.get_redis_client")
    def test_closes_redis_on_disconnect(self, mock_get_redis):
        brief_id = uuid4()

        async def fake_subscribe(*channels):
            return
            yield

        mock_client = MagicMock()
        mock_client.subscribe = fake_subscribe
        mock_get_redis.return_value = mock_client

        client = TestClient(app)
        with client.websocket_connect(
            f"/ws/briefs/{brief_id}/progress"
        ):
            pass

        mock_client.close.assert_called_once()

    @patch("app.routes.ws.get_redis_client")
    def test_sends_error_when_redis_unavailable(self, mock_get_redis):
        brief_id = uuid4()
        mock_get_redis.side_effect = ValueError("Redis not configured")

        client = TestClient(app)
        with client.websocket_connect(
            f"/ws/briefs/{brief_id}/progress"
        ) as ws:
            data = ws.receive_json()
            assert data["error"] == "Redis not configured"
