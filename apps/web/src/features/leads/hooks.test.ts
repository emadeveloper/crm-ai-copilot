import { describe, expect, it } from "vitest";
import { detailRefetchInterval } from "./hooks";

describe("detailRefetchInterval", () => {
  it("stops polling once the lead reaches a terminal state", () => {
    expect(detailRefetchInterval("synced")).toBe(false);
    expect(detailRefetchInterval("failed")).toBe(false);
  });

  it("keeps polling while the lead is still being processed", () => {
    expect(detailRefetchInterval("received")).toBe(3000);
    expect(detailRefetchInterval("enriching")).toBe(3000);
    expect(detailRefetchInterval("qualified")).toBe(3000);
    expect(detailRefetchInterval("syncing")).toBe(3000);
  });

  it("polls when the status is not yet known", () => {
    expect(detailRefetchInterval(undefined)).toBe(3000);
  });
});
