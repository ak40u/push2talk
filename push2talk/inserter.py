"""Text insertion at current cursor position via clipboard + Ctrl+V.

Uses clipboard approach because pyautogui.typewrite doesn't support Cyrillic.
Saves and restores previous clipboard contents to avoid data loss.
"""

from __future__ import annotations

import contextlib
import time

import keyboard
import pyperclip


def insert_text(text: str) -> None:
    """Copy text to clipboard, paste at cursor, restore previous clipboard."""
    if not text:
        return
    # Save current clipboard
    try:
        prev = pyperclip.paste()
    except Exception:
        prev = None

    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.send("ctrl+v")

    # Restore after paste completes
    if prev is not None:
        time.sleep(0.15)
        with contextlib.suppress(Exception):
            pyperclip.copy(prev)
