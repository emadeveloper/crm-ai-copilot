import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { server } from "../../test/msw";
import { renderWithQuery } from "../../test/render";
import { API_URL, makeLead, makeQualifiedLead } from "../../test/fixtures";
import { leadsKey } from "./hooks";
import { QueueView } from "./QueueView";

describe("QueueView", () => {
  it("lists leads with name, company, status and score band", async () => {
    server.use(
      http.get(`${API_URL}/leads`, () =>
        HttpResponse.json([
          makeQualifiedLead({ id: "a", contact: { ...makeLead().contact, name: "Ada Lovelace" } }),
          makeLead({
            id: "b",
            status: "enriching",
            contact: { ...makeLead().contact, name: "Alan Turing", company: "Bletchley Ltd" },
          }),
        ]),
      ),
    );

    renderWithQuery(<QueueView onSelect={vi.fn()} />);

    expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();
    const alanRow = screen.getByText("Alan Turing").closest("tr")!;
    expect(alanRow).toHaveTextContent("Bletchley Ltd");
    expect(alanRow).toHaveTextContent("enriching");

    const adaRow = screen.getByText("Ada Lovelace").closest("tr")!;
    expect(adaRow).toHaveTextContent("hot");
    expect(adaRow).toHaveTextContent("synced");
  });

  it("shows an empty state when there are no leads", async () => {
    server.use(http.get(`${API_URL}/leads`, () => HttpResponse.json([])));
    renderWithQuery(<QueueView onSelect={vi.fn()} />);
    expect(await screen.findByText(/no leads yet/i)).toBeInTheDocument();
  });

  it("calls onSelect with the lead id when a row is clicked", async () => {
    server.use(
      http.get(`${API_URL}/leads`, () => HttpResponse.json([makeLead({ id: "lead-42" })])),
    );
    const onSelect = vi.fn();
    renderWithQuery(<QueueView onSelect={onSelect} />);

    await userEvent.click(await screen.findByText("Ada Lovelace"));
    await waitFor(() => expect(onSelect).toHaveBeenCalledWith("lead-42"));
  });

  it("reflects a status change on refetch without a full reload (spec: web-dashboard)", async () => {
    server.use(
      http.get(`${API_URL}/leads`, () =>
        HttpResponse.json([makeLead({ id: "x", status: "enriching" })]),
      ),
    );
    const { client } = renderWithQuery(<QueueView onSelect={vi.fn()} />);
    const row = (await screen.findByText("Ada Lovelace")).closest("tr")!;
    expect(row).toHaveTextContent("enriching");

    server.use(
      http.get(`${API_URL}/leads`, () =>
        HttpResponse.json([makeQualifiedLead({ id: "x" })]),
      ),
    );
    await client.refetchQueries({ queryKey: leadsKey });

    await waitFor(() => expect(row).toHaveTextContent("synced"));
  });

  it("keeps showing already-loaded leads when the network is offline (spec: web-dashboard)", async () => {
    server.use(
      http.get(`${API_URL}/leads`, () => HttpResponse.json([makeLead({ id: "y" })])),
    );
    const { client } = renderWithQuery(<QueueView onSelect={vi.fn()} />);
    expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();

    server.use(http.get(`${API_URL}/leads`, () => HttpResponse.error()));
    await client.refetchQueries({ queryKey: leadsKey }).catch(() => undefined);

    // Cached data survives the failed refetch — the queue stays readable offline.
    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
  });
});
