from celery import Celery

celery_app = Celery(
    "magnet",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.task_routes = {
    "app.tasks.*": {"queue": "default"},
}
