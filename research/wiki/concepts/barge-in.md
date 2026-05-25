---
title: Barge-In
type: concept
sources:
  - research/raw/articles/voice-backend-sketch.md
related:
  - "[[voice-backend-sketch]]"
  - "[[voice-session-state-machine]]"
  - "[[voice-wire-protocol]]"
  - "[[voice-activity-detection]]"
created: 2026-05-25
updated: 2026-05-25
confidence: high
---

# Barge-In

Barge-in is the ability for the user to interrupt the assistant mid-sentence — start talking while the server is still streaming TTS, and have the server stop talking and start listening. It is the single most important UX property of a real-time voice loop; without it the conversation feels walkie-talkie.

## Two triggers

The session can leave `SPEAKING` for `LISTENING` for either of two reasons:

1. **Implicit barge-in.** [[voice-activity-detection]] on the inbound mic stream fires `speech_start` while the session is in `SPEAKING`.
2. **Explicit interrupt.** The client sends an `interrupt` text frame (e.g. the user tapped a stop button).

Both paths are unified in [[voice-session-state-machine]]:

```
SPEAKING --(barge-in | client interrupt)--> LISTENING + emit cancel
```

## Server side: `cancel`

When the transition fires, the server emits a `cancel` text frame naming the `utterance_id` of the TTS stream it just abandoned. It stops queuing new binary frames for that `utterance_id`.

## Client side: drain the queue

The client drops any queued binary buffers whose header `utterance_id` matches the cancelled one. Buffers already handed to Web Audio for playback will keep playing unless the client also stops the audio node — the wire protocol leaves that choice to the client (see [[voice-wire-protocol]]).

## Why the `utterance_id` header exists

It exists *for* barge-in. Without it, after a `cancel` the client would have to either flush every queued buffer (and risk discarding audio from a *new* utterance whose first packets arrived before the cancel) or trust strict in-order delivery. Tagging each frame with the utterance it belongs to makes the drop unambiguous.

## Echo-cancellation caveat

Energy-based VAD on the mic stream cannot tell the user's voice apart from the assistant's voice bleeding out of the user's speakers and back into the mic. The sketch lists "client-side AEC + server-side energy gate during `SPEAKING`" as deferred work specifically to avoid spurious barge-ins from acoustic echo.
