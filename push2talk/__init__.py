"""Push2Talk — push-to-talk speech recognition for Windows."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("push2talk")
except PackageNotFoundError:
    __version__ = "1.0.0"  # fallback for uninstalled dev mode
