/**
 * Tests for Incident API request construction.
 */

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  createIncident,
  deleteIncident,
  getIncident,
  listIncidents,
  updateIncident,
} from "./incidents.js";


const accessToken = "incident-access-token";
const incidentId = "42c05419-1147-4abf-ad19-a49ee01c5679";

const incidentResponse = {
  id: incidentId,
  title: "Payment API latency",
  description: "Response times exceeded the objective.",
  service_name: "payment-api",
  severity: "high",
  status: "open",
  created_at: "2026-09-05T18:00:00Z",
  updated_at: "2026-09-05T18:00:00Z",
};


/**
 * Create a JSON response returned by the mocked Fetch API.
 */
function jsonResponse(payload, status = 200) {
  return new Response(
    JSON.stringify(payload),
    {
      status,
      headers: {
        "Content-Type": "application/json",
      },
    },
  );
}


/**
 * Return the options supplied to the latest Fetch API call.
 */
function latestRequestOptions() {
  const calls = globalThis.fetch.mock.calls;

  return calls[calls.length - 1][1];
}


describe("Incident API", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists Incidents with pagination and authorization", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      jsonResponse([incidentResponse]),
    );

    const incidents = await listIncidents(accessToken, {
      offset: 20,
      limit: 10,
    });

    expect(incidents).toEqual([incidentResponse]);
    expect(globalThis.fetch.mock.calls[0][0]).toBe(
      "http://127.0.0.1:8000/api/incidents?offset=20&limit=10",
    );
    expect(
      latestRequestOptions().headers.get("Authorization"),
    ).toBe(`Bearer ${accessToken}`);
  });

  it("retrieves one Incident by its encoded identifier", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      jsonResponse(incidentResponse),
    );

    const incident = await getIncident(
      accessToken,
      incidentId,
    );

    expect(incident).toEqual(incidentResponse);
    expect(globalThis.fetch.mock.calls[0][0]).toBe(
      `http://127.0.0.1:8000/api/incidents/${incidentId}`,
    );
  });

  it("creates an Incident using the backend field names", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      jsonResponse(incidentResponse, 201),
    );

    await createIncident(accessToken, {
      title: "  Payment API latency  ",
      description: "  Response times exceeded the objective.  ",
      serviceName: "  payment-api  ",
      severity: "high",
    });

    const requestOptions = latestRequestOptions();

    expect(requestOptions.method).toBe("POST");
    expect(requestOptions.headers.get("Content-Type")).toBe(
      "application/json",
    );
    expect(JSON.parse(requestOptions.body)).toEqual({
      title: "Payment API latency",
      description: "Response times exceeded the objective.",
      service_name: "payment-api",
      severity: "high",
    });
  });

  it("sends only supplied fields during an Incident update", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      jsonResponse({
        ...incidentResponse,
        description: "Service performance has recovered.",
        status: "resolved",
      }),
    );

    await updateIncident(
      accessToken,
      incidentId,
      {
        description: "  Service performance has recovered.  ",
        status: "resolved",
      },
    );

    const requestOptions = latestRequestOptions();

    expect(requestOptions.method).toBe("PATCH");
    expect(JSON.parse(requestOptions.body)).toEqual({
      description: "Service performance has recovered.",
      status: "resolved",
    });
  });

  it("deletes an Incident and accepts an empty response", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      new Response(null, {
        status: 204,
      }),
    );

    const result = await deleteIncident(
      accessToken,
      incidentId,
    );

    expect(result).toBeNull();
    expect(latestRequestOptions().method).toBe("DELETE");
    expect(globalThis.fetch.mock.calls[0][0]).toBe(
      `http://127.0.0.1:8000/api/incidents/${incidentId}`,
    );
  });
});
