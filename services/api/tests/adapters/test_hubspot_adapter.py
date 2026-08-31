"""Task 4.4 — HubSpotPrivateAppAdapter contract tests (respx-mocked HTTP)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.adapters.crm.hubspot import HubSpotPrivateAppAdapter, split_name
from app.application.errors import CrmError
from app.domain.contact_details import ContactDetails
from app.domain.lead import Lead
from app.domain.value_objects import CrmContactId, Email

BASE = "https://api.hubapi.com"
SEARCH = f"{BASE}/crm/v3/objects/contacts/search"
CONTACTS = f"{BASE}/crm/v3/objects/contacts"
NOTES = f"{BASE}/crm/v3/objects/notes"


def _lead(name: str = "Ada Lovelace", email: str = "ada@example.com") -> Lead:
    return Lead.register(
        source="website-form",
        contact=ContactDetails(name=name, email=Email(email), company="Analytical Engines"),
    )


@pytest.fixture
def adapter() -> HubSpotPrivateAppAdapter:
    client = httpx.AsyncClient(base_url=BASE, headers={"Authorization": "Bearer test-token"})
    return HubSpotPrivateAppAdapter(client)


@pytest.mark.parametrize(
    ("full", "expected"),
    [
        ("Ada Lovelace", ("Ada", "Lovelace")),
        ("Cher", ("Cher", "")),
        ("Ada B Lovelace", ("Ada", "B Lovelace")),
        ("  Grace   Hopper  ", ("Grace", "Hopper")),
    ],
)
def test_split_name(full: str, expected: tuple[str, str]) -> None:
    assert split_name(full) == expected


@respx.mock
async def test_upsert_updates_an_existing_contact(adapter: HubSpotPrivateAppAdapter) -> None:
    respx.post(SEARCH).respond(json={"total": 1, "results": [{"id": "777"}]})
    patch_route = respx.patch(f"{CONTACTS}/777").respond(json={"id": "777"})

    result = await adapter.upsert_contact(_lead())

    assert result == CrmContactId("777")
    assert patch_route.called
    sent = patch_route.calls.last.request
    assert b'"firstname":"Ada"' in sent.content
    assert b'"lastname":"Lovelace"' in sent.content


@respx.mock
async def test_upsert_creates_a_contact_when_search_is_empty(
    adapter: HubSpotPrivateAppAdapter,
) -> None:
    respx.post(SEARCH).respond(json={"total": 0, "results": []})
    create_route = respx.post(CONTACTS).respond(json={"id": "999"})

    result = await adapter.upsert_contact(_lead())

    assert result == CrmContactId("999")
    body = create_route.calls.last.request.content
    assert b'"email":"ada@example.com"' in body
    assert b'"firstname":"Ada"' in body


@respx.mock
async def test_upsert_raises_crm_error_on_rate_limit(
    adapter: HubSpotPrivateAppAdapter,
) -> None:
    respx.post(SEARCH).respond(status_code=429, json={"message": "rate limited"})
    with pytest.raises(CrmError):
        await adapter.upsert_contact(_lead())


@respx.mock
async def test_upsert_raises_crm_error_when_create_fails(
    adapter: HubSpotPrivateAppAdapter,
) -> None:
    respx.post(SEARCH).respond(json={"total": 0, "results": []})
    respx.post(CONTACTS).respond(status_code=500, json={"message": "boom"})
    with pytest.raises(CrmError):
        await adapter.upsert_contact(_lead())


@respx.mock
async def test_attach_note_posts_body_and_association(
    adapter: HubSpotPrivateAppAdapter,
) -> None:
    route = respx.post(NOTES).respond(json={"id": "note-1"})

    await adapter.attach_note(CrmContactId("777"), "AI score: 82/100")

    body = route.calls.last.request.content
    assert b"AI score: 82/100" in body
    assert b'"777"' in body  # association to the contact


@respx.mock
async def test_attach_note_raises_crm_error_on_server_failure(
    adapter: HubSpotPrivateAppAdapter,
) -> None:
    respx.post(NOTES).respond(status_code=502, json={"message": "bad gateway"})
    with pytest.raises(CrmError):
        await adapter.attach_note(CrmContactId("777"), "note")
