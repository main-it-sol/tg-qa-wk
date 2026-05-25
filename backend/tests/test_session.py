"""Tests for the VoiceSession state machine + barge-in handling."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import pytest

from virtrav.voice.adapters import FakeLLM, FakeSTT, FakeTTS, LLMAdapter, TTSAdapter
from virtrav.voice.protocol import decode_audio_frame
from virtrav.voice.session import SessionState, VoiceSession

from .conftest import ScriptedVAD


def _build_session(
    *,
    stt: FakeSTT | None = None,
    llm: LLMAdapter | None = None,
    tts: TTSAdapter | None = None,
    vad: ScriptedVAD | None = None,
) -> tuple[VoiceSession, list[str], list[bytes], ScriptedVAD, FakeSTT]:
    text_out: list[str] = []
    bin_out: list[bytes] = []

    async def emit_text(msg: str) -> None:
        text_out.append(msg)

    async def emit_binary(data: bytes) -> None:
        bin_out.append(data)

    stt = stt or FakeSTT(response="shalom rabbi")
    llm = llm or FakeLLM(tokens=["hi ", "there."])
    tts = tts or FakeTTS(chunk=b"\xaa\xbb")
    vad = vad or ScriptedVAD()
    session = VoiceSession(
        stt=stt, llm=llm, tts=tts, vad=vad,
        emit_text=emit_text, emit_binary=emit_binary,
    )
    return session, text_out, bin_out, vad, stt


async def _drain(session: VoiceSession) -> None:
    task = session.response_task
    if task is not None:
        try:
            await task
        except asyncio.CancelledError:
            pass


def _types(text_out: list[str]) -> list[str]:
    return [json.loads(t)["type"] for t in text_out]


async def test_new_session_is_idle() -> None:
    session, *_ = _build_session()
    assert session.state == SessionState.IDLE


async def test_silence_does_not_change_state() -> None:
    session, text_out, bin_out, vad, _ = _build_session()
    await session.on_audio(b"\x00" * 100)
    assert session.state == SessionState.IDLE
    assert text_out == [] and bin_out == []


async def test_speech_then_silence_runs_full_pipeline() -> None:
    session, text_out, bin_out, vad, stt = _build_session(
        llm=FakeLLM(tokens=["t1", "t2", "t3"]),
        tts=FakeTTS(chunk=b"\xaa\xbb"),
    )
    vad.events_to_emit = ["speech_start"]
    await session.on_audio(b"\x10" * 10)
    assert session.state == SessionState.LISTENING
    # STT should be receiving audio now.
    assert bytes(stt.fed) == b"\x10" * 10

    vad.events_to_emit = ["speech_end"]
    await session.on_audio(b"\x00" * 4)  # not fed once user stops speaking
    await _drain(session)

    assert _types(text_out) == ["transcript", "speech_start", "speech_end"]
    assert len(bin_out) == 3  # one chunk per LLM token
    utt_ids = {decode_audio_frame(f)[0] for f in bin_out}
    assert utt_ids == {1}
    seqs = [decode_audio_frame(f)[1] for f in bin_out]
    assert seqs == [0, 1, 2]
    assert session.state == SessionState.LISTENING


async def test_explicit_interrupt_cancels_response() -> None:
    # Slow LLM that hangs partway so we can interrupt mid-flight.
    started = asyncio.Event()

    class SlowLLM(LLMAdapter):
        async def stream(self, prompt: str) -> AsyncIterator[str]:
            started.set()
            yield "first "
            await asyncio.sleep(10)  # would block forever; we cancel
            yield "never"

    session, text_out, bin_out, vad, _ = _build_session(llm=SlowLLM())
    vad.events_to_emit = ["speech_start"]
    await session.on_audio(b"\x10" * 4)
    vad.events_to_emit = ["speech_end"]
    await session.on_audio(b"\x00" * 4)

    await started.wait()
    await session.on_interrupt()

    types_seen = _types(text_out)
    assert "cancel" in types_seen
    assert "speech_end" not in types_seen
    assert session.state == SessionState.LISTENING


async def test_barge_in_cancels_active_response() -> None:
    started = asyncio.Event()

    class SlowLLM(LLMAdapter):
        async def stream(self, prompt: str) -> AsyncIterator[str]:
            started.set()
            yield "first "
            await asyncio.sleep(10)
            yield "never"

    session, text_out, bin_out, vad, stt = _build_session(llm=SlowLLM())

    vad.events_to_emit = ["speech_start"]
    await session.on_audio(b"\x10" * 4)
    vad.events_to_emit = ["speech_end"]
    await session.on_audio(b"\x00" * 4)
    await started.wait()

    # New speech arrives while server is mid-response.
    vad.events_to_emit = ["speech_start"]
    await session.on_audio(b"\x20" * 4)

    types_seen = _types(text_out)
    assert "cancel" in types_seen
    assert session.state == SessionState.LISTENING
    assert stt.reset_calls >= 1  # reset on barge-in before new utterance


async def test_close_cancels_inflight_and_closes_stt() -> None:
    class SlowLLM(LLMAdapter):
        async def stream(self, prompt: str) -> AsyncIterator[str]:
            yield "x"
            await asyncio.sleep(10)
            yield "y"

    session, _, _, vad, stt = _build_session(llm=SlowLLM())
    vad.events_to_emit = ["speech_start"]
    await session.on_audio(b"\x10" * 4)
    vad.events_to_emit = ["speech_end"]
    await session.on_audio(b"\x00" * 4)

    await session.close()
    assert stt.closed is True


async def test_speech_end_without_prior_speech_start_is_noop() -> None:
    session, text_out, _, vad, _ = _build_session()
    vad.events_to_emit = ["speech_end"]
    await session.on_audio(b"\x00" * 4)
    assert session.state == SessionState.IDLE
    assert text_out == []
