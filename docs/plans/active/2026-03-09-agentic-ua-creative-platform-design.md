# Magnet — Agentic UA Creative Performance Platform

## Design Document

**Date:** 2026-03-09
**Status:** Approved

---

## 1. Overview

Magnet is an agentic AI platform for mobile game user acquisition (UA) creative production. It generates diverse creative concepts from a game profile, then produces video ads through a three-strategy system: COMPOSE real assets, GENERATE AI elements, and RENDER programmatic templates — all assembled via FFmpeg. The system uses provider-agnostic interfaces throughout, allowing model/service swaps via configuration.

### Core Value Proposition

Remove the production bottleneck in game UA. Instead of the traditional linear flow (brief → production → resize → iterate → test → often fail), Magnet enables continuous concept exploration and testing at scale, so teams find winning creatives faster.

---

## 2. Architecture

### Service-Oriented Hybrid (Python + TypeScript)

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│                    Next.js (TypeScript)                               │
│   Dashboard · Upload · Brief Review · Preview · Creative Library     │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ REST / WebSocket
┌──────────────────────────▼───────────────────────────────────────────┐
│                      API GATEWAY                                     │
│                  FastAPI (Python)                                     │
│         Auth · Rate Limiting · Request Routing                       │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                                 │
│                  Python (Celery + Redis)                              │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │              AGENTIC PIPELINE CONTROLLER                     │     │
│  │  Manages the flow: Concept → Production → QA → Delivery     │     │
│  └──────┬──────────────┬──────────────┬────────────────────────┘     │
│         │              │              │                               │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌────▼─────────┐                    │
│  │  Concept    │ │  Video     │ │  QA          │                     │
│  │  Agent      │ │  Agent     │ │  Agent       │                     │
│  │  (LLM)     │ │  (FFmpeg)  │ │  (LLM+CV)   │                     │
│  └─────────────┘ └────────────┘ └──────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                      DATA LAYER                                      │
│  PostgreSQL        Redis           S3/MinIO        Vector DB         │
│  (metadata,        (queue,         (assets,        (Qdrant -         │
│   projects,        cache,          renders)        embeddings,       │
│   users)           sessions)                       later)            │
└──────────────────────────────────────────────────────────────────────┘
```

### Why Hybrid (Python + TypeScript)

The product requires both deep ML/CV capabilities and interactive web/JS output:

- **Python side:** LLM orchestration, video processing (FFmpeg, PySceneDetect, OpenCV), ML models (scene detection, performance prediction, creative embeddings), all agent logic.
- **TypeScript side:** Web application (Next.js), and later, playable ad generation (HTML5/JS output IS JavaScript — Phaser.js, PixiJS).

### Why Service-Oriented

- Team will expand — separate services = parallel development.
- Multiple coding agents working simultaneously — service boundaries = no merge conflicts.
- Each service maps to a different domain and skillset.

---

## 3. Data Model

### Core Entities

**User** — id, email, name, org_id, role, created_at

**Project** — id, user_id, name, status, created_at

**GameProfile** — id, project_id, genre, target_audience, core_mechanics[], art_style, brand_guidelines (jsonb), competitors[], key_selling_points[]

**Asset** — id, project_id, type (gameplay/screenshot/logo/character/audio), s3_key, duration, dimensions, metadata (jsonb), created_at

**CreativeBrief** — id, project_id, hook_type, narrative_angle, script, target_emotion, cta_text, reference_ads[], target_format, target_duration, status (draft/approved/producing/complete), generated_by (agent/human), created_at

**RenderJob** — id, brief_id, status (queued/rendering/done/failed), template_id, composition (jsonb), output_s3_key, render_duration_ms, error_message, created_at

### Composition JSON (the contract between AI and rendering)

The `RenderJob.composition` field fully describes the video as a layered timeline:

```json
{
  "duration": 15,
  "resolution": [1080, 1920],
  "fps": 30,
  "layers": [
    {
      "type": "video",
      "asset_id": "asset_123",
      "start": 0,
      "end": 8,
      "trim": [12.5, 20.5],
      "position": [0, 0],
      "effects": ["zoom_in_slow"]
    },
    {
      "type": "text",
      "content": "Can you beat level 50?",
      "font": "brand_bold",
      "start": 0,
      "end": 3,
      "position": "top_center",
      "animation": "fade_in"
    },
    {
      "type": "audio",
      "asset_id": "asset_456",
      "start": 0,
      "end": 15,
      "volume": 0.8
    }
  ]
}
```

### Storage Strategy

| Data | Store | Why |
|------|-------|-----|
| Users, projects, briefs, jobs | PostgreSQL | Relational, queryable, transactional |
| Uploaded assets, rendered videos | S3/MinIO | Blob storage, CDN-compatible |
| Job queue, cache, sessions | Redis | Fast, ephemeral, pub/sub for WebSocket |
| Composition JSON | PostgreSQL JSONB | Queryable, versioned with the job record |
| Creative embeddings (later) | Qdrant | Vector similarity search at scale |

### Deferred Entities

- `PerformanceMetrics` — CTR, IPM, spend per creative (comes with ad network integration)
- `CreativeEmbedding` — vector representations for similarity/trend detection
- `Template` — reusable video templates (for now, templates live as code)

---

## 4. Agentic Pipeline — Concept Agent

### Three-Step Chained Approach

**Step 1: STRATEGIZE** — LLM analyzes game profile, identifies hook categories that fit genre, selects emotional angles. Output: list of creative directions.

**Step 2: EXPAND** — For each direction, LLM generates a full brief with shot-by-shot scene plan (including strategy tags: COMPOSE/GENERATE/RENDER), script, voiceover text, CTA options. Output: list of CreativeBriefs.

**Step 3: DIVERSIFY** — LLM reviews all generated briefs, checks for redundancy, suggests mutations on promising directions. Output: final diverse set.

### Hook Taxonomy (built into system prompts)

| Hook Category | Examples | Best for |
|---------------|----------|----------|
| Fail/Challenge | "I can't get past level 5", "99% fail" | Casual, puzzle |
| Satisfaction | Oddly satisfying loops, ASMR-style | Idle, merge, casual |
| Comparison | "Level 1 vs Level 100", "Noob vs Pro" | RPG, strategy |
| Emotional | Story-driven narrative, character journey | RPG, narrative |
| UGC-style | Fake reaction, "I found this game and..." | All genres |
| Fake gameplay | Pin-pull, choice-based, exaggerated mechanics | Casual, hyper-casual |
| FOMO/Social | "Everyone's playing this", trending parody | All genres |
| Tutorial bait | "Here's a trick most players don't know" | Strategy, mid-core |

This taxonomy is extensible. Later, the Intelligence Agent feeds trending patterns in automatically.

### Prompt Architecture

Each step gets a focused system prompt with structured output (JSON mode). Chained, not monolithic — allows independent tuning per step.

### Provider Abstraction

```python
class LLMProvider(Protocol):
    async def generate(self, messages: list, schema: dict) -> dict: ...

