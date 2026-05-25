# Implementation Plan — Virtual Rabbi AI Platform (study.dbavach.com)

Based on `SPEC.md`. Concrete implementation steps grouped by phase.

## Step 0 — Project Setup (Week 1)

1. **Repository structure** (monorepo recommended):
   ```
   virt-rav/
   ├── backend/         # FastAPI app
   ├── ai-pipeline/     # ingestion + embeddings + fine-tuning
   ├── frontend/        # Next.js (rabbi panel + student panel)
   ├── infra/           # Docker, Kubernetes/Proxmox manifests
   └── docs/
   ```
2. Initialize Git, CI/CD (GitHub Actions), pre-commit hooks, `.env.example`.
3. Provision dev environment with Docker Compose: Postgres, Redis, Qdrant, MinIO (S3-compatible storage), an LLM endpoint (Ollama for local dev).

## Step 1 — Infrastructure (Weeks 1–3)

1. Provision the production server per spec (32–64 vCPU, 128–256 GB RAM, A100/H100 or 2–4× RTX 4090, NVMe 8–20 TB, 10 Gbps).
2. Install **Proxmox VE** (or k8s) and split nodes: AI-processing, database, frontend, vector DB.
3. Set up:
   - PostgreSQL (users, rabbis, lessons metadata, dialogues)
   - Redis (sessions, cache, queues)
   - Qdrant (vector embeddings — pick one of Qdrant/Weaviate/Milvus; Qdrant is simplest)
   - S3/MinIO (raw audio, video, books, PDFs)
