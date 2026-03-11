"""Celery task for processing render jobs via the Video Agent."""

import asyncio
import logging
import tempfile
from uuid import UUID

from app.db import SessionLocal
from app.repositories.brief_repository import BriefRepository
from app.repositories.job_repository import RenderJobRepository
from app.worker import celery_app

logger = logging.getLogger(__name__)


def _publish_progress(
    job_id: str,
    brief_id: str,
    *,
    status: str,
    progress_pct: int | None = None,
    phase: str | None = None,
    message: str | None = None,
) -> None:
    """Publish a progress event to Redis. Best-effort — never raises."""
    try:
        from app.repositories.redis_client import get_redis_client
        from app.schemas.progress import ProgressEvent

        client = get_redis_client()
        event = ProgressEvent(
            job_id=UUID(job_id),
            brief_id=UUID(brief_id),
            status=status,
            phase=phase,
            progress_pct=progress_pct,
            message=message,
        )
        client.publish(event.to_channel(), event.to_json())
        client.close()
    except Exception:
        logger.debug("Failed to publish progress for job %s", job_id)


@celery_app.task(name="app.tasks.render.process_render_job")
def process_render_job(job_id: str) -> None:
    """Process a render job asynchronously via the Video Agent pipeline.

    Updates job status through the lifecycle: queued -> rendering -> done.
    On failure, sets status to 'failed' with the error message.
    Publishes progress events to Redis at each lifecycle transition.
    """
    session = SessionLocal()
    brief_id: str | None = None
    try:
        job_repo = RenderJobRepository(session)
        job = job_repo.get_by_id(UUID(job_id))
        if job is None:
            raise ValueError(f"RenderJob {job_id} not found")

        brief_id = str(job.brief_id)

        job_repo.update(UUID(job_id), {"status": "rendering"})
        session.commit()
        _publish_progress(
            job_id, brief_id,
            status="rendering", progress_pct=5, message="Render job started",
        )

        brief_repo = BriefRepository(session)
        brief = brief_repo.get_by_id(job.brief_id)
        if brief is None:
            raise ValueError(f"CreativeBrief {job.brief_id} not found")

        s3_key, composition = _run_video_agent(brief, job_id)

        job_repo.update(UUID(job_id), {
            "status": "done",
            "output_s3_key": s3_key,
            "composition": composition.model_dump() if composition else None,
        })
        session.commit()
        _publish_progress(
            job_id, brief_id,
            status="done", progress_pct=100, message="Render complete",
        )
    except Exception as exc:
        session.rollback()
        try:
            job_repo = RenderJobRepository(session)
            job_repo.update(UUID(job_id), {
                "status": "failed",
                "error_message": str(exc),
            })
            session.commit()
        except Exception:
            logger.exception("Failed to mark job %s as failed", job_id)
        if brief_id is not None:
            _publish_progress(
                job_id, brief_id,
                status="failed", message=str(exc),
            )
        raise
    finally:
        session.close()


def _run_video_agent(brief, job_id: str):
    """Create providers and run the Video Agent pipeline.

    Bridges sync Celery task to async Video Agent via asyncio.run().
    """
    from app.agents.video_agent import VideoAgent
    from app.providers.image import get_image_provider
    from app.providers.music import get_music_provider
    from app.providers.tts import get_tts_provider
    from app.repositories.s3_client import get_s3_client
    from app.schemas.brief import BriefRead

    brief_read = BriefRead.model_validate(brief)

    tts = get_tts_provider()
    music = get_music_provider()
    image = get_image_provider()

    try:
        s3 = get_s3_client()
    except ValueError:
        logger.warning("S3 not configured, Video Agent will skip uploads")
        s3 = None

    asset_session = SessionLocal()
    try:
        from app.repositories.asset_repository import AssetRepository

        asset_repo = AssetRepository(asset_session)
        agent = VideoAgent(
            tts_provider=tts,
            music_provider=music,
            image_provider=image,
            asset_repo=asset_repo,
            s3_client=s3,
        )

        work_dir = tempfile.mkdtemp(prefix=f"magnet_render_{job_id}_")
        return asyncio.run(agent.produce(brief_read, work_dir))
    finally:
        asset_session.close()
        asyncio.run(_cleanup_providers(tts, music, image))


async def _cleanup_providers(*providers):
    """Close any providers that have an aclose method."""
    for p in providers:
        if hasattr(p, "aclose"):
            await p.aclose()
