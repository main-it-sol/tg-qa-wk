---
title: Voice Session State Machine
type: concept
sources:
  - research/raw/articles/voice-backend-sketch.md
related:
  - "[[voice-backend-sketch]]"
  - "[[barge-in]]"
  - "[[voice-wire-protocol]]"
  - "[[voice-activity-detection]]"
created: 2026-05-25
updated: 2026-05-25
confidence: high
---

# Voice Session State Machine

The `VoiceSession` orchestrator (`src/virtrav/voice/session.py`) tracks one user's conversation as a four-state machine. The transitions are driven by VAD events on the inbound mic stream, by completion of the LLM/TTS pipeline, and by explicit client `interrupt` messages.

## States

- **IDLE** — no active speech in either direction. Default at hello.
- **LISTENING** — user is talking; PCM is being forwarded to STT.
- **THINKING** — user has stopped; STT result is being sent to the LLM and TTS is being primed.
- **SPEAKING** — server is streaming TTS PCM back to the client.

## Transitions

```
IDLE      --(user speech_start)--> LISTENING
LISTENING --(user speech_end)----> THINKING
THINKING  --(first TTS chunk)----> SPEAKING
SPEAKING  --(TTS done)-----------> LISTENING
SPEAKING  --(barge-in | client interrupt)--> LISTENING + emit cancel
```

The `speech_start` / `speech_end` transitions come from [[voice-activity-detection]]. The `cancel` emission is the server-side half of [[barge-in]] and references the same `utterance_id` the client uses to drop queued audio (see [[voice-wire-protocol]]).

## Why these states (and not more)

The sketch collapses everything between `speech_end` and the first audible TTS chunk into a single `THINKING` state — there is no separate "STT done" or "LLM streaming" state visible on the wire. Two consequences:

- Clients don't need to render intermediate "thinking…" indicators differently from "transcribing…"; one UI state covers both.
- The orchestrator is free to start TTS speculatively before LLM completion, as long as it gates the `SPEAKING` transition on the first TTS chunk actually being ready to send.

## Loop after SPEAKING

After TTS finishes, the machine returns to `LISTENING`, not `IDLE`. The assumption is that a conversation is ongoing, so the mic stays hot and VAD is armed. `IDLE` is only re-entered on session close / error.

## Open items not in the source

- Behaviour on STT or LLM failure mid-`THINKING` is not specified — presumably an `error` text frame and a return to `LISTENING`, but the sketch does not say.
- Timeout behaviour in `THINKING` is not specified.
