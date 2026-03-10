# Session Lifecycle

## Default: flush-only (reads within the same request)

`BaseRepository` methods call `session.flush()`, not `session.commit()`. This stages SQL within the current transaction so subsequent reads in the same request see the changes, but nothing is persisted until an explicit `commit()`. The `get_db()` dependency calls `session.close()` on cleanup, which rolls back any uncommitted transaction.

For simple CRUD routes (create, return response), this works because the flushed data is readable within the request and the lack of commit is harmless — the response already contains the data the client needs.

## When to commit explicitly

Call `session.commit()` in the service layer when:
- **Dispatching async tasks** — Celery workers run in separate sessions and cannot see unflushed rows. Commit before calling `dispatch_task()`.
- **Multi-step operations** — when a later step depends on a prior write being visible to external systems.

```python
# Service dispatches a Celery task after creating a record
job = self._job_repo.create_from_schema(data)
self._session.commit()  # worker must see this row
dispatch_task(str(job.id))
```

## Rules

1. Repositories never commit — they only `flush()`.
2. Services own the commit decision when cross-process visibility is needed.
3. Routes never commit directly — delegate to services.
