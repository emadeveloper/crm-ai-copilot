"""DisabledCrmGateway — used when no HubSpot token is configured; every call raises CrmError."""

from __future__ import annotations

import pytest

from app.adapters.crm.disabled import DisabledCrmGateway
from app.application.errors import CrmError
from app.domain.contact_details import ContactDetails
from app.domain.lead import Lead
from app.domain.value_objects import CrmContactId, Email


def _lead() -> Lead:
    return Lead.register(
        source="website-form",
        contact=ContactDetails(name="Ada Lovelace", email=Email("ada@example.com")),
    )


async def test_upsert_contact_raises_crm_error() -> None:
    with pytest.raises(CrmError, match="disabled"):
        await DisabledCrmGateway().upsert_contact(_lead())


async def test_attach_note_raises_crm_error() -> None:
    with pytest.raises(CrmError, match="disabled"):
        await DisabledCrmGateway().attach_note(CrmContactId("777"), "note")
