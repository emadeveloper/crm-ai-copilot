# ai-enrichment Specification

## Purpose

Given a lead, produce an `Enrichment`, a `Score`, and a `ReplyDraft` by calling an LLM through the
`LLMProvider` port. The domain and application layers depend only on the port, never on a vendor SDK.

## Requirements

### Requirement: Enrichment, score and draft generation

For a lead in status `received` or `enriching`, the system MUST call the `LLMProvider` to produce,
in one logical operation:
- `Enrichment`: inferred `industry`, `company_size_band`, `seniority`, and a list of `intent_signals`;
- `Score`: an integer `value` in `0..100`, a `band` of `hot | warm | cold`, and a short `rationale`;
- `ReplyDraft`: a `subject` and `body` in a professional tone that references the lead's `message`.

It MUST persist all three atomically, linked to the lead, and MUST operate only on the data present
on the lead — it MUST NOT fabricate contact identifiers (phone, address, alternate emails).

#### Scenario: Successful enrichment

- GIVEN a lead in status `received` with a `message`
- WHEN the enrichment operation runs
- THEN an `Enrichment`, a `Score` (value 0..100, band, rationale), and a `ReplyDraft` are persisted and linked to the lead
- AND the `ReplyDraft.body` refers to the content of the lead's `message`

#### Scenario: Score value out of range is rejected

- GIVEN the provider returns a score `value` of `140`
- WHEN the operation processes the response
- THEN the result is rejected as invalid and nothing is persisted
- AND the lead is not left in a partially enriched state

### Requirement: Provider abstraction

Enrichment MUST depend only on the `LLMProvider` port. Replacing the adapter (e.g. Gemini AI Studio
↔ Vertex AI) MUST NOT require changes to domain or application code, only to configuration and the
adapter module.

#### Scenario: Adapter swap leaves core untouched

- GIVEN the app is configured with `GeminiAIStudioAdapter`
- WHEN it is reconfigured to a different `LLMProvider` implementation
- THEN no file under the domain or application layer changes
- AND enrichment produces the same aggregate shape

### Requirement: Rate-limit and transient-failure handling

On a provider rate-limit or transient error, the system MUST retry with exponential backoff up to a
bounded number of attempts. If all attempts fail, it MUST set the lead status to `failed` with an
error reason and MUST NOT persist a partial result.

#### Scenario: Retry then succeed

- GIVEN the provider returns a rate-limit error on the first call and a valid result on the second
- WHEN the enrichment operation runs
- THEN the operation retries after a backoff delay and persists the successful result
- AND the lead status is not `failed`

#### Scenario: Exhausted retries

- GIVEN the provider returns errors for every attempt
- WHEN the bounded retry count is reached
- THEN the lead status is `failed` with a recorded reason
- AND no `Enrichment`, `Score`, or `ReplyDraft` is persisted for that lead
