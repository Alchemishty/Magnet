# Fixes

## Completion phases get skipped in long skill workflows

In `/implement-feature`, Phases 4-5 (retrospective, plan archival) were skipped because user ad-hoc requests mid-workflow pulled attention away from the skill's checklist. Fix: the skill now creates "Move plan to completed" and "Run retrospective" as explicit tasks in the task list during Phase 1 setup. These stay visible as pending reminders even when context-switching to user requests.

- **Context:** Any multi-phase skill that spans many conversation turns
- **Source:** 2026-03-10 LLM provider feature — retrospective was never run until user noticed

## Test file exceeds 300-line enforcement limit

When adding tests to an existing file, check `wc -l` before committing. The enforcement rule (`check-file-size.sh`) rejects files over 300 lines. Fix by removing decorative comments (section separators) or splitting the file. Class names already describe sections — separator comments are redundant.

- **Context:** Any test file that grows through iterative feature work
- **Source:** CI failure on PR #6 (2026-03-10), `test_brief_routes.py` hit 304 lines

## Run ruff format on the full codebase periodically

New files get formatted but existing files may not match. Running `ruff format .` on the full `packages/api/` directory keeps everything consistent and avoids CI drift. Do this as a standalone commit after merging features.

- **Context:** After merging any feature branch
- **Source:** 2026-03-10, 47 files needed reformatting after LLM provider merge

## str(Exception) vs str(exc) — class vs instance

`str(Exception)` converts the Exception *class* to string (giving `"<class 'Exception'>">`), not the error message. Always use `except Exception as exc:` and then `str(exc)` to get the actual error message.

- **Context:** Any error handler that logs or stores exception messages
- **Source:** 2026-03-10 Celery task integration, caught during deslop

## patch.dict scope vs module reload for env var tests

`@patch.dict("os.environ", {...})` restores the env only *after* the test method returns. A `reload(module)` inside the test runs while the patch is active. To restore the module to default config after the test, use a `pytest.fixture(autouse=True)` with `yield` + `reload()` in the teardown — this runs after the patch.dict decorator has cleaned up.

- **Context:** Tests that reload modules to verify env-based configuration
- **Source:** CodeRabbit review on PR #7 (2026-03-10)
