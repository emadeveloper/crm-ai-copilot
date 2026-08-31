import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { server } from "../../test/msw";
import { renderWithQuery } from "../../test/render";
import { API_URL } from "../../test/fixtures";
import { AddLeadForm } from "./AddLeadForm";

async function fillAndSubmit(email = "ada@example.com") {
  await userEvent.type(screen.getByLabelText(/name/i), "Ada Lovelace");
  await userEvent.type(screen.getByLabelText(/email/i), email);
  await userEvent.type(screen.getByLabelText(/company/i), "Analytical Engines");
  await userEvent.click(screen.getByRole("button", { name: /add lead/i }));
}

describe("AddLeadForm", () => {
  it("submits the lead and reports the new id on success", async () => {
    let received: unknown;
    server.use(
      http.post(`${API_URL}/leads`, async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ id: "new-lead-1", deduplicated: false }, { status: 201 });
      }),
    );
    const onCreated = vi.fn();
    renderWithQuery(<AddLeadForm onCreated={onCreated} />);

    await fillAndSubmit();

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith("new-lead-1"));
    expect(received).toMatchObject({
      source: expect.any(String),
      contact: { name: "Ada Lovelace", email: "ada@example.com" },
    });
    expect(screen.getByLabelText(/name/i)).toHaveValue("");
  });

  it("shows a validation error when the API rejects the payload with 422", async () => {
    server.use(
      http.post(`${API_URL}/leads`, () =>
        HttpResponse.json({ detail: "not a valid email address" }, { status: 422 }),
      ),
    );
    const onCreated = vi.fn();
    renderWithQuery(<AddLeadForm onCreated={onCreated} />);

    // Passes the browser's <input type="email"> check but fails the server's stricter rule.
    await fillAndSubmit("ada@localhost");

    expect(await screen.findByRole("alert")).toHaveTextContent(/check the form/i);
    expect(onCreated).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/name/i)).toHaveValue("Ada Lovelace");
  });
});
