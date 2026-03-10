# Video Agent Implementation Plan

**Goal:** Build the Video Agent production pipeline that takes an approved CreativeBrief and produces a rendered video ad through four phases: PLAN, PREPARE, ASSEMBLE, POST-PROCESS.

**Architecture:** The Video Agent lives in `app/agents/video_agent.py`, following the same pattern as `ConceptAgent`. It orchestrates provider calls (TTS, music, image) via Protocol interfaces, programmatic template renderers for RENDER scenes, and an FFmpeg assembler for final video composition. The Celery render task (`app/tasks/render.py`) invokes the agent synchronously (it already runs in a worker process). Provider implementations follow the established factory pattern from `providers/llm/`.

## Assumptions

- FFmpeg is available on the system PATH (installed in Docker image and dev environment)
- Pillow is available for programmatic template rendering (add to dependencies)
- S3/MinIO client is available for uploading rendered videos (boto3)
- The brief's `scene_plan` field contains structured scene data matching the design doc format
- For MVP, TTS uses ElevenLabs API; music and image providers use local stubs (silence audio / solid color placeholder)
- Video generation (Runway/Kling) is deferred to Phase 2 per design doc
- COMPOSE strategy requires assets already uploaded to S3 with valid `s3_key` on the Asset model
- Target output: 9:16 vertical (1080x1920), 15-30 seconds, MP4 H.264

## Open Questions

All resolved:

1. **ElevenLabs voice ID:** User-customizable per video. The `Scene` schema accepts an optional `voice` field. Falls back to `ELEVENLABS_DEFAULT_VOICE` env var.
2. **S3 bucket configuration:** Already defined in `.env.example` — `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`. MinIO runs in docker-compose.
3. **Asset download:** Confirmed — download from S3 to a temp directory for FFmpeg processing.
4. **Template fonts:** User-customizable (from game profile `brand_guidelines` or brief). Default font bundled in `packages/api/assets/fonts/`. Templates accept an optional `font` param, falling back to the default.

## Context and Orientation

- **Files to read before starting:** `app/agents/concept_agent.py` (agent pattern), `app/providers/base.py` (Protocol pattern), `app/providers/llm/` (factory pattern), `app/tasks/render.py` (Celery task), `app/schemas/composition.py` (composition contract)
- **Patterns to follow:** Provider abstraction (`docs/conventions/provider-abstraction.md`), error handling (`docs/conventions/error-handling.md`), session lifecycle (`docs/conventions/session-lifecycle.md`)
- **Related decisions:** None yet — this is the first rendering implementation
- **Similar existing code:** `ConceptAgent` for agent orchestration, `LLMProvider` implementations for provider pattern, `JobService.create_job` for Celery dispatch pattern

## Steps

### Step 1: [DONE] Scene plan and execution plan schemas
**Files:**
- `packages/api/app/schemas/scene_plan.py` (create)
- `packages/api/app/schemas/execution_plan.py` (create)

**Tests:**
- `packages/api/tests/unit/schemas/test_scene_plan.py` (create)
- `packages/api/tests/unit/schemas/test_execution_plan.py` (create)

**What to do:**
Define Pydantic models for the Video Agent's input and internal data structures:

`scene_plan.py` — Models for the brief's `scene_plan` JSON (currently untyped `dict`):
- `Scene`: strategy (COMPOSE/GENERATE/RENDER), type (hook/real_gameplay/fake_gameplay/endcard/etc.), duration, plus strategy-specific fields: `asset_query` (COMPOSE), `generator`+`prompt` (GENERATE), `template`+`params` (RENDER). All scenes accept optional `font` for text customization.
- `AudioPlan`: voiceover (strategy, generator, script, optional `voice` for user-chosen ElevenLabs voice ID) and music (strategy, generator, prompt) — both optional
- `ScenePlan`: scenes (list[Scene]), audio (AudioPlan | None), validated with at least one scene

`execution_plan.py` — Models for the Video Agent's internal execution plan:
- `PreparedScene`: scene index, strategy, status (pending/ready/failed), output_path (path to prepared clip), error message
- `PreparedAudio`: type (voiceover/music), status, output_path
- `ExecutionPlan`: brief_id, scenes (list[PreparedScene]), audio (list[PreparedAudio]), work_dir (temp directory path)

Tests: Validate construction, required fields, strategy enum validation, scene_plan with missing scenes raises ValidationError.

**Verify:** `cd packages/api && pytest tests/unit/schemas/test_scene_plan.py tests/unit/schemas/test_execution_plan.py -v`

### Step 2: [DONE] TTS provider (ElevenLabs)
**Files:**
- `packages/api/app/providers/tts/__init__.py` (create)
- `packages/api/app/providers/tts/elevenlabs.py` (create)

