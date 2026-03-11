# Frontend Dashboard — Foundation + Project Setup

## Design Document

**Date:** 2026-03-11
**Status:** Approved
**Scope:** Foundation infrastructure (Tailwind, shadcn/ui, API client, layout) + Project Setup screen

---

## Decisions

- **Scope:** Foundation + one screen (Project Setup). Other screens follow in later PRs.
- **Auth:** Stubbed with hardcoded user ID. Clerk integration deferred.
- **Theme:** Dark theme as default via CSS variables.
- **Data fetching:** React Query (TanStack Query) only. Zustand deferred until multi-screen UI state is needed.
- **Approach:** Page-first — Project Setup as simple page flow, not a wizard.

---

## 1. Foundation Infrastructure

### Tailwind + shadcn/ui
- Tailwind CSS 3.x with PostCSS and `tailwind.config.ts`
- Dark theme default via CSS variables in `globals.css`
- shadcn/ui initialized, components in `components/ui/`
- Initial components: Button, Input, Label, Card, Textarea, Select, Badge, Separator

### API Client Layer
- `lib/api/client.ts` — fetch wrapper with base URL from `NEXT_PUBLIC_API_URL`, JSON headers, error handling
- `lib/api/projects.ts` — typed functions for project CRUD
- `lib/api/game-profiles.ts` — typed functions for game profile CRUD
- `lib/types/` — TypeScript interfaces matching backend Pydantic schemas

### React Query
- QueryClientProvider wrapping app in layout.tsx
- Custom hooks in `lib/hooks/` for projects and game profiles

### Layout Shell
- Collapsible dark sidebar (left) with nav items: Projects, Creative Library (disabled), Settings (disabled)
- Top area: "Magnet" branding + placeholder user avatar
- Main content area to the right
- Responsive: sidebar collapses to icons on small screens

### Routing
```
/                       → redirect to /projects
/projects               → projects list
/projects/new           → create project form
/projects/[id]          → project detail + game profile form
```

---

## 2. Project Setup Screen

### /projects — Projects List
- Card grid showing project name, status badge, created date
- "New Project" button → /projects/new
- Paginated via React Query

### /projects/new — Create Project
- Form with project name field + "Create Project" button
- On submit: POST /api/projects with stubbed user_id
- On success: redirect to /projects/[id]

### /projects/[id] — Project Detail + Game Profile
- Header: project name + status badge
- Game Profile form fields:
  - Genre (text input)
  - Target Audience (text input)
  - Core Mechanics (tag-style multi-input)
  - Art Style (text input)
  - Brand Guidelines (textarea)
  - Competitors (tag-style multi-input)
  - Key Selling Points (tag-style multi-input)
- "Save Profile" → POST (create) or PATCH (update)
- Success feedback on save
- "Generate Concepts" button (disabled, coming soon)

### Error Handling
- Form validation on required fields
- API error display (toast or inline)
- Loading states via React Query isPending/isError

---

## 3. Testing Strategy

- API client functions: unit tests with mocked fetch
- React components: component tests with React Testing Library
- React Query hooks: hook tests
- Existing WebSocket hook tests remain unchanged

---

## 4. Backend Endpoints Consumed

```
POST   /api/projects                         → create project
GET    /api/projects?user_id=...             → list projects
GET    /api/projects/{id}                    → get project
PATCH  /api/projects/{id}                    → update project
DELETE /api/projects/{id}                    → delete project
POST   /api/projects/{id}/game-profile       → create game profile
GET    /api/projects/{id}/game-profile       → get game profile
PATCH  /api/projects/{id}/game-profile       → update game profile
```

All endpoints return JSON with Pydantic-validated schemas. Pagination via offset/limit query params.
