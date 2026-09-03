# web-dashboard Specification

## Purpose

A React installable PWA that shows the lead queue, per-lead detail (enrichment, score, reply draft,
sync state), and a form to add a lead manually. It consumes the API through a generated client.

## Requirements

### Requirement: Lead queue view

The dashboard MUST list leads newest-first, each row showing name, company, status, and score band.
It MUST reflect status changes (e.g. `received → synced`) without a full page reload.

#### Scenario: Queue lists leads with status

- GIVEN three leads exist with different statuses
- WHEN the user opens the dashboard
- THEN all three are listed newest-first with name, company, status, and score band

#### Scenario: Status updates without reload

- GIVEN a lead shown as `enriching`
- WHEN its pipeline reaches `synced`
- THEN the row updates to `synced` without the user reloading the page

### Requirement: Lead detail view

Selecting a lead MUST show its enrichment fields, numeric score with band and rationale, the reply
draft (`subject` and `body`), and its sync state. When the lead has a synced CRM contact, the view
MUST show a link to that contact. While the selected lead is still being processed (its status is
not `synced` and not `failed`), the detail view MUST reflect the lead's status and score changes
without the user reloading the page. Once the lead reaches `synced` or `failed`, the view MAY stop
polling.

#### Scenario: Detail shows derived data

- GIVEN a lead that is enriched, scored, and synced
- WHEN the user selects it
- THEN the view shows enrichment fields, score value + band + rationale, the reply draft, and a link to the HubSpot contact

#### Scenario: Detail for an unprocessed lead

- GIVEN a lead still in `received`
- WHEN the user selects it
- THEN the view shows contact data and a "pending enrichment" state, with no score or draft

#### Scenario: Detail reflects progress without a reload

- GIVEN the user has selected a lead shown as `enriching` with no score
- WHEN its pipeline reaches `qualified` and a score is produced
- THEN the open detail view updates to `qualified` and shows the score, band, rationale and reply draft, without the user reloading or reopening it

### Requirement: Responsive two-column layout

The dashboard MUST present the lead queue and the selected lead's detail **side by side** on wide
viewports, and **stacked in a single column** on narrow viewports. The page body MUST NOT scroll
horizontally at any viewport width. The lead queue MUST remain scrollable independently of the
detail panel.

#### Scenario: Side by side on a wide viewport

- GIVEN the viewport is at least 1024px wide and a lead is selected
- WHEN the dashboard renders
- THEN the queue and the lead detail are both visible without vertical scrolling past one to reach the other

#### Scenario: Single column on a narrow viewport

- GIVEN the viewport is 375px wide
- WHEN the dashboard renders
- THEN the queue and (when open) the detail are stacked vertically in one column
- AND the page body has no horizontal scrollbar

#### Scenario: Wide content stays contained

- GIVEN a lead whose reply-draft body is a long unbroken string
- WHEN its detail is shown
- THEN the text wraps or scrolls within the detail panel and the page body still does not scroll horizontally

### Requirement: Manual lead creation

The dashboard MUST provide a form that submits to `POST /leads`. On success the new lead MUST appear
in the queue as `received`. Validation errors from the API MUST be shown against the form.

#### Scenario: Manual add succeeds

- GIVEN the user fills the add-lead form with a valid name and email
- WHEN they submit
- THEN the lead appears in the queue as `received`

#### Scenario: Manual add rejected

- GIVEN the user submits the form with an invalid email
- WHEN the API responds `422`
- THEN the form shows the validation error and no row is added

### Requirement: Installable and offline-tolerant

The app MUST be installable (valid web app manifest + registered service worker). When offline, it
MUST still render a read-only view of leads already loaded in the current session.

#### Scenario: Offline read

- GIVEN the user has loaded the queue and one lead detail while online
- WHEN the network goes offline and the user revisits that lead
- THEN the previously loaded lead data is still displayed
