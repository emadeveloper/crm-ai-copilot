import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "./StatusBadge";

const STATUSES = ["received", "enriching", "qualified", "syncing", "synced", "failed"] as const;

describe("StatusBadge", () => {
  it.each(STATUSES)("renders the %s status text verbatim", (status) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(status)).toBeInTheDocument();
  });

  it("exposes the status via a data attribute for styling hooks", () => {
    render(<StatusBadge status="qualified" />);
    expect(screen.getByText("qualified").closest("[data-status]")).toHaveAttribute(
      "data-status",
      "qualified",
    );
  });

  it("does not uppercase the DOM text (transform is visual only)", () => {
    render(<StatusBadge status="enriching" />);
    expect(screen.getByText("enriching").textContent).toBe("enriching");
  });
});
