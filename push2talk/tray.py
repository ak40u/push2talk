"""Tray icon helpers: constants, icon loading and creation."""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

# Available STT engines
ENGINES: dict[str, str] = {"yandex": "Yandex SpeechKit", "openai": "OpenAI Whisper"}

# Tray icon colors for each state
COLORS: dict[str, str] = {
    "ready": "#4CAF50",
    "recording": "#F44336",
    "processing": "#FFC107",
}

# Resolve icon path (works for dev and frozen exe)
if getattr(sys, "frozen", False):
    _ICON_DIR: str = sys._MEIPASS  # type: ignore[attr-defined]
else:
    _ICON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ICON_PATH: str = os.path.join(_ICON_DIR, "push2talk.ico")


def _load_base_icon(size: int = 64) -> Image.Image:
    """Load push2talk.ico and resize to given size."""
    try:
        img = Image.open(_ICON_PATH)
        img = img.resize((size, size), Image.LANCZOS)
        return img.convert("RGBA")
    except Exception:
        # Fallback: plain circle
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(img).ellipse([4, 4, size - 4, size - 4], fill="#4CAF50")
        return img


def create_icon_image(color: str, size: int = 64) -> Image.Image:
    """Base icon with a small colored status dot in bottom-right corner."""
    img = _load_base_icon(size).copy()
    draw = ImageDraw.Draw(img)
    # Status dot: bottom-right corner
    dot_r = size // 6
    margin = 2
    draw.ellipse(
        [size - dot_r * 2 - margin, size - dot_r * 2 - margin, size - margin, size - margin],
        fill=color,
        outline="#1a1a2e",
        width=max(1, size // 32),
    )
    return img
