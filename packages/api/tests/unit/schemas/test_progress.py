"""Tests for progress event schemas."""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.progress import ProgressEvent


class TestProgressEvent:
    def test_create_with_all_fields(self):
        job_id = uuid4()
        brief_id = uuid4()
        event = ProgressEvent(
            job_id=job_id,
            brief_id=brief_id,
            status="rendering",
            phase="PREPARE",
            progress_pct=40,
            message="Preparing scenes",
        )
        assert event.job_id == job_id
        assert event.brief_id == brief_id
        assert event.status == "rendering"
        assert event.phase == "PREPARE"
        assert event.progress_pct == 40
        assert event.message == "Preparing scenes"
        assert isinstance(event.timestamp, datetime)

    def test_create_minimal(self):
        job_id = uuid4()
        brief_id = uuid4()
        event = ProgressEvent(
            job_id=job_id,
            brief_id=brief_id,
            status="queued",
        )
        assert event.phase is None
        assert event.progress_pct is None
        assert event.message is None

    def test_timestamp_defaults_to_utcnow(self):
        before = datetime.now(timezone.utc)
        event = ProgressEvent(
            job_id=uuid4(),
            brief_id=uuid4(),
            status="done",
        )
        after = datetime.now(timezone.utc)
        assert before <= event.timestamp <= after

    def test_to_channel_uses_brief_id(self):
        brief_id = uuid4()
        event = ProgressEvent(
            job_id=uuid4(),
            brief_id=brief_id,
            status="rendering",
        )
        assert event.to_channel() == f"progress:brief:{brief_id}"

    def test_to_json_returns_valid_json(self):
        import json

        event = ProgressEvent(
            job_id=uuid4(),
            brief_id=uuid4(),
            status="done",
            phase="POST-PROCESS",
            progress_pct=100,
            message="Complete",
        )
        raw = event.to_json()
        parsed = json.loads(raw)
        assert parsed["status"] == "done"
        assert parsed["phase"] == "POST-PROCESS"
        assert parsed["progress_pct"] == 100
        assert parsed["message"] == "Complete"

    def test_progress_pct_bounds(self):
        import pytest

        with pytest.raises(Exception):
            ProgressEvent(
                job_id=uuid4(),
                brief_id=uuid4(),
                status="rendering",
                progress_pct=-1,
            )
        with pytest.raises(Exception):
            ProgressEvent(
                job_id=uuid4(),
                brief_id=uuid4(),
                status="rendering",
                progress_pct=101,
            )

    def test_invalid_status_rejected(self):
        import pytest

        with pytest.raises(Exception):
            ProgressEvent(
                job_id=uuid4(),
                brief_id=uuid4(),
                status="invalid_status",
            )
