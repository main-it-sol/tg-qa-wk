"""FastAPI WebSocket route wiring a ``VoiceSession`` to a browser client.

Protocol summary (see ``protocol.py``):

* Client → server: text JSON control messages, plus raw binary PCM
  (int16 LE, sample rate negotiated in ``hello``).
* Server → client: text JSON control messages plus binary audio frames
  prefixed with an 8-byte ``(utterance_id, seq)`` header.

This module is intentionally thin — all real logic lives in
``VoiceSession`` so it can be unit-tested without a WebSocket.
"""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .adapters import FakeLLM, FakeSTT, FakeTTS, LLMAdapter, STTAdapter, TTSAdapter
from .protocol import make_msg, parse_msg
from .session import VoiceSession
from .vad import VAD, EnergyVAD

SessionFactory = Callable[[WebSocket], VoiceSession]


def default_session_factory(ws: WebSocket) -> VoiceSession:
    # Replaced in production wiring; ships sane fakes so the route is runnable.
    stt: STTAdapter = FakeSTT()
    llm: LLMAdapter = FakeLLM()
    tts: TTSAdapter = FakeTTS()
    vad: VAD = EnergyVAD(sample_rate=16_000)

    async def emit_text(msg: str) -> None:
        await ws.send_text(msg)

    async def emit_binary(data: bytes) -> None:
        await ws.send_bytes(data)

    return VoiceSession(
        stt=stt, llm=llm, tts=tts, vad=vad,
        emit_text=emit_text, emit_binary=emit_binary,
    )


def build_router(session_factory: SessionFactory = default_session_factory) -> APIRouter:
    router = APIRouter()

    @router.websocket("/voice")
    async def voice_ws(ws: WebSocket) -> None:
        await ws.accept()
        session = session_factory(ws)
        await ws.send_text(make_msg("hello", sample_rate=24_000, format="pcm_s16le"))
        try:
            while True:
                msg = await ws.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if (text := msg.get("text")) is not None:
                    try:
                        ctrl = parse_msg(text)
                    except ValueError as e:
                        await ws.send_text(make_msg("error", reason=str(e)))
                        continue
                    if ctrl["type"] == "interrupt":
                        await session.on_interrupt()
                    # other client types are no-ops for now
                elif (data := msg.get("bytes")) is not None:
                    await session.on_audio(data)
        except WebSocketDisconnect:
            pass
        finally:
            await session.close()

    return router
