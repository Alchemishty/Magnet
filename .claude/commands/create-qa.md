---
name: create-qa
description: QA checklist generator from diff
---

# create-qa

Generate a QA checklist based on the current branch diff, with domain awareness.

## Workflow

1. Get the current branch name: `git branch --show-current`.
2. Get the diff: `git diff main..HEAD` (all changes on this branch).
3. Read `docs/domain.md` for domain entities and categories (if it exists).
4. Read `harness.yaml` for `commands.test`, `commands.analyze`, and any relevant start/run commands.
5. Generate `qa/QA-<branch-name>.md` with this structure:

```markdown
# QA Checklist: <branch-name>

Generated: <date>
Branch: <branch-name>
Changes: <N files changed, N insertions, N deletions>

## Change-Specific QA

These items are derived directly from the diff. They are the most important items to verify.

- [ ] <specific scenario based on what changed>
- [ ] <another scenario>
...

## Domain QA

These items cover general functionality that may be affected by the changes.

### <Domain Entity 1> (from docs/domain.md)
- [ ] <scenario>
- [ ] <scenario>

### <Domain Entity 2>
- [ ] <scenario>
...

## Regression
- [ ] Existing tests pass (run: <commands.test from harness.yaml>)
- [ ] Static analysis clean (run: <commands.analyze from harness.yaml>)
- [ ] Application starts without errors (run: <appropriate start command>)
```

6. Each checklist item should be:
   - Specific (not "check the feature works" -- describe the exact scenario)
   - Actionable (a tester can follow it)
   - Referencing actual UI elements, API endpoints, or behaviors from the diff

## Rules

- Change-specific items come FIRST -- they are the most important.
- Domain categories come from `docs/domain.md`, never hardcoded.
- If `docs/domain.md` does not exist, only generate change-specific items and the regression section. Omit the Domain QA section entirely.
- Commands in the Regression section must come from `harness.yaml`.
- Create the `qa/` directory if it does not already exist.
