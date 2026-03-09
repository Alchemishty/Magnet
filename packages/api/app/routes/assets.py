"""FastAPI routes for Asset operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.errors import DatabaseError, NotFoundError
from app.routes.dependencies import get_asset_service
from app.schemas.asset import AssetCreate, AssetCreateBody, AssetRead
from app.services.asset_service import AssetService

router = APIRouter(tags=["assets"])


@router.post(
    "/api/projects/{project_id}/assets",
    response_model=AssetRead,
    status_code=201,
)
def create_asset(
    project_id: UUID,
    body: AssetCreateBody,
    service: AssetService = Depends(get_asset_service),
) -> AssetRead:
    """Create a new asset within a project."""
    data = AssetCreate(project_id=project_id, **body.model_dump())
    try:
        asset = service.create_asset(data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return asset


@router.get(
    "/api/projects/{project_id}/assets",
    response_model=list[AssetRead],
)
def list_assets(
    project_id: UUID,
    asset_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: AssetService = Depends(get_asset_service),
) -> list[AssetRead]:
    """List assets for a project with optional filtering."""
    try:
        assets = service.list_assets(
            project_id, asset_type=asset_type, offset=offset, limit=limit
        )
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return assets


@router.get(
    "/api/assets/{asset_id}",
    response_model=AssetRead,
)
def get_asset(
    asset_id: UUID,
    service: AssetService = Depends(get_asset_service),
) -> AssetRead:
    """Get a single asset by ID."""
    try:
        asset = service.get_asset(asset_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return asset


@router.delete(
    "/api/assets/{asset_id}",
    status_code=204,
)
def delete_asset(
    asset_id: UUID,
    service: AssetService = Depends(get_asset_service),
) -> Response:
    """Delete an asset by ID."""
    try:
        service.delete_asset(asset_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return Response(status_code=204)
