---
title: Virtual Rabbi — Voice Backend Sketch
type: source-summary
sources:
  - research/raw/articles/voice-backend-sketch.md
related:
  - "[[voice-session-state-machine]]"
  - "[[voice-wire-protocol]]"
  - "[[voice-activity-detection]]"
  - "[[barge-in]]"
  - "[[adapter-pattern-stt-llm-tts]]"
created: 2026-05-25
updated: 2026-05-25
confidence: high
---

# Virtual Rabbi — Voice Backend Sketch

TDD scaffold for the Phase 2 voice loop of the Virtual Rabbi project. Deliberately avoids WebRTC; uses raw WebSocket + int16-LE PCM + Web Audio on the client. The orchestration layer is designed so a later 2D avatar can be driven from the same TTS stream via blendshapes.

## Scope of the source

- Layout of `src/virtrav/voice/` (protocol, vad, adapters, session, ws) and `tests/`
- Wire protocol over a single WebSocket (text JSON + binary PCM)
- Session state machine with barge-in
- Adapter ABCs for STT/LLM/TTS so tests run against fakes only
- Explicitly-deferred work: avatar driver, server-side resampler, jitter buffer, echo cancellation

## Key design choices

- **No WebRTC.** A single WebSocket carries both control and audio. Reduces moving parts; trades off built-in NAT traversal, congestion control, and AEC.
- **Binary header on server→client only.** Frames are 8 bytes: `(utterance_id: uint32, seq: uint32, big-endian)` + int16-LE PCM. The client uses `utterance_id` to drop queued buffers on `cancel`. See [[voice-wire-protocol]].
- **Energy-based VAD with hysteresis.** No ML model in the hot path. See [[voice-activity-detection]].
- **Four-state session.** `IDLE → LISTENING → THINKING → SPEAKING`, with barge-in collapsing `SPEAKING → LISTENING` and emitting a `cancel`. See [[voice-session-state-machine]] and [[barge-in]].
- **ABCs for STT/LLM/TTS.** Real adapters (faster-whisper, vLLM/Ollama/Anthropic, XTTS-v2/Piper/ElevenLabs) plug into the same orchestrator that the test fakes use. See [[adapter-pattern-stt-llm-tts]].

## Out of scope (per the source)

1. Avatar driver — audio→viseme/blendshape stream alongside PCM.
2. Server-side resampler so the client can be told one sample rate.
3. Per-session jitter buffer / pacing so the client never starves.
4. Echo cancellation hint (client AEC + server energy gate during `SPEAKING`).

## Confidence

High for what is in the source; the source is the canonical design sketch. Anything beyond the four bullets above (perf numbers, choice of real adapter, deployment topology) is not covered here.
