---
title: Voice Pipeline Overview (WebSocket Handler)
type: concept
sources:
  - research/raw/articles/voice-backend-sketch.md
related:
  - "[[voice-backend-sketch]]"
  - "[[voice-session-state-machine]]"
  - "[[voice-wire-protocol]]"
  - "[[voice-activity-detection]]"
  - "[[barge-in]]"
  - "[[adapter-pattern-stt-llm-tts]]"
created: 2026-05-29
updated: 2026-05-29
confidence: high
---

# Voice Pipeline Overview

The WebSocket handler follows a **layered design** with clear separation of concerns:

```
ws.py           — FastAPI route (thin wiring layer)
protocol.py     — frame encoding/decoding (JSON control + binary audio)
session.py      — state machine orchestrator (all real logic)
vad.py          — voice activity detection
adapters.py     — STT / LLM / TTS interfaces + fakes
```

The key insight: `session.py` has **zero dependency on WebSocket** — it talks to the outside world through two callbacks (`emit_text`, `emit_binary`). This makes the entire orchestrator unit-testable without a live socket.

## `ws.py` — The route layer

`build_router()` creates an `APIRouter` with a single WebSocket endpoint at `/voice`.

**Flow on connect:**

1. Accepts the WS upgrade
2. Calls `session_factory(ws)` — by default `default_session_factory`, which wires up `FakeSTT`, `FakeLLM`, `FakeTTS`, and `EnergyVAD`
3. Immediately sends a `hello` control message advertising 24 kHz PCM s16le audio
4. Enters a `receive` loop dispatching text → control messages, binary → audio data
5. On disconnect or error, calls `session.close()` to clean up the response task

**The factory function** is injectable:

```python
SessionFactory = Callable[[WebSocket], VoiceSession]
```

The signature `build_router(session_factory=default_session_factory)` means you can swap in real adapters (e.g. faster-whisper + vLLM + Piper) at the wiring level without touching anything else.

**Message dispatch** is minimal — only `interrupt` is handled from the client currently. Other client-to-server message types are intentionally no-ops (future: config changes, etc.).

## `protocol.py` — Wire format

Two frame types share the same WebSocket connection. See [[voice-wire-protocol]] for full details.

### Text frames (JSON control messages)

All messages have a `"type"` field plus optional fields:

| Direction | Type | Fields |
|---|---|---|
| Server → Client | `hello` | `sample_rate`, `format` |
| Server → Client | `transcript` | `text`, `final` |
| Server → Client | `speech_start` | `utterance_id` |
| Server → Client | `speech_end` | `utterance_id` |
| Server → Client | `cancel` | `utterance_id` |
| Server → Client | `error` | `reason` |
| Client → Server | `interrupt` | — |

`make_msg` serializes with compact separators to minimize wire overhead. `parse_msg` validates that the payload decodes to a JSON object with a string `"type"` field.

### Binary frames (audio data)

**Server → Client** audio frames have an 8-byte header:

```
[utterance_id: uint32 big-endian][seq: uint32 big-endian][PCM data...]
```

Why `utterance_id` + `seq`? So the client can implement **barge-in** correctly. When a `cancel` message arrives, the client knows which utterance IDs to flush from its playback queue. The sequence number helps order frames if they arrive out of order (though over a single WS they should not).

**Client → Server** audio is just raw PCM bytes — no header needed since client audio is not tagged with utterance IDs.

## `session.py` — The state machine

This is the brains of the operation. See [[voice-session-state-machine]] for the detailed state diagram.

### States

```
IDLE → LISTENING → THINKING → SPEAKING → LISTENING (loop)
                  ↑                         │
                  └── barge-in / interrupt ──┘
```

- **IDLE** — waiting for user to speak
- **LISTENING** — user is speaking, STT is accumulating audio
- **THINKING** — user stopped speaking, STT is finalizing, LLM is generating
- **SPEAKING** — TTS is producing audio, being streamed to client

### Key methods

**`on_audio(pcm)`** — called from the WS route whenever binary arrives. It:
1. Pushes PCM through the VAD, which emits `speech_start` / `speech_end` events (see [[voice-activity-detection]])
2. On `speech_start` → calls `_handle_speech_start()`
3. On `speech_end` → calls `_handle_speech_end()`
4. If user is currently speaking, feeds PCM into STT

**`_handle_speech_start()`** implements **barge-in** (see [[barge-in]]):
- If currently SPEAKING or a response task is running, it cancels the in-flight response
- Resets STT (discards any partial transcription)
- Transitions to LISTENING

**`_handle_speech_end()`** starts the response pipeline:
- Transitions to THINKING
- Assigns a new `utterance_id`
- Spawns an `asyncio.Task` for `_respond(utt_id)`

