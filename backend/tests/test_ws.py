"""Integration tests for the FastAPI WebSocket route."""

from __future__ import annotations

import json
from typing import AsyncIterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from virtrav.voice.adapters import FakeLLM, FakeSTT, FakeTTS
from virtrav.voice.protocol import decode_audio_frame, make_msg
from virtrav.voice.session import VoiceSession
from virtrav.voice.ws import build_router

from .conftest import ScriptedVAD


@pytest.fixture
def app_factory():
    """Build an app with a session factory we can pre-program for the test."""

    def factory(vad: ScriptedVAD, *, stt=None, llm=None, tts=None) -> FastAPI:
        stt = stt or FakeSTT(response="hello rabbi")
        llm = llm or FakeLLM(tokens=["greetings."])
        tts = tts or FakeTTS(chunk=b"\xaa\xbb")

        def make_session(ws):
            async def emit_text(msg: str) -> None:
                await ws.send_text(msg)

            async def emit_binary(data: bytes) -> None:
                await ws.send_bytes(data)

            return VoiceSession(
                stt=stt, llm=llm, tts=tts, vad=vad,
                emit_text=emit_text, emit_binary=emit_binary,
            )

        app = FastAPI()
        app.include_router(build_router(make_session))
        return app

    return factory


def test_ws_sends_hello_on_connect(app_factory) -> None:
    vad = ScriptedVAD()
    app = app_factory(vad)
    with TestClient(app) as client:
        with client.websocket_connect("/voice") as ws:
            hello = json.loads(ws.receive_text())
            assert hello["type"] == "hello"
            assert hello["format"] == "pcm_s16le"
            assert hello["sample_rate"] == 24_000


def test_ws_streams_audio_response_for_user_turn(app_factory) -> None:
    vad = ScriptedVAD()
    app = app_factory(vad)
    with TestClient(app) as client:
        with client.websocket_connect("/voice") as ws:
            ws.receive_text()  # discard hello

            vad.events_to_emit = ["speech_start"]
            ws.send_bytes(b"\x10" * 16)
            vad.events_to_emit = ["speech_end"]
            ws.send_bytes(b"\x00" * 4)

            transcript = json.loads(ws.receive_text())
            assert transcript == {
                "type": "transcript", "text": "hello rabbi", "final": True,
            }
            speech_start = json.loads(ws.receive_text())
            assert speech_start["type"] == "speech_start"
            audio = ws.receive_bytes()
            utt, seq, payload = decode_audio_frame(audio)
            assert utt == speech_start["utterance_id"]
            assert seq == 0
            assert payload == b"\xaa\xbb"
            speech_end = json.loads(ws.receive_text())
            assert speech_end == {
                "type": "speech_end", "utterance_id": speech_start["utterance_id"],
            }


def test_ws_honors_explicit_interrupt(app_factory) -> None:
    import asyncio

    class SlowLLM:
        async def stream(self, prompt: str) -> AsyncIterator[str]:
            yield "first "
            await asyncio.sleep(10)
            yield "never"

    vad = ScriptedVAD()
    app = app_factory(vad, llm=SlowLLM())
    with TestClient(app) as client:
        with client.websocket_connect("/voice") as ws:
            ws.receive_text()  # hello
            vad.events_to_emit = ["speech_start"]
            ws.send_bytes(b"\x10" * 4)
            vad.events_to_emit = ["speech_end"]
            ws.send_bytes(b"\x00" * 4)
            # consume transcript + speech_start so the response is mid-flight
            assert json.loads(ws.receive_text())["type"] == "transcript"
            assert json.loads(ws.receive_text())["type"] == "speech_start"
            # we expect one audio frame for "first " before SlowLLM stalls
            ws.receive_bytes()
            ws.send_text(make_msg("interrupt"))
            cancel = json.loads(ws.receive_text())
            assert cancel["type"] == "cancel"


def test_ws_rejects_malformed_control_message(app_factory) -> None:
    vad = ScriptedVAD()
    app = app_factory(vad)
    with TestClient(app) as client:
        with client.websocket_connect("/voice") as ws:
            ws.receive_text()  # hello
            ws.send_text("not json at all")
            err = json.loads(ws.receive_text())
            assert err["type"] == "error"
