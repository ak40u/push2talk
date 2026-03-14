"""Application configuration loaded from .env file."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

# Resolve base dir: next to .exe (frozen) or project root (dev)
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(_BASE_DIR, ".env"))

_sa_raw = os.getenv("SA_KEY_PATH", "sa-key.json")
SA_KEY_PATH = _sa_raw if os.path.isabs(_sa_raw) else os.path.join(_BASE_DIR, _sa_raw)
HOTKEY = os.getenv("HOTKEY", "right ctrl")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
LANGUAGE = os.getenv("LANGUAGE", "en-US")

# Microphone device index (empty = system default)
_mic_raw = os.getenv("MICROPHONE_INDEX", "")
MICROPHONE_INDEX: int | None = int(_mic_raw) if _mic_raw.strip() else None

# Max items in recognition history tray submenu
HISTORY_SIZE = int(os.getenv("HISTORY_SIZE", "20"))

# OpenAI API key for gpt-4o-mini-transcribe (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default STT engine: "yandex" or "openai"
STT_ENGINE = os.getenv("STT_ENGINE", "openai")


def validate() -> list[str]:
    """Check required config values. Return list of errors."""
    errors = []
    if not HOTKEY:
        errors.append("HOTKEY not set in .env")
    if STT_ENGINE not in ("yandex", "openai"):
        errors.append(f"Unknown STT_ENGINE '{STT_ENGINE}', must be 'yandex' or 'openai'")
    if not (8000 <= SAMPLE_RATE <= 48000):
        errors.append(f"SAMPLE_RATE={SAMPLE_RATE} out of range (8000-48000)")
    if not (1 <= HISTORY_SIZE <= 100):
        errors.append(f"HISTORY_SIZE={HISTORY_SIZE} out of range (1-100)")
    # Validate selected engine has credentials
    if STT_ENGINE == "yandex" and not os.path.exists(SA_KEY_PATH):
        errors.append(f"STT_ENGINE=yandex but SA key not found: {SA_KEY_PATH}")
    if STT_ENGINE == "openai" and not OPENAI_API_KEY:
        errors.append("STT_ENGINE=openai but OPENAI_API_KEY is empty")
    return errors
