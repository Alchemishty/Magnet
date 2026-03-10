# Review Lessons

## CodeRabbit catches resource leaks

CodeRabbit (configured as CHILL profile) reliably flags unclosed resources like httpx clients. When adding any provider or client that holds a connection, proactively add cleanup before the PR — don't wait for review to catch it.

- **Context:** Any PR that introduces httpx.AsyncClient, database connections, or similar resources
- **Source:** PR #6 review (2026-03-10)

## CodeRabbit checks error handling completeness

CodeRabbit traces exception paths through dependency injection. It flagged that `ValueError` from the provider factory could bubble uncaught through `Depends`. When adding new dependencies that can raise, trace all exception paths to the route handler.

- **Context:** Any route that adds new `Depends` injections
- **Source:** PR #6 review (2026-03-10)
