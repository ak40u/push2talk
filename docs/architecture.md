# Architecture

## System Overview

Push2Talk is a Windows desktop application that captures microphone audio on hotkey press and delivers recognized text to the active window via the clipboard.

```
┌──────────────────────────────────────────────────────────┐
│                     Push2Talk Process                    │
│                                                          │
│  Main Thread          Tray Thread       Overlay Thread   │
│  ──────────           ───────────       ──────────────   │
│  keyboard hooks  ───▶ pystray icon      tkinter loop     │
│  (Windows req.)       menu builder      poll() every 50ms│
│        │                   │                  │          │
│        ▼                   │                  │          │
│  Worker Thread             │                  │          │
│  ─────────────             │                  │          │
│  AudioRecorder             │                  │          │
│  STT API call  ────────────┘                  │          │
│  insert_text   ───────────────────────────────┘          │
└──────────────────────────────────────────────────────────┘
```

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Orchestrates all components; hotkey event dispatch; state management |
| `tray.py` | Builds and rebuilds pystray menu; status icon images |
| `recorder.py` | sounddevice InputStream; WASAPI device enumeration; PCM byte output |
| `recognizer.py` | Yandex SpeechKit REST calls; 29s chunking for long recordings |
| `openai_recognizer.py` | OpenAI Whisper transcription API |
| `inserter.py` | Writes text to clipboard, sends Ctrl+V to active window |
| `sounds.py` | winsound beeps for start/stop feedback |
| `history.py` | Thread-safe `deque` of recent transcriptions |
| `recording_overlay.py` | Transparent click-through tkinter window; two animation modes |
| `autostart.py` | Creates/removes `.bat` in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup` |
| `config.py` | Reads `.env` via python-dotenv; validates required credentials |
| `logging_setup.py` | Rotating file handler; log level from environment |
| `yandex_iam_auth.py` | JWT generation, IAM token exchange, thread-safe caching |

## Data Flow

```
Hotkey DOWN
    │
    ├─▶ icon → "recording" (red dot)
    ├─▶ AudioRecorder.start()           sounddevice InputStream opens
    ├─▶ overlay.show_recording()        pulsing dot + sound bars
    └─▶ play_start_sound()              winsound beep

Hotkey UP
    │
    ├─▶ overlay.show_processing()       spinner animation
    ├─▶ icon → "processing" (amber dot)
    ├─▶ AudioRecorder.stop() → bytes    PCM 16-bit mono
    ├─▶ play_stop_sound()
    └─▶ Thread(target=_process_audio)
            │
            ├─ [yandex] YandexIAMAuth.get_token()
            │           recognize(audio_bytes, iam_token, lang, rate)
            │           └─ REST POST (chunked if >29s)
            │
            └─ [openai] recognize_openai(audio_bytes, api_key, lang, rate)
                        └─ REST POST to OpenAI transcription endpoint

            │
            ├─▶ history.add(text)
            ├─▶ rebuild_menu()
            ├─▶ insert_text(text)       pyperclip.copy + Ctrl+V
            ├─▶ overlay.hide()
            └─▶ icon → "ready" (green dot)
```

## Threading Model

| Thread | Type | Role | Notes |
|---|---|---|---|
| Main | foreground | `keyboard.hook_key` + `stop_event.wait()` | Must be main thread on Windows |
| Tray | daemon | `pystray.Icon.run()` | Message pump for tray icon |
| Overlay | daemon | `tkinter.mainloop()` via `poll()` | Own event loop, polled every 50 ms |
| Worker | daemon | STT API call + text insertion | Spawned per recognition request |

The overlay uses a polling approach (`root.after(50, _poll)`) rather than direct thread communication, making it safe to call `show_recording()` / `hide()` from any thread.

## Application State Machine

```
        ┌──────────┐
        │  ready   │◀─────────────────────────────┐
        └────┬─────┘                               │
             │ hotkey DOWN                         │
             ▼                                     │
        ┌──────────┐                               │
        │recording │                               │
        └────┬─────┘                               │
             │ hotkey UP                           │
             ▼                                     │
        ┌──────────┐  STT result / error           │
        │processing│────────────────────────────────┘
        └──────────┘
```

Guard conditions prevent re-entry: `is_recording` and `_is_processing` flags block duplicate hotkey events.

## Security

- **Credentials** stored in `.env` (never committed); loaded via python-dotenv at startup.
- **Yandex IAM token** cached in memory; auto-refreshed 5 minutes before 1-hour expiry. Token never written to disk.
- **OpenAI key** passed directly in `Authorization` header per request.
- **Clipboard** is the only IPC mechanism used — no network server, no named pipes.
- The `.exe` build includes no credentials; `.env` and `sa-key.json` are separate files placed alongside the binary.
