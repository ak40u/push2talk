# Push2Talk

> Push-to-talk speech recognition for Windows. Hold a key, speak, release — text appears at your cursor.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/ak40u/push2talk/actions/workflows/ci.yml/badge.svg)](https://github.com/ak40u/push2talk/actions)

## Features

- **Push-to-talk** — configurable hotkey (default: Right Ctrl), no always-on listening
- **Dual STT engines** — Yandex SpeechKit and OpenAI Whisper, switchable at runtime
- **Auto-paste** — recognized text inserted at cursor via clipboard
- **Visual feedback** — animated overlay (recording: pulsing dot + sound bars; processing: spinner)
- **System tray** — color-coded status dot, recognition history, mic & engine switching
- **Windows autostart** — optional launch on login via Startup folder
- **Single-file distribution** — packages as standalone `.exe` via PyInstaller

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────┐
│  Hold Key   │────▶│  Record Mic  │────▶│  STT Engine   │────▶│  Paste   │
│  (hotkey)   │     │  PCM 16kHz   │     │  (API call)   │     │  Ctrl+V  │
└─────────────┘     └──────────────┘     └───────────────┘     └──────────┘
       │                                        │
       ▼                                        ▼
  ┌──────────┐                          ┌──────────────┐
  │ Overlay  │                          │   History    │
  │ (tkinter)│                          │  (tray menu) │
  └──────────┘                          └──────────────┘
```

Tray icon status dot: **green** = ready, **red** = recording, **amber** = processing.

## Quick Start

### Prerequisites

- Windows 10 or 11
- Python 3.11+
- OpenAI API key (or Yandex Cloud service account key for Yandex engine)

### Installation

```bash
git clone https://github.com/ak40u/push2talk.git
cd push2talk

python -m venv .venv
.venv\Scripts\activate

pip install -e .

copy .env.example .env
```

### Configuration

Edit `.env` with your credentials (see [Configuration](#configuration) below), then:

```bash
python run.py
```

The app runs in the system tray. Hold your hotkey to start recording, release to transcribe.

## Configuration

Copy `.env.example` to `.env` and set the values:

| Variable | Default | Description |
|---|---|---|
| `HOTKEY` | `right ctrl` | Push-to-talk key (any name accepted by the `keyboard` library) |
| `STT_ENGINE` | `openai` | Active engine: `openai` or `yandex` |
| `LANGUAGE` | `en-US` | BCP-47 language code for recognition |
| `SAMPLE_RATE` | `16000` | Microphone sample rate in Hz |
| `MICROPHONE_INDEX` | *(empty)* | Sounddevice device index — empty uses system default |
| `HISTORY_SIZE` | `20` | Maximum items kept in the tray history submenu |
| `SA_KEY_PATH` | `sa-key.json` | Path to Yandex service account authorized key (JSON) |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key (required for default `openai` engine) |

**Hotkey examples:** `right ctrl`, `f9`, `scroll lock`, `pause`, `insert`

**Language codes:** `ru-RU`, `en-US`, `de-DE`, `fr-FR` (engine-dependent)

See [docs/configuration.md](docs/configuration.md) for full setup guides for both STT providers.

## Building Executable

```bash
pip install pyinstaller

pyinstaller --onefile --windowed --icon=push2talk.ico \
  --add-data "push2talk.ico;." \
  run.py
```

Place `.env` and `sa-key.json` (if using Yandex) next to the generated `.exe` in `dist/`.

## Project Structure

```
push2talk/
├── app.py               # Push2Talk application class, hotkey handling
├── tray.py              # System tray icon management
├── recorder.py          # Audio recording via sounddevice (WASAPI)
├── recognizer.py        # Yandex SpeechKit STT (REST API, chunked)
├── openai_recognizer.py # OpenAI Whisper STT
├── inserter.py          # Text insertion at cursor via clipboard
├── sounds.py            # Audio feedback (winsound beeps)
├── history.py           # Thread-safe recognition history (deque)
├── recording_overlay.py # Animated overlay window (tkinter, click-through)
├── autostart.py         # Windows autostart via Startup folder .bat
├── config.py            # Configuration from .env
├── logging_setup.py     # Rotating file logger
├── yandex_iam_auth.py   # Yandex IAM token (JWT → IAM exchange, cached)
└── py.typed             # PEP 561 marker
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run
python run.py

# Lint & format
ruff check .
ruff format .

# Type check
mypy push2talk/

# Tests
pytest -v
```

See [docs/development.md](docs/development.md) for the full development guide and [docs/architecture.md](docs/architecture.md) for system design.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
