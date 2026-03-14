"""Tests for push2talk.recognizer module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_response(result: str, status: int = 200):
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {"result": result}
    mock.raise_for_status = MagicMock()
    if status >= 400:
        from requests import HTTPError

        mock.raise_for_status.side_effect = HTTPError(response=mock)
    return mock


def test_empty_audio_returns_empty_string():
    from push2talk.recognizer import recognize

    result = recognize(b"", "token")
    assert result == ""


def test_single_chunk_recognize():
    from push2talk.recognizer import recognize

    audio = b"\x00\x01" * 100  # well under chunk size
    expected = "hello world"

    with patch("push2talk.recognizer.requests.post") as mock_post:
        mock_post.return_value = _make_response(expected)
        result = recognize(audio, "test-token", "ru-RU", 16000)

    assert result == expected
    mock_post.assert_called_once()


def test_single_chunk_sends_correct_headers():
    from push2talk.recognizer import recognize

    audio = b"\x00" * 100

    with patch("push2talk.recognizer.requests.post") as mock_post:
        mock_post.return_value = _make_response("ok")
        recognize(audio, "my-iam-token", "ru-RU", 16000)

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer my-iam-token"
    assert call_kwargs["params"]["lang"] == "ru-RU"
    assert call_kwargs["params"]["format"] == "lpcm"
    assert call_kwargs["params"]["sampleRateHertz"] == "16000"


def test_multi_chunk_splits_and_joins():
    from push2talk.recognizer import CHUNK_BYTES, recognize

    # 1.5 chunks worth of data → 2 chunks (1 full + 1 partial)
    audio = b"\x00" * (CHUNK_BYTES + CHUNK_BYTES // 2)

    responses = [
        _make_response("part one"),
        _make_response("part two"),
    ]

    with patch("push2talk.recognizer.requests.post") as mock_post:
        mock_post.side_effect = responses
        result = recognize(audio, "token", "ru-RU", 16000)

    assert result == "part one part two"
    assert mock_post.call_count == 2


def test_api_error_raises():
    from requests import HTTPError

    from push2talk.recognizer import _recognize_rest

    with patch("push2talk.recognizer.requests.post") as mock_post:
        mock_post.return_value = _make_response("", status=401)
        with pytest.raises(HTTPError):
            _recognize_rest(b"\x00" * 100, "bad-token", "ru-RU", 16000)


def test_multi_chunk_partial_failure_skips_chunk():
    """If one chunk fails, others still get joined."""
    from push2talk.recognizer import CHUNK_BYTES, recognize

    # 1.5 chunks → 2 chunks
    audio = b"\x00" * (CHUNK_BYTES + CHUNK_BYTES // 2)

    fail_resp = _make_response("", status=500)
    ok_resp = _make_response("second part")

    with patch("push2talk.recognizer.requests.post") as mock_post:
        mock_post.side_effect = [fail_resp, ok_resp]
        result = recognize(audio, "token")

    assert result == "second part"


def test_recognize_returns_empty_result_when_api_returns_no_result():
    from push2talk.recognizer import recognize

    with patch("push2talk.recognizer.requests.post") as mock_post:
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {}  # no "result" key
        mock_post.return_value = resp
        result = recognize(b"\x00" * 100, "token")

    assert result == ""
