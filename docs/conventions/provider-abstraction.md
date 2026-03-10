# Provider Abstraction Pattern

All external services use Protocol-based interfaces:

```python
class LLMProvider(Protocol):
    async def generate(self, messages: list[dict], schema: dict | None = None) -> dict: ...

class TTSProvider(Protocol):
    async def synthesize(self, text: str, voice: str) -> bytes: ...

class MusicProvider(Protocol):
    async def generate(self, prompt: str, duration: int) -> bytes: ...
```

Concrete implementations live in `providers/<category>/`. Configuration selects which implementation is active. Services and Agents never reference concrete providers directly.

## Provider Lifecycle

Providers that hold resources (HTTP clients, connections) must implement an `aclose()` async method. FastAPI dependencies that yield providers must use `try/finally` to call `aclose()` after the request:

```python
async def get_llm_provider() -> AsyncGenerator:
    provider = _get_llm_provider()
    try:
        yield provider
    finally:
        await provider.aclose()
```
