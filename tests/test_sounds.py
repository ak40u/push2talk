"""Tests for push2talk.sounds module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_play_start_sound_calls_beep(mock_winsound):
    from push2talk.sounds import play_start_sound

    with patch("push2talk.sounds.threading.Thread") as mock_thread_cls:
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread
        play_start_sound()

    mock_thread_cls.assert_called_once()
    mock_thread.start.assert_called_once()
    # Verify daemon=True
    call_kwargs = mock_thread_cls.call_args.kwargs
    assert call_kwargs.get("daemon") is True


def test_play_stop_sound_calls_beep(mock_winsound):
    from push2talk.sounds import play_stop_sound

    with patch("push2talk.sounds.threading.Thread") as mock_thread_cls:
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread
        play_stop_sound()

    mock_thread_cls.assert_called_once()
    mock_thread.start.assert_called_once()
    call_kwargs = mock_thread_cls.call_args.kwargs
    assert call_kwargs.get("daemon") is True


def test_play_start_sound_beep_frequency(mock_winsound):
    """Start sound uses 1200 Hz, 100ms."""
    from push2talk.sounds import play_start_sound

    captured = {}

    def fake_thread(target=None, daemon=None):
        captured["target"] = target
        m = MagicMock()
        m.start = MagicMock()
        return m

    with patch("push2talk.sounds.threading.Thread", side_effect=fake_thread):
        play_start_sound()

    # Execute the lambda to trigger winsound.Beep
    captured["target"]()
    mock_winsound.Beep.assert_called_once_with(1200, 100)


def test_play_stop_sound_beep_frequency(mock_winsound):
    """Stop sound uses 800 Hz, 150ms."""
    from push2talk.sounds import play_stop_sound

    captured = {}

    def fake_thread(target=None, daemon=None):
        captured["target"] = target
        m = MagicMock()
        m.start = MagicMock()
        return m

    with patch("push2talk.sounds.threading.Thread", side_effect=fake_thread):
        play_stop_sound()

    captured["target"]()
    mock_winsound.Beep.assert_called_once_with(800, 150)


def test_play_start_sound_is_nonblocking(mock_winsound):
    """Start sound returns immediately (thread is started, not joined)."""
    from push2talk.sounds import play_start_sound

    started = []

    class FakeThread:
        def __init__(self, target=None, daemon=None):
            self._target = target
        def start(self):
            started.append(True)
            # Do NOT call self._target() — verifies non-blocking

    with patch("push2talk.sounds.threading.Thread", FakeThread):
        play_start_sound()

    assert started == [True]
    mock_winsound.Beep.assert_not_called()  # not called synchronously
