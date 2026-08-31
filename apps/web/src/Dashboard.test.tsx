import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { Dashboard } from "./Dashboard";
import { API_URL, makeLead, makeQualifiedLead } from "./test/fixtures";
import { server } from "./test/msw";
import { renderWithQuery } from "./test/render";

describe("Dashboard", () => {
  it("selecting a lead from the queue opens its detail panel", async () => {
    server.use(
      http.get(`${API_URL}/leads`, () =>
        HttpResponse.json([makeLead({ id: "lead-1" })]),
      ),
      http.get(`${API_URL}/leads/lead-1`, () =>
        HttpResponse.json(makeQualifiedLead({ id: "lead-1" })),
      ),
    );

    renderWithQuery(<Dashboard />);

    await userEvent.click(await screen.findByText("Ada Lovelace"));

    await waitFor(() =>
      expect(screen.getByRole("region", { name: /lead detail/i })).toBeInTheDocument(),
    );
    expect(await screen.findByText(/Enterprise buyer with budget/)).toBeInTheDocument();
  });
});
