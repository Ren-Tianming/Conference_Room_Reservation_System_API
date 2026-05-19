from __future__ import annotations

import logging
import sys


def configure_logging(debug: bool) -> None:
    """Configure application-wide structured-ish console logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        stream=sys.stdout,
        force=True,
    )
