"""Shared pytest fixtures for Push2Talk tests."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub out Windows-only / hardware modules before any push2talk import
# ---------------------------------------------------------------------------

def _make_stub(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    return mod


# winsound — not available outside Windows; stub before import
if "winsound" not in sys.modules:
    ws = _make_stub("winsound")
    ws.Beep = MagicMock()  # type: ignore[attr-defined]
    sys.modules["winsound"] = ws

# sounddevice stub
if "sounddevice" not in sys.modules:
    sd = _make_stub("sounddevice")
    sd.query_hostapis = MagicMock(return_value=[])  # type: ignore[attr-defined]
    sd.query_devices = MagicMock(return_value=[])   # type: ignore[attr-defined]
    sd.InputStream = MagicMock()                    # type: ignore[attr-defined]
    sd.CallbackFlags = MagicMock()                  # type: ignore[attr-defined]
    sys.modules["sounddevice"] = sd

# keyboard stub
if "keyboard" not in sys.modules:
    kb = _make_stub("keyboard")
    kb.send = MagicMock()          # type: ignore[attr-defined]
    kb.add_hotkey = MagicMock()    # type: ignore[attr-defined]
    kb.remove_hotkey = MagicMock() # type: ignore[attr-defined]
    sys.modules["keyboard"] = kb

# pyperclip stub
if "pyperclip" not in sys.modules:
    pc = _make_stub("pyperclip")
    pc.copy = MagicMock()   # type: ignore[attr-defined]
    pc.paste = MagicMock(return_value="")  # type: ignore[attr-defined]
    sys.modules["pyperclip"] = pc

# pystray stub (used by tray/app at import time)
if "pystray" not in sys.modules:
    pt = _make_stub("pystray")
    pt.Icon = MagicMock()        # type: ignore[attr-defined]
    pt.Menu = MagicMock()        # type: ignore[attr-defined]
    pt.MenuItem = MagicMock()    # type: ignore[attr-defined]
    sys.modules["pystray"] = pt

# tkinter stub (recording_overlay uses it; not available in headless CI)
if "tkinter" not in sys.modules:
    _tk = _make_stub("tkinter")
    _tk.Tk = MagicMock()        # type: ignore[attr-defined]
    _tk.Canvas = MagicMock()    # type: ignore[attr-defined]
    sys.modules["tkinter"] = _tk

# PIL / Pillow stub
if "PIL" not in sys.modules:
    pil = _make_stub("PIL")
    img_mod = _make_stub("PIL.Image")
    img_mod.new = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]
    pil.Image = img_mod  # type: ignore[attr-defined]
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = img_mod

# ImageDraw stub
if "PIL.ImageDraw" not in sys.modules:
    idraw = _make_stub("PIL.ImageDraw")
    idraw.Draw = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]
    sys.modules["PIL.ImageDraw"] = idraw


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_sounddevice():
    """Return the stubbed sounddevice module for manipulation in tests."""
    return sys.modules["sounddevice"]


@pytest.fixture()
def mock_keyboard():
    """Return the stubbed keyboard module."""
    return sys.modules["keyboard"]


@pytest.fixture()
def mock_requests():
    """Patch requests.post for the duration of a test."""
    with patch("requests.post") as mock_post:
        yield mock_post


@pytest.fixture()
def mock_pyperclip():
    """Return the stubbed pyperclip module with fresh mocks."""
    pc = sys.modules["pyperclip"]
    pc.copy.reset_mock()
    pc.paste.reset_mock()
    pc.paste.side_effect = None  # clear any side_effect from prior tests
    pc.paste.return_value = ""
    return pc


@pytest.fixture()
def mock_winsound():
    """Return the stubbed winsound module with fresh Beep mock."""
    ws = sys.modules["winsound"]
    ws.Beep.reset_mock()
    return ws


@pytest.fixture()
def tmp_startup(tmp_path, monkeypatch):
    """Point APPDATA to a temp dir so autostart tests don't touch the real FS."""
    fake_startup = tmp_path / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    fake_startup.mkdir(parents=True)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    return fake_startup
