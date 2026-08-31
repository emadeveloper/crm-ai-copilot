# lead-pipeline Specification

## Purpose

Drive each lead through enrichment and CRM sync asynchronously via the `TaskQueue` port and a worker,
with an explicit, persisted status lifecycle.

## Requirements

### Requirement: Status lifecycle

A lead MUST progress through `received → enriching → qualified → syncing → synced`. From any active
step it MAY move to `failed`. The only backward transitions allowed are explicit retries:
`failed → enriching` or `failed → syncing`. Every transition MUST be persisted.

#### Scenario: Happy path progression

- GIVEN a newly submitted lead in `received`
- WHEN the pipeline processes it end to end
- THEN its status moves `received → enriching → qualified → syncing → synced`
- AND each transition is persisted in order

#### Scenario: Illegal transition rejected

- GIVEN a lead in status `synced`
- WHEN something attempts to move it directly to `enriching` without a retry
- THEN the transition is rejected and the status stays `synced`

### Requirement: Non-blocking submission

Submitting a lead MUST enqueue a task and return immediately. The `POST /leads` response MUST NOT
wait on any LLM or CRM call. A worker MUST consume the queue and run enrichment, then sync.

#### Scenario: Response does not wait on the pipeline

- GIVEN the LLM provider takes several seconds to respond
- WHEN a client sends `POST /leads`
- THEN the response returns before enrichment completes
- AND a task for that lead is present in the queue

### Requirement: Retry, throttle and durability

The worker MUST throttle LLM calls to stay within the provider's configured rate budget. Failed
tasks MUST be retried with exponential backoff up to a bounded attempt count, then parked as
`failed`. Enqueued and in-progress tasks MUST survive a process restart — the queue MUST NOT be
in-memory only.

#### Scenario: Throttling under burst

- GIVEN 30 leads are submitted within one minute and the provider budget is 15 requests/minute
- WHEN the worker processes the queue
- THEN it spreads LLM calls so the per-minute budget is not exceeded
- AND all 30 leads are eventually processed

#### Scenario: Tasks survive restart

- GIVEN 5 tasks are queued and 1 is in progress
- WHEN the worker process restarts
- THEN the 5 queued tasks and the interrupted task are still processed after restart

#### Scenario: Bounded retries then park

- GIVEN a task whose enrichment fails on every attempt
- WHEN the bounded retry count is exhausted
- THEN the task is parked and the lead status is `failed` with a reason
