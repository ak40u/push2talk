# AGENTS.md

This file provides guidance to AI coding agents working with this repository.

## Project Overview

**Name:** Push2Talk
**Type:** Python Desktop Application
**Description:** Push-to-talk speech recognition for Windows. Hold a hotkey to record, release to recognize and paste text at cursor position. Supports Yandex SpeechKit and OpenAI Whisper STT engines.

## Tech Stack
- Python 3.11+
- sounddevice (audio recording)
- keyboard (global hotkeys)
- pystray (system tray)
- tkinter (recording overlay)
- requests (STT API calls)

## Project Structure

```
push2talk/          # Main package
├── app.py          # Push2Talk application class
├── tray.py         # System tray icon management
├── recorder.py     # Audio recording (sounddevice)
├── recognizer.py   # Yandex SpeechKit STT
├── openai_recognizer.py  # OpenAI Whisper STT
├── inserter.py     # Text insertion via clipboard
├── sounds.py       # Audio feedback (winsound)
├── history.py      # Recognition history
├── recording_overlay.py  # Animated overlay (tkinter)
├── autostart.py    # Windows autostart management
├── config.py       # Configuration from .env
├── logging_setup.py # Logging configuration
└── yandex_iam_auth.py   # Yandex IAM authentication
```
