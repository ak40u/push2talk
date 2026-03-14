"""Push2Talk entry point."""

from push2talk.app import Push2Talk


def main() -> None:
    """Start the Push2Talk application."""
    app = Push2Talk()
    app.run()
