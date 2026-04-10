# Production & Preview Screen Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a production section to the project detail page where users can trigger video rendering from approved briefs, monitor real-time progress via WebSocket, and preview completed videos with an HTML5 player.

**Architecture:** Extends the project detail page with a production section. Uses the existing job CRUD endpoints and the `useBriefProgress` WebSocket hook for real-time progress. Each approved brief gets a "Produce" button that creates a render job. Job status is displayed with a progress bar. Completed jobs show a video preview player using presigned S3 download URLs.

**Tech Stack:** Next.js 14, TypeScript, Tailwind + shadcn/ui, TanStack React Query, vitest

---

## Assumptions
- Backend job endpoints are complete (`POST jobs`, `GET jobs`, `GET job`, `PATCH job`)
- WebSocket progress endpoint works (`/ws/briefs/{brief_id}/progress`)
- The `useBriefProgress` hook already exists and handles reconnection
- `ProgressEvent` type already exists in `lib/types/progress.ts`
- Completed jobs have `output_s3_key` pointing to the rendered video in S3
- The asset download URL endpoint (`GET /api/assets/{id}/download-url`) pattern can be reused for job output (backend has `GET /api/jobs/{id}` which includes `output_s3_key`)

## Open Questions
- None — backend is complete, WebSocket hook exists, patterns are established.

## Context and Orientation
- **Files to read before starting:** `packages/api/app/schemas/job.py` (backend types), `packages/web/lib/useBriefProgress.ts` (existing WebSocket hook), `packages/web/lib/types/progress.ts` (existing ProgressEvent type)
- **Patterns to follow:** `docs/conventions/naming.md`, `docs/conventions/import-ordering.md`
- **Similar existing code:** `lib/api/briefs.ts` + `lib/hooks/use-briefs.ts` + `components/concept-review.tsx`

## Steps

### Step 1: Create TypeScript types for RenderJob

**Files:**
- Create: `packages/web/lib/types/job.ts`

**Tests:** No unit tests — type-only file verified by build.

**What to do:** Create TypeScript interfaces:
- `JobStatus` — union type: `"queued" | "rendering" | "done" | "failed"`
- `Job` — mirrors `JobRead` (id, brief_id, status, composition, output_s3_key, render_duration_ms, error_message, celery_task_id, created_at, updated_at)
- `JobCreate` — mirrors `JobCreateBody` (status?: JobStatus, composition?: object)

**Verify:** `cd packages/web && npx tsc --noEmit`

---

### Step 2: Build job API client functions

**Files:**
- Create: `packages/web/lib/api/jobs.ts`
- Test: `packages/web/__tests__/unit/api-jobs.test.ts`

**Tests:** Test each function calls the correct API method with the right path. Mock `@/lib/api/client`.

**What to do:** Create typed API functions:
- `createJob(briefId: string, data?: JobCreate)` → `apiPost<Job>` to `/api/briefs/{briefId}/jobs`
- `listJobs(briefId: string, status?: JobStatus)` → `apiGet<Job[]>` with optional status query param
- `getJob(jobId: string)` → `apiGet<Job>`

**Verify:** `cd packages/web && npx vitest run __tests__/unit/api-jobs.test.ts`

---

### Step 3: Create React Query hooks for jobs

**Files:**
- Create: `packages/web/lib/hooks/use-jobs.ts`
- Test: `packages/web/__tests__/unit/use-jobs.test.tsx`

**Tests:** Test `useJobs` returns data from `listJobs`. Test `useCreateJob` calls `createJob` and invalidates. Test `useJob` fetches a single job.

**What to do:** Create hooks:
- `useJobs(briefId: string)` — useQuery with key `["jobs", "list", briefId]`
- `useJob(jobId: string)` — useQuery with key `["jobs", "detail", jobId]`, polls every 5s when status is "queued" or "rendering" (refetchInterval)
- `useCreateJob(briefId: string)` — useMutation calling `createJob`, invalidates `["jobs"]` and updates brief status to "producing" via `useUpdateBrief`

