"""Yandex SpeechKit speech-to-text recognition.

Sends audio to REST API in <=30s chunks. For long recordings (up to 20min+),
audio is split into chunks and each is recognized separately.
Uses IAM token auth from service account authorized key.
"""

from __future__ import annotations

import logging

import requests

from push2talk.stt_common import recognize_chunked

log = logging.getLogger("push2talk")

YANDEX_STT_REST_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

# 29s chunk (slightly under 30s limit for safety). 16kHz 16-bit mono.
CHUNK_SECONDS = 29
BYTES_PER_SECOND = 16000 * 2  # sample_rate * 2 bytes (16-bit)
CHUNK_BYTES = CHUNK_SECONDS * BYTES_PER_SECOND  # 928,000


def recognize(
    audio_data: bytes,
    iam_token: str,
    lang: str = "ru-RU",
    sample_rate: int = 16000,
) -> str:
    """Recognize speech from raw PCM audio bytes.

    Splits into 29s chunks if audio exceeds REST API 30s limit.
    """
    if not audio_data:
        return ""

    chunk_bytes = CHUNK_SECONDS * sample_rate * 2
    if len(audio_data) <= chunk_bytes:
        return _recognize_rest(audio_data, iam_token, lang, sample_rate)

    return recognize_chunked(
        audio_data,
        chunk_size=chunk_bytes,
        recognize_fn=lambda chunk: _recognize_rest(chunk, iam_token, lang, sample_rate),
        engine_name="Yandex",
        sample_rate=sample_rate,
    )


def _recognize_rest(
    audio_data: bytes,
    iam_token: str,
    lang: str,
    sample_rate: int,
) -> str:
    """REST API for single chunk (<=30s)."""
    response = requests.post(
        YANDEX_STT_REST_URL,
        headers={"Authorization": f"Bearer {iam_token}"},
        params={
            "lang": lang,
            "format": "lpcm",
            "sampleRateHertz": sample_rate,
        },
        data=audio_data,
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("result", "")
