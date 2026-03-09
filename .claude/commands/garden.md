---
name: garden
description: Entropy scan and cleanup — keep the codebase healthy
---

Run an entropy scan across the codebase. Identify and fix low-hanging issues; report anything requiring human judgment. This skill runs as part of /implement-feature (post-implementation) and can be invoked standalone.

## Setup

1. Read `harness.yaml` at the project root. Extract:
   - `enforcement.file_size_limit` (default: 300)
   - `docs.max_doc_lines` (default: 200)
   - `docs.root` (default: `docs/`)
   - `docs.architecture` (default: `docs/architecture.md`)
   - `gardening.checks` list
   - `commands.analyze` (linter command)
   - `commands.test` (test command)
   - `stack.language` (to determine source file extensions)

2. Determine source file extensions from `stack.language`:
   - python: `.py`
   - typescript/javascript: `.ts`, `.tsx`, `.js`, `.jsx`
   - dart: `.dart`
   - go: `.go`
   - rust: `.rs`
   - java: `.java`, `.kt`
   - Fallback: use all common source extensions

## Checks

Run each check below. Collect results into a report.

### 1. File Size Check

- Find all source files (respect `.gitignore`, skip generated files, `node_modules`, `build/`, `dist/`, `.dart_tool/`, `__pycache__/`, vendor dirs)
- Count lines per file
- Flag any file exceeding `enforcement.file_size_limit`
- Suggestion: "Consider splitting [file] into smaller modules ([N] lines, limit is [limit])"

### 2. Docs Freshness Check

- Read `docs/architecture.md` — extract any directory or file path references. Verify each path actually exists in the repo.
- Read `AGENTS.md` — extract any file path references or links. Verify each target exists.
- Report stale references: "[file]:[line] references [path] which does not exist"

### 3. Test Coverage Gap Check

- List all source files in the project's source directories
- For each, check if a corresponding test file exists using the project's test mirroring convention (check `docs/testing.md` if it exists for the convention, otherwise infer from existing test structure)
- Report source files with no corresponding test
- Exclude from the check: config files, entry points, generated files (`*.g.*`, `*.freezed.*`, `*.gen.*`), barrel/index files, type definition files

### 4. Unused Code Check

- Find source files that are never imported by any other source file
- Exclude entry points, test files, generated files, config files, and migration files
- Report potential dead code: "[file] is not imported by any other source file"
- This is a heuristic — mark findings as "potential" so the human can verify

### 5. Doc Size Check

- Check all files in `docs/` against `docs.max_doc_lines` threshold
- If any file exceeds the threshold: invoke /doc-split for those files

### 6. Scratch Cleanup

- Check if `scratch/` directory exists and has files
- If running as part of post-feature cleanup (invoked by `/implement-feature`): delete all files in `scratch/`
- Report: "Cleaned N files from scratch/" or "scratch/ is clean"

### 7. Memory Freshness Check

- If `memory/` directory exists and has files, scan each file for file path references
- Verify that referenced paths still exist in the project
- Report stale references as "Needs Attention" — do not auto-fix memory entries (the agent who wrote them had context you may lack)

## Auto-Fix Policy

**Fix automatically** (and commit):
- Stale doc references where the correct path is unambiguous (e.g., file was renamed and only one candidate exists)
- Obvious dead imports within a file (unused import statements)
- Scratch directory cleanup (delete all files in `scratch/`)

Commit auto-fixes with message: `chore: gardening — <what was fixed>`

**Report only** (do not fix):
- Files exceeding size limit (splitting requires architectural judgment)
- Missing test files (human decides priority)
- Potential dead code files (human verifies before deletion)
- Ambiguous stale references (multiple candidates or path was deleted entirely)
- Stale memory entries (memory was written with context you may not have)

## Output Format

Print a summary at the end:

```
## Garden Report

### Auto-fixed
- <description of each auto-fix, or "None">

### Needs Attention
- [ ] <issue description and suggestion>
- [ ] <issue description and suggestion>

### Clean
- <checks that passed with no issues>
```

$ARGUMENTS