**Verify:** `cd packages/web && npx vitest run __tests__/unit/use-jobs.test.tsx`

---

### Step 4: Build the job progress card component

**Files:**
- Create: `packages/web/components/job-card.tsx`
- Test: `packages/web/__tests__/unit/job-card.test.tsx`

**Tests:** Test renders job status badge. Test renders progress bar when rendering. Test renders "Done" state with duration. Test renders error message when failed.

**What to do:** Create a `JobCard` component:
- Props: `job: Job`, `progress?: ProgressEvent` (optional real-time data from WebSocket)
- Status badge (secondary for queued, default for rendering, primary for done, destructive for failed)
- Progress bar: when rendering, show a horizontal bar at `progress_pct%` with phase label (e.g., "PREPARE — 40%")
- Use Tailwind for the progress bar (no extra dependency): outer div with bg-muted, inner div with bg-primary and width percentage
- Done state: show render duration (formatted as seconds), "View" button
- Failed state: show error message in destructive text
- Queued state: show "Waiting..." with muted text

**Verify:** `cd packages/web && npx vitest run __tests__/unit/job-card.test.tsx`

---

### Step 5: Build the video preview component

**Files:**
- Create: `packages/web/components/video-preview.tsx`
- Test: `packages/web/__tests__/unit/video-preview.test.tsx`

**Tests:** Test renders video element when URL is provided. Test renders placeholder when no URL.

**What to do:** Create a `VideoPreview` component:
- Props: `jobId: string` (fetches download URL), or `url: string | null` for direct usage
- When jobId provided: fetch the job, if done and has output_s3_key, construct a download URL via `getJob` + `apiGet` pattern (the backend returns output_s3_key on the job, but we need a presigned URL — use a new `getJobDownloadUrl` function or construct from the S3 key)
- Simpler approach: accept `outputS3Key: string | null` as prop, and have the parent fetch the presigned URL
- HTML5 `<video>` element with controls, dark background, responsive sizing (max-w-2xl, aspect-video)
- Poster/placeholder when no video: dark area with play icon and "No video yet" text

**Verify:** `cd packages/web && npx vitest run __tests__/unit/video-preview.test.tsx`

---

### Step 6: Build the production section component

**Files:**
- Create: `packages/web/components/production.tsx`
- Test: `packages/web/__tests__/unit/production.test.tsx`

**Tests:** Test renders "Production" title. Test shows brief selector or list of approved briefs. Test shows "Produce Video" button.

**What to do:** Create a `Production` component:
- Props: `projectId: string`
- Wrapped in Card with "Production" title
- Fetches approved briefs via `useBriefs(projectId, "approved")`
- For each approved brief: show brief summary (hook type + narrative) with a "Produce Video" button
- When "Produce Video" is clicked: calls `useCreateJob` to start a render job
- Below each brief: show its jobs via `useJobs(briefId)` as JobCard components
- Connect WebSocket via `useBriefProgress(briefId)` — merge progress events into job cards
- When a job is done: show VideoPreview below the job card
- Empty state: "No approved briefs. Approve briefs in the Concept Review section."

**Verify:** `cd packages/web && npx vitest run __tests__/unit/production.test.tsx && npm run build`

---

### Step 7: Add production section to project detail page

**Files:**
- Modify: `packages/web/app/projects/[id]/page.tsx`

**Tests:** No new test file.

**What to do:** Import `Production` and add it below `ConceptReview` with a `Separator`.

**Verify:** `cd packages/web && npm run build`

---

## Validation
After all steps:
1. `cd packages/web && npx vitest run` — all tests pass
2. `cd packages/web && npx eslint .` — no lint errors
3. `cd packages/web && npm run build` — build succeeds
4. `bash enforcement/run-all.sh` — all enforcement checks pass
5. Navigate to `/projects/[id]` — all sections visible (profile, assets, concepts, production)
6. Approve a brief → "Produce Video" button appears in Production section
7. Click "Produce Video" → job created, real-time progress via WebSocket
8. Job completes → video preview appears with HTML5 player

## Decision Log
(Populated during implementation)
