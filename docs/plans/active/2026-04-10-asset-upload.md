# Asset Upload Screen Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an asset upload section to the project detail page where users can drag-and-drop files (gameplay video, screenshots, logos, character art, audio), upload them via presigned S3 URLs, and view/delete uploaded assets.

**Architecture:** Extends the existing project detail page with a new `AssetUpload` component. Uses the presigned URL flow: frontend requests a presigned PUT URL from the API, uploads the file directly to S3, then registers the asset in the database. React Query manages asset list state. A drop zone component handles drag-and-drop with upload progress tracking.

**Tech Stack:** Next.js 14, TypeScript, Tailwind + shadcn/ui, TanStack React Query, vitest

---

## Assumptions
- Backend asset endpoints are complete and working (`POST presigned-upload`, `POST assets`, `GET assets`, `DELETE assets/{id}`, `GET download-url`)
- S3/MinIO is configured in the backend (presigned URLs work)
- The existing API client pattern (`lib/api/client.ts`) is reused; S3 PUT upload uses raw `fetch` since it bypasses the API

## Open Questions
- None — backend is complete, frontend patterns are established.

## Context and Orientation
- **Files to read before starting:** `packages/api/app/schemas/asset.py` (backend types), `packages/web/lib/api/client.ts` (API client pattern), `packages/web/app/projects/[id]/page.tsx` (page to modify)
- **Patterns to follow:** `docs/conventions/naming.md` (kebab-case files, PascalCase components), `docs/conventions/import-ordering.md` (@/ alias)
- **Similar existing code:** `lib/api/projects.ts` + `lib/hooks/use-projects.ts` + `components/game-profile-form.tsx` — same fetch/hook/component pattern

## Steps

### Step 1: Create TypeScript types for Asset

**Files:**
- Create: `packages/web/lib/types/asset.ts`

**Tests:** No unit tests — type-only file verified by build.

**What to do:** Create TypeScript interfaces mirroring the backend Pydantic schemas:
- `AssetType` — union type: `"gameplay" | "screenshot" | "logo" | "character" | "audio"`
- `Asset` — mirrors `AssetRead` (id, project_id, asset_type, s3_key, filename, content_type, size_bytes, duration_ms, width, height, metadata_, created_at, updated_at)
- `AssetCreate` — mirrors `AssetCreateBody` (asset_type, s3_key, filename, content_type, size_bytes, duration_ms, width, height, metadata_)
- `PresignedUploadRequest` — { filename, content_type, asset_type }
- `PresignedUploadResponse` — { upload_url, s3_key }

**Verify:** `cd packages/web && npx tsc --noEmit`

---

### Step 2: Build asset API client functions

**Files:**
- Create: `packages/web/lib/api/assets.ts`
- Test: `packages/web/__tests__/unit/api-assets.test.ts`

**Tests:** Test that each function calls the correct API client method with the right path and arguments. Mock `@/lib/api/client`.

