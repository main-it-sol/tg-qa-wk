# Wiki Index

Master catalog of all wiki pages. Updated on every ingest / edit.

## Sources

- [[voice-backend-sketch]] — `sources/voice-backend-sketch.md` — Virtual Rabbi Phase 2 voice loop design sketch (WebSocket + PCM, no WebRTC). Source: `research/raw/articles/voice-backend-sketch.md`.
- [[software-testing-continuous-delivery]] — `sources/software-testing-continuous-delivery.md` — Atlassian primer on testing levels, CD pipeline-as-gate, and recommended test-mix strategy. Source: `research/raw/articles/software-testing-continuous-delivery.md`.

## Concepts

- [[voice-session-state-machine]] — `concepts/voice-session-state-machine.md` — Four-state `VoiceSession` orchestrator (IDLE / LISTENING / THINKING / SPEAKING) with barge-in.
- [[voice-wire-protocol]] — `concepts/voice-wire-protocol.md` — Single-WebSocket protocol: JSON text control frames + int16-LE PCM binary frames with utterance-id header server→client.
- [[voice-activity-detection]] — `concepts/voice-activity-detection.md` — Energy-based VAD with hysteresis; drives `speech_start` / `speech_end` events.
- [[barge-in]] — `concepts/barge-in.md` — User interrupts assistant mid-TTS; server emits `cancel`, client drains queued buffers by `utterance_id`.
- [[adapter-pattern-stt-llm-tts]] — `concepts/adapter-pattern-stt-llm-tts.md` — STT/LLM/TTS ABCs + fakes so tests run with no external services.
- [[testing-levels]] — `concepts/testing-levels.md` — The four conventional levels: unit, integration, functional/E2E, exploratory.
- [[testing-strategy]] — `concepts/testing-strategy.md` — Choosing where to spend test effort; test-type-by-deliverable heuristic.
- [[continuous-delivery]] — `concepts/continuous-delivery.md` — Test-gated automated pipeline; dev-owned quality replacing QA handoff.

## Entities

_(none yet)_

## Comparisons

_(none yet)_
