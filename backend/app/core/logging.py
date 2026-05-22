from __future__ import annotations

import logging
import sys


def configure_logging(debug: bool, log_level: str = "INFO") -> None:
    """Configure application-wide structured-ish console logging."""
    level = logging.DEBUG if debug else getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        stream=sys.stdout,
        force=True,
    )
