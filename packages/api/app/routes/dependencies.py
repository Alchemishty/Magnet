"""FastAPI dependency functions for injecting services."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.asset_service import AssetService
from app.services.brief_service import BriefService
from app.services.concept_service import ConceptService
from app.services.job_service import JobService
from app.services.project_service import ProjectService


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
