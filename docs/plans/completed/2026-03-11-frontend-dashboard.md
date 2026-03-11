# Frontend Dashboard — Foundation + Project Setup

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up the frontend foundation (Tailwind, shadcn/ui, API client, layout shell) and build the Project Setup screen with CRUD operations.

**Architecture:** Next.js 14 App Router with React Query for server state. Thin fetch-based API client talks to the FastAPI backend. Dark-themed UI via Tailwind + shadcn/ui. Stubbed auth with hardcoded user ID.

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS 3, shadcn/ui, TanStack React Query, vitest

---

## Context and Orientation

- **Conventions:** TypeScript files use `kebab-case.ts(x)`. Components use `PascalCase`. Imports use `@/` alias. See `docs/conventions/naming.md` and `docs/conventions/import-ordering.md`.
- **Existing code:** `lib/useBriefProgress.ts` and `lib/types/progress.ts` exist — don't break them. Tests in `__tests__/unit/`.
- **Backend schemas:** `packages/api/app/schemas/project.py` defines `ProjectCreate`, `ProjectRead`, `ProjectUpdate`, `GameProfileCreateBody`, `GameProfileRead`, `GameProfileUpdate`.
- **Enforcement:** Files must stay under 300 lines. No unused imports.
- **Test commands:** `cd packages/web && npx vitest run`
- **Lint commands:** `cd packages/web && npx eslint .`

## Open Questions

- None — all decisions made during brainstorming.

## Decision Log

- Used getBaseUrl() function instead of top-level const for testability (Step 4)
- Installed tailwindcss v3 (not v4) for PostCSS compatibility (Step 1)
- Added @radix-ui/react-slot for Button asChild prop (Step 2)
- Excluded vitest.config.ts from tsconfig.json to fix vite type conflict during build

---

## Steps

### Step 1: Install Tailwind CSS and configure dark theme

**What to do:** Install Tailwind CSS 3 with PostCSS and autoprefixer. Create config files. Set up `globals.css` with dark theme CSS variables matching shadcn/ui conventions. Update `layout.tsx` to import globals.css and apply the dark class.

**Files:**
- Create: `packages/web/tailwind.config.ts`
- Create: `packages/web/postcss.config.js`
- Create: `packages/web/app/globals.css`
- Modify: `packages/web/app/layout.tsx`
- Modify: `packages/web/package.json` (new deps)

**Tests:** No unit tests — verified by build.

**Verify:** `cd packages/web && npm run build`

---

### Step 2: Initialize shadcn/ui and install base components

**What to do:** Initialize shadcn/ui with the `new-york` style and dark theme. Install components: button, input, label, card, textarea, badge, separator. These go into `components/ui/`.

**Files:**
- Create: `packages/web/components.json` (shadcn config)
- Create: `packages/web/lib/utils.ts` (cn helper)
- Create: `packages/web/components/ui/button.tsx`
- Create: `packages/web/components/ui/input.tsx`
- Create: `packages/web/components/ui/label.tsx`
- Create: `packages/web/components/ui/card.tsx`
- Create: `packages/web/components/ui/textarea.tsx`
- Create: `packages/web/components/ui/badge.tsx`
- Create: `packages/web/components/ui/separator.tsx`

**Tests:** No unit tests — these are vendored components.

**Verify:** `cd packages/web && npm run build`

---

### Step 3: Create TypeScript types matching backend schemas

**What to do:** Create TypeScript interfaces that mirror the backend Pydantic schemas for Project and GameProfile. These are the API contract types.

**Files:**
- Create: `packages/web/lib/types/project.ts`
- Create: `packages/web/lib/types/game-profile.ts`

**Tests:** No unit tests — type-only files verified by build.

**Verify:** `cd packages/web && npx tsc --noEmit`

Types to create:

```typescript
// lib/types/project.ts
export interface Project {
  id: string;
  user_id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface ProjectCreate {
  name: string;
  user_id: string;
}

export interface ProjectUpdate {
  name?: string;
  status?: string;
}
```

```typescript
// lib/types/game-profile.ts
export interface GameProfile {
  id: string;
  project_id: string;
  genre: string | null;
  target_audience: string | null;
  core_mechanics: string[] | null;
  art_style: string | null;
  brand_guidelines: Record<string, unknown> | null;
  competitors: string[] | null;
  key_selling_points: string[] | null;
  created_at: string;
  updated_at: string | null;
}

export interface GameProfileCreate {
  genre?: string | null;
  target_audience?: string | null;
  core_mechanics?: string[] | null;
  art_style?: string | null;
  brand_guidelines?: Record<string, unknown> | null;
  competitors?: string[] | null;
  key_selling_points?: string[] | null;
}

export type GameProfileUpdate = GameProfileCreate;
```

---

### Step 4: Build API client with fetch wrapper

**What to do:** Create a thin fetch wrapper (`api-client.ts`) that handles base URL, JSON headers, and error responses. Then create typed functions for projects and game-profiles. Write tests first.

**Files:**
- Create: `packages/web/lib/api/client.ts`
- Create: `packages/web/lib/api/projects.ts`
- Create: `packages/web/lib/api/game-profiles.ts`
- Test: `packages/web/__tests__/unit/api-client.test.ts`
- Test: `packages/web/__tests__/unit/api-projects.test.ts`

**Tests:**
- `api-client.test.ts`: test that `apiGet`/`apiPost`/`apiPatch`/`apiDelete` call fetch with correct URL, headers, and handle error responses
- `api-projects.test.ts`: test `createProject`, `listProjects`, `getProject` call the client correctly

**Verify:** `cd packages/web && npx vitest run`

