---
title: Voice Activity Detection (energy + hysteresis)
type: concept
sources:
  - research/raw/articles/voice-backend-sketch.md
related:
  - "[[voice-backend-sketch]]"
  - "[[voice-session-state-machine]]"
  - "[[voice-wire-protocol]]"
created: 2026-05-25
updated: 2026-05-25
confidence: medium
---

# Voice Activity Detection (energy + hysteresis)

VAD lives in `src/virtrav/voice/vad.py`. It decides, from the inbound mic PCM stream, when the user has started and stopped speaking — driving the `speech_start` / `speech_end` events that move [[voice-session-state-machine]] between `LISTENING` and `THINKING`.

## Approach

- **Energy-based**, not ML. The detector looks at short-term signal energy (typically RMS) rather than running a neural classifier.
- **Hysteresis** — two thresholds (or two timing windows) so that the detector does not flip rapidly between speech / no-speech around a single threshold. A higher bar to *enter* speech, a lower bar (and/or longer silence) to *exit* it.

The sketch does not pin specific threshold values, frame sizes, or window lengths; those are implementation knobs.

## Why energy + hysteresis (and not WebRTC VAD or Silero)

- Fits the "fakes only, no external services" testing constraint — energy is trivial to compute in pure Python over numpy arrays.
- Deterministic and inspectable; tests can feed synthetic PCM and assert exact transition timings.
- Adequate for a first slice; the orchestrator design does not change if VAD is later swapped for a heavier model behind the same interface.

## Interaction with barge-in

During `SPEAKING`, the server is emitting its own TTS audio while the client mic continues to stream. If the user starts talking, VAD on the inbound stream fires `speech_start` even though the session is in `SPEAKING` — this is the trigger for [[barge-in]]. The deferred "echo cancellation hint" item (server-side energy gate during `SPEAKING`) exists specifically because the *client's* speakers leaking into the *client's* mic can also trip energy-based VAD, producing false barge-ins.

## Open items not in the source

- Exact thresholds, frame size, RMS window length.
- Whether VAD runs on raw PCM or after any pre-filtering (high-pass to drop DC, etc.).
