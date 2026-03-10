"""Celery task for processing render jobs."""

import logging
from uuid import UUID

from app.db import SessionLocal
from app.repositories.job_repository import RenderJobRepository
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.render.process_render_job", bind=True)
def process_render_job(self, job_id: str) -> None:
    """Process a render job asynchronously.

    Updates job status through the lifecycle: queued -> rendering -> done.
    On failure, sets status to 'failed' with the error message.
    """
    session = SessionLocal()
    try:
        repo = RenderJobRepository(session)
        job = repo.get_by_id(UUID(job_id))
        if job is None:
            raise ValueError(f"RenderJob {job_id} not found")

        repo.update(UUID(job_id), {
            "status": "rendering",
            "celery_task_id": self.request.id,
        })
        session.commit()

        logger.info("Processing render job %s (pipeline placeholder)", job_id)

        repo.update(UUID(job_id), {"status": "done"})
        session.commit()
    except Exception as exc:
        session.rollback()
        try:
            repo = RenderJobRepository(session)
            repo.update(UUID(job_id), {
                "status": "failed",
                "error_message": str(exc),
            })
            session.commit()
        except Exception:
            logger.exception("Failed to mark job %s as failed", job_id)
        raise
    finally:
        session.close()
