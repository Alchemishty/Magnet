# Concept Review Screen Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a concept review section to the project detail page where users can trigger AI concept generation, browse generated creative briefs, edit/approve/discard them, and view scene plans.

**Architecture:** Extends the project detail page with a concept review section below assets. Uses the existing brief CRUD endpoints and the concept generation trigger. React Query manages brief list state. Each brief is displayed as a card with hook type, script, emotion, and scene plan summary. Users can edit fields inline, change status (draft→approved), or delete briefs.

**Tech Stack:** Next.js 14, TypeScript, Tailwind + shadcn/ui, TanStack React Query, vitest

---

## Assumptions
- Backend brief endpoints are complete (`POST concepts`, `GET briefs`, `GET/PATCH/DELETE brief`)
- Concept generation requires a GameProfile with genre and target_audience
- Scene plan is a JSON dict displayed read-only (editing scene plans is out of scope)
- The "Generate Concepts" button on the game profile form (currently disabled) will be replaced by one in this section

## Open Questions
- None — backend is complete, UI patterns are established.

## Context and Orientation
- **Files to read before starting:** `packages/api/app/schemas/brief.py` (backend types), `packages/web/lib/api/client.ts` (API client pattern), `packages/web/app/projects/[id]/page.tsx` (page to modify)
- **Patterns to follow:** `docs/conventions/naming.md`, `docs/conventions/import-ordering.md`
- **Similar existing code:** `lib/api/assets.ts` + `lib/hooks/use-assets.ts` + `components/asset-upload.tsx`

## Steps

### Step 1: Create TypeScript types for Brief

**Files:**
- Create: `packages/web/lib/types/brief.ts`

**Tests:** No unit tests — type-only file verified by build.

**What to do:** Create TypeScript interfaces mirroring the backend Pydantic schemas:
- `BriefStatus` — union type: `"draft" | "approved" | "producing" | "complete"`
- `Brief` — mirrors `BriefRead` (id, project_id, hook_type, narrative_angle, script, voiceover_text, target_emotion, cta_text, reference_ads, target_format, target_duration, status, generated_by, scene_plan, created_at, updated_at)
- `BriefUpdate` — all fields optional (hook_type, narrative_angle, script, voiceover_text, target_emotion, cta_text, status, scene_plan, target_format, target_duration)

**Verify:** `cd packages/web && npx tsc --noEmit`

---

### Step 2: Build brief API client functions

**Files:**
- Create: `packages/web/lib/api/briefs.ts`
- Test: `packages/web/__tests__/unit/api-briefs.test.ts`

**Tests:** Test each function calls the correct API method with the right path. Mock `@/lib/api/client`.

**What to do:** Create typed API functions:
- `generateConcepts(projectId: string)` → `apiPost<Brief[]>` to `/api/projects/{projectId}/concepts` with empty body
- `listBriefs(projectId: string, status?: BriefStatus)` → `apiGet<Brief[]>` with optional status query param
- `getBrief(briefId: string)` → `apiGet<Brief>`
- `updateBrief(briefId: string, data: BriefUpdate)` → `apiPatch<Brief>`
- `deleteBrief(briefId: string)` → `apiDelete`

**Verify:** `cd packages/web && npx vitest run __tests__/unit/api-briefs.test.ts`

---

### Step 3: Create React Query hooks for briefs

**Files:**
- Create: `packages/web/lib/hooks/use-briefs.ts`
- Test: `packages/web/__tests__/unit/use-briefs.test.tsx`

**Tests:** Test `useBriefs` returns data from `listBriefs`. Test `useGenerateConcepts` calls `generateConcepts`. Test `useUpdateBrief` calls `updateBrief` and invalidates. Test `useDeleteBrief`.

**What to do:** Create hooks:
- `useBriefs(projectId: string, status?: BriefStatus)` — useQuery with key `["briefs", "list", projectId, status]`
- `useGenerateConcepts(projectId: string)` — useMutation calling `generateConcepts`, invalidates `["briefs"]`
- `useUpdateBrief(briefId: string)` — useMutation calling `updateBrief`, invalidates `["briefs"]`
- `useDeleteBrief()` — useMutation calling `deleteBrief`, invalidates `["briefs"]`

**Verify:** `cd packages/web && npx vitest run __tests__/unit/use-briefs.test.tsx`

---

### Step 4: Build the brief card component

**Files:**
- Create: `packages/web/components/brief-card.tsx`
- Test: `packages/web/__tests__/unit/brief-card.test.tsx`

**Tests:** Test renders hook type, script excerpt, status badge. Test renders approve and delete buttons. Test approve button calls updateBrief with status "approved".

**What to do:** Create a `BriefCard` component displaying a single brief:
- Props: `brief: Brief`, `onApprove: () => void`, `onDelete: () => void`
- Card layout with:
  - Header: hook type badge + status badge + generated_by indicator
  - Body: narrative angle, script (truncated to ~3 lines with expand), target emotion, CTA text
  - Scene plan summary: count of scenes, list of strategies used (COMPOSE/GENERATE/RENDER)
  - Footer: target format + duration, Approve button (if draft), Delete button
- Approve button sets status to "approved" via callback
- Visual distinction for approved vs draft briefs (border color or opacity)

**Verify:** `cd packages/web && npx vitest run __tests__/unit/brief-card.test.tsx`

---

### Step 5: Build the concept review section component

**Files:**
- Create: `packages/web/components/concept-review.tsx`
- Test: `packages/web/__tests__/unit/concept-review.test.tsx`

**Tests:** Test renders "Creative Concepts" title. Test renders "Generate Concepts" button. Test shows empty state when no briefs. Test renders brief cards when briefs exist.

**What to do:** Create a `ConceptReview` component:
- Props: `projectId: string`
- Wrapped in Card with "Creative Concepts" title
- "Generate Concepts" button at top — calls `useGenerateConcepts`, shows loading state while generating
- Status filter: optional tabs or buttons for All / Draft / Approved (filter via `useBriefs` status param)
- Grid of `BriefCard` components for each brief
- Empty state: "No concepts yet. Generate concepts from your game profile."
- Loading and error states
- Wire approve/delete callbacks through hooks

**Verify:** `cd packages/web && npx vitest run __tests__/unit/concept-review.test.tsx && npm run build`

---

### Step 6: Add concept review section to project detail page

**Files:**
- Modify: `packages/web/app/projects/[id]/page.tsx`

**Tests:** No new test file.

**What to do:** Import `ConceptReview` and add it below `AssetUpload` with a `Separator` between them.

**Verify:** `cd packages/web && npm run build`

---

## Validation
After all steps:
1. `cd packages/web && npx vitest run` — all tests pass
2. `cd packages/web && npx eslint .` — no lint errors
3. `cd packages/web && npm run build` — build succeeds
4. `bash enforcement/run-all.sh` — all enforcement checks pass
5. Navigate to `/projects/[id]` — game profile + assets + concept review visible
6. Click "Generate Concepts" → briefs appear as cards
7. Click "Approve" on a brief → status changes to approved
8. Click delete → brief removed

## Decision Log
(Populated during implementation)
