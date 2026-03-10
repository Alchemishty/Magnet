# S3 Integration Implementation Plan

**Goal:** Provide complete S3/MinIO storage integration — presigned upload/download URLs, asset download for COMPOSE scenes, S3 cleanup on delete, and a reusable S3Client class that replaces inline boto3 usage.
**Architecture:** A standalone `S3Client` class in the repositories layer wraps all boto3 operations. It is injected via FastAPI `Depends` into services that need storage access. The existing asset routes gain presigned URL endpoints. The Video Agent's inline boto3 code is replaced with S3Client injection.

## Assumptions
- boto3 is already in dependencies (confirmed in pyproject.toml)
- MinIO is already in docker-compose and env vars are defined in .env.example
- The Asset model already has `s3_key`, `filename`, `content_type` fields
- No database migration is needed — all required columns exist

## Open Questions
- None — design decisions resolved in brainstorming (single S3Client class, repositories layer placement)

## Context and Orientation
- **Files to read before starting:** `app/repositories/asset_repository.py`, `app/services/asset_service.py`, `app/routes/assets.py`, `app/routes/dependencies.py`, `app/agents/video_agent.py`
- **Patterns to follow:** Repository pattern from `docs/conventions/session-lifecycle.md`, error handling from `docs/conventions/error-handling.md`, dependency injection pattern from `app/routes/dependencies.py`
- **Similar existing code:** `app/providers/llm/` for factory pattern, `app/routes/dependencies.py` for `Depends` injection

## Steps

### Step 1: Create S3Client class
**Files:** `packages/api/app/repositories/s3_client.py`
**Tests:** `packages/api/tests/unit/repositories/test_s3_client.py`
**What to do:** Create `S3Client` with these methods:
- `__init__(self, endpoint_url, access_key, secret_key, bucket)` — stores config, creates boto3 client, calls `_ensure_bucket()` to create bucket if missing
- `upload_file(self, local_path: str, s3_key: str) -> str` — uploads a local file, returns the s3_key
- `download_file(self, s3_key: str, local_path: str) -> str` — downloads to local path, returns local_path
- `generate_presigned_upload_url(self, s3_key: str, content_type: str, expires_in: int = 3600) -> str` — presigned PUT URL
- `generate_presigned_download_url(self, s3_key: str, expires_in: int = 3600) -> str` — presigned GET URL
- `delete_object(self, s3_key: str) -> None` — deletes an object
- `head_object(self, s3_key: str) -> dict | None` — returns metadata dict or None if not found

Add a factory function `get_s3_client()` that reads `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET` from env vars and returns an `S3Client` instance. Raise `ValueError` if `S3_BUCKET` is not set.

Add `StorageError` to `app/errors.py` for wrapping boto3 exceptions at the boundary.

Tests: mock `boto3.client` and verify each method calls the right boto3 API. Test `_ensure_bucket()` handles both "bucket exists" and "bucket doesn't exist" cases. Test factory raises `ValueError` when env vars missing.
**Verify:** `cd packages/api && pytest tests/unit/repositories/test_s3_client.py -x`

### Step 2: Add presigned URL schemas
**Files:** `packages/api/app/schemas/asset.py`
**Tests:** `packages/api/tests/unit/schemas/test_asset.py`
**What to do:** Add two new Pydantic models:
- `PresignedUploadRequest` — fields: `filename: str`, `content_type: str`, `asset_type: AssetType`
- `PresignedUploadResponse` — fields: `upload_url: str`, `s3_key: str`, `fields: dict` (empty for PUT-based presigned URLs, but present for future POST policy support)

Tests: validate schema creation and serialization.
**Verify:** `cd packages/api && pytest tests/unit/schemas/test_asset.py -x`

