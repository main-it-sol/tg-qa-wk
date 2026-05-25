"""Tests for the wire protocol."""

from __future__ import annotations

import json

import pytest

from virtrav.voice.protocol import (
    HEADER_LEN,
    decode_audio_frame,
    encode_audio_frame,
    make_msg,
    parse_msg,
)


class TestAudioFrame:
    def test_round_trip(self) -> None:
        pcm = b"\x01\x02\x03\x04"
        frame = encode_audio_frame(utterance_id=7, seq=3, pcm=pcm)
        utt, seq, payload = decode_audio_frame(frame)
        assert (utt, seq, payload) == (7, 3, pcm)

    def test_header_is_eight_bytes(self) -> None:
        assert HEADER_LEN == 8
        frame = encode_audio_frame(utterance_id=0, seq=0, pcm=b"")
        assert len(frame) == HEADER_LEN

    def test_decode_rejects_short_frame(self) -> None:
        with pytest.raises(ValueError):
            decode_audio_frame(b"\x00\x00\x00")

    def test_encode_rejects_negative_ids(self) -> None:
        with pytest.raises(ValueError):
            encode_audio_frame(utterance_id=-1, seq=0, pcm=b"")
        with pytest.raises(ValueError):
            encode_audio_frame(utterance_id=0, seq=-1, pcm=b"")

    def test_header_is_big_endian(self) -> None:
        # 0x00000001 0x00000002 → first 8 bytes are exactly that, big-endian.
        frame = encode_audio_frame(utterance_id=1, seq=2, pcm=b"")
        assert frame[:HEADER_LEN] == b"\x00\x00\x00\x01\x00\x00\x00\x02"


class TestControlMessage:
    def test_make_msg_includes_type(self) -> None:
        text = make_msg("hello", sample_rate=24_000)
        data = json.loads(text)
        assert data == {"type": "hello", "sample_rate": 24_000}

    def test_make_msg_rejects_duplicate_type(self) -> None:
        with pytest.raises(ValueError):
            make_msg("hello", type="other")

    def test_parse_msg_accepts_valid(self) -> None:
        msg = parse_msg('{"type":"interrupt"}')
        assert msg == {"type": "interrupt"}

    def test_parse_msg_accepts_bytes(self) -> None:
        msg = parse_msg(b'{"type":"interrupt"}')
        assert msg["type"] == "interrupt"

    def test_parse_msg_rejects_non_object(self) -> None:
        with pytest.raises(ValueError):
            parse_msg("[1,2,3]")

    def test_parse_msg_rejects_missing_type(self) -> None:
        with pytest.raises(ValueError):
            parse_msg('{"foo":"bar"}')

    def test_parse_msg_rejects_non_string_type(self) -> None:
        with pytest.raises(ValueError):
            parse_msg('{"type":42}')
