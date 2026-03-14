"""Microphone audio recorder using sounddevice.

Records 16-bit PCM mono audio at configurable sample rate.
Thread-safe start/stop with raw PCM byte output for Yandex STT API.
"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import sounddevice as sd


def _get_wasapi_hostapi_index() -> int | None:
    """Find Windows WASAPI host API index."""
    for i, api in enumerate(sd.query_hostapis()):
        if "WASAPI" in api["name"]:
            return i
    return None


# Names to exclude from mic list (not real microphones)
_EXCLUDED = {"stereo mix", "pc speaker", "sound mapper", "primary sound"}


def list_input_devices() -> list[dict[str, Any]]:
    """Return deduplicated list of real input devices (WASAPI only)."""
    devices = sd.query_devices()
    wasapi = _get_wasapi_hostapi_index()
    result = []
    for i, d in enumerate(devices):
        if d["max_input_channels"] <= 0:
            continue
        # Filter to WASAPI if available (avoids MME/DirectSound duplicates)
        if wasapi is not None and d["hostapi"] != wasapi:
            continue
        # Skip virtual/non-mic entries
        if any(ex in d["name"].lower() for ex in _EXCLUDED):
            continue
        result.append(
            {
                "index": i,
                "name": d["name"],
                "channels": d["max_input_channels"],
                "default_sr": d["default_samplerate"],
            }
        )
    return result


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, device: int | None = None):
        self.sample_rate = sample_rate
        self.device = device  # None = system default
        self._recording = False
        self._frames: list[np.ndarray] = []
        self._stream = None
        self._lock = threading.Lock()

    def _audio_callback(
        self,
        indata: np.ndarray,
        frame_count: int,
        time_info: Any,
        status: sd.CallbackFlags,
    ) -> None:
        """Called by sounddevice for each audio block."""
        if self._recording:
            self._frames.append(indata.copy())

    def start(self) -> None:
        """Begin recording from configured microphone."""
        with self._lock:
            self._frames = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                device=self.device,
                callback=self._audio_callback,
            )
            self._stream.start()

    def stop(self) -> bytes:
        """Stop recording, return raw PCM 16-bit bytes."""
        with self._lock:
            self._recording = False
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            frames = self._frames
            self._frames = []
        if not frames:
            return b""
        audio = np.concatenate(frames)
        return audio.tobytes()

    @property
    def is_recording(self) -> bool:
        return self._recording
