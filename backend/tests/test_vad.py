"""Tests for the energy-based VAD."""

from __future__ import annotations

import pytest

from virtrav.voice.vad import EnergyVAD
from .conftest import pcm_silence, pcm_tone


def test_silence_alone_never_emits(energy_vad: EnergyVAD) -> None:
    events = energy_vad.push(pcm_silence(2000))
    assert events == []


def test_speech_then_silence_emits_start_then_end(energy_vad: EnergyVAD) -> None:
    # Speech long enough to cross min_speech_ms (120 ms).
    speech = pcm_tone(400)
    silence = pcm_silence(800)
    events = energy_vad.push(speech + silence)
    assert events == ["speech_start", "speech_end"]


def test_short_speech_blip_is_ignored(energy_vad: EnergyVAD) -> None:
    # Below min_speech_ms (120 ms).
    events = energy_vad.push(pcm_tone(60) + pcm_silence(800))
    assert events == []


def test_brief_silence_inside_speech_does_not_end(energy_vad: EnergyVAD) -> None:
    # Speech, then a tiny gap (well under min_silence_ms=300), then more speech.
    audio = pcm_tone(400) + pcm_silence(150) + pcm_tone(400)
    events = energy_vad.push(audio)
    assert events == ["speech_start"]


def test_handles_partial_frames_across_pushes(energy_vad: EnergyVAD) -> None:
    speech = pcm_tone(400)
    # Push in awkward chunk sizes (not aligned to frame_bytes).
    mid = len(speech) // 2 + 7  # offset so it doesn't align to frames
    events = energy_vad.push(speech[:mid])
    events += energy_vad.push(speech[mid:])
    events += energy_vad.push(pcm_silence(800))
    assert events == ["speech_start", "speech_end"]


def test_invalid_thresholds_rejected() -> None:
    with pytest.raises(ValueError):
        EnergyVAD(sample_rate=16_000, speech_rms=100.0, silence_rms=200.0)
