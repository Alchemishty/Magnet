"""Unit tests for Celery worker configuration."""

from unittest.mock import patch

from app.worker import celery_app


class TestCeleryAppConfig:
    def test_broker_url_defaults_to_localhost(self):
        assert "redis://localhost:6379/0" in celery_app.conf.broker_url

    def test_result_backend_defaults_to_localhost(self):
        assert "redis://localhost:6379/1" in celery_app.conf.result_backend

    def test_task_serializer_is_json(self):
        assert celery_app.conf.task_serializer == "json"

    def test_result_serializer_is_json(self):
        assert celery_app.conf.result_serializer == "json"

    def test_accept_content_includes_json(self):
        assert "json" in celery_app.conf.accept_content

    def test_task_track_started_enabled(self):
        assert celery_app.conf.task_track_started is True

    def test_task_routes_configured(self):
        routes = celery_app.conf.task_routes
        assert "app.tasks.*" in routes
        assert routes["app.tasks.*"] == {"queue": "default"}


class TestCeleryAppEnvOverrides:
    @patch.dict(
        "os.environ",
        {
            "CELERY_BROKER_URL": "redis://custom:6379/0",
            "CELERY_RESULT_BACKEND": "redis://custom:6379/1",
        },
    )
    def test_reads_broker_from_env(self):
        from importlib import reload

        import app.worker as worker_module

        reload(worker_module)

        assert worker_module.celery_app.conf.broker_url == "redis://custom:6379/0"

        # Restore defaults
        reload(worker_module)

    @patch.dict(
        "os.environ",
        {
            "CELERY_BROKER_URL": "redis://custom:6379/0",
            "CELERY_RESULT_BACKEND": "redis://custom:6379/1",
        },
    )
    def test_reads_backend_from_env(self):
        from importlib import reload

        import app.worker as worker_module

        reload(worker_module)

        assert (
            worker_module.celery_app.conf.result_backend == "redis://custom:6379/1"
        )

        # Restore defaults
        reload(worker_module)
