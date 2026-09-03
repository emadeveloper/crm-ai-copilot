import { act, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "../../test/msw";
import { renderWithQuery } from "../../test/render";
import { API_URL, makeLead, makeQualifiedLead } from "../../test/fixtures";
import { LeadDetail } from "./LeadDetail";
import { leadKey } from "./hooks";

describe("LeadDetail", () => {
  it("shows enrichment, score, reply draft, sync state and a HubSpot link", async () => {
    server.use(
      http.get(`${API_URL}/leads/lead-1`, () =>
        HttpResponse.json(makeQualifiedLead({ id: "lead-1" })),
      ),
    );

    renderWithQuery(<LeadDetail leadId="lead-1" />);

    expect(await screen.findByText("fintech")).toBeInTheDocument();
    expect(screen.getByText(/82/)).toBeInTheDocument();
    expect(screen.getByText(/hot/i)).toBeInTheDocument();
    expect(screen.getByText(/Enterprise buyer with budget/)).toBeInTheDocument();
    expect(screen.getByText("Thanks for reaching out")).toBeInTheDocument();
    expect(screen.getByText(/Hi Ada, happy to help/)).toBeInTheDocument();

    const link = screen.getByRole("link", { name: /hubspot/i });
    expect(link).toHaveAttribute("href", expect.stringContaining("50123"));
  });

  it("shows a pending state for a lead that has not been enriched", async () => {
    server.use(
      http.get(`${API_URL}/leads/lead-2`, () =>
        HttpResponse.json(makeLead({ id: "lead-2", status: "received" })),
      ),
    );

    renderWithQuery(<LeadDetail leadId="lead-2" />);

    expect(await screen.findByText(/pending enrichment/i)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /hubspot/i })).not.toBeInTheDocument();
  });

  it("reflects progress without a reload", async () => {
    let calls = 0;
    server.use(
      http.get(`${API_URL}/leads/lead-3`, () => {
        calls += 1;
        if (calls === 1) {
          return HttpResponse.json(
            makeLead({ id: "lead-3", status: "enriching" }),
          );
        }
        return HttpResponse.json(
          makeQualifiedLead({ id: "lead-3", status: "qualified" }),
        );
      }),
    );

    const { client } = renderWithQuery(<LeadDetail leadId="lead-3" />);

    // In-progress snapshot: enriching, not yet scored.
    expect(await screen.findByText(/pending enrichment/i)).toBeInTheDocument();
    expect(screen.getByText("enriching")).toBeInTheDocument();
    expect(screen.queryByText(/82/)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Enterprise buyer with budget/),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Thanks for reaching out")).not.toBeInTheDocument();
    const panelBefore = screen.getByRole("article");

    // Pipeline advances; the open panel refetches in place (no remount).
    await act(async () => {
      await client.refetchQueries({ queryKey: leadKey("lead-3") });
    });

    // Same container, now reflecting the terminal qualified state.
    expect(
      await screen.findByText("Thanks for reaching out"),
    ).toBeInTheDocument();
    expect(screen.getByText("qualified")).toBeInTheDocument();
    expect(screen.getByText(/82/)).toBeInTheDocument();
    expect(screen.getByText(/hot/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Enterprise buyer with budget/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Hi Ada, happy to help/)).toBeInTheDocument();
    expect(screen.getByRole("article")).toBe(panelBefore);
    expect(screen.queryByText(/pending enrichment/i)).not.toBeInTheDocument();
  });

  it("shows a not-found message on 404", async () => {
    server.use(
      http.get(`${API_URL}/leads/missing`, () =>
        HttpResponse.json({ detail: "lead not found" }, { status: 404 }),
      ),
    );

    renderWithQuery(<LeadDetail leadId="missing" />);

    expect(await screen.findByText(/not found/i)).toBeInTheDocument();
  });
});
