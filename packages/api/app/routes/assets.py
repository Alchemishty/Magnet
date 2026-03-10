"""FastAPI routes for Asset operations."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.errors import DatabaseError, NotFoundError
from app.repositories.s3_client import S3Client
from app.routes.dependencies import get_asset_service, get_s3_client
from app.schemas.asset import (
    AssetCreate,
    AssetCreateBody,
    AssetRead,
    AssetType,
    PresignedUploadRequest,
    PresignedUploadResponse,
)
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
    asset_type: AssetType | None = Query(default=None),
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


@router.post(
    "/api/projects/{project_id}/assets/presigned-upload",
    response_model=PresignedUploadResponse,
)
def presigned_upload(
    project_id: UUID,
    body: PresignedUploadRequest,
    s3: S3Client = Depends(get_s3_client),
) -> PresignedUploadResponse:
    """Generate a presigned URL for direct-to-S3 asset upload."""
    s3_key = f"uploads/{project_id}/{uuid4()}_{body.filename}"
    upload_url = s3.generate_presigned_upload_url(s3_key, body.content_type)
    return PresignedUploadResponse(upload_url=upload_url, s3_key=s3_key)


@router.get("/api/assets/{asset_id}/download-url")
def download_url(
    asset_id: UUID,
    service: AssetService = Depends(get_asset_service),
    s3: S3Client = Depends(get_s3_client),
) -> dict:
    """Generate a presigned download URL for an asset."""
    try:
        asset = service.get_asset(asset_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    url = s3.generate_presigned_download_url(asset.s3_key)
    return {"download_url": url}