class ClaudeProvider(LLMProvider): ...
class OpenAIProvider(LLMProvider): ...
```

Same pattern for all providers (TTS, music, image, video gen).

---

## 5. Video Agent — Production Pipeline

### Four Phases

**Phase 1: PLAN** — Parse brief's scene plan. Match COMPOSE scenes to available assets. Identify GENERATE and RENDER tasks. Output: ExecutionPlan with dependency graph.

**Phase 2: PREPARE** (parallelized) — Execute all scene preparation tasks concurrently where possible:

- **COMPOSE:** Analyze source assets, run scene detection, select best segments via LLM, crop/resize.
- **GENERATE:** Dispatch to external APIs — TTS, music, image, video generation.
- **RENDER:** Execute programmatic templates — text hooks, fake gameplay, endcards.

**Phase 3: ASSEMBLE** — Build FFmpeg filter graph from composition JSON. Layer video clips on timeline with transitions. Mix audio tracks. Apply global effects. Encode to final MP4.

**Phase 4: POST-PROCESS** — Encode to ad network specs, generate thumbnail, upload to S3, update RenderJob status.

### Three Scene Strategies

```
                    CreativeBrief
                         │
            ┌────────────▼────────────────┐
            │     SCENE PLANNER           │
            │  Each scene tagged with:    │
            │    COMPOSE / GENERATE /     │
            │    RENDER                   │
            └─────┬──────┬──────┬────────┘
                  │      │      │
         ┌────────▼┐  ┌──▼──────▼──┐  ┌────────────┐
         │COMPOSE  │  │ GENERATE   │  │  RENDER    │
         │Real     │  │AI-created  │  │Programmatic│
         │assets   │  │elements    │  │templates   │
         └────┬────┘  └─────┬──────┘  └─────┬──────┘
              └─────────────▼───────────────┘
                     ASSEMBLER (FFmpeg)
                         │
                    Final Video
