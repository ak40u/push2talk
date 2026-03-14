"""Tests for push2talk.yandex_iam_auth module."""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, mock_open, patch

FAKE_SA_KEY = {
    "id": "key-id-123",
    "service_account_id": "sa-id-456",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----",
}


def _make_auth(key_dict=None):
    """Create YandexIAMAuth with mocked file I/O."""
    key_data = json.dumps(key_dict or FAKE_SA_KEY)
    with patch("builtins.open", mock_open(read_data=key_data)):
        from push2talk.yandex_iam_auth import YandexIAMAuth

        return YandexIAMAuth("fake/path/sa-key.json")


def _make_token_response(token: str = "iam-token-abc"):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"iamToken": token}
    return resp


def test_init_loads_key_file():
    """Constructor reads the SA key file."""
    key_data = json.dumps(FAKE_SA_KEY)
    with patch("builtins.open", mock_open(read_data=key_data)) as m:
        from push2talk.yandex_iam_auth import YandexIAMAuth

        YandexIAMAuth("some/path.json")
    m.assert_called_once_with("some/path.json")


def test_make_jwt_uses_correct_fields():
    """JWT payload has iss, aud, iat, exp fields."""
    auth = _make_auth()

    with patch("push2talk.yandex_iam_auth.jwt.encode") as mock_encode:
        mock_encode.return_value = "signed-jwt"
        auth._make_jwt()

    call_args = mock_encode.call_args
    payload = call_args[0][0]
    assert payload["iss"] == FAKE_SA_KEY["service_account_id"]
    assert payload["aud"] == "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_make_jwt_uses_kid_header():
    auth = _make_auth()

    with patch("push2talk.yandex_iam_auth.jwt.encode") as mock_encode:
        mock_encode.return_value = "signed-jwt"
        auth._make_jwt()

    call_kwargs = mock_encode.call_args[1]
    assert call_kwargs["headers"]["kid"] == FAKE_SA_KEY["id"]
    assert call_kwargs["algorithm"] == "PS256"


def test_get_token_calls_refresh_on_first_call():
    auth = _make_auth()

    with (
        patch("push2talk.yandex_iam_auth.jwt.encode", return_value="jwt"),
        patch("push2talk.yandex_iam_auth.requests.post") as mock_post,
    ):
        mock_post.return_value = _make_token_response("token-first")
        token = auth.get_token()

    assert token == "token-first"
    mock_post.assert_called_once()


def test_get_token_caches_on_second_call():
    """Second call within expiry window reuses token without HTTP."""
    auth = _make_auth()

    with (
        patch("push2talk.yandex_iam_auth.jwt.encode", return_value="jwt"),
        patch("push2talk.yandex_iam_auth.requests.post") as mock_post,
    ):
        mock_post.return_value = _make_token_response("cached-token")
        token1 = auth.get_token()
        token2 = auth.get_token()

    assert token1 == token2 == "cached-token"
    assert mock_post.call_count == 1  # only one HTTP call


def test_get_token_refreshes_when_expired():
    """Token is refreshed when expires_at is in the past."""
    auth = _make_auth()

    with (
        patch("push2talk.yandex_iam_auth.jwt.encode", return_value="jwt"),
        patch("push2talk.yandex_iam_auth.requests.post") as mock_post,
    ):
        mock_post.side_effect = [
            _make_token_response("old-token"),
            _make_token_response("new-token"),
        ]
        # Get initial token
        auth.get_token()
        # Force expiry
        auth._expires_at = time.time() - 1
        token = auth.get_token()

    assert token == "new-token"
    assert mock_post.call_count == 2


def test_refresh_posts_to_iam_url():
    auth = _make_auth()

    with (
        patch("push2talk.yandex_iam_auth.jwt.encode", return_value="test-jwt"),
        patch("push2talk.yandex_iam_auth.requests.post") as mock_post,
    ):
        mock_post.return_value = _make_token_response()
        auth.get_token()

    call_args = mock_post.call_args
    assert "iam.api.cloud.yandex.net" in call_args[0][0]
    assert call_args[1]["json"]["jwt"] == "test-jwt"
