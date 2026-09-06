/**
 * Tests for operational dashboard API requests.
 */

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import { getDashboardSummary } from "./dashboard.js";


const accessToken = "dashboard-access-token";

const dashboardSummary = {
  total_incidents: 4,
  active_incidents: 2,
  critical_incidents: 1,
  resolved_incidents: 1,
  affected_services: 2,
  status_counts: {
    open: 1,
    investigating: 1,
    resolved: 1,
    closed: 1,
  },
  severity_counts: {
    low: 1,
    medium: 1,
    high: 1,
    critical: 1,
  },
};


/**
 * Create a JSON response returned by the mocked Fetch API.
 */
function jsonResponse(payload) {
  return new Response(
    JSON.stringify(payload),
    {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    },
  );
}


describe("Dashboard API", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads the authenticated operational summary", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      jsonResponse(dashboardSummary),
    );

    const summary = await getDashboardSummary(accessToken);

    expect(summary).toEqual(dashboardSummary);
    expect(globalThis.fetch.mock.calls[0][0]).toBe(
      "http://127.0.0.1:8000/api/dashboard/summary",
    );

    const requestOptions = globalThis.fetch.mock.calls[0][1];

    expect(
      requestOptions.headers.get("Authorization"),
    ).toBe(`Bearer ${accessToken}`);
  });
});
