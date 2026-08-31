"""Minimal logging setup. Line-oriented; swap for JSON logs when shipping to a log aggregator."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
