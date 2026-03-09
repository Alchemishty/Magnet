---
name: retrospective
description: Post-implementation retrospective that captures learnings to memory and proposes doc improvements
---

# Retrospective

Run a structured retrospective after completing a feature implementation (or standalone for any session). The goal is to extract durable learnings from this session and write them to `memory/` so future sessions benefit. This turns one-time problem-solving into reusable knowledge.

## When to Run

- After `/implement-feature` completes (Phase 5 invokes this)
- After code review cycles complete (Phase 4 invokes this after addressing reviewer feedback)
- After any significant debugging session
- After any session where you learned something non-obvious about the codebase
- Standalone, when the user asks to capture learnings

## Setup

1. Read `harness.yaml` at the project root (for project context).
2. Read all files in `memory/` (to avoid duplicating existing entries).
3. If a plan file was involved, read it (including the Decision Log section).
4. If `scratch/session-state.md` exists, read it for session context.

---

## Step 1: Reflect on the Session

Answer these questions internally (do not print them all to the user — they guide your analysis). Not all questions apply to every retrospective — skip any that are irrelevant to the session type.

### 1a: What patterns worked well?
- Which coding patterns, architectural decisions, or approaches led to clean implementations?
- Did any conventions from `docs/conventions.md` prove especially useful?
- Were there patterns you followed that made the verification gate pass on the first try?

### 1b: What errors recurred?
- Which errors or test failures came up more than once?
- What was the root cause each time?
- What is the fix that future agents should know?

### 1c: What was missing from documentation?
- Were there gaps in `docs/architecture.md`, `docs/conventions.md`, or `docs/domain.md` that caused confusion?
- Did you have to discover something by reading code that should have been documented?
- Were any `docs/decisions/` records missing that would have saved time?

### 1d: What was unclear in skills or harness config?
- Did any skill instructions lead to confusion or wrong approaches?
- Were any `harness.yaml` commands incorrect or missing?
- Did the enforcement rules flag false positives or miss real issues?

### 1e: What user preferences were discovered?
- Did the user express preferences about workflow, tooling, or style?
- Did the user correct your approach in a way that reveals a standing preference?
- Did the user approve or reject approaches in a way that implies future guidance?

### 1f: What did code review feedback reveal? (after review cycles)
- Which review comments pointed out patterns you should have followed? These are high-signal — the reviewer is teaching you the team's standards.
- Were there recurring comment themes across review cycles? (e.g., "always add error handling for X", "prefer Y pattern over Z")
- Did the reviewer flag conventions not documented in `docs/conventions.md`? These are documentation gaps.
- Were any review comments about test quality or coverage? Note what the expected standard is.
- Did the reviewer suggest architectural changes? These may warrant a `docs/decisions/` entry.

**Review feedback is the highest-signal input for memory.** Reviewers explicitly state what the team expects. If a reviewer says "we always do X" and it's not in conventions.md, both write it to `memory/patterns.md` AND propose adding it to conventions.md.

---

## Step 2: Write to Memory

For each finding from Step 1, check if an existing entry in `memory/` already covers it. If so, update that entry. If not, append to the appropriate file.

### Target files

| Finding type | Memory file |
|-------------|-------------|
| Coding patterns that worked | `memory/patterns.md` |
| Error fixes and debugging insights | `memory/fixes.md` |
| User workflow and tool preferences | `memory/preferences.md` |
| Domain knowledge discovered | `memory/domain.md` |
| Reviewer-enforced standards | `memory/patterns.md` |
| Review feedback themes | `memory/review-lessons.md` |

### Format for memory entries

Each entry should be self-contained and scannable:

```markdown
## <Short descriptive title>

<1-3 sentences explaining the pattern, fix, or preference.>

- **Context:** <when this applies>
- **Source:** <how this was discovered — e.g., "2026-03-10 user-auth feature">
```

### Rules for writing memory

1. **Only write confirmed findings** — patterns validated in this session, not speculation
2. **Check for duplicates first** — read existing memory files before writing
3. **Update over append** — if an existing entry covers the same topic, update it. If the old entry is now wrong, mark it `[SUPERSEDED]` with a date and reason rather than deleting it
4. **Be specific** — "pytest fails when fixture X is missing" is useful; "tests can fail" is not
5. **Include source context** — mention the feature or date so future agents can trace the origin
6. **Keep entries concise** — each entry should be 3-6 lines, not paragraphs

---

## Step 3: Propose Documentation Improvements

If Step 1c or 1d revealed gaps, propose specific edits. Do NOT make the edits automatically — present them to the user for approval.

### Format

```
## Proposed Documentation Improvements

### 1. [Target file]: [What to add/change]
**Gap found:** <what was missing or unclear>
**Proposed fix:** <specific text to add or change>

### 2. [Target file]: [What to add/change]
...

Should I apply any of these changes?
```

### What to propose

- Missing conventions in `docs/conventions.md` (patterns you had to discover by reading code)
- Missing domain knowledge in `docs/domain.md` (business rules you had to infer)
- Stale or incorrect information in `docs/architecture.md`
- Missing decision records in `docs/decisions/`
- Incorrect or missing commands in `harness.yaml`

### What NOT to propose

- Rewrites of working documentation
- Style preferences that aren't clearly wrong
- Changes to skills (these require more careful consideration)
- Anything speculative — only propose changes backed by evidence from this session

---

## Step 4: Report Summary

Present a concise summary to the user:

```
## Retrospective Summary

### Learnings captured to memory/
- <N> new entries written
- <N> existing entries updated
- Files updated: <list>

### Documentation gaps found
- <N> improvements proposed (see above)
- <or "None — docs are up to date">

### Session stats (if available)
- Verification retries: <N>
- Most common error type: <description>
- Steps completed: <N> of <total>
```

---

## Rules

1. **Never write speculative memory.** Only write findings confirmed by evidence in this session.
2. **Never auto-edit documentation.** Propose changes to the user; let them approve.
3. **Always check existing memory first.** Read `memory/` files before writing to avoid duplication.
4. **Keep it brief.** The retrospective should take 1-2 minutes, not 10. Focus on the highest-signal findings.
5. **Memory is for patterns, not events.** Write "When X happens, fix it with Y" — not "On March 10 I fixed a bug."
