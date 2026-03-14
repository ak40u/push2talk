"""Tests for push2talk.openai_recognizer module."""

from __future__ import annotations

import io
import wave
from unittest.mock import MagicMock, patch

import pytest


def _make_response(text: str, status: int = 200):
    mock = MagicMock()
    mock.status_code = status
    mock.text = text
    mock.raise_for_status = MagicMock()
    if status >= 400:
        from requests import HTTPError

        mock.raise_for_status.side_effect = HTTPError(response=mock)
    return mock


def test_pcm_to_wav_valid_header():
    from push2talk.openai_recognizer import _pcm_to_wav

    pcm = b"\x00\x01" * 1000
    wav_bytes = _pcm_to_wav(pcm, sample_rate=16000)

    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2  # 16-bit
        assert wf.getframerate() == 16000
        assert wf.getnframes() == len(pcm) // 2


def test_pcm_to_wav_contains_pcm_data():
    from push2talk.openai_recognizer import _pcm_to_wav

    pcm = bytes(range(256))
    wav_bytes = _pcm_to_wav(pcm, sample_rate=8000)
    # PCM data should be embedded after WAV header (44 bytes)
    assert pcm in wav_bytes


def test_empty_audio_returns_empty_string():
    from push2talk.openai_recognizer import recognize_openai

    result = recognize_openai(b"", "sk-key")
    assert result == ""


def test_single_chunk_recognize():
    from push2talk.openai_recognizer import recognize_openai

    audio = b"\x00\x01" * 500
    expected = "transcribed text"

    with patch("push2talk.openai_recognizer.requests.post") as mock_post:
        mock_post.return_value = _make_response(f"  {expected}  ")
        result = recognize_openai(audio, "sk-test", "ru", 16000)

    assert result == expected
    mock_post.assert_called_once()


def test_single_chunk_sends_correct_auth():
    from push2talk.openai_recognizer import recognize_openai

    audio = b"\x00" * 100

    with patch("push2talk.openai_recognizer.requests.post") as mock_post:
        mock_post.return_value = _make_response("ok")
        recognize_openai(audio, "sk-mykey", "ru-RU", 16000)

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer sk-mykey"


def test_single_chunk_language_truncated():
    """Language is truncated to 2 chars (ru-RU -> ru)."""
    from push2talk.openai_recognizer import recognize_openai

    audio = b"\x00" * 100

    with patch("push2talk.openai_recognizer.requests.post") as mock_post:
        mock_post.return_value = _make_response("ok")
        recognize_openai(audio, "sk-key", "ru-RU", 16000)

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["data"]["language"] == "ru"


def test_multi_chunk_splits_and_joins():
    from push2talk.openai_recognizer import recognize_openai

    small_max = 200
    small_pcm_max = small_max - 44

    # 1.5x small_pcm_max → 2 chunks
    audio = b"\x00" * (small_pcm_max + small_pcm_max // 2)

    responses = [_make_response("chunk one"), _make_response("chunk two")]

    with (
        patch("push2talk.openai_recognizer.MAX_WAV_BYTES", small_max),
        patch("push2talk.openai_recognizer.requests.post") as mock_post,
    ):
        mock_post.side_effect = responses
        result = recognize_openai(audio, "sk-key", "ru", 16000)

    assert result == "chunk one chunk two"
    assert mock_post.call_count == 2


def test_api_error_raises():
    from requests import HTTPError

    from push2talk.openai_recognizer import _recognize_chunk

    with patch("push2talk.openai_recognizer.requests.post") as mock_post:
        mock_post.return_value = _make_response("", status=401)
        with pytest.raises(HTTPError):
            _recognize_chunk(b"\x00" * 100, "bad-key", "ru", 16000)


def test_multi_chunk_partial_failure_skips_chunk():
    """If first chunk HTTP fails, second chunk result is still returned."""
    from push2talk.openai_recognizer import recognize_openai

    # Patch MAX_WAV_BYTES to a tiny value so test data stays small
    small_max = 200  # bytes
    small_pcm_max = small_max - 44  # minus WAV header

    fail_resp = _make_response("", status=500)
    ok_resp = _make_response("second chunk")

    # Audio = 1.5x small_pcm_max → two chunks
    audio = b"\x00" * (small_pcm_max + small_pcm_max // 2)

    with (
        patch("push2talk.openai_recognizer.MAX_WAV_BYTES", small_max),
        patch("push2talk.openai_recognizer.requests.post") as mock_post,
    ):
        mock_post.side_effect = [fail_resp, ok_resp]
        result = recognize_openai(audio, "sk-key")

    assert result == "second chunk"
