"""OpenAI gpt-4o-mini-transcribe speech-to-text recognition.

Converts raw PCM audio to WAV in-memory, sends to OpenAI transcription API.
Supports chunking for long recordings (max 25MB per request).
"""

from __future__ import annotations

import io
import logging
import wave

import requests

from push2talk.stt_common import recognize_chunked

log = logging.getLogger("push2talk")

OPENAI_API_URL = "https://api.openai.com/v1/audio/transcriptions"
MODEL = "gpt-4o-mini-transcribe"

# Max ~24MB to stay under 25MB API limit
MAX_WAV_BYTES = 24 * 1024 * 1024
# PCM overhead for WAV header is negligible, but account for it
WAV_HEADER_SIZE = 44


def _pcm_to_wav(pcm_data: bytes, sample_rate: int) -> bytes:
    """Convert raw PCM 16-bit mono bytes to WAV format in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def recognize_openai(
    audio_data: bytes,
    api_key: str,
    lang: str = "ru",
    sample_rate: int = 16000,
) -> str:
    """Recognize speech via OpenAI gpt-4o-mini-transcribe.

    Splits into chunks if audio exceeds API size limit.
    """
    if not audio_data:
        return ""

    # Calculate max PCM bytes per chunk (WAV adds ~44 bytes header)
    max_pcm = MAX_WAV_BYTES - WAV_HEADER_SIZE

    if len(audio_data) <= max_pcm:
        return _recognize_chunk(audio_data, api_key, lang, sample_rate)

    return recognize_chunked(
        audio_data,
        chunk_size=max_pcm,
        recognize_fn=lambda chunk: _recognize_chunk(chunk, api_key, lang, sample_rate),
        engine_name="OpenAI",
        sample_rate=sample_rate,
    )


def _recognize_chunk(
    pcm_data: bytes,
    api_key: str,
    lang: str,
    sample_rate: int,
) -> str:
    """Send single WAV chunk to OpenAI transcription API."""
    wav_data = _pcm_to_wav(pcm_data, sample_rate)
    response = requests.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("audio.wav", wav_data, "audio/wav")},
        data={
            "model": MODEL,
            "language": lang[:2],  # "ru-RU" -> "ru"
            "response_format": "text",
        },
        timeout=60,
    )
    response.raise_for_status()
    result: str = response.text.strip()
    return result
