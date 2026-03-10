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


@celery_app.task(name="app.tasks.render.process_render_job")
def process_render_job(job_id: str) -> None:
    """Process a render job asynchronously via the Video Agent pipeline.

    Updates job status through the lifecycle: queued -> rendering -> done.
    On failure, sets status to 'failed' with the error message.
    """
    session = SessionLocal()
    try:
        job_repo = RenderJobRepository(session)
        job = job_repo.get_by_id(UUID(job_id))
        if job is None:
            raise ValueError(f"RenderJob {job_id} not found")

        job_repo.update(UUID(job_id), {"status": "rendering"})
        session.commit()

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
    from app.schemas.brief import BriefRead

    brief_read = BriefRead.model_validate(brief)

    tts = get_tts_provider()
    music = get_music_provider()
    image = get_image_provider()

    asset_session = SessionLocal()
    try:
        from app.repositories.asset_repository import AssetRepository

        asset_repo = AssetRepository(asset_session)
        agent = VideoAgent(
            tts_provider=tts,
            music_provider=music,
            image_provider=image,
            asset_repo=asset_repo,
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
