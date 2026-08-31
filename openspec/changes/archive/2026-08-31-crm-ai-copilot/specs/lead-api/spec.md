# lead-api Specification

## Purpose

The HTTP surface for submitting inbound leads and reading them back, over REST and a thin GraphQL
query slice. Both protocols are served by the same application services — no duplicated logic.

## Requirements

### Requirement: Lead submission over REST

The system MUST expose `POST /leads` accepting a JSON payload with `source` (string) and
`contact` (`name`, `email` required; `company`, `role`, `message` optional). It MUST validate the
payload, persist a new lead with status `received`, and respond `201` with the lead id. It MUST
respond `422` for a missing or malformed `email` and for a missing `name`. It SHOULD treat a repeat
`(email, source)` within 24h as the same lead and return the existing id with `200`.

#### Scenario: Valid lead accepted

- GIVEN a payload with `source` and a `contact` containing a valid `name` and `email`
- WHEN the client sends `POST /leads`
- THEN the response is `201` with a `lead.id`
- AND the stored lead has status `received`

#### Scenario: Invalid email rejected

- GIVEN a payload whose `contact.email` is `"not-an-email"`
- WHEN the client sends `POST /leads`
- THEN the response is `422` and no lead is persisted

#### Scenario: Duplicate submission deduplicated

- GIVEN a lead with `email` E and `source` S was created 1 hour ago
- WHEN a new `POST /leads` arrives with the same E and S
- THEN the response is `200` with the original `lead.id`
- AND no second lead is persisted

### Requirement: Lead retrieval over REST

The system MUST expose `GET /leads` returning a newest-first, paginated list (`limit`, `offset`)
of leads with their status and score band, and `GET /leads/{id}` returning the lead aggregate:
contact data, enrichment, score, reply draft, and sync state when each is present.

#### Scenario: List returns newest first

- GIVEN three leads created at t1 < t2 < t3
- WHEN the client sends `GET /leads?limit=10&offset=0`
- THEN the response lists them in order t3, t2, t1

#### Scenario: Detail includes derived data when present

- GIVEN a lead that has been enriched, scored, and synced
- WHEN the client sends `GET /leads/{id}`
- THEN the response includes enrichment fields, numeric score with band and rationale, the reply draft, and sync state

#### Scenario: Unknown id

- GIVEN no lead with id X
- WHEN the client sends `GET /leads/X`
- THEN the response is `404`

### Requirement: Lead retrieval over GraphQL

The system MUST expose a GraphQL endpoint with `lead(id: ID!)` and `leads(limit: Int, offset: Int)`
queries returning the same aggregate shape as the REST detail endpoint, resolved through the same
application services.

#### Scenario: GraphQL lead query matches REST detail

- GIVEN a lead with id X that has enrichment and score
- WHEN a client runs `query { lead(id: "X") { status score { value band } enrichment { industry } } }`
- THEN the returned values equal those from `GET /leads/X`

#### Scenario: GraphQL list pagination

- GIVEN 5 leads exist
- WHEN a client runs `query { leads(limit: 2, offset: 0) { id } }`
- THEN exactly 2 lead ids are returned, newest first
