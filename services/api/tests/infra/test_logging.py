"""Task 7.x — configure_logging sets the root level."""

from __future__ import annotations

import logging

from app.infra.logging import configure_logging


def test_configure_logging_applies_the_requested_level() -> None:
    try:
        configure_logging("DEBUG")
        assert logging.getLogger().level == logging.DEBUG
    finally:
        configure_logging("WARNING")
