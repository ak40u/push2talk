"""Yandex Cloud IAM token management from authorized key (JSON).

Generates JWT, exchanges for IAM token, caches until expiry.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import jwt
import requests

IAM_TOKEN_URL = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
TOKEN_LIFETIME = 3600  # request 1h token
REFRESH_MARGIN = 300   # refresh 5min before expiry


class YandexIAMAuth:
    def __init__(self, sa_key_path: str) -> None:
        with open(sa_key_path) as f:
            self._key: dict[str, Any] = json.load(f)
        self._token: str = ""
        self._expires_at: float = 0
        self._lock = threading.Lock()

    def _make_jwt(self) -> str:
        """Create signed JWT for IAM token exchange."""
        now = int(time.time())
        payload = {
            "iss": self._key["service_account_id"],
            "aud": IAM_TOKEN_URL,
            "iat": now,
            "exp": now + TOKEN_LIFETIME,
        }
        return jwt.encode(
            payload,
            self._key["private_key"],
            algorithm="PS256",
            headers={"kid": self._key["id"]},
        )

    def _refresh(self) -> None:
        """Exchange JWT for IAM token."""
        signed_jwt = self._make_jwt()
        resp = requests.post(
            IAM_TOKEN_URL,
            json={"jwt": signed_jwt},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["iamToken"]
        self._expires_at = time.time() + TOKEN_LIFETIME - REFRESH_MARGIN

    def get_token(self) -> str:
        """Return valid IAM token, refreshing if needed.

        Uses double-checked locking to avoid holding the lock during HTTP calls
        when the token is still valid.
        """
        if not self._token or time.time() >= self._expires_at:
            with self._lock:
                # Re-check after acquiring lock (another thread may have refreshed)
                if not self._token or time.time() >= self._expires_at:
                    self._refresh()
        return self._token
