"""Adapter interfaces for STT, LLM, TTS plus in-memory fakes for tests.

Real implementations (faster-whisper, vLLM/Ollama, XTTS/Piper) plug in
behind the same ABCs without touching the orchestrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class STTAdapter(ABC):
    @abstractmethod
    async def feed(self, pcm: bytes) -> None: ...

    @abstractmethod
    async def finalize(self) -> str:
        """Close the current utterance and return the final transcript."""

    @abstractmethod
    async def reset(self) -> None:
        """Discard any buffered audio (e.g. on barge-in)."""

    @abstractmethod
    async def close(self) -> None: ...


class LLMAdapter(ABC):
    @abstractmethod
    def stream(self, prompt: str) -> AsyncIterator[str]:
        """Yield response tokens (or chunks) as they're produced."""


class TTSAdapter(ABC):
    @abstractmethod
    def synthesize(self, tokens: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """Consume a stream of text tokens, yield PCM (int16 LE) chunks."""


# ----- fakes ---------------------------------------------------------------


class FakeSTT(STTAdapter):
    """STT that returns a canned transcript and tracks fed audio."""

    def __init__(self, response: str = "shalom") -> None:
        self.response = response
        self.fed: bytearray = bytearray()
        self.closed = False
        self.reset_calls = 0

    async def feed(self, pcm: bytes) -> None:
        self.fed.extend(pcm)

    async def finalize(self) -> str:
        out = self.response
        self.fed.clear()
        return out

    async def reset(self) -> None:
        self.fed.clear()
        self.reset_calls += 1

    async def close(self) -> None:
        self.closed = True


class FakeLLM(LLMAdapter):
    """LLM that yields a fixed list of tokens, recording the prompt."""

    def __init__(self, tokens: list[str] | None = None) -> None:
        self.tokens = tokens if tokens is not None else ["I ", "am ", "here."]
        self.last_prompt: str | None = None

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        self.last_prompt = prompt
        for tok in self.tokens:
            yield tok


class FakeTTS(TTSAdapter):
    """TTS that emits a fixed PCM chunk per token, recording inputs."""

    def __init__(self, chunk: bytes | None = None) -> None:
        # 10 ms of silence at 24 kHz int16
        self.chunk = chunk if chunk is not None else b"\x00\x00" * 240
        self.received_tokens: list[str] = []

    async def synthesize(self, tokens: AsyncIterator[str]) -> AsyncIterator[bytes]:
        async for tok in tokens:
            self.received_tokens.append(tok)
            yield self.chunk
