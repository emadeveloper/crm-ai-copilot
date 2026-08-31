import type { Lead } from "../api/leads";

export function makeLead(overrides: Partial<Lead> = {}): Lead {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    source: "website-form",
    status: "received",
    failure_reason: null,
    created_at: "2026-08-30T12:00:00Z",
    updated_at: "2026-08-30T12:00:00Z",
    contact: {
      name: "Ada Lovelace",
      email: "ada@example.com",
      company: "Analytical Engines",
      role: "CTO",
      message: "pricing?",
    },
    enrichment: null,
    score: null,
    reply_draft: null,
    sync_state: null,
    ...overrides,
  };
}

export function makeQualifiedLead(overrides: Partial<Lead> = {}): Lead {
  return makeLead({
    status: "synced",
    enrichment: {
      industry: "fintech",
      company_size_band: "51-200",
      seniority: "c-level",
      intent_signals: ["asked about pricing"],
    },
    score: { value: 82, band: "hot", rationale: "Enterprise buyer with budget" },
    reply_draft: { subject: "Thanks for reaching out", body: "Hi Ada, happy to help..." },
    sync_state: {
      status: "synced",
      crm_contact_id: "50123",
      failure_reason: null,
      synced_at: "2026-08-30T12:05:00Z",
    },
    ...overrides,
  });
}

export const API_URL = "http://localhost:8000";
