---
name: implement-feature
description: Autonomous feature implementation orchestrator
---

# Implement Feature

Autonomous orchestrator that takes a feature from plan through to merge-ready PR. This is the primary workflow — it coordinates planning, implementation, verification, cleanup, and review.

## Input

Accept either:
- A **plan file path** (e.g., `docs/plans/active/2026-03-07-user-auth.md`)
- A **natural language feature description** (e.g., "Add password reset flow with email verification")

If both are ambiguous, ask the human to clarify.

## Setup

Before anything else, read `harness.yaml` at the project root. Parse and hold in context:
- `commands` — every command you run comes from here
- `verification.checks` — the pre-commit gate checks
- `verification.max_retries` — how many times to retry before escalating (default 3)
- `review.max_review_cycles` — how many review cycles before escalating (default 3)
- `review.provider` — the review agent (e.g., coderabbit)
- `docs` — paths for plans, decisions, architecture
- `enforcement` — rules to enforce
- `gardening` — post-feature checks

Also read `AGENTS.md` to understand project-specific agent rules.

Determine the repo owner and name from git remote for use in `gh api` calls:
```bash
git remote get-url origin
```

---

## Phase 1: Planning

### If input is natural language (no plan file provided):
1. Invoke `/create-plan` with the feature description
2. Wait for the human to review and approve the plan
3. Do NOT proceed until the human explicitly approves

### If input is a plan file:
1. Read the plan file
2. Extract the ordered steps from the `## Steps` section
3. Confirm with the human: "I found N steps in the plan. Proceeding with implementation."

### Create task list
Create a task list from the plan steps. Each step becomes a task. This tracks progress visibly throughout the workflow.

### Create a feature branch
```bash
git checkout -b feat/<short-topic-name>
```
Use a descriptive branch name derived from the plan title.

---

## Phase 2: Implementation Loop

For each step in the plan, in order:

### 2.1 — Read the step requirements
Read the step from the plan file. Understand:
- Which files to create or modify (listed under **Files:**)
- What tests are needed (listed under **Tests:**)
- What the step does (listed under **What to do:**)
- How to verify it (listed under **Verify:**)

If the step references patterns from `docs/conventions.md` or `docs/architecture.md`, read those sections now.

### 2.2 — Write or update tests first (TDD)
- Write the test(s) for this step before writing the implementation
- Run the tests to confirm they fail as expected (red phase):
  ```
  # Use commands.test or commands.test_unit from harness.yaml
  ```
- If a test framework or helper is missing, create it as part of this step

### 2.3 — Implement the code
- Write the implementation to make the tests pass
- Follow patterns from `docs/conventions.md`
- Keep changes focused — one logical change per step

### 2.4 — Run the step's verify command
If the step has a **Verify:** section with a specific command, run it now to confirm the step works before committing.

### 2.5 — Stage changes and commit
Stage the files changed in this step (prefer specific file paths over `git add .`):
```bash
git add <specific-files>
git commit -m "<descriptive message for this step>"
```

### 2.6 — Pre-commit verification gate
The pre-commit gate fires automatically on commit. Here is what it does and how to handle it:

1. Read `harness.yaml` -> `verification.checks`
2. Run each check in order (lint, test, enforcement — whatever is configured)
3. **If all checks pass:** the commit succeeds. Move on.
4. **If any check fails:**
   - Read the error output carefully
   - Identify the root cause
   - Fix the issue
   - Stage the fix and retry the commit
   - Track the retry count
5. **After `verification.max_retries` consecutive failures (default 3): STOP IMMEDIATELY.**
   - Do NOT keep trying
   - Print a clear error summary:
     ```
     VERIFICATION FAILED after [N] retries.

     Failing check: [check name]
     Last error output:
     [paste relevant error output]

     What I tried:
     [list each fix attempt]

     I need your help to resolve this before continuing.
     ```
   - Wait for the human to help

### 2.7 — Update the plan file
After a successful commit, update the plan file to mark the step as done. Add a checkmark or `[DONE]` prefix to the step heading:
```markdown
### Step 1: [DONE] Set up database models
```

---

## Phase 3: Cleanup

After ALL steps in the plan are complete:

