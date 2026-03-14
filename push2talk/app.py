"""Push2Talk application class — orchestrates tray, hotkey, recording, and recognition."""

from __future__ import annotations

import logging
import os
import sys
import threading

import keyboard
import pystray

from push2talk.autostart import disable_autostart, enable_autostart, is_autostart_enabled
from push2talk.config import (
    HISTORY_SIZE,
    HOTKEY,
    LANGUAGE,
    MICROPHONE_INDEX,
    OPENAI_API_KEY,
    SA_KEY_PATH,
    SAMPLE_RATE,
    STT_ENGINE,
    validate,
)
from push2talk.history import RecognitionHistory
from push2talk.inserter import insert_text
from push2talk.openai_recognizer import recognize_openai
from push2talk.recognizer import recognize as yandex_recognize
from push2talk.recorder import AudioRecorder, list_input_devices
from push2talk.recording_overlay import RecordingOverlay
from push2talk.sounds import play_start_sound, play_stop_sound
from push2talk.tray import COLORS, ENGINES, create_icon_image
from push2talk.yandex_iam_auth import YandexIAMAuth

log = logging.getLogger("push2talk")


class Push2Talk:
    def __init__(self) -> None:
        self.recorder = AudioRecorder(
            sample_rate=SAMPLE_RATE,
            device=MICROPHONE_INDEX,
        )
        self._auth: YandexIAMAuth | None = None  # lazy init — only when Yandex engine is used
        self._active_mic: int | None = MICROPHONE_INDEX
        self._is_processing: bool = False
        self._processing_lock = threading.Lock()
        self.icon: pystray.Icon | None = None
        self._stop_event = threading.Event()
        self.history = RecognitionHistory(maxlen=HISTORY_SIZE)
        self._overlay = RecordingOverlay()
        self._stt_engine: str = STT_ENGINE  # "yandex" or "openai"

    # --- Icon ---

    def _update_icon(self, state: str) -> None:
        if not self.icon:
            return
        tooltips = {
            "ready": f"Push2Talk - Ready [{HOTKEY}]",
            "recording": "Push2Talk - Recording...",
            "processing": "Push2Talk - Recognizing...",
        }
        self.icon.icon = create_icon_image(COLORS.get(state, "#9E9E9E"))
        self.icon.title = tooltips.get(state, "Push2Talk")

    # --- Hotkey (FIXED: single hook_key with event type filtering) ---

    def _on_hotkey_event(self, event: keyboard.KeyboardEvent) -> None:
        """Single callback for both press and release of hotkey."""
        # Filter: only react to the exact key configured (e.g. 'right ctrl', not 'left ctrl')
        if event.name != HOTKEY:
            return
        if event.event_type == "down":
            # Guard against key repeat: skip if already recording or processing
            with self._processing_lock:
                if self.recorder.is_recording or self._is_processing:
                    return
            self._update_icon("recording")
            try:
                self.recorder.start()
            except Exception as e:
                log.error("Mic error: %s", e)
                self._update_icon("ready")
                return
            play_start_sound()
            self._overlay.show_recording()

        elif event.event_type == "up":
            if not self.recorder.is_recording:
                return
            self._overlay.show_processing()
            with self._processing_lock:
                self._is_processing = True
            self._update_icon("processing")
            audio_data = self.recorder.stop()
            engine = self._stt_engine  # snapshot before thread
            play_stop_sound()
            threading.Thread(
                target=self._process_audio, args=(audio_data, engine), daemon=True,
            ).start()

    def _process_audio(self, audio_data: bytes, engine: str) -> None:
        """Recognize audio and insert text at cursor."""
        try:
            if not audio_data:
                log.warning("No audio data captured")
                return
            log.info("Audio: %d bytes (%.1fs) [%s]", len(audio_data),
                     len(audio_data) / SAMPLE_RATE / 2, engine)

            if engine == "openai":
                text = recognize_openai(
                    audio_data, OPENAI_API_KEY, LANGUAGE, SAMPLE_RATE,
                )
            else:
                if self._auth is None:
                    self._auth = YandexIAMAuth(SA_KEY_PATH)
                iam_token = self._auth.get_token()
                text = yandex_recognize(
                    audio_data, iam_token, LANGUAGE, SAMPLE_RATE,
                )
            log.info("Recognized %d chars", len(text))
            if text:
                self.history.add(text)
                self._rebuild_menu()
                insert_text(text)
        except Exception as e:
            log.error("Recognition error: %s", e)
        finally:
            with self._processing_lock:
                self._is_processing = False
            self._overlay.hide()
            self._update_icon("ready")

    # --- Tray menu ---

    def _select_microphone(self, device_index: int | None) -> None:
        """Switch active microphone at runtime."""
        self._active_mic = device_index
        self.recorder.device = device_index
        self._rebuild_menu()
        name = "System Default" if device_index is None else f"Device {device_index}"
        log.info("Microphone switched to: %s", name)

    def _make_mic_handler(self, device_index: int | None):
        """Closure factory for mic selection menu items."""
        def handler(icon: pystray.Icon, item: pystray.MenuItem) -> None:
            self._select_microphone(device_index)
        return handler

    def _make_mic_checker(self, device_index: int):
        """Closure factory for mic checkmark (avoids loop variable capture)."""
        def checker(item: pystray.MenuItem) -> bool:
            return self._active_mic == device_index
        return checker

    def _make_engine_handler(self, engine_key: str):
        def handler(icon: pystray.Icon, item: pystray.MenuItem) -> None:
            # Validate credentials before switching
            if engine_key == "openai" and not OPENAI_API_KEY:
                log.warning("Cannot switch to OpenAI: OPENAI_API_KEY not set")
                return
            if engine_key == "yandex" and not os.path.exists(SA_KEY_PATH):
                log.warning("Cannot switch to Yandex: SA key not found")
                return
            self._stt_engine = engine_key
            self._rebuild_menu()
            log.info("STT engine switched to: %s", ENGINES[engine_key])
        return handler

    def _make_engine_checker(self, engine_key: str):
        def checker(item: pystray.MenuItem) -> bool:
            return self._stt_engine == engine_key
        return checker

    def _quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Clean shutdown."""
        keyboard.unhook_all()
        self._overlay.stop()
        self._stop_event.set()
        icon.stop()

    def _build_menu(self) -> pystray.Menu:
        # History submenu
        history_items = []
        for text in self.history.get_items():
            display = text[:50] + "..." if len(text) > 50 else text
            history_items.append(
                pystray.MenuItem(display, self._make_copy_handler(text))
            )
        if history_items:
            history_entry = pystray.MenuItem(
                "History", pystray.Menu(*history_items),
            )
        else:
            history_entry = pystray.MenuItem(
                "History (empty)", None, enabled=False,
            )

        # Microphone selector submenu
        devices = list_input_devices()
        mic_items = [
            pystray.MenuItem(
                "System Default",
                self._make_mic_handler(None),
                checked=lambda item: self._active_mic is None,
            ),
        ]
        for d in devices:
            idx = d["index"]
            mic_items.append(
                pystray.MenuItem(
                    f"[{idx}] {d['name']}",
                    self._make_mic_handler(idx),
                    checked=self._make_mic_checker(idx),
                ),
            )

        # STT engine selector submenu
        engine_items = []
        for key, label in ENGINES.items():
            engine_items.append(
                pystray.MenuItem(
                    label,
                    self._make_engine_handler(key),
                    checked=self._make_engine_checker(key),
                ),
            )

        return pystray.Menu(
            pystray.MenuItem(f"Push2Talk [{HOTKEY}]", None, enabled=False),
            pystray.Menu.SEPARATOR,
            history_entry,
            pystray.MenuItem("STT Engine", pystray.Menu(*engine_items)),
            pystray.MenuItem("Microphone", pystray.Menu(*mic_items)),
            pystray.MenuItem(
                "Autostart",
                self._toggle_autostart,
                checked=lambda item: is_autostart_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    def _rebuild_menu(self) -> None:
        """Rebuild tray menu with updated history."""
        if self.icon:
            self.icon.menu = self._build_menu()

    @staticmethod
    def _toggle_autostart(icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Toggle Windows autostart on/off."""
        if is_autostart_enabled():
            disable_autostart()
        else:
            enable_autostart()

    @staticmethod
    def _make_copy_handler(text: str):
        """Closure factory to avoid loop variable capture bug."""
        def handler(icon: pystray.Icon, item: pystray.MenuItem) -> None:
            import pyperclip
            pyperclip.copy(text)
        return handler

    # --- Main entry ---

    def run(self) -> None:
        """Start the application."""
        errors = validate()
        if errors:
            for e in errors:
                log.error("Config error: %s", e)
            log.error("Create .env file from .env.example")
            sys.exit(1)

        # 1. Create tray icon
        self.icon = pystray.Icon(
            "push2talk",
            create_icon_image(COLORS["ready"]),
            f"Push2Talk - Ready [{HOTKEY}]",
            self._build_menu(),
        )

        # 2. Run tray in DAEMON thread (frees main thread for keyboard)
        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        # 3. Hook hotkey on MAIN thread
        keyboard.hook_key(HOTKEY, self._on_hotkey_event, suppress=False)

        log.info("Started. Hold [%s] to record.", HOTKEY)

        # 4. Block main thread until quit
        self._stop_event.wait()
