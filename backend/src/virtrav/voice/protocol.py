"""Wire protocol for the voice WebSocket.

Two frame kinds share the same WebSocket:

* Text frames carry JSON control messages: ``{"type": "...", ...}``.
* Binary frames carry PCM audio prefixed with an 8-byte header
  ``(utterance_id: uint32, seq: uint32)`` so the client can drop stale
  audio on barge-in without parsing the payload.

Client audio (mic) is sent as raw PCM bytes — no header is required
because client audio is not tagged with utterance ids.
"""

from __future__ import annotations

import json
import struct
from typing import Any

_HEADER_FMT = ">II"
HEADER_LEN = struct.calcsize(_HEADER_FMT)  # 8

CLIENT_MSG_TYPES = frozenset({"hello", "interrupt"})
SERVER_MSG_TYPES = frozenset(
    {"hello", "transcript", "speech_start", "speech_end", "cancel", "error"}
)


def encode_audio_frame(utterance_id: int, seq: int, pcm: bytes) -> bytes:
    if utterance_id < 0 or seq < 0:
        raise ValueError("utterance_id and seq must be non-negative")
    return struct.pack(_HEADER_FMT, utterance_id, seq) + pcm


def decode_audio_frame(frame: bytes) -> tuple[int, int, bytes]:
    if len(frame) < HEADER_LEN:
        raise ValueError(f"audio frame shorter than header ({len(frame)} < {HEADER_LEN})")
    utt_id, seq = struct.unpack(_HEADER_FMT, frame[:HEADER_LEN])
    return utt_id, seq, frame[HEADER_LEN:]


def make_msg(type_: str, **fields: Any) -> str:
    if "type" in fields:
        raise ValueError("'type' is set positionally; do not pass as keyword")
    return json.dumps({"type": type_, **fields}, separators=(",", ":"))


def parse_msg(payload: str | bytes) -> dict[str, Any]:
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("control message must be a JSON object")
    if "type" not in data or not isinstance(data["type"], str):
        raise ValueError("control message missing 'type' string")
    return data
