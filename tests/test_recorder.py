"""Tests for push2talk.recorder module."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def reset_sd_mocks():
    """Reset sounddevice mocks before each test."""
    sd = sys.modules["sounddevice"]
    sd.query_hostapis.reset_mock()
    sd.query_devices.reset_mock()
    sd.InputStream.reset_mock()
    yield


def _make_stream_mock():
    m = MagicMock()
    m.start = MagicMock()
    m.stop = MagicMock()
    m.close = MagicMock()
    return m


def test_is_recording_initial_false():
    from push2talk.recorder import AudioRecorder
    r = AudioRecorder()
    assert r.is_recording is False


def test_start_sets_recording_true():
    from push2talk.recorder import AudioRecorder
    sd = sys.modules["sounddevice"]
    stream_mock = _make_stream_mock()
    sd.InputStream.return_value = stream_mock

    r = AudioRecorder()
    r.start()
    assert r.is_recording is True


def test_stop_sets_recording_false():
    from push2talk.recorder import AudioRecorder
    sd = sys.modules["sounddevice"]
    stream_mock = _make_stream_mock()
    sd.InputStream.return_value = stream_mock

    r = AudioRecorder()
    r.start()
    r.stop()
    assert r.is_recording is False


def test_stop_calls_stream_stop_and_close():
    from push2talk.recorder import AudioRecorder
    sd = sys.modules["sounddevice"]
    stream_mock = _make_stream_mock()
    sd.InputStream.return_value = stream_mock

    r = AudioRecorder()
    r.start()
    r.stop()
    stream_mock.stop.assert_called_once()
    stream_mock.close.assert_called_once()


def test_empty_recording_returns_empty_bytes():
    from push2talk.recorder import AudioRecorder
    sd = sys.modules["sounddevice"]
    stream_mock = _make_stream_mock()
    sd.InputStream.return_value = stream_mock

    r = AudioRecorder()
    r.start()
    result = r.stop()
    assert result == b""


def test_audio_callback_appends_frames():
    from push2talk.recorder import AudioRecorder
    sd = sys.modules["sounddevice"]
    stream_mock = _make_stream_mock()
    sd.InputStream.return_value = stream_mock

    r = AudioRecorder()
    r.start()

    # Simulate audio callback
    frame = np.array([[100], [200], [300]], dtype=np.int16)
    r._audio_callback(frame, 3, None, None)

    audio = r.stop()
    assert len(audio) == frame.tobytes().__len__()
    assert audio == frame.tobytes()


def test_audio_callback_ignored_when_not_recording():
    from push2talk.recorder import AudioRecorder
    r = AudioRecorder()
    # Not recording — callback should be a no-op
    frame = np.array([[100]], dtype=np.int16)
    r._audio_callback(frame, 1, None, None)
    assert r._frames == []


def test_start_uses_correct_params():
    from push2talk.recorder import AudioRecorder
    sd = sys.modules["sounddevice"]
    stream_mock = _make_stream_mock()
    sd.InputStream.return_value = stream_mock

    r = AudioRecorder(sample_rate=8000, device=2)
    r.start()

    call_kwargs = sd.InputStream.call_args.kwargs
    assert call_kwargs["samplerate"] == 8000
    assert call_kwargs["device"] == 2
    assert call_kwargs["channels"] == 1
    assert call_kwargs["dtype"] == "int16"


def test_list_input_devices_no_wasapi():
    """With no WASAPI host API, all input devices are returned."""
    from push2talk.recorder import list_input_devices
    sd = sys.modules["sounddevice"]
    sd.query_hostapis.return_value = [{"name": "MME"}]
    sd.query_devices.return_value = [
        {"name": "Microphone", "max_input_channels": 2, "hostapi": 0, "default_samplerate": 44100},
        {"name": "Speakers", "max_input_channels": 0, "hostapi": 0, "default_samplerate": 44100},
    ]
    devices = list_input_devices()
    assert len(devices) == 1
    assert devices[0]["name"] == "Microphone"


def test_list_input_devices_wasapi_filters_non_wasapi():
    """With WASAPI available, only WASAPI devices are returned."""
    from push2talk.recorder import list_input_devices
    sd = sys.modules["sounddevice"]
    sd.query_hostapis.return_value = [
        {"name": "MME"},
        {"name": "Windows WASAPI"},
    ]
    sd.query_devices.return_value = [
        {"name": "Mic MME", "max_input_channels": 1, "hostapi": 0, "default_samplerate": 44100},
        {"name": "Mic WASAPI", "max_input_channels": 1, "hostapi": 1, "default_samplerate": 44100},
    ]
    devices = list_input_devices()
    assert len(devices) == 1
    assert devices[0]["name"] == "Mic WASAPI"


def test_list_input_devices_excludes_virtual():
    """Stereo mix and similar virtual devices are excluded."""
    from push2talk.recorder import list_input_devices
    sd = sys.modules["sounddevice"]
    sd.query_hostapis.return_value = [{"name": "MME"}]
    sd.query_devices.return_value = [
        {"name": "Stereo Mix", "max_input_channels": 2, "hostapi": 0, "default_samplerate": 44100},
        {"name": "Real Mic", "max_input_channels": 1, "hostapi": 0, "default_samplerate": 44100},
    ]
    devices = list_input_devices()
    assert len(devices) == 1
    assert devices[0]["name"] == "Real Mic"


def test_list_input_devices_result_structure():
    from push2talk.recorder import list_input_devices
    sd = sys.modules["sounddevice"]
    sd.query_hostapis.return_value = [{"name": "MME"}]
    sd.query_devices.return_value = [
        {"name": "My Mic", "max_input_channels": 2, "hostapi": 0, "default_samplerate": 16000},
    ]
    devices = list_input_devices()
    assert devices[0]["index"] == 0
    assert devices[0]["name"] == "My Mic"
    assert devices[0]["channels"] == 2
    assert devices[0]["default_sr"] == 16000
