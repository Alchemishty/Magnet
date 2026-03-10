"""Service for publishing real-time progress events."""

from app.repositories.redis_client import RedisClient
from app.schemas.progress import ProgressEvent


class ProgressPublisher:
    """Publishes progress events to Redis channels."""

    def __init__(self, redis_client: RedisClient):
        self._redis = redis_client

    def publish(self, event: ProgressEvent) -> None:
        self._redis.publish(event.to_channel(), event.to_json())