**Tests:**
- `packages/api/tests/unit/providers/test_elevenlabs.py` (create)
- `packages/api/tests/unit/providers/test_tts_factory.py` (create)

**What to do:**
Implement the TTSProvider Protocol with an ElevenLabs backend:

`elevenlabs.py`:
- `ElevenLabsProvider` class with `httpx.AsyncClient`
- `synthesize(text, voice) -> bytes`: POST to ElevenLabs text-to-speech API, return audio bytes (mp3). `voice` param allows per-video customization; if empty/None, falls back to `ELEVENLABS_DEFAULT_VOICE` env var.
- `aclose()`: close the httpx client
- Config from env: `ELEVENLABS_API_KEY`, `ELEVENLABS_DEFAULT_VOICE` (fallback voice ID)

`__init__.py`:
- `get_tts_provider() -> TTSProvider`: factory function, reads `TTS_PROVIDER` env var (default: "elevenlabs")
- Raises `ValueError` for missing API key or unknown provider

Tests: Mock httpx calls, verify request format, verify `aclose()` closes client, verify factory raises on missing key. Follow patterns from `test_claude.py` and `test_llm_factory.py`.

**Verify:** `cd packages/api && pytest tests/unit/providers/test_elevenlabs.py tests/unit/providers/test_tts_factory.py -v`

### Step 3: [DONE] Music and image provider stubs
**Files:**
- `packages/api/app/providers/music/__init__.py` (create)
- `packages/api/app/providers/music/stub.py` (create)
- `packages/api/app/providers/image/__init__.py` (create)
- `packages/api/app/providers/image/stub.py` (create)

**Tests:**
- `packages/api/tests/unit/providers/test_music_stub.py` (create)
- `packages/api/tests/unit/providers/test_image_stub.py` (create)

**What to do:**
Create stub providers that satisfy the Protocol interfaces for MVP:

`music/stub.py`:
- `StubMusicProvider`: `generate(prompt, duration) -> bytes` returns silent WAV audio of the requested duration (generate valid WAV header + zero samples). No external API calls.
- `aclose()`: no-op

`image/stub.py`:
- `StubImageProvider`: `generate(prompt, width, height) -> bytes` returns a solid-color PNG of the requested dimensions using Pillow. Color derived from prompt hash for consistency. No external API calls.
- `aclose()`: no-op

Each `__init__.py` has a factory: `get_music_provider()`, `get_image_provider()`. Currently only returns stub. Follows the same factory pattern as LLM/TTS.

Tests: Verify returned bytes are valid WAV/PNG, correct dimensions/duration, factory returns correct type.

**Verify:** `cd packages/api && pytest tests/unit/providers/test_music_stub.py tests/unit/providers/test_image_stub.py -v`

### Step 4: [DONE] Programmatic template renderers
**Files:**
- `packages/api/app/rendering/templates/__init__.py` (create)
- `packages/api/app/rendering/templates/base.py` (create)
- `packages/api/app/rendering/templates/text_hook.py` (create)
- `packages/api/app/rendering/templates/endcard.py` (create)

**Tests:**
- `packages/api/tests/unit/rendering/test_text_hook.py` (create)
- `packages/api/tests/unit/rendering/test_endcard.py` (create)

**What to do:**
Implement the RENDER strategy's programmatic templates using Pillow for frame generation:

`base.py`:
- `TemplateRenderer` Protocol: `render(params: dict, duration: float, resolution: tuple[int, int], fps: int) -> bytes` — returns raw video frames as bytes (H.264 encoded via FFmpeg subprocess)
- `frames_to_video(frames: list[bytes], fps: int, resolution: tuple[int, int]) -> bytes` — helper that pipes PIL Image frames through FFmpeg stdin to produce MP4 bytes

`text_hook.py` — `TextHookRenderer`:
- Renders animated text on a colored background
- Params: `text` (required), `font` (optional, path to .ttf — falls back to bundled default), `font_size`, `bg_color`, `text_color`, `animation` (fade_in/slide_up/none)
- Generates frames using Pillow: text centered, with simple animation (opacity ramp for fade_in, y-offset ramp for slide_up)

`endcard.py` — `EndcardRenderer`:
- Renders a game logo/icon + CTA text + app store badge area
- Params: `cta_text` (required), `font` (optional, falls back to bundled default), `bg_color`, `game_name`
- Static frames (no animation needed for endcard)

`__init__.py`:
- `TEMPLATE_REGISTRY: dict[str, TemplateRenderer]` mapping template names to renderer instances
- `get_template(name: str) -> TemplateRenderer` with `ValueError` for unknown templates

Tests: Verify renderers produce non-empty bytes, correct frame count for duration, template registry lookup works, unknown template raises ValueError.

