---
title: Voice Wire Protocol (WebSocket)
type: concept
sources:
  - research/raw/articles/voice-backend-sketch.md
related:
  - "[[voice-backend-sketch]]"
  - "[[voice-session-state-machine]]"
  - "[[barge-in]]"
created: 2026-05-25
updated: 2026-05-25
confidence: high
---

# Voice Wire Protocol (WebSocket)

A single WebSocket per session carries both control messages and audio. No WebRTC, no separate signalling channel. Control rides on text frames as JSON; audio rides on binary frames as int16-LE PCM.

## Text frames (JSON)

`{"type": "...", ...}` in both directions.

- **client → server:** `hello`, `interrupt`
- **server → client:** `hello`, `transcript`, `speech_start`, `speech_end`, `cancel`, `error`

`speech_start` / `speech_end` are server-derived from [[voice-activity-detection]] and announced to the client so the UI can render listening cues without running its own VAD. `cancel` is the server's signal that an in-flight utterance has been aborted; see [[barge-in]].

## Binary frames

- **server → client:** 8-byte big-endian header `(utterance_id: uint32, seq: uint32)` followed by int16-LE PCM at the negotiated sample rate.
- **client → server:** raw int16-LE PCM (mic). No header.

The header asymmetry is deliberate: only outbound (server-spoken) audio needs to be cancellable mid-flight, because barge-in is the only case where queued audio must be discarded. Inbound mic audio is consumed immediately by VAD/STT and never queued for replay, so no per-frame metadata is needed.

## Cancellation semantics

When the server sends a `cancel` text frame, it names an `utterance_id`. The client is expected to drop any *queued* binary buffers whose header `utterance_id` matches that value. Buffers that have already been handed to Web Audio for playback will finish playing unless the client also stops the audio node — the wire protocol does not mandate one or the other.

## Sample-rate negotiation

The sample rate is negotiated in `hello` (not specified in the sketch beyond "negotiated"). A server-side resampler so the server can quote a single fixed rate is explicitly out of scope for this slice; see [[voice-backend-sketch]] "Next slices."

## Why not WebRTC

The sketch chooses raw WebSocket to:

- avoid the SDP/ICE/DTLS-SRTP machinery
- keep server-side audio handling in plain Python with no native media stack
- make tests trivially synchronous (no media engine to mock)

Trade-off: no built-in NAT traversal (irrelevant for direct client↔server), no built-in congestion control, no built-in AEC — all of which are deferred to later slices.
