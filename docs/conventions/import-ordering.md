# Import Ordering and Style

## Python (packages/api/)

```python
# 1. Standard library
import os
from datetime import datetime
from pathlib import Path

# 2. Third-party
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, String

# 3. Internal
from app.models.project import Project
from app.services.brief_service import BriefService
```

## TypeScript (packages/web/)

```typescript
// 1. Node built-ins
import path from 'node:path';

// 2. Third-party / framework
import React from 'react';
import { useQuery } from '@tanstack/react-query';

// 3. Internal
import { ProjectModel } from '@/models/project';
import { apiClient } from '@/lib/api-client';
```

## Rules

- Groups separated by a blank line. Alphabetical within groups.
- Remove unused imports — they fail CI.
- Prefer explicit imports over wildcards.
- Python: absolute imports from `app.` prefix. No relative imports across layers.
- TypeScript: use `@/` path alias for internal imports.
