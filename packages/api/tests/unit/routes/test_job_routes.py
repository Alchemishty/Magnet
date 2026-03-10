"""Tests for RenderJob route endpoints."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import NotFoundError
from app.routes.dependencies import get_job_service, get_task_dispatcher
from app.routes.jobs import router


def _make_job(**overrides):
    defaults = {
        "id": uuid4(),
        "brief_id": uuid4(),
        "status": "queued",
        "composition": None,
        "output_s3_key": None,
        "render_duration_ms": None,
        "error_message": None,
        "celery_task_id": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


@pytest.fixture()
def mock_service():
    return MagicMock()


@pytest.fixture()
def mock_dispatcher():
    return MagicMock()


@pytest.fixture()
def client(mock_service, mock_dispatcher):
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_job_service] = lambda: mock_service
    test_app.dependency_overrides[get_task_dispatcher] = lambda: mock_dispatcher
    return TestClient(test_app)


# ── POST /api/briefs/{brief_id}/jobs ─────────────────────────────


class TestCreateJob:
    def test_returns_201(self, client, mock_service):
        brief_id = uuid4()
        job = _make_job(brief_id=brief_id)
        mock_service.create_job.return_value = job

        resp = client.post(
            f"/api/briefs/{brief_id}/jobs",
            json={"brief_id": str(uuid4()), "status": "queued"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == str(job.id)
        assert data["brief_id"] == str(brief_id)

    def test_overrides_brief_id_from_path(self, client, mock_service):
        brief_id = uuid4()
        other_id = uuid4()
        job = _make_job(brief_id=brief_id)
        mock_service.create_job.return_value = job

        client.post(
            f"/api/briefs/{brief_id}/jobs",
            json={"brief_id": str(other_id), "status": "queued"},
        )

        call_data = mock_service.create_job.call_args[0][0]
        assert call_data.brief_id == brief_id

    def test_returns_404_when_brief_missing(self, client, mock_service):
        brief_id = uuid4()
        mock_service.create_job.side_effect = NotFoundError("CreativeBrief", brief_id)

        resp = client.post(
            f"/api/briefs/{brief_id}/jobs",
            json={"brief_id": str(brief_id), "status": "queued"},
        )

        assert resp.status_code == 404

    def test_passes_dispatcher_to_service(
        self, client, mock_service, mock_dispatcher
    ):
        brief_id = uuid4()
        job = _make_job(brief_id=brief_id)
        mock_service.create_job.return_value = job

        client.post(
            f"/api/briefs/{brief_id}/jobs",
            json={"status": "queued"},
        )

        call_kwargs = mock_service.create_job.call_args[1]
        assert call_kwargs["dispatch_task"] is mock_dispatcher


# ── GET /api/briefs/{brief_id}/jobs ──────────────────────────────


class TestListJobs:
    def test_returns_list(self, client, mock_service):
        brief_id = uuid4()
        jobs = [_make_job(brief_id=brief_id) for _ in range(3)]
        mock_service.list_jobs.return_value = jobs

        resp = client.get(f"/api/briefs/{brief_id}/jobs")

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_passes_query_params(self, client, mock_service):
        brief_id = uuid4()
        mock_service.list_jobs.return_value = []

        client.get(
            f"/api/briefs/{brief_id}/jobs",
            params={"status": "done", "offset": 10, "limit": 5},
        )

        mock_service.list_jobs.assert_called_once_with(
            brief_id, status="done", offset=10, limit=5
        )


# ── GET /api/jobs/{job_id} ───────────────────────────────────────


class TestGetJob:
    def test_returns_200(self, client, mock_service):
        job = _make_job()
        mock_service.get_job.return_value = job

        resp = client.get(f"/api/jobs/{job.id}")

        assert resp.status_code == 200
        assert resp.json()["id"] == str(job.id)

    def test_returns_404(self, client, mock_service):
        job_id = uuid4()
        mock_service.get_job.side_effect = NotFoundError("RenderJob", job_id)

        resp = client.get(f"/api/jobs/{job_id}")

        assert resp.status_code == 404


# ── PATCH /api/jobs/{job_id} ─────────────────────────────────────


class TestUpdateJob:
    def test_returns_200(self, client, mock_service):
        job = _make_job(status="rendering")
        mock_service.update_job.return_value = job

        resp = client.patch(
            f"/api/jobs/{job.id}",
            json={"status": "rendering"},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "rendering"

    def test_returns_404(self, client, mock_service):
        job_id = uuid4()
        mock_service.update_job.side_effect = NotFoundError("RenderJob", job_id)

        resp = client.patch(
            f"/api/jobs/{job_id}",
            json={"status": "done"},
        )

        assert resp.status_code == 404
