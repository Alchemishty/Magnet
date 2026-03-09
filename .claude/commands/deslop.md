---
name: deslop
description: Clean code philosophy — eliminate unnecessary comments, simplify code
---

Apply clean code philosophy to the specified files or directories. Focus on removing noise and improving clarity without changing behavior.

## Comment Guidelines

**Remove comments that:**
- Restate what the code obviously does (e.g., `// increment counter` before `counter++`)
- Describe "what" instead of "why" — the code itself shows what it does
- Are outdated or no longer match the code they annotate
- Exist because the code is unclear (fix the code instead of explaining it)
- Are commented-out code blocks (delete them — version control exists)
- Are TODO/FIXME items that are stale or will never be addressed

**Keep or add comments only when:**
- Explaining *why* a non-obvious decision was made
- Documenting external constraints or business rules not evident from code
- Warning about non-intuitive behavior or surprising edge cases
- Required for public API documentation (docstrings, JSDoc, Javadoc, etc.)
- Clarifying a workaround for a known bug in a dependency

## Code Simplification

- Rename variables and functions to be self-documenting instead of adding comments
- Extract well-named functions instead of commenting code blocks
- Use early returns to reduce nesting depth
- Remove dead code, unused variables, and redundant logic
- Simplify overly clever or complex expressions into readable steps
- Prefer explicit over implicit — clarity beats brevity
- Collapse single-use variables that add no semantic value
- Remove redundant type annotations where the type is obvious from context

## Scope Boundaries

- Do NOT add features or change observable behavior
- Do NOT refactor architecture or move files between modules
- Do NOT change public API signatures
- Do NOT modify test assertions or expected values
- Limit changes to readability, naming, comment cleanup, and minor simplification

## Philosophy

"Code is written for humans to read, and only incidentally for machines to execute."

If a comment is needed to understand code, first try to rewrite the code to be clearer. The best comment is the one you didn't need to write.

## Process

1. Read the target files fully before making any changes.
2. Identify all comments — classify each as "remove" or "keep" using the guidelines above.
3. Identify naming improvements and simplification opportunities.
4. Apply changes file by file. Keep diffs minimal.
5. Run the project's linter/analyzer (from `harness.yaml → commands.analyze`) to confirm zero new issues.
6. If any change is ambiguous, err on the side of leaving code untouched.

$ARGUMENTS
