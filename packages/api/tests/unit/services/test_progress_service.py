"""Tests for ProgressPublisher service."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.schemas.progress import ProgressEvent
from app.services.progress_service import ProgressPublisher


class TestProgressPublisher:
    def test_publish_calls_redis_with_channel_and_json(self):
        mock_redis = MagicMock()
        publisher = ProgressPublisher(mock_redis)

        event = ProgressEvent(
            job_id=uuid4(),
            brief_id=uuid4(),
            status="rendering",
            phase="PREPARE",
            progress_pct=40,
            message="Preparing scenes",
        )
        publisher.publish(event)

        mock_redis.publish.assert_called_once_with(
            event.to_channel(), event.to_json()
        )

    def test_publish_multiple_events(self):
        mock_redis = MagicMock()
        publisher = ProgressPublisher(mock_redis)
        brief_id = uuid4()

        events = [
            ProgressEvent(
                job_id=uuid4(), brief_id=brief_id, status="rendering", progress_pct=5
            ),
            ProgressEvent(
                job_id=uuid4(), brief_id=brief_id, status="done", progress_pct=100
            ),
        ]
        for event in events:
            publisher.publish(event)

        assert mock_redis.publish.call_count == 2
