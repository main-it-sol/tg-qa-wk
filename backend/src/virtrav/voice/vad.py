"""Energy-based VAD with hysteresis.

The VAD consumes int16 little-endian PCM and emits ``speech_start`` and
``speech_end`` events. It does not attempt to be production-grade — it
exists so the voice pipeline can be exercised end-to-end without pulling
in webrtcvad/silero. Swap in a smarter VAD by satisfying the same
``push(pcm) -> list[VADEvent]`` shape.
"""

from __future__ import annotations

import array
from typing import Literal, Protocol

VADEvent = Literal["speech_start", "speech_end"]


class VAD(Protocol):
    def push(self, pcm: bytes) -> list[VADEvent]: ...


def _rms_int16(pcm: bytes) -> float:
    if not pcm:
        return 0.0
    samples = array.array("h")
    samples.frombytes(pcm)
    sq = 0
    for s in samples:
        sq += s * s
    return (sq / len(samples)) ** 0.5


class EnergyVAD:
    def __init__(
        self,
        *,
        sample_rate: int,
        frame_ms: int = 30,
        speech_rms: float = 500.0,
        silence_rms: float = 250.0,
        min_speech_ms: int = 200,
        min_silence_ms: int = 500,
    ) -> None:
        if speech_rms <= silence_rms:
            raise ValueError("speech_rms must be greater than silence_rms")
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_bytes = sample_rate * frame_ms // 1000 * 2  # int16 = 2 bytes
        self.speech_rms = speech_rms
        self.silence_rms = silence_rms
        self.min_speech_ms = min_speech_ms
        self.min_silence_ms = min_silence_ms

        self._buf = bytearray()
        self._in_speech = False
        self._run_ms = 0  # ms accumulated in current candidate state

    def push(self, pcm: bytes) -> list[VADEvent]:
        events: list[VADEvent] = []
        self._buf.extend(pcm)
        while len(self._buf) >= self.frame_bytes:
            frame = bytes(self._buf[: self.frame_bytes])
            del self._buf[: self.frame_bytes]
            rms = _rms_int16(frame)
            if self._in_speech:
                if rms < self.silence_rms:
                    self._run_ms += self.frame_ms
                    if self._run_ms >= self.min_silence_ms:
                        events.append("speech_end")
                        self._in_speech = False
                        self._run_ms = 0
                else:
                    self._run_ms = 0
            else:
                if rms > self.speech_rms:
                    self._run_ms += self.frame_ms
                    if self._run_ms >= self.min_speech_ms:
                        events.append("speech_start")
                        self._in_speech = True
                        self._run_ms = 0
                else:
                    self._run_ms = 0
        return events
