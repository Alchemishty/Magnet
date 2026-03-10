# QA Checklist: feat/s3-integration

Generated: 2026-03-11
Branch: feat/s3-integration
Changes: 16 files changed, 775 insertions, 60 deletions

## Change-Specific QA

### S3Client

- [ ] With MinIO running, S3Client auto-creates bucket on first use if it doesn't exist
- [ ] `upload_file` uploads a local file to S3 and returns the s3_key
- [ ] `download_file` downloads an S3 object to a local path and returns the path
- [ ] `generate_presigned_upload_url` returns a valid PUT presigned URL with correct content type
- [ ] `generate_presigned_download_url` returns a valid GET presigned URL
- [ ] `delete_object` removes the object from S3
- [ ] `head_object` returns metadata for existing objects, None for missing
- [ ] `get_s3_client()` raises ValueError when S3_BUCKET env var is missing
- [ ] `get_s3_client()` works with all four env vars set (S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET)

### Presigned Upload Endpoint

- [ ] POST `/api/projects/{project_id}/assets/presigned-upload` with valid body returns 200 with `upload_url` and `s3_key`
- [ ] Returned `s3_key` follows pattern `uploads/{project_id}/{uuid}_{filename}`
- [ ] Rejects invalid `asset_type` with 422
- [ ] Using the returned presigned URL, a client can PUT a file directly to S3/MinIO

### Presigned Download Endpoint

- [ ] GET `/api/assets/{asset_id}/download-url` returns 200 with `download_url`
- [ ] Returns 404 for non-existent asset_id
- [ ] Using the returned presigned URL, a client can GET the file from S3/MinIO

### Asset Deletion S3 Cleanup

- [ ] DELETE `/api/assets/{asset_id}` removes the DB record AND the S3 object
- [ ] If S3 delete fails, the API still returns 204 (best-effort cleanup)
- [ ] If S3 is not configured, delete still works (DB-only)

### Video Agent COMPOSE

- [ ] COMPOSE scenes download the actual asset from S3 instead of writing a placeholder
- [ ] If S3Client is not provided, COMPOSE falls back to placeholder (no crash)

### Video Agent POST-PROCESS

- [ ] After FFmpeg assembly, the rendered video is uploaded to S3 via S3Client
- [ ] The s3_key follows pattern `renders/{job_id}/output.mp4`
- [ ] If S3Client is not provided, returns local file path (no crash)

### Celery Task

- [ ] The render Celery task injects S3Client into VideoAgent
- [ ] If S3 env vars are missing, task still runs with S3Client=None

## Domain QA

### Asset
- [ ] Full asset lifecycle: presigned upload URL -> PUT file -> create asset record -> list assets -> download URL -> delete (cleans S3)
- [ ] Asset types (gameplay, screenshot, logo, character, audio) all accepted by presigned upload

### RenderJob
- [ ] End-to-end: create brief -> trigger production -> Celery task runs Video Agent with S3 -> output_s3_key populated on job

## Regression
- [ ] Existing tests pass (run: `cd packages/api && pytest`)
- [ ] Static analysis clean (run: `cd packages/api && ruff check .`)
- [ ] Enforcement rules pass (run: `bash enforcement/run-all.sh`)
- [ ] Web tests pass (run: `cd packages/web && npx vitest run`)
- [ ] Web lint clean (run: `cd packages/web && npx eslint .`)