4. Configure CUDA drivers, NVIDIA Container Toolkit, vLLM/Ollama server.
5. Reverse proxy: Nginx + TLS (Let's Encrypt) for `study.dbavach.com`.

## Step 2 — Core Backend (Weeks 2–5)

1. **FastAPI** service with modules:
   - `auth/` — JWT, roles (rabbi, student, admin)
   - `rabbis/` — rabbi profiles, character settings (formality, humor, depth, etc.)
   - `students/` — profiles (age, language, level, interests, history, spiritual goals)
   - `materials/` — upload endpoints for video/audio/text/books
   - `dialogues/` — chat sessions, message history, per-student memory
   - `moderation/` — review queue, rollback log, citation checks
2. Background jobs via **Celery** or **RQ** for ingestion.
3. gRPC service for high-throughput AI calls (frontend → backend → gRPC → vLLM).

## Step 3 — AI Ingestion Pipeline (Weeks 3–7)

Build the pipeline described in SPEC §AI Pipeline:

1. **Upload** materials (multi-source connectors: Facebook, YouTube, Telegram, Zoom, Podcast RSS, websites).
2. **Speech-to-Text** — Whisper (large-v3) with Hebrew/Yiddish/Russian/English support.
3. **OCR** for scanned books — Tesseract or PaddleOCR; for Hebrew use a Hebrew-tuned model.
4. **Structure analysis** — segment by lesson/topic/sefer (Mishnah, Talmud, Chasidut, Kabbalah, Halacha, Shulchan Aruch, Tanach, Mussar).
5. **Topic extraction** — LLM-based tagging.
6. **Embeddings** — multilingual model (e.g. `intfloat/multilingual-e5-large`) → store in Qdrant with rich metadata (rabbi_id, source_type, sefer, perek, language).
7. **Indexing** — hybrid search (BM25 + dense) for citations.
8. **Personality fine-tuning** — LoRA/QLoRA on rabbi's Q&A pairs over a base LLM (Llama 3.1/Mistral). Keep base model versioned for rollback.
9. **Memory system** — per-student long-term memory store (summarized facts in Postgres + episodic embeddings in Qdrant).
10. **Dialogue training** — instruction tuning on dialogue transcripts.

## Step 4 — MVP Chat (Phase 1, Weeks 6–10)

Goal from SPEC Phase 1 — **one rabbi, upload lessons, chat, material search, AI answers.**

1. Student-facing chat UI (Next.js + Tailwind, streaming responses via SSE).
2. RAG pipeline: query → embed → Qdrant top-k → rerank → LLM with rabbi's persona system prompt + retrieved passages → cited answer.
3. Citation enforcement — every answer must reference source (sefer, page, lesson URL).
4. Rabbi admin panel (basic): upload, view dialogues, edit/correct answers (feedback feeds back into fine-tuning dataset).
5. Deploy MVP at `study.dbavach.com`. Pilot with one rabbi.

## Step 5 — Phase 2: Memory, Voice, Personalization (Months 4–6)

1. **Student memory** — after each session, summarize and persist; load relevant memories on next login (personal greetings, progress awareness).
2. **Character controls** — sliders in rabbi panel (formality, strictness, humor, depth, emotionality, pace, audience level) that adjust system prompt + sampling params.
3. **Voice** — TTS with voice cloning (XTTS-v2, F5-TTS, or ElevenLabs Pro with rabbi's consent recordings). Real-time streaming TTS.
4. **STT for student** — Whisper streaming so student can speak questions.
5. **Telegram & WhatsApp bots** — bridge to the same backend (Telegram Bot API, WhatsApp Cloud API).

### Step 5a — Voice loop scaffold (current sketch, `backend/`)

Decisions locked while building the TDD sketch:

- **Transport:** FastAPI WebSocket only (no WebRTC for now). We accept that we own jitter handling and barge-in, in exchange for a much smaller surface area and easier tests. WebRTC stays a Phase-3 option behind the same `VoiceSession` interface.
- **Audio formats:** client mic → server is raw int16-LE PCM at the rate negotiated in `hello` (16 kHz typical). Server → client is int16-LE PCM at 24 kHz, with each binary frame prefixed by an 8-byte header `(utterance_id: uint32, seq: uint32, big-endian)`. Header lets the client flush queued `AudioBufferSourceNode`s by `utterance_id` on barge-in without parsing the payload.
- **Control plane:** JSON text frames sharing the WebSocket.
  - client → server: `hello`, `interrupt`
  - server → client: `hello`, `transcript`, `speech_start`, `speech_end`, `cancel`, `error`
- **State machine:** `IDLE → LISTENING → THINKING → SPEAKING → LISTENING`. Barge-in or explicit `interrupt` cancels the in-flight LLM/TTS task and emits `cancel{utterance_id}`.
- **VAD:** energy-based with hysteresis (`min_speech_ms`, `min_silence_ms`) behind a `VAD` Protocol so webrtcvad/silero can drop in later.
- **Adapters:** `STTAdapter`, `LLMAdapter`, `TTSAdapter` ABCs. Sketch ships fakes only — real Whisper / vLLM / XTTS wiring deferred. The orchestrator and tests do not depend on any external service.
- **Resampling:** done client-side by the browser AudioContext for now. Server-side resample is on the next-slice list once we settle on the real TTS engine's native rate.
- **Testing:** pytest + pytest-asyncio (auto mode), 33 tests covering protocol, VAD, fakes, session state machine, and WebSocket integration via Starlette `TestClient`. All green.

Next slices, not yet built:

1. Audio → viseme/blendshape stream emitted alongside PCM (drives the 2D Live2D/Spine avatar).
2. Server-side resampler so we quote a single sample rate to all clients.
3. Per-session jitter buffer / pacing so the client never starves while still allowing snappy barge-in.
4. Echo-cancellation strategy (client AEC + server-side energy gate while SPEAKING).

## Step 6 — Safety & Moderation (parallel, ongoing)

1. Moderation queue: every AI answer scored for halachic risk → flagged ones go to rabbi for review before delivery (configurable per-topic).
2. Distortion guard: refuse to answer outside rabbi's known corpus; respond "I don't know" rather than hallucinate.
3. Source verification: regex/LLM check that every cited verse/sugya exists in the source corpus.
4. Full audit log of every prompt, response, model version, and retrieval set. Rollback to prior model snapshot on demand.
5. Rabbi approval workflow for new lessons before they enter training data.

## Step 7 — Phase 3: Avatars, Live Voice, Multi-Agent (Months 7–12)

1. **Avatars** — HeyGen/D-ID API or self-hosted SadTalker + Wav2Lip for lip-sync video.
2. **Real-time avatar** — LiveKit/WebRTC streaming of TTS + lip-synced video.
3. **Multi-agent** — separate specialist agents per discipline (Talmud agent, Halacha agent, Chasidut agent) orchestrated by a router agent in LangChain/LangGraph.
4. **Automatic course generation** — LLM builds curriculum from rabbi's materials; student progress tracking, homework, spiritual journal.
5. **AI-chevruta** — two students + AI study partner.
6. **Knowledge graph** — Neo4j linking sources, topics, rabbi's positions; powers citation and cross-reference UX.

## Step 8 — Scale (Months 12+)

1. Onboarding flow for 10–50 rabbis; per-rabbi isolated vector namespace + LoRA adapter.
2. Multi-tenant billing.
3. Multilingual expansion (Hebrew, English, Russian, Yiddish, French, Spanish).
4. International CDN, GPU autoscaling.

---

## Suggested Order to Start Tomorrow

1. Stand up the dev Docker Compose (Postgres + Redis + Qdrant + MinIO + Ollama).
2. Scaffold FastAPI with `auth`, `rabbis`, `materials` modules.
3. Implement upload + Whisper transcription + embedding into Qdrant.
4. Build minimal RAG chat against one rabbi's transcribed lessons.
5. Show it to the pilot rabbi, get feedback, iterate.
