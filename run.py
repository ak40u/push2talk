"""Entry point for Push2Talk application."""

import logging
import traceback

from push2talk.logging_setup import setup_logging

setup_logging()
log = logging.getLogger("push2talk")


def run():
    from push2talk.main import main
    try:
        main()
    except Exception:
        log.critical("Fatal crash:\n%s", traceback.format_exc())
        raise


if __name__ == "__main__":
    run()
