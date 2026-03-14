"""Shared helpers for STT recognition modules."""

from __future__ import annotations

import logging
from collections.abc import Callable

log = logging.getLogger("push2talk")


def recognize_chunked(
    audio_data: bytes,
    chunk_size: int,
    recognize_fn: Callable[[bytes], str],
    engine_name: str,
    sample_rate: int = 16000,
) -> str:
    """Split audio into chunks and recognize each, joining results.

    Args:
        audio_data: Raw PCM 16-bit mono audio bytes.
        chunk_size: Max bytes per chunk.
        recognize_fn: Callable that takes a chunk and returns recognized text.
        engine_name: Name for log messages (e.g. "Yandex", "OpenAI").
        sample_rate: Audio sample rate for duration logging.
    """
    parts: list[str] = []
    offset = 0
    chunk_num = 0
    while offset < len(audio_data):
        chunk = audio_data[offset : offset + chunk_size]
        chunk_num += 1
        log.info("%s chunk %d (%.1fs)...", engine_name, chunk_num, len(chunk) / sample_rate / 2)
        try:
            text = recognize_fn(chunk)
        except Exception as e:
            log.error("%s chunk %d failed: %s", engine_name, chunk_num, e)
        else:
            if text:
                parts.append(text)
        offset += chunk_size
    return " ".join(parts)
