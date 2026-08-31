import { type components, makeApiClient } from "@crm-ai/shared";

export type Lead = components["schemas"]["LeadOut"];
export type LeadCreated = components["schemas"]["LeadCreatedOut"];
export type LeadInput = components["schemas"]["LeadIn"];

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export const api = makeApiClient(BASE_URL);

export class LeadValidationError extends Error {}

export async function fetchLeads(): Promise<Lead[]> {
  const { data, error } = await api.GET("/leads", {
    params: { query: { limit: 50, offset: 0 } },
  });
  if (error || !data) throw new Error("Could not load leads");
  return data;
}

export async function fetchLead(id: string): Promise<Lead> {
  const { data, error, response } = await api.GET("/leads/{lead_id}", {
    params: { path: { lead_id: id } },
  });
  if (response.status === 404) throw new Error("Lead not found");
  if (error || !data) throw new Error("Could not load lead");
  return data;
}

export async function createLead(body: LeadInput): Promise<LeadCreated> {
  const { data, error, response } = await api.POST("/leads", { body });
  if (response.status === 422) {
    throw new LeadValidationError("Please check the form and try again");
  }
  if (error || !data) throw new Error("Could not create lead");
  return data;
}
