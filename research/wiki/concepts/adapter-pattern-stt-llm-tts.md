---
title: STT / LLM / TTS Adapter Pattern
type: concept
sources:
  - research/raw/articles/voice-backend-sketch.md
related:
  - "[[voice-backend-sketch]]"
  - "[[voice-session-state-machine]]"
  - "[[testing-levels]]"
  - "[[testing-strategy]]"
created: 2026-05-25
updated: 2026-05-26
confidence: high
---

# STT / LLM / TTS Adapter Pattern

`src/virtrav/voice/adapters.py` defines three abstract base classes — `STTAdapter`, `LLMAdapter`, `TTSAdapter` — and ships fake implementations alongside them. The `VoiceSession` orchestrator and the entire test suite only ever see the ABCs.

## What each ABC covers

- **`STTAdapter`** — streaming speech-to-text. Real implementation target: faster-whisper streaming.
- **`LLMAdapter`** — text in, streaming text out. Real implementation targets: vLLM, Ollama, Anthropic.
- **`TTSAdapter`** — text in, streaming PCM out. Real implementation targets: XTTS-v2, Piper, ElevenLabs.

## Why ABCs + fakes (the testing payoff)

The sketch's `tests/` directory uses pytest with "fakes only — no external services." This is the entire point of the adapter layer:

- No GPU required to run the test suite.
- No network, no API keys, no rate limits in CI.
- Deterministic timing — fakes can emit PCM chunks on a synthetic clock, so the [[voice-session-state-machine]] can be asserted at exact tick boundaries.

In [[testing-levels]] terms, this gives the project cheap unit + integration coverage of the orchestrator; in [[testing-strategy]] terms, those are exactly the high-value targets for headless code crossing third-party seams.

## Why three ABCs, not one

A naive "voice pipeline" interface (`audio in → audio out`) would hide the seams where the actual choices live: which STT, which LLM, which voice. The three-ABC split lets a deployment mix and match — e.g. faster-whisper + Ollama + Piper for fully-local, or faster-whisper + Anthropic + ElevenLabs for best quality.

## Where the orchestrator lives

The session orchestrator ([[voice-session-state-machine]]) holds one instance of each ABC and wires them together. Swapping any one of them does not touch session code or tests. This is the explicit invariant the sketch claims: "The session orchestrator and tests stay untouched."

## What is *not* abstracted

- The wire protocol ([[voice-wire-protocol]]) is fixed — it is the contract with the client, not with a backend.
- VAD ([[voice-activity-detection]]) is not behind an ABC in this slice. Could be later, with the same justification, if a heavier model is wanted.
