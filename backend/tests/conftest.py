"""Shared test fixtures."""

from __future__ import annotations

import array
import math
from typing import Iterable

import pytest

from virtrav.voice.vad import EnergyVAD, VADEvent


def pcm_silence(duration_ms: int, sample_rate: int = 16_000) -> bytes:
    n = sample_rate * duration_ms // 1000
    return b"\x00\x00" * n


def pcm_tone(duration_ms: int, *, sample_rate: int = 16_000, amplitude: int = 8000,
             freq: float = 220.0) -> bytes:
    n = sample_rate * duration_ms // 1000
    samples = array.array("h")
    for i in range(n):
        samples.append(int(amplitude * math.sin(2 * math.pi * freq * i / sample_rate)))
    return samples.tobytes()


class ScriptedVAD:
    """VAD that emits whatever events you set on ``events_to_emit`` next."""

    def __init__(self) -> None:
        self.events_to_emit: list[VADEvent] = []
        self.pushed: list[bytes] = []

    def push(self, pcm: bytes) -> list[VADEvent]:
        self.pushed.append(pcm)
        out, self.events_to_emit = self.events_to_emit, []
        return out


@pytest.fixture
def scripted_vad() -> ScriptedVAD:
    return ScriptedVAD()


@pytest.fixture
def energy_vad() -> EnergyVAD:
    return EnergyVAD(
        sample_rate=16_000,
        frame_ms=30,
        speech_rms=500.0,
        silence_rms=250.0,
        min_speech_ms=120,
        min_silence_ms=300,
    )


@pytest.fixture
def make_pcm() -> Iterable[callable]:
    return {"silence": pcm_silence, "tone": pcm_tone}
