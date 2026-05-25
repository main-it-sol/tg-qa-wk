"""Tests for the fake adapter implementations."""

from __future__ import annotations

from virtrav.voice.adapters import FakeLLM, FakeSTT, FakeTTS


async def test_fake_stt_buffers_and_finalizes() -> None:
    stt = FakeSTT(response="hello world")
    await stt.feed(b"abcd")
    await stt.feed(b"efgh")
    assert bytes(stt.fed) == b"abcdefgh"
    text = await stt.finalize()
    assert text == "hello world"
    # finalize empties the buffer
    assert bytes(stt.fed) == b""


async def test_fake_stt_reset_clears_buffer() -> None:
    stt = FakeSTT()
    await stt.feed(b"xyz")
    await stt.reset()
    assert bytes(stt.fed) == b""
    assert stt.reset_calls == 1


async def test_fake_llm_streams_tokens_and_records_prompt() -> None:
    llm = FakeLLM(tokens=["a", "b", "c"])
    out = []
    async for tok in llm.stream("hi"):
        out.append(tok)
    assert out == ["a", "b", "c"]
    assert llm.last_prompt == "hi"


async def test_fake_tts_emits_chunk_per_token() -> None:
    tts = FakeTTS(chunk=b"\xff\xfe")

    async def tokens():
        for t in ["one", "two", "three"]:
            yield t

    chunks = []
    async for c in tts.synthesize(tokens()):
        chunks.append(c)
    assert chunks == [b"\xff\xfe"] * 3
    assert tts.received_tokens == ["one", "two", "three"]
