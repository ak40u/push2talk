"""Tests for push2talk.config module."""

from __future__ import annotations

import os


def test_default_hotkey():
    import push2talk.config as cfg

    assert os.getenv("HOTKEY", "right ctrl") == cfg.HOTKEY


def test_default_sample_rate():
    import push2talk.config as cfg

    assert int(os.getenv("SAMPLE_RATE", "16000")) == cfg.SAMPLE_RATE


def test_default_language():
    import push2talk.config as cfg

    assert os.getenv("LANGUAGE", "en-US") == cfg.LANGUAGE


def test_default_history_size():
    import push2talk.config as cfg

    assert int(os.getenv("HISTORY_SIZE", "20")) == cfg.HISTORY_SIZE


def test_default_stt_engine():
    import push2talk.config as cfg

    assert cfg.STT_ENGINE in ("yandex", "openai")


def test_validate_unknown_engine(monkeypatch):
    import push2talk.config as cfg

    monkeypatch.setattr(cfg, "STT_ENGINE", "unknown_engine")
    monkeypatch.setattr(cfg, "HOTKEY", "right ctrl")
    errors = cfg.validate()
    assert any("STT_ENGINE" in e for e in errors)


def test_validate_yandex_missing_sa_key(monkeypatch, tmp_path):
    import push2talk.config as cfg

    monkeypatch.setattr(cfg, "STT_ENGINE", "yandex")
    monkeypatch.setattr(cfg, "HOTKEY", "right ctrl")
    monkeypatch.setattr(cfg, "SA_KEY_PATH", str(tmp_path / "nonexistent.json"))
    errors = cfg.validate()
    assert any("SA key" in e for e in errors)


def test_validate_yandex_valid(monkeypatch, tmp_path):
    import push2talk.config as cfg

    sa_key = tmp_path / "sa-key.json"
    sa_key.write_text("{}")
    monkeypatch.setattr(cfg, "STT_ENGINE", "yandex")
    monkeypatch.setattr(cfg, "HOTKEY", "right ctrl")
    monkeypatch.setattr(cfg, "SA_KEY_PATH", str(sa_key))
    errors = cfg.validate()
    assert errors == []


def test_validate_openai_missing_key(monkeypatch):
    import push2talk.config as cfg

    monkeypatch.setattr(cfg, "STT_ENGINE", "openai")
    monkeypatch.setattr(cfg, "HOTKEY", "right ctrl")
    monkeypatch.setattr(cfg, "OPENAI_API_KEY", "")
    errors = cfg.validate()
    assert any("OPENAI_API_KEY" in e for e in errors)


def test_validate_openai_valid(monkeypatch):
    import push2talk.config as cfg

    monkeypatch.setattr(cfg, "STT_ENGINE", "openai")
    monkeypatch.setattr(cfg, "HOTKEY", "right ctrl")
    monkeypatch.setattr(cfg, "OPENAI_API_KEY", "sk-test-key")
    errors = cfg.validate()
    assert errors == []


def test_validate_missing_hotkey(monkeypatch):
    import push2talk.config as cfg

    monkeypatch.setattr(cfg, "HOTKEY", "")
    monkeypatch.setattr(cfg, "STT_ENGINE", "openai")
    monkeypatch.setattr(cfg, "OPENAI_API_KEY", "sk-test")
    errors = cfg.validate()
    assert any("HOTKEY" in e for e in errors)
