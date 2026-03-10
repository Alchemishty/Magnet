# Coding Conventions

This document defines coding conventions for the Magnet monorepo. The Python (API) and TypeScript (Web) stacks each have language-specific rules. Shared principles apply to both.

- [Import Ordering and Style](./import-ordering.md) — module import grouping, ordering, and restrictions for Python and TypeScript
- [Naming Conventions](./naming.md) — file, class, function, variable, and constant naming for both stacks
- [Error Handling](./error-handling.md) — error patterns at each layer (routes, services, repositories) and core principles
- [Session Lifecycle](./session-lifecycle.md) — SQLAlchemy session flush vs commit, when to commit explicitly
- [Provider Abstraction](./provider-abstraction.md) — Protocol-based interfaces for external services and provider lifecycle
- [Serialization and Quality](./serialization-and-quality.md) — Composition JSON contract, serialization rules, code smells, formatting and linting