**Verify:** `cd packages/api && pytest tests/unit/rendering/test_text_hook.py tests/unit/rendering/test_endcard.py -v`

### Step 5: [DONE] FFmpeg assembler
**Files:**
- `packages/api/app/rendering/assembler.py` (create)

**Tests:**
- `packages/api/tests/unit/rendering/test_assembler.py` (create)

**What to do:**
Implement the ASSEMBLE phase — takes a Composition and prepared asset files, produces a final MP4:

`assembler.py`:
- `AssemblerError` exception for FFmpeg failures
- `assemble(composition: Composition, asset_map: dict[str, str], output_path: str) -> str`:
  - `composition`: the Composition schema (duration, resolution, fps, layers)
  - `asset_map`: maps layer asset_id/content references to local file paths
  - `output_path`: where to write the final MP4
  - Returns the output_path on success
- Builds an FFmpeg command that:
  - Inputs all referenced video/audio/image files
  - Applies trim filters for video layers with `trim` field
  - Overlays layers in timeline order using `overlay` filter
  - Draws text for text layers using `drawtext` filter (with font, position, timing)
  - Mixes audio tracks with volume adjustment
  - Encodes to H.264 MP4 at the specified resolution and fps
- Uses `subprocess.run` with timeout, captures stderr for error reporting
- Parses FFmpeg exit code and stderr to produce human-readable `AssemblerError` messages
- `probe_duration(file_path: str) -> float`: uses `ffprobe` to get media file duration

Tests: Unit tests mock `subprocess.run` to verify correct FFmpeg command construction. Test that AssemblerError is raised on non-zero exit code. Test command building for: video-only composition, audio+video, text overlay, trimmed clips.

**Verify:** `cd packages/api && pytest tests/unit/rendering/test_assembler.py -v`

### Step 6: [DONE] Video Agent — PLAN phase
**Files:**
- `packages/api/app/agents/video_agent.py` (create)

**Tests:**
- `packages/api/tests/unit/agents/test_video_agent_plan.py` (create)

**What to do:**
Implement the first phase of the Video Agent — parsing a brief's scene plan into an execution plan:

`video_agent.py`:
- `VideoAgentError` exception (mirrors `ConceptAgentError`)
- `VideoAgent` class:
  - Constructor accepts: `tts_provider: TTSProvider`, `music_provider: MusicProvider`, `image_provider: ImageProvider`, `asset_repo: AssetRepository` (for COMPOSE asset lookup)
  - `async def produce(self, brief: BriefRead, work_dir: str) -> str`: main entry point, runs all 4 phases, returns output file path
  - `def plan(self, brief: BriefRead, work_dir: str) -> ExecutionPlan`: PLAN phase
    - Validates brief has scene_plan with scenes
    - Parses scene_plan dict into ScenePlan Pydantic model
    - Creates ExecutionPlan with PreparedScene entries (one per scene, status=pending)
    - Creates PreparedAudio entries for voiceover/music if present
    - Sets work_dir on the execution plan
    - For COMPOSE scenes: validates that matching assets exist via asset_repo query (looks up by project_id + asset_type). Raises `VideoAgentError` if required assets are missing.
    - Returns the ExecutionPlan

Tests: Test plan phase with valid scene_plan produces correct ExecutionPlan. Test missing scene_plan raises error. Test COMPOSE scene with no matching assets raises error. Test mixed strategy scene plans (COMPOSE + GENERATE + RENDER).

**Verify:** `cd packages/api && pytest tests/unit/agents/test_video_agent_plan.py -v`

### Step 7: [DONE] Video Agent — PREPARE phase
**Files:**
- `packages/api/app/agents/video_agent.py` (modify)

**Tests:**
- `packages/api/tests/unit/agents/test_video_agent_prepare.py` (create)

**What to do:**
Implement the PREPARE phase — executes all scene preparation tasks:

