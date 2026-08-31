"""``CrmGateway`` backed by HubSpot's v3 CRM API using a Private App token.

The caller supplies a configured :class:`httpx.AsyncClient` (base URL + ``Authorization`` header).
Every non-2xx response is translated to :class:`CrmError` so the use case can isolate the failure.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from app.application.errors import CrmError
from app.domain.lead import Lead
from app.domain.value_objects import CrmContactId

# HubSpot's built-in contact <-> note association type.
_NOTE_TO_CONTACT_TYPE_ID = 202


def split_name(full_name: str) -> tuple[str, str]:
    """Split a display name into (first, last). Last may be empty."""
    parts = full_name.split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


class HubSpotPrivateAppAdapter:
    def __init__(self, http: httpx.AsyncClient, *, clock: Callable[[], float] = time.time) -> None:
        self._http = http
        self._clock = clock

    async def upsert_contact(self, lead: Lead) -> CrmContactId:
        first, last = split_name(lead.contact.name)
        properties = {
            "email": str(lead.contact.email),
            "firstname": first,
            "lastname": last,
        }
        if lead.contact.company:
            properties["company"] = lead.contact.company

        existing_id = await self._find_contact_id(str(lead.contact.email))
        if existing_id is not None:
            await self._request(
                "PATCH",
                f"/crm/v3/objects/contacts/{existing_id}",
                json={"properties": {k: v for k, v in properties.items() if k != "email"}},
            )
            return CrmContactId(existing_id)

        created = await self._request(
            "POST", "/crm/v3/objects/contacts", json={"properties": properties}
        )
        return CrmContactId(str(created["id"]))

    async def attach_note(self, contact_id: CrmContactId, note: str) -> None:
        await self._request(
            "POST",
            "/crm/v3/objects/notes",
            json={
                "properties": {
                    "hs_note_body": note,
                    "hs_timestamp": int(self._clock() * 1000),
                },
                "associations": [
                    {
                        "to": {"id": str(contact_id)},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": _NOTE_TO_CONTACT_TYPE_ID,
                            }
                        ],
                    }
                ],
            },
        )

    async def _find_contact_id(self, email: str) -> str | None:
        payload = await self._request(
            "POST",
            "/crm/v3/objects/contacts/search",
            json={
                "filterGroups": [
                    {"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}
                ],
                "properties": ["email"],
                "limit": 1,
            },
        )
        results = payload.get("results") or []
        return str(results[0]["id"]) if results else None

    async def _request(self, method: str, url: str, *, json: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._http.request(method, url, json=json)
        except httpx.HTTPError as exc:
            raise CrmError(f"HubSpot request failed: {exc}") from exc
        if response.status_code >= 400:
            raise CrmError(
                f"HubSpot {method} {url} -> {response.status_code}: {response.text[:200]}"
            )
        if not response.content:
            return {}
        data: dict[str, Any] = response.json()
        return data
