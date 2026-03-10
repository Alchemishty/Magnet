---
name: create-pr
description: PR creation with standards verification gate
---

# create-pr

Create a pull request only after all quality gates pass.

## Workflow

### Standards Gate (BLOCKING -- do not proceed if this fails)

1. Read `harness.yaml` --> `commands.analyze`. Run it. If it fails: STOP. Report errors. Do not create the PR.
2. Read `harness.yaml` --> `commands.test`. Run it. If it fails: STOP. Report errors. Do not create the PR.
3. If an `enforcement/` directory exists with `run-all.sh`: run it. If it fails: STOP. Report errors.
4. Only proceed if ALL three pass.

### Branch and Changes

5. Ensure you are on a feature branch (not main/master). If on main: create a branch from the current work.
6. Run `git status` and `git diff` to understand all changes.
7. Run `git log main..HEAD` (or equivalent) to see all commits on this branch.

### Generate PR Content

8. Write a PR title: short (<70 chars), imperative, describes the change.
9. Write PR body using this structure:

```markdown
## Summary
- Bullet points describing what changed and why (2-5 bullets)

## Changes
- List of files changed, grouped by type (new, modified, deleted)

## Testing
- What tests were added/modified
- How to verify manually (reference qa/QA-<branch>.md if it exists)

## Notes
- Anything reviewers should pay special attention to
- Any known limitations or follow-up work needed

---
Generated with [Agent Harness](https://github.com/Alchemishty/agent-harness)
```

### Create PR

10. Stage and commit any uncommitted changes.
11. Push: `git push -u origin <branch-name>`.
12. Create PR: `gh pr create --title "<title>" --body "<body>"`.
13. Report the PR URL.

## Rules

- The standards gate is NON-NEGOTIABLE. Never skip it.
- If the gate fails, tell the user what failed and how to fix it. Do not create the PR.
- PR title should describe WHAT changed, body describes WHY.
- Always use a HEREDOC for the PR body to preserve formatting.