**`_respond(utt_id)`** — the async pipeline:
1. Calls `stt.finalize()` → gets the transcript
2. Emits `transcript` control message to client
3. Prepends `system_prompt` if set
4. Calls `llm.stream(prompt)` → gets an `AsyncIterator[str]` of tokens
5. Calls `tts.synthesize(tokens)` → gets an `AsyncIterator[bytes]` of PCM chunks
6. Emits `speech_start`, then streams audio frames (with utterance_id + seq), then `speech_end`
7. Transitions to LISTENING

If the task is cancelled (barge-in or explicit interrupt), it emits `cancel` and transitions to LISTENING.

**`_cancel_response()`** — safely cancels the in-flight task:
- Checks if task exists and is not already done
- Calls `task.cancel()`
- Awaits the task (swallowing `CancelledError` or any adapter exception)

## `vad.py` — Energy-based VAD

A simple energy-based voice activity detector with hysteresis. See [[voice-activity-detection]] for details.

- Processes PCM in frames (default 30 ms)
- Uses RMS energy thresholds: `speech_rms` to trigger on, `silence_rms` to trigger off
- Requires `min_speech_ms` (200 ms) of sustained energy to emit `speech_start`
- Requires `min_silence_ms` (500 ms) of sustained silence to emit `speech_end`
- The hysteresis prevents rapid toggling

The `VAD` class is defined as a **Protocol** (structural typing), so any object with `push(pcm) -> list[VADEvent]` works — swap in Silero VAD or webrtcvad later without changing the session.

## `adapters.py` — Abstract interfaces + fakes

Three abstract base classes define the pipeline contracts. See [[adapter-pattern-stt-llm-tts]] for the full interface definitions.

```python
class STTAdapter(ABC):
    async def feed(pcm)            # stream audio in
    async def finalize() -> str    # get transcript
    async def reset()              # discard on barge-in
    async def close()

class LLMAdapter(ABC):
    def stream(prompt) -> AsyncIterator[str]  # yield tokens

class TTSAdapter(ABC):
    def synthesize(tokens) -> AsyncIterator[bytes]  # yield PCM chunks
```

Three **fake implementations** (`FakeSTT`, `FakeLLM`, `FakeTTS`) ship by default so the route is runnable out of the box. They are also used in unit tests.

## End-to-end data flow

```
Browser                    Server
  │                          │
  │──── websocket connect ──→│
  │←──── hello (24kHz) ─────│
  │                          │
  │──── PCM16 audio ────────→│  (user speaks)
  │                          │── VAD detects speech_start
  │                          │── feed PCM to FakeSTT
  │                          │── VAD detects speech_end
  │                          │── FakeSTT.finalize() → "shalom"
  │←──── transcript ────────│
  │                          │── FakeLLM.stream("shalom") → ["I ","am ","here."]
  │                          │── FakeTTS.synthesize(tokens) → silence chunks
  │←──── speech_start ──────│
  │←──── audio frame (seq 0)│
  │←──── audio frame (seq 1)│
  │←──── audio frame (seq 2)│
  │←──── speech_end ────────│
  │                          │
  │──── PCM16 audio ────────→│  (user barges in)
  │                          │── VAD detects speech_start
  │                          │── cancel in-flight response task
  │←──── cancel (utt_id) ───│
  │                          │── browser flushes audio queue
```

## Key design decisions

1. **No WS dependency in the session.** The callbacks pattern (`emit_text`, `emit_binary`) means the orchestrator is pure async Python — testable with `asyncio.run` and no WebSocket infrastructure.

2. **Asyncio task for response generation.** This lets the WS receive loop keep running (accepting interrupts, new audio) while a response is being generated. Without this, the server would be blocked during LLM/TTS.

3. **Barge-in via cancellation.** Cancelling the `asyncio.Task` propagates to the STT/LLM/TTS adapters (if they support it), and the `cancel` control message tells the client to flush audio. This is the "blueprint has been spent" problem documented in the [[voice-backend-sketch]] source.

4. **Sequenced audio frames.** The `(utterance_id, seq)` header lets the client discard stale audio immediately on barge-in rather than playing residual pre-cancel frames.

5. **Injection-ready.** Every dependency (VAD, STT, LLM, TTS) is behind an abstract interface, and the factory function is swappable at the route level.

## Related files

- `backend/src/virtrav/voice/ws.py` — FastAPI route wiring
- `backend/src/virtrav/voice/protocol.py` — frame encoding/decoding
- `backend/src/virtrav/voice/session.py` — orchestrator state machine
- `backend/src/virtrav/voice/vad.py` — voice activity detection
- `backend/src/virtrav/voice/adapters.py` — adapter interfaces + fakes
