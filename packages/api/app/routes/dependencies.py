"""FastAPI dependency functions for injecting services."""

from collections.abc import AsyncGenerator, Callable, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.agents.concept_agent import ConceptAgent
from app.db import get_db
from app.providers.llm import get_llm_provider as _get_llm_provider
from app.services.asset_service import AssetService
from app.services.brief_service import BriefService
from app.services.concept_service import ConceptService
from app.services.job_service import JobService
from app.services.project_service import ProjectService
from app.tasks.render import process_render_job


def get_project_service(
    db: Session = Depends(get_db),
) -> Generator[ProjectService, None, None]:
    yield ProjectService(db)


def get_brief_service(
    db: Session = Depends(get_db),
) -> Generator[BriefService, None, None]:
    yield BriefService(db)


def get_concept_service(
    db: Session = Depends(get_db),
) -> Generator[ConceptService, None, None]:
    yield ConceptService(db)


def get_asset_service(
    db: Session = Depends(get_db),
) -> Generator[AssetService, None, None]:
    yield AssetService(db)


def get_job_service(
    db: Session = Depends(get_db),
) -> Generator[JobService, None, None]:
    yield JobService(db)


def get_task_dispatcher() -> Callable[[str], object]:
    return process_render_job.delay


async def get_llm_provider() -> AsyncGenerator:
    provider = _get_llm_provider()
    try:
        yield provider
    finally:
        await provider.aclose()


async def get_concept_agent(
    llm=Depends(get_llm_provider),
) -> AsyncGenerator[ConceptAgent, None]:
    yield ConceptAgent(llm=llm)
