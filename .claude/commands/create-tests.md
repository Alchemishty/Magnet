---
name: create-tests
description: Tier-aware test generator
---

# create-tests

Generate tests for changed files, classified by tier, using project-specific patterns.

## Workflow

1. Read `harness.yaml` for: `stack.test_framework`, `commands.test`, `commands.test_unit`, `commands.test_integration`.
2. Read `docs/testing.md` for project-specific test patterns, helpers, and conventions.
3. Inspect what changed: run `git diff --name-only HEAD` (or `git diff --name-only` for unstaged changes).
4. For each changed file, classify by test tier:
   - Models, utilities, pure functions --> unit test
   - Services, repositories, API handlers with dependencies --> integration test
   - Full user flows --> e2e test
   - Use the decision matrix from `docs/testing.md` if available.
5. For each file needing tests:
   - Determine test file path using the mirroring convention from `docs/testing.md`.
   - Read the source file to understand its behavior.
   - Write tests following patterns from `docs/testing.md` (use existing helpers if documented).
   - Each test: descriptive name, Arrange-Act-Assert, one concept per test.
6. Run tests: execute the command from `harness.yaml` --> `commands.test`.
7. If tests fail: read output, fix, re-run (up to 3 retries).
8. Report: list tests written, tiers, pass/fail status.

## Rules

- Never hardcode test framework imports or assertions -- get them from `docs/testing.md`.
- Follow existing test patterns in the project (read a few existing tests first if they exist).
- Test behavior, not implementation.
- Include edge cases: empty inputs, null/missing values, error paths.
- If `commands.test_unit` or `commands.test_integration` are defined in `harness.yaml`, use the appropriate scoped command when running only the tier you just wrote.