### Step 3: Add presigned URL endpoints to asset routes
**Files:** `packages/api/app/routes/assets.py`, `packages/api/app/routes/dependencies.py`
**Tests:** `packages/api/tests/unit/routes/test_asset_routes.py`
**What to do:**
1. In `dependencies.py`, add `get_s3_client()` dependency that yields an `S3Client` instance (import `get_s3_client` from `app.repositories.s3_client`). Handle `ValueError` for missing config.
2. In `assets.py`, add two new endpoints:
   - `POST /api/projects/{project_id}/assets/presigned-upload` — accepts `PresignedUploadRequest`, generates an s3_key like `uploads/{project_id}/{uuid}_{filename}`, returns `PresignedUploadResponse` with the presigned PUT URL
   - `GET /api/assets/{asset_id}/download-url` — looks up the asset, generates a presigned download URL, returns `{"download_url": "..."}`
3. Wire `S3Client` into these endpoints via `Depends(get_s3_client)`.

Tests: mock `S3Client` and `AssetService`, verify endpoints return correct response shapes and status codes. Test 404 for missing asset on download-url. Test 500 when S3 config is missing.
**Verify:** `cd packages/api && pytest tests/unit/routes/test_asset_routes.py -x`

### Step 4: Wire S3 cleanup into asset deletion
**Files:** `packages/api/app/services/asset_service.py`
**Tests:** `packages/api/tests/unit/services/test_asset_service.py`
**What to do:**
1. `AssetService.__init__` accepts an optional `s3_client: S3Client | None = None` parameter.
2. `delete_asset()` — after successful DB delete, if `s3_client` is set, call `s3_client.delete_object(asset.s3_key)`. Log a warning if S3 delete fails (best-effort — don't fail the API call over orphaned S3 objects).
3. Update `get_asset_service` in `dependencies.py` to inject `S3Client` into `AssetService`.

Tests: verify delete calls `s3_client.delete_object()` with the asset's s3_key. Verify delete still works when s3_client is None. Verify S3 failure doesn't raise (logs warning instead).
**Verify:** `cd packages/api && pytest tests/unit/services/test_asset_service.py -x`

### Step 5: Wire S3 download into Video Agent COMPOSE
**Files:** `packages/api/app/agents/video_agent.py`
**Tests:** `packages/api/tests/unit/agents/test_video_agent_prepare.py`
**What to do:**
1. `VideoAgent.__init__` accepts an `s3_client: S3Client | None = None` parameter (store as `self._s3`).
2. Replace the placeholder in `_prepare_compose()`: if `self._s3` is set, call `self._s3.download_file(asset.s3_key, output_path)` instead of writing `b"compose_placeholder"`. If `self._s3` is None, fall back to existing placeholder behavior with a warning log.
3. Remove the direct `import boto3` from video_agent.py.
4. Replace inline boto3 usage in `post_process()` with `self._s3.upload_file(output_path, s3_key)`. If `self._s3` is None, log warning and return local path (existing behavior).

Tests: mock `S3Client` and verify `_prepare_compose` calls `download_file`. Verify `post_process` calls `upload_file` via S3Client. Verify fallback when s3_client is None.
**Verify:** `cd packages/api && pytest tests/unit/agents/ -x`

### Step 6: Update dependencies and Celery task wiring
**Files:** `packages/api/app/routes/dependencies.py`, `packages/api/app/tasks/render.py`
**Tests:** `packages/api/tests/unit/routes/test_job_routes.py`
**What to do:**
1. Update `get_concept_agent` or any agent factory in `dependencies.py` if needed.
2. In `tasks/render.py`, where the VideoAgent is instantiated for background task execution, inject an `S3Client` instance via `get_s3_client()`. The Celery task runs outside FastAPI's DI, so call `get_s3_client()` directly.
3. Verify the render task creates the S3Client and passes it to VideoAgent.

Tests: verify the Celery task passes S3Client to VideoAgent constructor.
**Verify:** `cd packages/api && pytest tests/unit/ -x`

## Validation
- Run full test suite: `cd packages/api && pytest`
- Run linter: `cd packages/api && ruff check .`
- Run enforcement: `bash enforcement/run-all.sh`
- Expected: all tests pass, no lint errors, no enforcement violations
- Presigned upload and download endpoints return valid response schemas
- Asset deletion triggers S3 cleanup
- Video Agent COMPOSE downloads from S3 instead of writing placeholder
- Video Agent POST-PROCESS uploads via S3Client instead of inline boto3

## Decision Log
