# Testing Guide

Testing strategy for the Magnet monorepo. Every behavioral change requires a corresponding test update.

---

## Test Tiers

```
        /\
       /  \        End-to-End (E2E) — deferred
      / few \      Full system, real dependencies
     /--------\
    /          \   Integration
   /  moderate  \  Multiple units, real DB or test server
  /--------------\
 /                \ Unit
/     many         \ Single function/class, mocked dependencies, fast
────────────────────
```

---

## File Location Convention

### Python (packages/api/)

```
packages/api/
├── app/
│   ├── models/user.py
│   ├── services/brief_service.py
│   └── agents/concept_agent.py
└── tests/
    ├── helpers/
    │   ├── factories.py          # Test data builders
    │   ├── mocks.py              # Shared mock definitions
    │   └── fixtures.py           # pytest fixtures (DB, client)
    ├── unit/
    │   ├── models/test_user.py
    │   ├── services/test_brief_service.py
    │   └── agents/test_concept_agent.py
    └── integration/
        ├── repositories/test_project_repository.py
        └── routes/test_projects.py
```

Naming: `test_<module>.py`. Test classes: `TestClassName`. Test methods: `test_<behavior>`.

### TypeScript (packages/web/)

```
packages/web/
├── app/
├── components/
├── lib/
└── __tests__/
    ├── helpers/
    │   └── factories.ts
    └── unit/
        ├── components/brief-card.test.tsx
        └── lib/api-client.test.ts
```

Naming: `<module>.test.ts(x)`.

---

## Decision Matrix: Which Tier?

| What you are testing | Tier | Why |
|---------------------|------|-----|
| Pydantic schema validation | Unit | Pure data, no dependencies |
| SQLAlchemy model field definitions | Unit | Schema check, no DB needed |
| Service business logic (mocked repos) | Unit | Test rules, not infrastructure |
| Concept Agent prompt construction | Unit | Pure function building messages |
| Composition JSON builder | Unit | Data structure assembly |
| FFmpeg command generation | Unit | String/filter graph building |
| Provider protocol compliance | Unit | Mock responses, verify interface |
| Repository against test database | Integration | Needs real PostgreSQL |
| API route returns correct status/body | Integration | Needs HTTP transport |
| Celery task execution flow | Integration | Needs Redis + worker |
| React component rendering | Unit | Mock API, test UI output |
| API client request formatting | Unit | Mock fetch, verify request shape |

---

## Test Helper Patterns

### Factories (Python)

```python
# tests/helpers/factories.py

from app.models.project import Project
from app.models.brief import CreativeBrief

def create_test_project(**overrides) -> Project:
    defaults = {
        "id": "test-project-123",
        "name": "Test Game",
        "status": "active",
    }
    return Project(**(defaults | overrides))

def create_test_brief(**overrides) -> CreativeBrief:
    defaults = {
        "id": "test-brief-456",
        "project_id": "test-project-123",
        "hook_type": "fail_challenge",
        "status": "draft",
    }
    return CreativeBrief(**(defaults | overrides))
```

### Factories (TypeScript)

```typescript
// __tests__/helpers/factories.ts

import type { Brief } from '@/models/brief';

export function createTestBrief(overrides?: Partial<Brief>): Brief {
  return {
    id: 'test-brief-456',
    projectId: 'test-project-123',
    hookType: 'fail_challenge',
    status: 'draft',
    ...overrides,
  };
}
```

### Mocking Providers (Python)

```python
# tests/helpers/mocks.py

class MockLLMProvider:
    def __init__(self, response: dict):
        self.response = response
        self.calls: list = []

    async def generate(self, messages: list, schema: dict | None = None) -> dict:
        self.calls.append({"messages": messages, "schema": schema})
        return self.response
```

### Mocking Async Services in Route Tests

When mocking services that have `async` methods (e.g., `ConceptService.generate_concepts`), use `AsyncMock()` from `unittest.mock` — not `MagicMock()`. `MagicMock` return values are not awaitable and will raise `TypeError` at runtime.

```python
from unittest.mock import AsyncMock, MagicMock

mock_brief_service = MagicMock()      # sync methods — fine
mock_concept_service = AsyncMock()    # async methods — must use AsyncMock
```

---

## Running Tests

```bash
# Python — all tests
cd packages/api && pytest

# Python — unit only
cd packages/api && pytest tests/unit/

# Python — integration only
cd packages/api && pytest tests/integration/

# Python — specific file
cd packages/api && pytest tests/unit/services/test_brief_service.py

# Python — with coverage
cd packages/api && pytest --cov=app tests/

# TypeScript — all tests
cd packages/web && npx vitest run

# TypeScript — specific file
cd packages/web && npx vitest run __tests__/unit/lib/api-client.test.ts

# TypeScript — with coverage
cd packages/web && npx vitest run --coverage
```

---

## Coverage Targets

| Package | Target | Focus |
|---------|--------|-------|
| API — models, schemas | 90% | Pure data, easy to test |
| API — services, agents | 80% | Core business logic |
| API — repositories | 70% | Integration tests cover these |
| API — routes | 70% | Integration tests via test client |
| Web — lib, components | 80% | UI logic and rendering |

---

## Principles

1. **Test behavior, not implementation** — if you refactor without changing behavior, tests pass.
2. **One concept per test** — one assertion focus per test function.
3. **Descriptive names** — `test_rejects_brief_when_project_has_no_profile`, not `test1`.
4. **Arrange-Act-Assert** — three phases, separated by blank lines.
5. **Edge cases** — empty inputs, missing fields, error paths, duplicate operations.
6. **TDD by default** — write the test first, watch it fail, then implement.
