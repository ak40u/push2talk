"""Audio feedback for recording start/stop using Windows winsound."""

from __future__ import annotations

import threading
import winsound


def play_start_sound() -> None:
    """High chirp when recording starts. Non-blocking."""
    threading.Thread(target=lambda: winsound.Beep(1200, 100), daemon=True).start()


def play_stop_sound() -> None:
    """Lower tone when recording stops. Non-blocking."""
    threading.Thread(target=lambda: winsound.Beep(800, 150), daemon=True).start()