### 3.1 — Full codebase enforcement check
Run all verification checks from `harness.yaml` -> `verification.checks` against the full codebase (not just changed files). Fix any issues found.

### 3.2 — Deslop
Invoke `/deslop` to clean up generated code:
- Remove unnecessary comments
- Tighten verbose patterns
- Clean up any slop introduced during implementation

### 3.3 — Garden
Invoke `/garden` for an entropy scan:
- Doc freshness (do docs still match the code?)
- Coverage gaps (any new code without tests?)
- File sizes (anything exceeding `enforcement.file_size_limit`?)
- Unused imports and exports

Address any findings before proceeding.

### 3.4 — Generate QA checklist
Invoke `/create-qa` to generate a manual QA checklist based on the changes made. This goes into the PR description or a linked QA doc.

---

## Phase 4: PR and Review

### 4.1 — Create the PR
Invoke `/create-pr` to handle the standards gate (lint, test, enforcement) and PR creation. This skill will:
- Run all verification checks (blocking gate — stops if any fail)
- Push the branch
- Create the PR with a properly formatted title and body

If `/create-pr` fails the standards gate, fix the issues and invoke it again.

### 4.2 — Wait for review
Wait 30 seconds for the review agent (e.g., CodeRabbit) to begin its review:
```bash
sleep 30
```

### 4.3 — Poll for review comments
Get the PR number from the `gh pr create` output, then poll:
```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments
```

### 4.4 — Address review comments
For each review comment:

**If actionable** (requests a code change):
- Read the comment and the referenced code
- Make the fix
- Commit with a message referencing the review (e.g., `fix: address review — <what was fixed>`)
- Push

**If informational** (suggestion, praise, question, or nitpick you disagree with):
- Reply inline via `gh api`:
  ```bash
  gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies -f body="<response>"
  ```

**If unclear** (you do not understand the comment):
- Do NOT guess. Reply asking for clarification, and escalate to the human.

### 4.5 — Re-review loop
After pushing fixes:
1. Wait 30 seconds for re-review
2. Poll for new comments
3. Address new comments
4. Repeat

Loop up to `review.max_review_cycles` (from `harness.yaml`, default 3).

### 4.6 — Resolution
**If the review agent approves or there are no new actionable comments:**
```
PR is ready for merge: <PR URL>

Summary of changes:
- [bullet points]

Review cycles completed: [N]
All review comments addressed.

Please review and merge when ready.
```

**If max review cycles reached with unresolved comments:**
```
REVIEW ESCALATION after [N] cycles.

Unresolved comments:
1. [file:line] — [summary of comment] — [why it's unresolved]
2. ...

I need your guidance on these before continuing.

PR URL: <url>
```

---

## Phase 5: Completion

After the human merges the PR:

1. Move the plan file from `docs/plans/active/` to `docs/plans/completed/`:
   ```bash
   git mv docs/plans/active/<plan-file>.md docs/plans/completed/<plan-file>.md
   git commit -m "chore: move completed plan to archive"
   git push
   ```

2. Report final summary:
   ```
   Feature complete: <feature name>

   Commits: [N]
   Files changed: [N]
   Tests added: [N]
   Review cycles: [N]
   Plan: docs/plans/completed/<plan-file>.md
   ```

---

## Critical Rules

1. **NEVER hardcode any command.** Every shell command for lint, test, build, format, etc. MUST come from `harness.yaml` -> `commands` or `verification.checks`. The only exceptions are git and gh commands.
2. **Read `harness.yaml` at the start** and reference it throughout. If the file changes mid-workflow (unlikely but possible), re-read it.
3. **When stuck: STOP and escalate.** Do not guess, do not loop endlessly, do not make assumptions about what the human wants. Print what you know and ask for help.
4. **Keep the plan file updated** as a living document. Mark steps done, record decisions in the Decision Log section.
5. **Each commit should be atomic** — one logical change. Do not bundle unrelated changes. Do not make giant commits.
6. **Stage specific files** when committing. Prefer `git add <file1> <file2>` over `git add .` or `git add -A`.
7. **Never merge PRs.** That is the human's decision.
8. **Never dismiss review comments.** Address them or escalate.
9. **Never skip verification.** The pre-commit gate exists for a reason.
10. **Test first, implement second.** Write failing tests before writing implementation code.
