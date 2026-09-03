# Delta for web-dashboard

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Lead detail view

Selecting a lead MUST show its enrichment fields, numeric score with band and rationale, the reply
draft (`subject` and `body`), and its sync state. When the lead has a synced CRM contact, the view
MUST show a link to that contact. While the selected lead is still being processed (its status is
not `synced` and not `failed`), the detail view MUST reflect the lead's status and score changes
without the user reloading the page. Once the lead reaches `synced` or `failed`, the view MAY stop
polling.
(Previously: the detail view was a one-time snapshot taken when the lead was selected; only the
queue refreshed on its own.)

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
