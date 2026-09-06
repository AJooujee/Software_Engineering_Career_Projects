/**
 * Integration tests for filtering the Incident workspace.
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
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { IncidentsPage } from "./IncidentsPage.jsx";


const authContext = vi.hoisted(() => ({
  current: null,
}));


// Replace authentication with a stable viewer session.
vi.mock("../auth/AuthContext.jsx", () => ({
  useAuth: () => authContext.current,
}));


const exampleIncident = {
  id: "e7c55154-16a7-4877-a2b1-b46335942a43",
  title: "Orders API error rate",
  description: "Customer requests are returning server errors.",
  service_name: "orders-api",
  severity: "critical",
  status: "open",
  created_at: "2026-09-05T18:53:00Z",
  updated_at: "2026-09-05T18:53:00Z",
};

const filteredIncident = {
  ...exampleIncident,
  id: "payment-incident-id",
  title: "Payment API latency",
  description: "Payment requests are delayed.",
  service_name: "payments-api",
  severity: "high",
  status: "investigating",
};


/**
 * Create a mocked JSON response for the shared API client.
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


describe("IncidentsPage filters", () => {
  beforeEach(() => {
    authContext.current = {
      accessToken: "viewer-access-token",
      user: {
        id: "viewer-user-id",
        email: "viewer@example.com",
        full_name: "Phase Six Viewer",
        role: "viewer",
        is_active: true,
      },
      logout: vi.fn(),
    };

    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("applies and clears Incident filters", async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse([exampleIncident]),
      )
      .mockResolvedValueOnce(
        jsonResponse([filteredIncident]),
      )
      .mockResolvedValueOnce(
        jsonResponse([exampleIncident]),
      );

    const user = userEvent.setup();

    render(<IncidentsPage />);

    await screen.findAllByText("Orders API error rate");

    await user.type(
      screen.getByLabelText("Search incidents"),
      "payment latency",
    );
    await user.selectOptions(
      screen.getByLabelText("Filter by status"),
      "investigating",
    );
    await user.selectOptions(
      screen.getByLabelText("Filter by severity"),
      "high",
    );
    await user.type(
      screen.getByLabelText("Filter by service"),
      "payments-api",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Apply filters",
      }),
    );

    expect(
      await screen.findAllByText("Payment API latency"),
    ).toHaveLength(2);

    const filteredUrl = new URL(
      fetchMock.mock.calls[1][0],
    );

    // Confirm the UI maps each field to the backend query contract.
    expect(filteredUrl.searchParams.get("offset")).toBe("0");
    expect(filteredUrl.searchParams.get("limit")).toBe("10");
    expect(filteredUrl.searchParams.get("search")).toBe(
      "payment latency",
    );
    expect(filteredUrl.searchParams.get("status")).toBe(
      "investigating",
    );
    expect(filteredUrl.searchParams.get("severity")).toBe(
      "high",
    );
    expect(filteredUrl.searchParams.get("service_name")).toBe(
      "payments-api",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Clear filters",
      }),
    );

    expect(
      await screen.findAllByText("Orders API error rate"),
    ).toHaveLength(2);

    const clearedUrl = new URL(
      fetchMock.mock.calls[2][0],
    );

    expect(clearedUrl.searchParams.get("offset")).toBe("0");
    expect(clearedUrl.searchParams.has("search")).toBe(false);
    expect(clearedUrl.searchParams.has("status")).toBe(false);
    expect(clearedUrl.searchParams.has("severity")).toBe(false);
    expect(
      clearedUrl.searchParams.has("service_name"),
    ).toBe(false);

    expect(
      screen.getByLabelText("Search incidents"),
    ).toHaveValue("");
    expect(
      screen.getByLabelText("Filter by status"),
    ).toHaveValue("");
    expect(
      screen.getByLabelText("Filter by severity"),
    ).toHaveValue("");
    expect(
      screen.getByLabelText("Filter by service"),
    ).toHaveValue("");
  });

  it("shows an empty state for unmatched filters", async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse([exampleIncident]),
      )
      .mockResolvedValueOnce(jsonResponse([]));

    const user = userEvent.setup();

    render(<IncidentsPage />);

    await screen.findAllByText("Orders API error rate");

    await user.type(
      screen.getByLabelText("Search incidents"),
      "missing service",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Apply filters",
      }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "No incidents match the current filters",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: "Clear filters",
      }),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("heading", {
        name: "No incidents have been reported",
      }),
    ).not.toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
