# Serialization and Quality

## Composition JSON Contract

The `RenderJob.composition` field is the contract between AI planning and video rendering. It fully describes a video as a layered timeline:

```json
{
  "duration": 15,
  "resolution": [1080, 1920],
  "fps": 30,
  "layers": [
    { "type": "video", "asset_id": "...", "start": 0, "end": 8 },
    { "type": "text", "content": "...", "start": 0, "end": 3 },
    { "type": "audio", "asset_id": "...", "start": 0, "end": 15 }
  ]
}
```

Schema changes to Composition JSON require a decision record in `docs/decisions/`.

## Serialization

- External data (JSON, DB): `snake_case` keys.
- Internal Python: `snake_case` attributes.
- Internal TypeScript: `camelCase` properties.
- Pydantic handles Python ↔ JSON translation. TypeScript API client transforms at the boundary.
- Enums stored as string names, never numeric indices.
- Dates as ISO 8601 UTC strings. Local time only at display layer.

## Code Smells

| Smell | Fix |
|-------|-----|
| File exceeds 300 lines | Split into focused modules |
| Empty except/catch block | Add logging at minimum |
| Hardcoded URLs, secrets, magic numbers | Extract to env vars or constants |
| Raw DB queries in routes | Move to repository |
| Provider SDK calls outside providers/ | Wrap in provider interface |
| Missing mounted/alive check after await in React | Add cleanup or abort controller |

## Formatting and Linting

- **Python:** `ruff check` (linting), `ruff format` (formatting). Zero warnings policy.
- **TypeScript:** `eslint` (linting), `prettier` (formatting). Zero warnings policy.
- Line length: 88 (Python/ruff), default (TypeScript/prettier).
- Trailing commas: yes (both languages).
