# Migration path: HubSpot Private App token → OAuth2 (multi-tenant)

**Status:** design note (Phase 3 of the roadmap). The MVP integrates a single demo HubSpot
account with a Private App token, which is the right call for a portfolio demo and still a real
third-party API integration.

## When you need OAuth

Only for **multi-tenant** — letting other people connect *their* HubSpot from an "Install"
button. A Private App token is per-account and hand-issued; it cannot represent many customers.

## The port

`app/domain/ports.py`:

```python
class CrmGateway(Protocol):
    async def upsert_contact(self, lead: Lead) -> CrmContactId: ...
    async def attach_note(self, contact_id: CrmContactId, note: str) -> None: ...
```

`HubSpotPrivateAppAdapter` sets a static `Authorization: Bearer <token>` header on its
`httpx.AsyncClient`. That is the only thing OAuth changes.

## Shape of the change

1. **Install flow** — add routes:
   - `GET /crm/hubspot/connect` → redirect to HubSpot's authorization URL (client id, scopes
     `crm.objects.contacts.read/write`, `crm.objects.notes.write`, redirect URI).
   - `GET /crm/hubspot/callback?code=...` → exchange the code for
     `{ access_token, refresh_token, expires_in }`.

2. **Token store** — a `hubspot_tokens` table keyed by tenant id, holding the refresh token
   (encrypted) and the access-token expiry.

3. **`HubSpotOAuthAdapter`** — same request methods as today, but:
   - the client's `Authorization` header is set per call from a `TokenProvider(tenant_id)`;
   - `TokenProvider` refreshes the access token when it is within ~5 min of expiry
     (`POST /oauth/v1/token` with `grant_type=refresh_token`) and writes the new value back.

4. **`Lead` gains a `tenant_id`** (or the pipeline task carries it) so the worker knows which
   token to use.

## What stays the same

`SyncLeadToCrm`, the contact search/upsert/notes logic, the `CrmError` translation, and the
idempotent re-sync behaviour are all unchanged — they operate through the port.

## Keep both

Select the adapter by config. Single-tenant deployments (and CI) keep the zero-ceremony Private
App token; SaaS deployments use OAuth.
