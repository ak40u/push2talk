# Contributing to Push2Talk

## Prerequisites

- Python 3.11+
- Windows (required — uses `winsound`, `keyboard`, system tray APIs)

## Dev Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
```

## Code Style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for issues
ruff check .

# Auto-fix
ruff check --fix .

# Format code
ruff format .
```

Configuration is in `pyproject.toml` (`[tool.ruff]`).

## Type Checking

```bash
mypy push2talk/
```

## Running Tests

```bash
pytest

# With coverage report
pytest --cov=push2talk --cov-report=term-missing
```

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat:     new feature
fix:      bug fix
docs:     documentation only
refactor: code change that is not a fix or feature
test:     adding or fixing tests
chore:    build process or tooling changes
```

Examples:
```
feat: add pause/resume hotkey support
fix: prevent duplicate clipboard paste on fast release
docs: document STT engine configuration
```

## Environment Setup

Copy `.env.example` to `.env` and fill in your credentials:

```bash
copy .env.example .env
```

Required for Yandex SpeechKit: create a service account key and set `SA_KEY_PATH`.
Required for OpenAI Whisper: set `OPENAI_API_KEY`.

## Pull Requests

- Keep PRs focused on a single concern
- Ensure `ruff check .` and `mypy push2talk/` pass before submitting
- Add or update tests for changed behavior
- Do not commit `.env`, `sa-key.json`, or any credentials