API client shape:

```typescript
// lib/api/client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function apiGet<T>(path: string): Promise<T> { ... }
export async function apiPost<T>(path: string, body: unknown): Promise<T> { ... }
export async function apiPatch<T>(path: string, body: unknown): Promise<T> { ... }
export async function apiDelete(path: string): Promise<void> { ... }
```

```typescript
// lib/api/projects.ts
export async function createProject(data: ProjectCreate): Promise<Project> { ... }
export async function listProjects(userId: string, offset?: number, limit?: number): Promise<Project[]> { ... }
export async function getProject(id: string): Promise<Project> { ... }
export async function updateProject(id: string, data: ProjectUpdate): Promise<Project> { ... }
export async function deleteProject(id: string): Promise<void> { ... }
```

```typescript
// lib/api/game-profiles.ts
export async function createGameProfile(projectId: string, data: GameProfileCreate): Promise<GameProfile> { ... }
export async function getGameProfile(projectId: string): Promise<GameProfile> { ... }
export async function updateGameProfile(projectId: string, data: GameProfileUpdate): Promise<GameProfile> { ... }
```

---

### Step 5: Set up React Query provider and project hooks

**What to do:** Install `@tanstack/react-query`. Create a client-component provider wrapper. Create custom hooks for project and game-profile queries/mutations. Write tests.

**Files:**
- Modify: `packages/web/package.json` (add @tanstack/react-query)
- Create: `packages/web/components/providers.tsx`
- Modify: `packages/web/app/layout.tsx` (wrap with Providers)
- Create: `packages/web/lib/hooks/use-projects.ts`
- Create: `packages/web/lib/hooks/use-game-profile.ts`
- Test: `packages/web/__tests__/unit/use-projects.test.tsx`

**Tests:**
- `use-projects.test.tsx`: test `useProjects` returns data from listProjects, test `useCreateProject` calls createProject and invalidates query

**Verify:** `cd packages/web && npx vitest run`

Hook shapes:

```typescript
// lib/hooks/use-projects.ts
export function useProjects(userId: string) { ... }       // useQuery
export function useProject(id: string) { ... }             // useQuery
export function useCreateProject() { ... }                 // useMutation
export function useUpdateProject(id: string) { ... }       // useMutation
export function useDeleteProject() { ... }                 // useMutation
```

```typescript
// lib/hooks/use-game-profile.ts
export function useGameProfile(projectId: string) { ... }          // useQuery
export function useCreateGameProfile(projectId: string) { ... }    // useMutation
export function useUpdateGameProfile(projectId: string) { ... }    // useMutation
```

---

### Step 6: Build layout shell with sidebar navigation

**What to do:** Create the app shell with a dark sidebar, nav items, and main content area. The sidebar has "Magnet" branding at top, navigation links (Projects active, others disabled), and a stubbed user avatar at bottom. Use shadcn/ui components. Write a component test.

**Files:**
- Create: `packages/web/components/sidebar.tsx`
- Create: `packages/web/components/app-shell.tsx`
- Modify: `packages/web/app/layout.tsx` (use AppShell)
- Test: `packages/web/__tests__/unit/sidebar.test.tsx`

**Tests:**
- `sidebar.test.tsx`: test that sidebar renders "Magnet" branding, renders "Projects" nav link, renders disabled "Creative Library" item

**Verify:** `cd packages/web && npx vitest run && npm run build`

---

### Step 7: Build projects list page

**What to do:** Create the `/projects` page showing project cards with name, status badge, and created date. Include a "New Project" button linking to `/projects/new`. Use the `useProjects` hook. Also redirect `/` to `/projects`. Write component test.

**Files:**
- Modify: `packages/web/app/page.tsx` (redirect to /projects)
- Create: `packages/web/app/projects/page.tsx`
- Create: `packages/web/components/project-card.tsx`
- Test: `packages/web/__tests__/unit/project-card.test.tsx`

**Tests:**
- `project-card.test.tsx`: test that card renders project name, status badge, and formatted date

**Verify:** `cd packages/web && npx vitest run && npm run build`

---

### Step 8: Build create project page

**What to do:** Create `/projects/new` with a form containing project name input and "Create Project" button. On submit, call `useCreateProject` with a hardcoded `user_id` stub. On success, redirect to `/projects/[id]`. Write component test.

**Files:**
- Create: `packages/web/app/projects/new/page.tsx`
- Create: `packages/web/components/create-project-form.tsx`
- Create: `packages/web/lib/constants.ts` (STUB_USER_ID)
- Test: `packages/web/__tests__/unit/create-project-form.test.tsx`

**Tests:**
- `create-project-form.test.tsx`: test that form renders name input and submit button, test that submit calls createProject with correct data

**Verify:** `cd packages/web && npx vitest run && npm run build`

---

### Step 9: Build project detail page with game profile form

**What to do:** Create `/projects/[id]` page showing project header (name + status badge) and game profile form. The form has fields for genre, target audience, core mechanics (comma-separated input), art style, brand guidelines (textarea), competitors (comma-separated), key selling points (comma-separated). Save button creates or updates the profile. Write component test.

**Files:**
- Create: `packages/web/app/projects/[id]/page.tsx`
- Create: `packages/web/components/game-profile-form.tsx`
- Create: `packages/web/components/tag-input.tsx` (reusable comma-separated → array input)
- Test: `packages/web/__tests__/unit/game-profile-form.test.tsx`

**Tests:**
- `game-profile-form.test.tsx`: test that form renders all fields, test that submit calls createGameProfile with correct payload

**Verify:** `cd packages/web && npx vitest run && npm run build`
