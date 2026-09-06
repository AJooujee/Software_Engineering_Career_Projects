/**
 * Tests for administrator audit-history API requests.
 */

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import { listAuditEvents } from "./audit-events.js";


const accessToken = "administrator-access-token";

const auditEvent = {
  id: "bc726221-b86d-46a4-a8f1-20bc56f032af",
  actor_user_id: "5ed29c73-20d1-4305-bf0c-9fa69936b8b4",
  actor_email: "admin@example.com",
  actor_role: "admin",
  action: "incident.created",
  resource_type: "incident",
  resource_id: "fd4f2558-3210-4bc5-8738-c75194106a67",
  resource_label: "Payment API latency",
  changes: {
    status: {
      from: null,
      to: "open",
    },
  },
  created_at: "2026-09-05T20:00:00Z",
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


describe("Audit API", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists paginated audit events with authorization", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      jsonResponse([auditEvent]),
    );

    const events = await listAuditEvents(accessToken, {
      offset: 50,
      limit: 25,
    });

    expect(events).toEqual([auditEvent]);
    expect(globalThis.fetch.mock.calls[0][0]).toBe(
      "http://127.0.0.1:8000/api/audit-events"
      + "?offset=50&limit=25",
    );

    const requestOptions = globalThis.fetch.mock.calls[0][1];

    expect(
      requestOptions.headers.get("Authorization"),
    ).toBe(`Bearer ${accessToken}`);
  });
});
