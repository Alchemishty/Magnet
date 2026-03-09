"""Project and GameProfile routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from app.errors import DatabaseError, NotFoundError
from app.routes.dependencies import get_project_service
from app.schemas.project import (
    GameProfileCreate,
    GameProfileCreateBody,
    GameProfileRead,
    GameProfileUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ── projects ──────────────────────────────────────────────────────


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    body: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    try:
        result = service.create_project(body)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return ProjectRead.model_validate(result)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    user_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectRead]:
    try:
        results = service.list_projects(user_id)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return [ProjectRead.model_validate(r) for r in results]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    try:
        result = service.get_project(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return ProjectRead.model_validate(result)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    try:
        result = service.update_project(project_id, body)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return ProjectRead.model_validate(result)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> Response:
    try:
        service.delete_project(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return Response(status_code=204)


# ── game profiles ────────────────────────────────────────────────


@router.post(
    "/{project_id}/game-profile",
    response_model=GameProfileRead,
    status_code=201,
)
def create_game_profile(
    project_id: UUID,
    body: GameProfileCreateBody,
    service: ProjectService = Depends(get_project_service),
) -> GameProfileRead:
    data = GameProfileCreate(project_id=project_id, **body.model_dump())
    try:
        result = service.create_game_profile(data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return GameProfileRead.model_validate(result)


@router.get(
    "/{project_id}/game-profile",
    response_model=GameProfileRead,
)
def get_game_profile(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> GameProfileRead:
    try:
        result = service.get_game_profile(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return GameProfileRead.model_validate(result)


@router.patch(
    "/{project_id}/game-profile",
    response_model=GameProfileRead,
)
def update_game_profile(
    project_id: UUID,
    body: GameProfileUpdate,
    service: ProjectService = Depends(get_project_service),
) -> GameProfileRead:
    try:
        result = service.update_game_profile(project_id, body)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return GameProfileRead.model_validate(result)