**What to do:** Create typed API functions following the `lib/api/projects.ts` pattern:
- `requestPresignedUpload(projectId, data: PresignedUploadRequest)` → `apiPost<PresignedUploadResponse>`
- `uploadFileToS3(uploadUrl: string, file: File)` → raw `fetch` PUT with file body and Content-Type header (this does NOT go through the API client — it's a direct S3 call)
- `createAsset(projectId, data: AssetCreate)` → `apiPost<Asset>`
- `listAssets(projectId, assetType?: AssetType)` → `apiGet<Asset[]>` with optional query param
- `deleteAsset(assetId: string)` → `apiDelete`
- `getDownloadUrl(assetId: string)` → `apiGet<{ download_url: string }>`

**Verify:** `cd packages/web && npx vitest run __tests__/unit/api-assets.test.ts`

---

### Step 3: Create React Query hooks for assets

**Files:**
- Create: `packages/web/lib/hooks/use-assets.ts`
- Test: `packages/web/__tests__/unit/use-assets.test.tsx`

**Tests:** Test `useAssets` returns data from `listAssets`. Test `useUploadAsset` calls the presigned flow. Test `useDeleteAsset` calls `deleteAsset` and invalidates the query.

**What to do:** Create hooks following the `lib/hooks/use-projects.ts` pattern:
- `useAssets(projectId: string, assetType?: AssetType)` — useQuery wrapping `listAssets`
- `useUploadAsset(projectId: string)` — useMutation that orchestrates the 3-step upload flow: (1) request presigned URL, (2) PUT file to S3, (3) register asset. Returns progress state. Invalidates `["assets"]` on success.
- `useDeleteAsset()` — useMutation wrapping `deleteAsset`, invalidates `["assets"]`

The `useUploadAsset` mutation function accepts `{ file: File, assetType: AssetType }` and chains the three API calls internally.

**Verify:** `cd packages/web && npx vitest run __tests__/unit/use-assets.test.tsx`

---

### Step 4: Build the drop zone component

**Files:**
- Create: `packages/web/components/drop-zone.tsx`
- Test: `packages/web/__tests__/unit/drop-zone.test.tsx`

**Tests:** Test that the component renders the drop area text. Test that clicking triggers a file input. Test that the `onFiles` callback is called when files are selected.

**What to do:** Create a reusable `DropZone` component:
- Props: `onFiles: (files: File[]) => void`, `accept?: string` (MIME types), `disabled?: boolean`
- Visual: dashed border area with icon (lucide `Upload`), "Drag files here or click to browse" text
- Drag state: highlight border on dragover
- Uses a hidden `<input type="file" multiple>` triggered by click
- Handles both drag-and-drop (`onDrop`) and click-to-browse
- Does NOT handle upload logic — just emits files to parent

**Verify:** `cd packages/web && npx vitest run __tests__/unit/drop-zone.test.tsx`

---

### Step 5: Build the asset list component

**Files:**
- Create: `packages/web/components/asset-list.tsx`
- Test: `packages/web/__tests__/unit/asset-list.test.tsx`

**Tests:** Test that it renders asset filenames. Test that it shows asset type badges. Test that delete button is present.

**What to do:** Create an `AssetList` component:
- Props: `projectId: string`
- Uses `useAssets(projectId)` to fetch and display assets
- Shows each asset as a row/card with: filename, asset type badge, file size (formatted), created date, delete button
- Delete button uses `useDeleteAsset` with confirmation
- Loading and empty states
- Icon per asset type (lucide: `Video` for gameplay, `Image` for screenshot, `Palette` for logo, `User` for character, `Music` for audio)

**Verify:** `cd packages/web && npx vitest run __tests__/unit/asset-list.test.tsx`

---

### Step 6: Build the asset upload section component

**Files:**
- Create: `packages/web/components/asset-upload.tsx`
- Test: `packages/web/__tests__/unit/asset-upload.test.tsx`

**Tests:** Test that the component renders the drop zone and asset type selector. Test that the asset list is rendered below.

**What to do:** Create an `AssetUpload` component that composes DropZone + AssetList:
- Props: `projectId: string`
- Contains: asset type selector (dropdown with the 5 types), DropZone, upload progress indicator, AssetList below
- When files are dropped: auto-detect asset type from MIME (video/* → gameplay, image/* → screenshot, audio/* → audio) with the selector as override
- Calls `useUploadAsset` for each file
- Shows upload progress per file (pending/uploading/done/error)
- Wrapped in a Card with "Assets" title
- Upload state tracked in local state: `{ file: File, status: "uploading" | "done" | "error", error?: string }[]`

**Verify:** `cd packages/web && npx vitest run __tests__/unit/asset-upload.test.tsx && npm run build`

---

### Step 7: Add asset upload section to project detail page

**Files:**
- Modify: `packages/web/app/projects/[id]/page.tsx`

**Tests:** No new test file — existing page is a thin wrapper.

**What to do:** Import `AssetUpload` and add it below `GameProfileForm` on the project detail page. Add a `Separator` between the two sections.

**Verify:** `cd packages/web && npm run build`

---

## Validation
After all steps:
1. `cd packages/web && npx vitest run` — all tests pass
2. `cd packages/web && npx eslint .` — no lint errors
3. `cd packages/web && npm run build` — build succeeds
4. `bash enforcement/run-all.sh` — all enforcement checks pass
5. Navigate to `/projects/[id]` — game profile form + asset upload section visible
6. Drop a file → presigned URL requested → file uploaded to S3 → asset appears in list
7. Delete an asset → removed from list

## Decision Log
(Populated during implementation)
