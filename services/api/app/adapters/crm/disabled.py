"""``CrmGateway`` no-op used when no HubSpot token is configured.

Wired in the composition root whenever ``HUBSPOT_PRIVATE_APP_TOKEN`` is unset. Any call raises
:class:`CrmError` — with CRM sync disabled the worker never enqueues a SYNC task, so in practice
these methods are unreachable; the raise only guards a misconfigured direct call.
"""

from __future__ import annotations

from app.application.errors import CrmError
from app.domain.lead import Lead
from app.domain.value_objects import CrmContactId

_DISABLED = "CRM sync is disabled: set HUBSPOT_PRIVATE_APP_TOKEN to enable"


class DisabledCrmGateway:
    async def upsert_contact(self, lead: Lead) -> CrmContactId:
        raise CrmError(_DISABLED)

    async def attach_note(self, contact_id: CrmContactId, note: str) -> None:
        raise CrmError(_DISABLED)
