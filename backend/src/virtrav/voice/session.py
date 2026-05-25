"""Voice session orchestrator.

State machine:

    IDLE --(user speech_start)--> LISTENING
    LISTENING --(user speech_end)--> THINKING
    THINKING --(first TTS chunk)--> SPEAKING
    SPEAKING --(TTS done)--> LISTENING
    SPEAKING --(barge-in | client interrupt)--> LISTENING (cancel)

Barge-in: while the response task is running, a fresh user
``speech_start`` cancels the in-flight LLM/TTS work and emits a
``cancel`` control message so the client can flush its audio queue —
this is the bug the README calls "blueprint has been spent".
"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import Awaitable, Callable

from .adapters import LLMAdapter, STTAdapter, TTSAdapter
from .protocol import encode_audio_frame, make_msg
from .vad import VAD


class SessionState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


EmitText = Callable[[str], Awaitable[None]]
EmitBinary = Callable[[bytes], Awaitable[None]]


class VoiceSession:
    def __init__(
        self,
        *,
        stt: STTAdapter,
        llm: LLMAdapter,
        tts: TTSAdapter,
        vad: VAD,
        emit_text: EmitText,
        emit_binary: EmitBinary,
        system_prompt: str = "",
    ) -> None:
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.vad = vad
        self.emit_text = emit_text
        self.emit_binary = emit_binary
        self.system_prompt = system_prompt

        self.state: SessionState = SessionState.IDLE
        self._user_speaking = False
        self._next_utt_id = 1
        self._response_task: asyncio.Task[None] | None = None

    @property
    def response_task(self) -> asyncio.Task[None] | None:
        return self._response_task

    async def on_audio(self, pcm: bytes) -> None:
        events = self.vad.push(pcm)
        for ev in events:
            if ev == "speech_start":
                await self._handle_speech_start()
            elif ev == "speech_end":
                await self._handle_speech_end()
        if self._user_speaking:
            await self.stt.feed(pcm)

    async def on_interrupt(self) -> None:
        await self._cancel_response()

    async def close(self) -> None:
        await self._cancel_response()
        await self.stt.close()

    # ----- internal --------------------------------------------------------

    async def _handle_speech_start(self) -> None:
        self._user_speaking = True
        # Barge-in while we were speaking: stop talking, drop pending audio.
        if self.state == SessionState.SPEAKING or self._response_task is not None:
            await self._cancel_response()
        await self.stt.reset()
        self.state = SessionState.LISTENING

    async def _handle_speech_end(self) -> None:
        if not self._user_speaking:
            return
        self._user_speaking = False
        if self.state != SessionState.LISTENING:
            return
        self.state = SessionState.THINKING
        utt_id = self._next_utt_id
        self._next_utt_id += 1
        self._response_task = asyncio.create_task(self._respond(utt_id))

    async def _respond(self, utt_id: int) -> None:
        try:
            transcript = await self.stt.finalize()
            await self.emit_text(make_msg("transcript", text=transcript, final=True))
            prompt = (
                f"{self.system_prompt}\n\nUser: {transcript}\nAssistant:"
                if self.system_prompt
                else transcript
            )
            tokens = self.llm.stream(prompt)
            chunks = self.tts.synthesize(tokens)

            await self.emit_text(make_msg("speech_start", utterance_id=utt_id))
            self.state = SessionState.SPEAKING
            seq = 0
            async for chunk in chunks:
                await self.emit_binary(encode_audio_frame(utt_id, seq, chunk))
                seq += 1
            await self.emit_text(make_msg("speech_end", utterance_id=utt_id))
            self.state = SessionState.LISTENING
        except asyncio.CancelledError:
            await self.emit_text(make_msg("cancel", utterance_id=utt_id))
            self.state = SessionState.LISTENING
            raise
        finally:
            self._response_task = None

    async def _cancel_response(self) -> None:
        task = self._response_task
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            # Don't let a misbehaving adapter mask the cancel path.
            pass
