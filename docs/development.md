# Development Guide

## Environment Setup

Requires Python 3.11 or later and a Windows machine (some dependencies are Windows-only).

```bash
git clone https://github.com/USER/push2talk.git
cd push2talk

python -m venv .venv
.venv\Scripts\activate

# Install package + dev dependencies
pip install -e ".[dev]"

# Copy and configure environment
copy .env.example .env
```

Edit `.env` with your STT credentials before running. See [docs/configuration.md](configuration.md).

## Running

```bash
python run.py
```

The app starts in the system tray. Right-click the icon to access settings and quit.

Logs are written to `push2talk.log` in the project root (rotating, max 1 MB × 3 files).

## Project Structure

```
push2talk/          # Application package
├── app.py          # Main application class, hotkey dispatch
├── config.py       # .env loading and validation
├── recorder.py     # Audio capture (sounddevice, WASAPI)
├── recognizer.py   # Yandex SpeechKit STT
├── openai_recognizer.py  # OpenAI Whisper STT
├── inserter.py     # Clipboard text insertion
├── tray.py         # System tray icon and menu
├── recording_overlay.py  # Animated tkinter overlay
├── history.py      # Recognition history (thread-safe deque)
├── sounds.py       # Beep feedback (winsound)
├── autostart.py    # Windows Startup folder integration
├── yandex_iam_auth.py    # Yandex IAM token management
└── logging_setup.py      # Rotating file logger

tests/              # pytest test suite
run.py              # Entry point
pyproject.toml      # Project metadata and tool config
.env.example        # Configuration template
```

## Linting and Formatting

```bash
# Check for issues
ruff check .

# Auto-fix and format
ruff format .
ruff check --fix .
```

Ruff is configured in `pyproject.toml` with `line-length = 100` targeting Python 3.11.

## Type Checking

```bash
mypy push2talk/
```

mypy is configured with `ignore_missing_imports = true` to handle Windows-only stubs (pystray, keyboard, winsound).

## Testing

```bash
# Run all tests
pytest -v

# With coverage
pytest --cov=push2talk --cov-report=term-missing
```

Tests live in `tests/`. Components with external dependencies (sounddevice, keyboard hooks, tray) use mocks; pure logic modules (config validation, history, IAM auth) are tested directly.

## Building a Standalone Executable

```bash
pip install pyinstaller

pyinstaller --onefile --windowed \
  --icon=push2talk.ico \
  --add-data "push2talk.ico;." \
  run.py
```

Output: `dist/run.exe`

Rename to `push2talk.exe` and place `.env` and `sa-key.json` (if using Yandex) in the same directory as the `.exe`.

The `--windowed` flag suppresses the console window. Omit it during debugging to see log output in the terminal.

## Architecture Reference

See [docs/architecture.md](architecture.md) for:
- Threading model (main / tray / overlay / worker threads)
- Data flow from hotkey press to text paste
- Application state machine
- Security considerations
