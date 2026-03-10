# Review Lessons

## CodeRabbit catches resource leaks

CodeRabbit (configured as CHILL profile) reliably flags unclosed resources like httpx clients. When adding any provider or client that holds a connection, proactively add cleanup before the PR — don't wait for review to catch it.

- **Context:** Any PR that introduces httpx.AsyncClient, database connections, or similar resources
- **Source:** PR #6 review (2026-03-10)

## CodeRabbit checks error handling completeness

CodeRabbit traces exception paths through dependency injection. It flagged that `ValueError` from the provider factory could bubble uncaught through `Depends`. When adding new dependencies that can raise, trace all exception paths to the route handler.

- **Context:** Any route that adds new `Depends` injections
- **Source:** PR #6 review (2026-03-10)

## CodeRabbit verifies transaction timing for async dispatch

CodeRabbit traces the session lifecycle through `get_db()` → `flush()` → `close()` and flags cases where async workers won't see uncommitted data. When adding Celery task dispatch, proactively commit before dispatching — don't wait for review to catch the race condition.

- **Context:** Any PR that dispatches async tasks after DB writes
- **Source:** PR #7 review (2026-03-10)

## CodeRabbit catches incomplete mock side_effect lists

When a mock's `side_effect` list has fewer entries than the number of calls, the extra calls raise `StopIteration` which can mask bugs. CodeRabbit verifies that error-path tests actually exercise the error-handling code, not just the exception propagation. Ensure side_effect lists match the full call sequence including error handlers.

- **Context:** Tests with multi-step mock side_effect sequences
- **Source:** PR #7 review (2026-03-10)

## CodeRabbit flags missing Alembic migrations

When adding a new column to an ORM model, CodeRabbit cross-references the migration files. Always create an Alembic migration in the same PR that adds a model column — don't defer it.

- **Context:** Any PR that modifies SQLAlchemy model columns
- **Source:** PR #7 review (2026-03-10)