Add to `VideoAgent`:
- `async def prepare(self, plan: ExecutionPlan) -> ExecutionPlan`: PREPARE phase
  - Iterates over scenes in the execution plan
  - For each scene by strategy:
    - **COMPOSE**: Download asset from S3 to work_dir (placeholder: copy from local path). Trim to scene duration using FFmpeg (`ffmpeg -i input -ss start -t duration -c copy output`). Update PreparedScene with output_path, status=ready.
    - **GENERATE**: Call the appropriate provider (image_provider.generate for image scenes). Write output bytes to work_dir. Update PreparedScene with output_path, status=ready.
    - **RENDER**: Look up template in TEMPLATE_REGISTRY, call `render()` with scene params. Write output bytes to work_dir. Update PreparedScene with output_path, status=ready.
  - For audio:
    - Voiceover: call `tts_provider.synthesize(script, voice)`, write to work_dir
    - Music: call `music_provider.generate(prompt, duration)`, write to work_dir
  - On any provider/template error: set PreparedScene.status=failed with error_message, continue to next scene (don't abort entire pipeline — the brief may still be usable with partial scenes)
  - After all preparation: if ALL scenes failed, raise `VideoAgentError`. Otherwise return updated ExecutionPlan.

Tests: Mock all providers. Test COMPOSE scene preparation writes file and sets status=ready. Test GENERATE scene calls correct provider. Test RENDER scene calls template registry. Test audio preparation. Test partial failure (one scene fails, others succeed). Test total failure raises VideoAgentError.

**Verify:** `cd packages/api && pytest tests/unit/agents/test_video_agent_prepare.py -v`

### Step 8: [DONE] Video Agent — ASSEMBLE, POST-PROCESS, and Celery integration
**Files:**
- `packages/api/app/agents/video_agent.py` (modify)
- `packages/api/app/tasks/render.py` (modify)
- `packages/api/app/routes/dependencies.py` (modify)

**Tests:**
- `packages/api/tests/unit/agents/test_video_agent_assemble.py` (create)
- `packages/api/tests/unit/tasks/test_render.py` (modify — update existing placeholder tests)

**What to do:**

**ASSEMBLE phase** — add to `VideoAgent`:
- `def assemble(self, plan: ExecutionPlan) -> Composition`: builds a `Composition` from the prepared scenes
  - Creates CompositionLayer entries from each ready PreparedScene (maps output_path to asset references, sets timeline positions based on cumulative duration)
  - Adds audio layers for voiceover and music
  - Returns the Composition
- `def build_and_render(self, composition: Composition, plan: ExecutionPlan) -> str`: calls `assembler.assemble()` with the composition and asset map, returns output path

**POST-PROCESS phase** — add to `VideoAgent`:
- `async def post_process(self, output_path: str, job_id: str) -> str`: uploads the rendered MP4 to S3, returns the S3 key
  - S3 key format: `renders/{job_id}/output.mp4`
  - Uses boto3 client configured from existing env vars: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`
  - For MVP: if S3 is not configured, skip upload and return local path

**Wire the full `produce()` method:**
- `produce(brief, work_dir)` calls: plan → prepare → assemble → build_and_render → post_process
- Wraps in try/finally to clean up work_dir temp files

**Update `tasks/render.py`:**
- Replace placeholder with actual Video Agent invocation
- Create providers (TTS, music, image) and asset repo within the task
- Fetch the brief from DB (need brief data for scene_plan)
- Create a temp directory for work_dir
- Call `video_agent.produce(brief, work_dir)`
- Update job with: composition JSON, output_s3_key, render_duration_ms, status=done
- On failure: status=failed with error_message
- Clean up providers (aclose) in finally block
- Note: Celery tasks are sync, but providers are async. Use `asyncio.run()` to bridge (same pattern used in other sync→async bridges)

**Update `routes/dependencies.py`:**
- No new route dependencies needed (the task creates its own providers internally since it runs in a separate Celery worker process)

Tests for assemble: Mock assembler, verify Composition is built correctly from execution plan. Test timeline positioning. Test audio layer inclusion.
Tests for render task: Update existing tests to verify the full pipeline is invoked. Mock VideoAgent.produce, verify it's called with correct args. Test failure path still sets job to failed.

**Verify:** `cd packages/api && pytest tests/unit/agents/test_video_agent_assemble.py tests/unit/tasks/test_render.py -v`

## Validation

After all steps are complete, run the full verification suite:

1. `cd packages/api && ruff check .` — lint passes
2. `cd packages/api && pytest -x` — all tests pass
3. `bash enforcement/run-all.sh` — architectural enforcement passes

Expected outcomes:
- All existing tests continue to pass (no regressions)
- New test files cover: scene plan schemas, execution plan schemas, TTS provider, music stub, image stub, text hook template, endcard template, FFmpeg assembler, Video Agent PLAN/PREPARE/ASSEMBLE phases, updated render task
- The render task invokes the full Video Agent pipeline instead of the placeholder
- Provider factory pattern is consistent with existing LLM provider pattern
- Import direction is respected: models -> schemas -> repositories -> services -> agents -> routes

## Decision Log

1. **Test frame resolution reduced** — Template renderer tests originally used 1080x1920 at 30fps which caused OOM when running the full test suite (432+ tests). Reduced to 100x100 at 10fps for unit tests. Production resolution is validated by the schema, not the unit tests.
2. **asyncio.run() bridge in Celery task** — Celery tasks are synchronous but providers are async. Used `asyncio.run()` to bridge, with provider cleanup in a separate `asyncio.run()` call in the `finally` block.
3. **Lazy imports in render task** — Provider factories and VideoAgent are imported inside `_run_video_agent()` to avoid circular imports and heavy module loading at worker startup.
