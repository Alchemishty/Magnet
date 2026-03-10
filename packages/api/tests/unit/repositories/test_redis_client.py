"""Tests for Redis pub/sub client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.redis_client import RedisClient, get_redis_client


class TestRedisClient:
    def test_publish_calls_redis_publish(self):
        mock_redis = MagicMock()
        client = RedisClient.__new__(RedisClient)
        client._redis = mock_redis
        client._url = "redis://localhost:6379/0"

        client.publish("test-channel", '{"status": "done"}')

        mock_redis.publish.assert_called_once_with(
            "test-channel", '{"status": "done"}'
        )

    @pytest.mark.asyncio
    async def test_subscribe_yields_messages(self):
        mock_pubsub = AsyncMock()
        messages = [
            {"type": "subscribe", "data": 1},
            {"type": "message", "data": b'{"status": "rendering"}'},
            {"type": "message", "data": b'{"status": "done"}'},
            None,
        ]
        call_count = 0

        async def fake_get_message(ignore_subscribe_messages, timeout):
            nonlocal call_count
            if call_count < len(messages):
                msg = messages[call_count]
                call_count += 1
                return msg
            return None

        mock_pubsub.get_message = fake_get_message
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.aclose = AsyncMock()

        mock_async_redis = MagicMock()
        mock_async_redis.pubsub.return_value = mock_pubsub
        mock_async_redis.aclose = AsyncMock()

        client = RedisClient.__new__(RedisClient)
        client._url = "redis://localhost:6379/0"

        received = []
        with patch(
            "app.repositories.redis_client.async_redis.from_url",
            return_value=mock_async_redis,
        ):
            stream = client.subscribe("test-channel")
            try:
                received.append(await stream.__anext__())
                received.append(await stream.__anext__())
            finally:
                await stream.aclose()

        assert received == [
            '{"status": "rendering"}',
            '{"status": "done"}',
        ]
        mock_pubsub.unsubscribe.assert_awaited_once()
        mock_pubsub.aclose.assert_awaited_once()
        mock_async_redis.aclose.assert_awaited_once()

    def test_close_calls_redis_close(self):
        mock_redis = MagicMock()
        client = RedisClient.__new__(RedisClient)
        client._redis = mock_redis

        client.close()

        mock_redis.close.assert_called_once()


class TestGetRedisClient:
    @patch.dict("os.environ", {"REDIS_URL": "redis://custom:6379/0"}, clear=False)
    @patch("app.repositories.redis_client.redis.Redis.from_url")
    def test_uses_redis_url_env(self, mock_from_url):
        mock_from_url.return_value = MagicMock()
        client = get_redis_client()
        assert client._url == "redis://custom:6379/0"

    @patch.dict(
        "os.environ",
        {"CELERY_BROKER_URL": "redis://celery:6379/0"},
        clear=True,
    )
    @patch("app.repositories.redis_client.redis.Redis.from_url")
    def test_falls_back_to_celery_broker_url(self, mock_from_url):
        mock_from_url.return_value = MagicMock()
        client = get_redis_client()
        assert client._url == "redis://celery:6379/0"

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.repositories.redis_client.redis.Redis.from_url")
    def test_falls_back_to_default(self, mock_from_url):
        mock_from_url.return_value = MagicMock()
        client = get_redis_client()
        assert client._url == "redis://localhost:6379/0"