```

**COMPOSE** — Use real uploaded assets. Trim gameplay footage, crop screenshots, overlay text. Fast, reliable, authentic. Essentially free after infrastructure costs.

**GENERATE** — AI-creates elements that don't exist. Hook scenes, voiceovers, soundtracks, AI avatars, novel imagery. This is where novelty and scale come from. Uses external APIs (ElevenLabs, Suno, image/video gen models — provider-agnostic, swappable via config).

**RENDER** — Programmatically code-render scenes. Animated text sequences, UI mockups, fake gameplay mechanics, progress bars, stat comparisons. Too structured for gen models, too dynamic for static templates. MVP uses Pillow + Cairo for frame-by-frame generation → FFmpeg encode.

### Scene Plan Example (LLM output)

```json
{
  "scenes": [
    {
      "strategy": "GENERATE",
      "type": "hook",
      "duration": 2,
      "generator": "heygen",
      "prompt": "Young woman looking at phone, shocked expression"
    },
    {
      "strategy": "RENDER",
      "type": "fake_gameplay",
      "duration": 4,
      "template": "pin_pull_fail",
      "params": {"difficulty": "obvious_fail", "theme": "water"}
    },
    {
      "strategy": "COMPOSE",
      "type": "real_gameplay",
      "duration": 5,
      "asset_query": "gameplay footage, most action-dense segment"
    },
    {
      "strategy": "COMPOSE",
      "type": "endcard",
      "duration": 2,
      "template": "endcard_standard"
    }
  ],
  "audio": {
    "voiceover": {
      "strategy": "GENERATE",
      "generator": "elevenlabs",
      "script": "Think you can do better? Download now and prove it!"
    },
    "music": {
      "strategy": "GENERATE",
      "generator": "suno",
      "prompt": "upbeat casual game background music, 15 seconds"
    }
  }
}
```

### Execution Plan & Parallelism

Independent tasks (TTS, music gen, asset trimming) run in parallel via Celery. Template rendering can depend on generated assets. Assembly waits for all preparation tasks. Celery `chord` and `chain` primitives express the dependency graph.

### Transition Library (MVP)

| Transition | Implementation |
|-----------|----------------|
| Hard cut | FFmpeg concat |
| Cross dissolve | FFmpeg `xfade=fade` |
| Swipe (L/R/U/D) | FFmpeg `xfade=slideleft` |
| Zoom through | Scale + position keyframes |
| Flash/white | Brightness spike between clips |

### Error Handling

- External API calls: automatic retry with exponential backoff.
- Failed GENERATE tasks: job marked failed with clear error, not silently degraded.
- FFmpeg errors: parsed and surfaced as human-readable messages.
- Each phase checkpoints to S3 — retries don't re-generate prepared clips.

---

## 6. Web Application

### Tech Stack

| Layer | Choice | Reasoning |
|-------|--------|-----------|
| Framework | Next.js 14+ (App Router) | SSR, API routes for BFF, strong DX |
| Styling | Tailwind + shadcn/ui | Fast to build, consistent components |
| State | React Query + Zustand | Server state + UI state |
| Video preview | HTML5 `<video>` | Native, no dependencies |
| File upload | Presigned S3 URLs (resumable) | Large gameplay footage support |
| Real-time | WebSocket (Socket.IO or native WS) | Pipeline progress pushed to client |
| Auth | Clerk (MVP) | Fast setup, migrate later if needed |

### Core Screens

1. **Project Setup** — Game name, genre, mechanics, audience, art style, brand guidelines, competitors, key selling points.
2. **Asset Upload** — Drag-and-drop for gameplay video, screenshots, logos, character art, audio.
3. **Concept Review** — Browse generated briefs with hook type, emotion, scene-by-scene plan. Edit, approve, or discard. Optional user direction ("try humor hooks").
4. **Production & Preview** — Real-time pipeline progress via WebSocket. Video player when complete.
5. **Creative Library** — Browse all produced creatives. Filter, sort, download.

### API Endpoints

```
POST   /api/projects                    → Create project + game profile
POST   /api/projects/:id/assets         → Get presigned upload URL
POST   /api/projects/:id/concepts       → Trigger concept generation
GET    /api/projects/:id/briefs         → List generated briefs
PATCH  /api/briefs/:id                  → Edit a brief
POST   /api/briefs/:id/produce          → Trigger video production
GET    /api/jobs/:id                    → Poll job status
GET    /api/jobs/:id/stream             → WebSocket for real-time progress
GET    /api/creatives                   → List completed videos
GET    /api/creatives/:id/download      → Presigned download URL
```

### Real-Time Progress

Celery workers publish state changes to Redis pub/sub keyed by job ID. API gateway subscribes and forwards to WebSocket clients.

---

## 7. Deployment & Infrastructure

### Dev Environment

Single `docker-compose up` boots the full stack:

- **web** — Next.js (port 3000)
- **api** — FastAPI (port 8000)
- **worker** — Celery (N replicas)
- **postgres** — PostgreSQL 16
- **redis** — Redis 7
- **minio** — S3-compatible object storage

### Production

| Component | Service |
|-----------|---------|
| Web (Next.js) | Vercel or AWS ECS |
| API (FastAPI) | AWS ECS Fargate or Railway |
| Workers (Celery) | AWS ECS Fargate (key scaling unit) |
| PostgreSQL | AWS RDS or Supabase |
| Redis | AWS ElastiCache or Upstash |
| Object Storage | AWS S3 |
| CDN | CloudFront |

### Scaling Strategy

The bottleneck is rendering (CPU-bound FFmpeg). LLM and API calls are I/O-bound.

- **Low load:** 2 workers handle everything.
- **Medium load:** Split into "generate" queue (I/O workers, cheap) and "render" queue (CPU workers, beefy).
- **High load:** Add "ml" queue with GPU workers for scene detection, embeddings, etc.

Celery named queues and worker routing handle this natively.

### Cost Estimate (~100 videos/month)

| Category | Monthly Cost |
|----------|-------------|
| Infrastructure (ECS, RDS, Redis, S3, CDN) | ~$90-120 |
| External APIs (TTS, music, LLM, image gen) | ~$130-310 |
| **Total** | **~$220-430** |

Video generation APIs (Runway/Kling) are the cost wildcard. COMPOSE and RENDER strategies are essentially free.

### Monorepo Structure

```
magnet/
├── docker-compose.yml
├── .env.example
├── packages/
│   ├── web/                    # Next.js frontend
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── package.json
│   │   └── Dockerfile
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   ├── agents/
│   │   │   │   ├── concept_agent.py
│   │   │   │   └── video_agent.py
│   │   │   ├── providers/
│   │   │   │   ├── base.py     # Abstract interfaces
│   │   │   │   ├── llm/
│   │   │   │   ├── tts/
│   │   │   │   ├── music/
│   │   │   │   ├── image/
│   │   │   │   └── video/
│   │   │   ├── rendering/
│   │   │   │   ├── assembler.py
│   │   │   │   ├── templates/
│   │   │   │   └── composer.py
│   │   │   ├── worker.py
│   │   │   └── tasks/
│   │   ├── alembic/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── shared/                 # Shared types/constants
├── scripts/
│   ├── seed.py
│   └── test_pipeline.py
└── docs/
    └── plans/
