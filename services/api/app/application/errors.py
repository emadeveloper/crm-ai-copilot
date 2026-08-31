"""Failure vocabulary for the application layer and the adapters that feed its ports."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for application-level failures."""


class LLMTemporaryError(ApplicationError):
    """A transient LLM failure (rate limit, timeout, 5xx) — safe to retry."""


class LLMResponseInvalid(ApplicationError):
    """The LLM returned something that cannot be turned into a valid analysis — do not retry."""


class CrmError(ApplicationError):
    """The CRM gateway failed (auth, rate limit, network)."""


class LeadNotReadyForSync(ApplicationError):
    """Sync was requested for a lead with no score or reply draft yet."""

    def __init__(self, lead_id: str) -> None:
        self.lead_id = lead_id
        super().__init__(f"lead {lead_id} has no score/reply draft to sync")
