---
name: create-plan
description: Generate implementation plans from feature descriptions
---

# Create Plan

Generate a structured, step-by-step implementation plan for a feature. The plan becomes the blueprint that `/implement-feature` executes autonomously.

## Input

Accept either:
- A **natural language feature description** (e.g., "Add user profile editing with avatar upload")
- A **reference to an issue or ticket** (e.g., a GitHub issue URL — fetch it via `gh issue view`)

If the input is vague, ask clarifying questions before proceeding. Do not generate a plan from ambiguous requirements.

---

## Step 1: Gather Context

Read these files from the project. Check if each exists before reading — skip any that are missing.

### From harness.yaml
Read `harness.yaml` at the project root. Extract:
- `stack` — language, framework, test framework, linter, ORM
- `commands` — all available commands (test, lint, build, etc.)
- `platforms` — what platforms the project targets
- `docs` — paths to architecture, conventions, domain, decisions
- `enforcement` — architectural rules that must be respected

### From project docs
Read each of these (using paths from `harness.yaml` -> `docs`, falling back to defaults):
- **Architecture doc** (`docs/architecture.md`) — project structure, layers, data flow
- **Conventions doc** (`docs/conventions.md`) — coding patterns, naming, imports, state management
- **Domain doc** (`docs/domain.md`) — business entities, relationships, domain rules
- **Decisions directory** (`docs/decisions/`) — read titles and status lines first, then drill into only the decisions relevant to this feature

### From memory
If a `memory/` directory exists, read its files. These contain cross-session learned patterns, recurring fixes, and user preferences that should inform the plan.

### Context budget during planning
Planning reads many files. To avoid bloating your context window before you even start writing the plan:
- For docs files: extract only the **sections relevant to this feature**, not the entire file
- For source files: if scanning a large file to understand its structure, keep only a summary (class names, method signatures, key patterns) — write full output to `scratch/` if needed
- For decisions/: read titles first, then drill into relevant ones only

### From git history
```bash
git log --oneline -20
```
Review the last 20 commits to understand:
- Commit message style and conventions
- Recent areas of change
- Current development velocity and focus

---

## Step 2: Analyze the Feature

With full project context loaded, break down the feature:

1. **Decompose into logical components** — What are the distinct pieces of work? Think in terms of: data model, business logic, API/UI layer, tests.

2. **Identify affected architectural layers** — Using the architecture doc, determine which layers this feature touches. Respect the dependency direction from `enforcement.import_direction`.

3. **Identify files to create or modify** — Be specific. List exact file paths using the project's established directory structure. If a new directory pattern is needed, note it explicitly.

4. **Identify required tests** — For each component, determine what tests are needed. Consider:
   - Unit tests for pure logic
   - Integration tests for cross-layer behavior
   - Widget/component tests for UI (if applicable)
   - What test helpers or fixtures might be needed

5. **Identify dependencies between steps** — Which steps must come before others? Order by dependency: foundational pieces first (models, then services, then UI).

6. **Identify open questions** — What is unclear? What assumptions are you making? These MUST be listed in the plan for the human to resolve.

---

## Step 3: Generate the Plan

Write the plan file to the active plans directory:
```
docs/plans/active/YYYY-MM-DD-<topic>.md
```

Use today's date. The topic should be a short kebab-case slug (e.g., `user-profile-editing`, `password-reset-flow`).

### Plan structure

```markdown
# <Feature Name> Implementation Plan

**Goal:** One sentence describing what this feature does and why.
**Architecture:** 2-3 sentences about the technical approach — which layers are involved, what patterns to use, any key design choices.

## Assumptions
- List assumptions that must hold true for this plan to work
- e.g., "The users table already has an avatar_url column"
- e.g., "We are using the existing auth middleware, not creating a new one"

## Open Questions
- List anything that needs clarification before implementation starts
- e.g., "Should avatar uploads go to S3 or Supabase Storage?"
- e.g., "What is the max file size for avatars?"
- (The human must resolve these before /implement-feature begins)

## Context and Orientation
- **Files to read before starting:** list key files the agent should read for context
- **Patterns to follow:** reference specific sections of docs/conventions.md
- **Related decisions:** reference relevant entries in docs/decisions/
- **Similar existing code:** point to existing features that follow the same pattern

## Steps

### Step 1: <Component Name>
**Files:** list every file to create or modify, with full paths
**Tests:** list every test file to create or modify, with full paths
**What to do:** clear, specific description of what to implement in this step. Include enough detail that there is no ambiguity about what "done" looks like.
**Verify:** the specific command to run to confirm this step works (from harness.yaml commands)

### Step 2: <Component Name>
**Files:** ...
**Tests:** ...
**What to do:** ...
**Verify:** ...

(Repeat for each step)

## Validation
- How to verify the entire feature works end-to-end after all steps are complete
- List the commands to run (from harness.yaml)
- Describe expected outcomes (what should pass, what should be visible)

## Decision Log
(This section starts empty. During implementation, /implement-feature records any
non-obvious choices made here — e.g., "Chose to use a separate table instead of
a JSONB column because...")
```

---

## Step 4: Present for Approval

After writing the plan file, present it to the human:

```
Plan written to: docs/plans/active/YYYY-MM-DD-<topic>.md

Summary:
- [N] steps
- Key components: [list the main things being built]
- Estimated files: [N] new, [N] modified

Open questions that need your input:
1. [question]
2. [question]

Please review the plan. When you are ready, say "approved" to begin implementation,
or provide feedback for revisions.
```

Do NOT proceed with any implementation until the human explicitly approves.

If the human requests changes to the plan, update the plan file and present again.

---

## Rules

1. **All commands in the plan MUST come from `harness.yaml`.** Do not hardcode `pytest`, `flutter test`, `npm test`, etc. Reference the command key (e.g., "Run `commands.test` from harness.yaml") or write the actual value read from the file.

2. **Steps must be ordered by dependency.** Foundational pieces first (data models, then repositories/services, then API/UI). A step should never reference code that has not been created in a prior step.

3. **Each step must be independently verifiable.** Every step has a **Verify:** section with a concrete command. After completing a step, you should be able to confirm it works without completing later steps.

4. **Include exact file paths.** Do not write "create a model file." Write "create `src/models/user_profile.py`." Use the project's actual directory structure.

5. **Keep steps small.** One logical change per step. If a step description exceeds ~10 lines, it is probably too large — split it.

6. **Surface uncertainties explicitly.** If you are unsure about an approach, put it in Open Questions. Do not bury assumptions inside step descriptions.

7. **Respect existing patterns.** If the codebase has an established way of doing something (from conventions doc or existing code), the plan should follow that pattern — not introduce a new one — unless there is a documented reason to change.

8. **Do not plan beyond the feature scope.** If you notice unrelated improvements while analyzing the codebase, note them separately (e.g., "Noticed: X could be refactored") but do not include them in the plan steps.