```

---

## 8. MVP Scope

### In Scope

- Project setup with game profile
- Asset upload (gameplay video, screenshots, logos, character art)
- Concept Agent: generates 10+ diverse creative briefs per run
- Brief review, editing, approval
- Video production: full PLAN → PREPARE → ASSEMBLE → POST-PROCESS pipeline
- COMPOSE strategy: trim and select from uploaded footage
- GENERATE strategy: TTS voiceover, music generation, image generation
- RENDER strategy: 3-5 templates (text hook, endcard, stat comparison, simple fake gameplay)
- Real-time progress via WebSocket
- Preview and download
- Creative library
- Basic auth (Clerk)
- Target format: 9:16 vertical, 15-30 seconds

### Deferred

| Feature | Phase |
|---------|-------|
| Playable ad generation (TypeScript service) | Phase 2 |
| Market intelligence agent | Phase 2 |
| Ad network integration (Meta, AppLovin, Unity) | Phase 2 |
| Performance feedback loop | Phase 2 |
| Multi-format output (1:1, 16:9) | Phase 2 |
| QA Agent (automated LLM + CV review) | Phase 2 |
| Video generation models (Runway/Kling) | Phase 2 |
| Scene detection via CV models | Phase 2 |
| Creative embeddings / vector search | Phase 3 |
| Performance prediction models | Phase 3 |
| Custom fine-tuned models | Phase 3 |
| Team collaboration / multi-user | Phase 3 |
| Creative fatigue prediction | Phase 3 |

---

## 9. Success Criteria

| Criteria | Metric |
|----------|--------|
| End-to-end works | Upload assets → get rendered video ad |
| Concept diversity | 10 briefs show meaningfully different angles |
| Output quality | Professional enough to run as a real UA ad |
| Production speed | Concept to rendered video in under 5 minutes |
| Reliability | 90%+ jobs complete without intervention |
| Template quality | Polished, not "developer art" |

---

## 10. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Generic/repetitive LLM concepts | Medium | Hook taxonomy, diversify step, user direction input |
| FFmpeg pipeline complexity | Medium | Tight composition JSON schema, incremental complexity |
| Voice/music tone mismatch | Medium | Tone/mood in prompts, per-element regeneration |
| Cheap-looking templates | High (complex ones) | Start with simple polished templates only |
| Linear API cost scaling | Certain | COMPOSE/RENDER are free, cache assets, use GENERATE strategically |
| Video gen models too slow/expensive | High | Deferred to Phase 2, MVP proves pipeline without them |
