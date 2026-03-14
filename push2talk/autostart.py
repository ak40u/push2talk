"""Windows autostart management via shell:startup folder.

Creates/removes a .bat launcher in the Windows Startup folder
so Push2Talk runs automatically on login. Only works when
running as a frozen .exe (PyInstaller).
"""

from __future__ import annotations

import logging
import os
import sys

log = logging.getLogger("push2talk")

STARTUP_BAT_NAME = "Push2Talk.bat"


def _get_startup_folder() -> str:
    """Return path to Windows Startup folder."""
    return os.path.join(
        os.environ["APPDATA"],
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
    )


def is_frozen() -> bool:
    """Check if running as PyInstaller .exe."""
    return getattr(sys, "frozen", False)


def is_autostart_enabled() -> bool:
    """Check if autostart .bat exists in Startup folder."""
    bat_path = os.path.join(_get_startup_folder(), STARTUP_BAT_NAME)
    return os.path.exists(bat_path)


def enable_autostart() -> bool:
    """Create .bat in Startup folder. Returns True on success."""
    if not is_frozen():
        log.warning("Autostart only available when running as .exe")
        return False
    exe_path = sys.executable
    bat_path = os.path.join(_get_startup_folder(), STARTUP_BAT_NAME)
    try:
        with open(bat_path, "w") as f:
            f.write(f'@start "" "{exe_path}"\n')
        log.info("Autostart enabled")
        return True
    except OSError as e:
        log.error("Failed to enable autostart: %s", e)
        return False


def disable_autostart() -> bool:
    """Remove .bat from Startup folder. Returns True on success."""
    bat_path = os.path.join(_get_startup_folder(), STARTUP_BAT_NAME)
    try:
        if os.path.exists(bat_path):
            os.remove(bat_path)
        log.info("Autostart disabled")
        return True
    except OSError as e:
        log.error("Failed to disable autostart: %s", e)
        return False
