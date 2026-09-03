import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreMeter } from "./ScoreMeter";

describe("ScoreMeter", () => {
  it("renders the value and band as text", () => {
    render(<ScoreMeter value={82} band="hot" />);
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("hot")).toBeInTheDocument();
  });

  it("is an accessible meter with the value bounds", () => {
    render(<ScoreMeter value={82} band="hot" />);
    const meter = screen.getByRole("meter");
    expect(meter).toHaveAttribute("aria-valuenow", "82");
    expect(meter).toHaveAttribute("aria-valuemin", "0");
    expect(meter).toHaveAttribute("aria-valuemax", "100");
  });

  it("sizes the fill bar to the value", () => {
    render(<ScoreMeter value={40} band="warm" data-testid="m" />);
    const fill = screen.getByTestId("m-fill");
    expect(fill).toHaveStyle({ width: "40%" });
  });

  it("clamps out-of-range values for the bar width", () => {
    render(<ScoreMeter value={140} band="hot" data-testid="m" />);
    expect(screen.getByTestId("m-fill")).toHaveStyle({ width: "100%" });
  });

  it("renders a compact variant with the same numbers", () => {
    render(<ScoreMeter value={61} band="warm" size="sm" />);
    expect(screen.getByText("61")).toBeInTheDocument();
    expect(screen.getByText("warm")).toBeInTheDocument();
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "61");
  });
});
