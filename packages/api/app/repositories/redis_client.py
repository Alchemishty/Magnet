"""Redis pub/sub client for real-time progress events."""

import logging
import os
from collections.abc import AsyncGenerator

import redis
import redis.asyncio as async_redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Wraps Redis pub/sub for publishing and subscribing to progress channels."""

    def __init__(self, url: str):
        self._url = url
        self._redis = redis.Redis.from_url(url)

    def publish(self, channel: str, message: str) -> None:
        self._redis.publish(channel, message)

    async def subscribe(self, *channels: str) -> AsyncGenerator[str, None]:
        async_conn = async_redis.from_url(self._url)
        pubsub = async_conn.pubsub()
        try:
            await pubsub.subscribe(*channels)
            while True:
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if msg is not None and msg["type"] == "message":
                    yield msg["data"].decode("utf-8")
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.aclose()
            await async_conn.aclose()

    def close(self) -> None:
        self._redis.close()


def get_redis_client() -> RedisClient:
    url = os.environ.get(
        "REDIS_URL",
        os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    )
    return RedisClient(url)
