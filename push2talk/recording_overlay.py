"""Recording overlay - animated indicator centered on screen.

Two modes: 'recording' (red pulsing dot + sound bars)
and 'processing' (amber spinning dots + text).
Transparent, always-on-top, click-through tkinter window.
"""

from __future__ import annotations

import ctypes
import math
import threading
import tkinter as tk

# Windows click-through constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

_TRANSPARENT = "#010101"

# Visual settings
_WIDTH, _HEIGHT = 200, 72
_BG = "#1a1a2e"
_RED = "#F44336"
_AMBER = "#FFC107"
_FPS_MS = 45


class RecordingOverlay:
    """Transparent always-on-top overlay with recording/processing modes."""

    def __init__(self) -> None:
        self._root: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None
        self._mode: str | None = None  # "recording" | "processing" | None
        self._next_mode: str | None = None
        self._hide_flag = threading.Event()
        self._quit_flag = threading.Event()
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._step = 0
        self._anim_id: str | None = None  # tracks after() to prevent stacking
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3)

    # --- Public API (thread-safe) ---

    def show_recording(self) -> None:
        """Show recording animation."""
        with self._lock:
            self._next_mode = "recording"

    def show_processing(self) -> None:
        """Switch to processing/transcribing animation."""
        with self._lock:
            self._next_mode = "processing"

    def hide(self) -> None:
        self._hide_flag.set()

    def stop(self) -> None:
        self._quit_flag.set()

    # --- Internal tkinter loop ---

    def _run(self):
        self._root = tk.Tk()
        root = self._root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", _TRANSPARENT)
        root.config(bg=_TRANSPARENT)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        x = (sw - _WIDTH) // 2
        y = (sh - _HEIGHT) // 2 - 80
        root.geometry(f"{_WIDTH}x{_HEIGHT}+{x}+{y}")

        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT,
        )

        self._canvas = tk.Canvas(
            root, width=_WIDTH, height=_HEIGHT,
            bg=_TRANSPARENT, highlightthickness=0,
        )
        self._canvas.pack()
        root.withdraw()
        self._ready.set()
        self._poll()
        root.mainloop()

    def _poll(self):
        if self._quit_flag.is_set():
            self._root.destroy()
            return

        # Handle mode switch
        with self._lock:
            new_mode = self._next_mode
            self._next_mode = None

        if new_mode:
            # Cancel previous animation chain to prevent stacking
            if self._anim_id:
                self._root.after_cancel(self._anim_id)
                self._anim_id = None
            if self._mode is None:
                self._root.deiconify()
            self._mode = new_mode
            self._step = 0
            self._animate()

        if self._hide_flag.is_set():
            self._hide_flag.clear()
            if self._anim_id:
                self._root.after_cancel(self._anim_id)
                self._anim_id = None
            self._mode = None
            self._root.withdraw()
            self._canvas.delete("all")

        self._root.after(50, self._poll)

    # --- Animation dispatcher ---

    def _animate(self):
        if self._mode is None:
            return
        self._canvas.delete("all")
        self._rounded_rect(6, 4, _WIDTH - 6, _HEIGHT - 4, 18, fill=_BG, outline="")

        if self._mode == "recording":
            self._draw_recording()
        elif self._mode == "processing":
            self._draw_processing()

        self._step += 1
        self._anim_id = self._root.after(_FPS_MS, self._animate)

    # --- Recording animation (red dot + rings + sound bars) ---

    def _draw_recording(self):
        c = self._canvas
        cy = _HEIGHT // 2
        phase = self._step * 0.15
        dot_cx = 38

        # Expanding pulse rings
        for i in range(3):
            rp = (phase - i * 1.2) % 4.0
            if rp > 3.0:
                continue
            ring_r = 10 + rp * 7
            fade = max(0.0, 1.0 - rp / 3.0)
            r = int(244 * fade + 26 * (1 - fade))
            g = int(67 * fade + 26 * (1 - fade))
            b = int(54 * fade + 46 * (1 - fade))
            c.create_oval(
                dot_cx - ring_r, cy - ring_r,
                dot_cx + ring_r, cy + ring_r,
                outline=f"#{r:02x}{g:02x}{b:02x}", width=2,
            )

        # Pulsing red dot
        pulse = 1.0 + 0.25 * math.sin(phase * 2.5)
        dr = int(8 * pulse)
        c.create_oval(
            dot_cx - dr, cy - dr, dot_cx + dr, cy + dr,
            fill=_RED, outline="",
        )

        c.create_text(68, cy, text="REC", fill=_RED,
                       font=("Segoe UI", 13, "bold"), anchor="w")

        # Sound wave bars
        for i in range(5):
            bar_h = 4 + 12 * abs(math.sin(phase * 1.6 + i * 0.9))
            bx = 120 + i * 12
            c.create_rectangle(bx, cy - bar_h, bx + 5, cy + bar_h,
                               fill=_RED, outline="")

    # --- Processing animation (spinning dots + text) ---

    def _draw_processing(self):
        c = self._canvas
        cy = _HEIGHT // 2
        phase = self._step * 0.12
        spinner_cx = 38

        # Spinning dots in a circle
        num_dots = 8
        ring_r = 14
        for i in range(num_dots):
            angle = phase + i * (2 * math.pi / num_dots)
            dx = spinner_cx + ring_r * math.cos(angle)
            dy = cy + ring_r * math.sin(angle)
            # Dots fade: the "leading" dot is brightest
            fade = (num_dots - i) / num_dots
            r_val = int(255 * fade + 26 * (1 - fade))
            g_val = int(193 * fade + 26 * (1 - fade))
            b_val = int(7 * fade + 46 * (1 - fade))
            dot_r = 2 + 2 * fade
            c.create_oval(
                dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r,
                fill=f"#{r_val:02x}{g_val:02x}{b_val:02x}", outline="",
            )

        # Animated ellipsis: 1-3 dots cycle
        dots = "." * (1 + self._step // 8 % 3)
        c.create_text(68, cy, text=f"Transcribing{dots}", fill=_AMBER,
                       font=("Segoe UI", 11, "bold"), anchor="w")
    # --- Helpers ---

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1 + r, y1,  x2 - r, y1,  x2, y1,  x2, y1 + r,
            x2, y2 - r,  x2, y2,  x2 - r, y2,  x1 + r, y2,
            x1, y2,  x1, y2 - r,  x1, y1 + r,  x1, y1,
        ]
        self._canvas.create_polygon(pts, smooth=True, **kw)
