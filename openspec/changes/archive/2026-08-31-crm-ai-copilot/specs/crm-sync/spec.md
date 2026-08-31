# crm-sync Specification

## Purpose

Push a qualified lead — its score and reply draft — into HubSpot through the `CrmGateway` port, and
record the outcome as `SyncState` on the lead.

## Requirements

### Requirement: Contact upsert with note

For a lead that has a `Score` and a `ReplyDraft`, the system MUST upsert a HubSpot contact keyed by
`email` (create when absent; update `firstname`, `lastname`, `company` when present) and MUST attach
a note to that contact containing the score `value`, `band`, `rationale`, and the reply draft
`subject` and `body`. On success it MUST record `SyncState` with the HubSpot `contact_id`, a
`synced_at` timestamp, and status `synced`.

#### Scenario: New contact created and annotated

- GIVEN a scored lead whose `email` matches no HubSpot contact
- WHEN the sync operation runs
- THEN a HubSpot contact is created with the lead's name and company
- AND a note with the score and reply draft is attached to it
- AND `SyncState.status` is `synced` with a stored `contact_id`

#### Scenario: Existing contact updated, not duplicated

- GIVEN a scored lead whose `email` matches an existing HubSpot contact
- WHEN the sync operation runs
- THEN the existing contact is updated and a note is attached
- AND no second contact is created

### Requirement: Idempotent re-sync

Re-syncing a lead that already has a `SyncState.contact_id` MUST reuse that id and MUST NOT create a
duplicate contact. The system SHOULD add a fresh note rather than duplicating an identical one.

#### Scenario: Re-sync reuses stored contact id

- GIVEN a lead with `SyncState.contact_id = C` and status `synced`
- WHEN the sync operation runs again for that lead
- THEN the operation targets contact `C`
- AND no new contact is created

### Requirement: Sync failure isolation

On a `CrmGateway` error (auth, rate limit, network), the system MUST set `SyncState.status` to
`failed` with a reason, leave the lead eligible for retry, and MUST preserve the existing
`Enrichment`, `Score`, and `ReplyDraft`.

#### Scenario: Gateway error does not lose derived data

- GIVEN a scored lead and a `CrmGateway` that returns an authentication error
- WHEN the sync operation runs
- THEN `SyncState.status` is `failed` with a recorded reason
- AND the lead's enrichment, score, and reply draft remain intact
- AND the lead can be retried later
