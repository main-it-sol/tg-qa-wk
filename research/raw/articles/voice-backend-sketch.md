# Virtual Rabbi — voice backend sketch

TDD scaffold for the Phase 2 voice loop: WebSocket + PCM + Web Audio
(no WebRTC), with the orchestration that will later drive the 2D
avatar's blendshapes.

## Layout

```
src/virtrav/
  voice/
    protocol.py   binary audio header + JSON control messages
    vad.py        energy-based VAD with hysteresis
    adapters.py   STT / LLM / TTS ABCs + fakes
    session.py    VoiceSession state machine (barge-in aware)
    ws.py         FastAPI WebSocket route
  app.py
tests/            pytest, fakes only — no external services
```

## Wire protocol

* **Text frames** carry JSON: `{"type": "...", ...}`.
  * client → server: `hello`, `interrupt`
  * server → client: `hello`, `transcript`, `speech_start`, `speech_end`, `cancel`, `error`
* **Binary frames**, server → client: 8-byte header `(utterance_id: uint32, seq: uint32, big-endian)` followed by int16-LE PCM at the negotiated sample rate. Client drops queued buffers whose `utterance_id` matches a `cancel`.
* **Binary frames**, client → server: raw int16-LE PCM (mic), no header.

## State machine

```
IDLE --(user speech_start)--> LISTENING
LISTENING --(user speech_end)--> THINKING
THINKING --(first TTS chunk)--> SPEAKING
SPEAKING --(TTS done)--> LISTENING
SPEAKING --(barge-in | client interrupt)--> LISTENING + emit cancel
```

## Quickstart

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn virtrav.app:app --reload
```

## Swapping in real adapters

Subclass the ABCs in `voice/adapters.py`:

* `STTAdapter` — wrap faster-whisper streaming
* `LLMAdapter` — wrap vLLM / Ollama / Anthropic
* `TTSAdapter` — wrap XTTS-v2 / Piper / ElevenLabs

The session orchestrator and tests stay untouched.

## Next slices (not in this sketch)

1. Avatar driver (audio → viseme/blendshape stream) emitted alongside PCM.
2. Server-side resampler so we can quote a single sample rate to the client.
3. Per-session jitter buffer / pacing so the client never starves.
4. Echo cancellation hint (client-side AEC + server-side energy gate during SPEAKING).
