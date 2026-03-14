"""Tests for push2talk.autostart module."""

from __future__ import annotations

import sys
from unittest.mock import patch


def test_is_frozen_false_in_dev():
    from push2talk.autostart import is_frozen
    # In test env (not PyInstaller), sys.frozen is not set
    assert is_frozen() is False


def test_is_frozen_true_when_attr_set():
    from push2talk.autostart import is_frozen
    with patch.object(sys, "frozen", True, create=True):
        assert is_frozen() is True


def test_is_autostart_enabled_false_when_bat_missing(tmp_startup):
    from push2talk import autostart
    result = autostart.is_autostart_enabled()
    assert result is False


def test_is_autostart_enabled_true_when_bat_exists(tmp_startup):
    from push2talk import autostart
    bat = tmp_startup / autostart.STARTUP_BAT_NAME
    bat.write_text("@start \"\" \"C:\\fake.exe\"\n")
    result = autostart.is_autostart_enabled()
    assert result is True


def test_enable_autostart_returns_false_when_not_frozen(tmp_startup):
    from push2talk.autostart import enable_autostart
    # is_frozen() returns False in test env
    result = enable_autostart()
    assert result is False


def test_enable_autostart_creates_bat_when_frozen(tmp_startup, monkeypatch):
    from push2talk import autostart
    monkeypatch.setattr(autostart, "is_frozen", lambda: True)
    with patch.object(sys, "executable", "C:\\fake\\push2talk.exe"):
        result = autostart.enable_autostart()

    assert result is True
    bat = tmp_startup / autostart.STARTUP_BAT_NAME
    assert bat.exists()
    content = bat.read_text()
    assert "push2talk.exe" in content


def test_enable_autostart_bat_content_format(tmp_startup, monkeypatch):
    from push2talk import autostart
    monkeypatch.setattr(autostart, "is_frozen", lambda: True)
    with patch.object(sys, "executable", "C:\\myapp\\app.exe"):
        autostart.enable_autostart()

    bat = tmp_startup / autostart.STARTUP_BAT_NAME
    content = bat.read_text()
    assert content.startswith("@start")
    assert "app.exe" in content


def test_disable_autostart_returns_true_when_no_bat(tmp_startup):
    from push2talk.autostart import disable_autostart
    result = disable_autostart()
    assert result is True


def test_disable_autostart_removes_existing_bat(tmp_startup, monkeypatch):
    from push2talk import autostart
    bat = tmp_startup / autostart.STARTUP_BAT_NAME
    bat.write_text("@start \"\" \"C:\\fake.exe\"\n")
    assert bat.exists()

    result = autostart.disable_autostart()
    assert result is True
    assert not bat.exists()


def test_disable_autostart_returns_false_on_oserror(tmp_startup, monkeypatch):
    from push2talk import autostart
    bat = tmp_startup / autostart.STARTUP_BAT_NAME
    bat.write_text("@start \"\" \"C:\\fake.exe\"\n")

    with patch("push2talk.autostart.os.remove", side_effect=OSError("permission denied")):
        result = autostart.disable_autostart()

    assert result is False
