/**
 * Integration-style component tests for the operational dashboard.
 */

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import {
  render,
  screen,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DashboardPage } from "./DashboardPage.jsx";


const testState = vi.hoisted(() => ({
  auth: null,
  getBackendHealth: vi.fn(),
  getDashboardSummary: vi.fn(),
  listAuditEvents: vi.fn(),
}));


// Replace external state and requests with deterministic test controls.
vi.mock("../auth/AuthContext.jsx", () => ({
  useAuth: () => testState.auth,
}));

vi.mock("../api/health.js", () => ({
  getBackendHealth: testState.getBackendHealth,
}));

vi.mock("../api/dashboard.js", () => ({
  getDashboardSummary: testState.getDashboardSummary,
}));

vi.mock("../api/audit-events.js", () => ({
  listAuditEvents: testState.listAuditEvents,
}));


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
 * Configure one authenticated dashboard user.
 */
function useTestRole(role) {
  testState.auth = {
    accessToken: `${role}-access-token`,
    user: {
      id: `${role}-user-id`,
      email: `${role}@example.com`,
      full_name: `Phase Six ${role}`,
      role,
      is_active: true,
    },
    logout: vi.fn(),
  };
}


describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useTestRole("viewer");

    testState.getBackendHealth.mockResolvedValue({
      status: "healthy",
      service: "cloud-operations-api",
    });
    testState.getDashboardSummary.mockResolvedValue(
      dashboardSummary,
    );
    testState.listAuditEvents.mockResolvedValue([
      auditEvent,
    ]);
  });

  it("renders current metrics and operational breakdowns", async () => {
    render(<DashboardPage />);

    const totalCard = await screen.findByRole(
      "article",
      { name: "Total incidents" },
    );
    const activeCard = screen.getByRole(
      "article",
      { name: "Active incidents" },
    );
    const criticalCard = screen.getByRole(
      "article",
      { name: "Critical incidents" },
    );
    const servicesCard = screen.getByRole(
      "article",
      { name: "Affected services" },
    );

    expect(
      within(totalCard).getByText("4"),
    ).toBeInTheDocument();
    expect(
      within(activeCard).getByText("2"),
    ).toBeInTheDocument();
    expect(
      within(criticalCard).getByText("1"),
    ).toBeInTheDocument();
    expect(
      within(servicesCard).getByText("2"),
    ).toBeInTheDocument();

    const lifecycle = screen.getByRole(
      "region",
      { name: "Incident lifecycle" },
    );
    const severity = screen.getByRole(
      "region",
      { name: "Severity distribution" },
    );

    expect(
      within(lifecycle).getByText("Investigating"),
    ).toBeInTheDocument();
    expect(
      within(lifecycle).getByText("Resolved"),
    ).toBeInTheDocument();
    expect(
      within(severity).getByText("Critical"),
    ).toBeInTheDocument();

    expect(testState.getDashboardSummary).toHaveBeenCalledWith(
      "viewer-access-token",
      expect.objectContaining({
        signal: expect.anything(),
      }),
    );

    // Non-administrators never request restricted audit history.
    expect(testState.listAuditEvents).not.toHaveBeenCalled();
  });

  it("shows recent audit activity only to administrators", async () => {
    useTestRole("admin");

    render(<DashboardPage />);

    const auditRegion = await screen.findByRole(
      "region",
      { name: "Recent audit activity" },
    );

    expect(
      within(auditRegion).getByText("Incident created"),
    ).toBeInTheDocument();
    expect(
      within(auditRegion).getByText("Payment API latency"),
    ).toBeInTheDocument();
    expect(
      within(auditRegion).getByText("admin@example.com"),
    ).toBeInTheDocument();

    expect(testState.listAuditEvents).toHaveBeenCalledWith(
      "admin-access-token",
      expect.objectContaining({
        limit: 8,
        signal: expect.anything(),
      }),
    );
  });

  it("allows a failed metric request to be retried", async () => {
    const user = userEvent.setup();

    testState.getDashboardSummary
      .mockRejectedValueOnce(
        new Error("Metrics temporarily unavailable."),
      )
      .mockResolvedValueOnce(dashboardSummary);

    render(<DashboardPage />);

    expect(
      await screen.findByText(
        "Metrics temporarily unavailable.",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Retry metrics",
      }),
    );

    const totalCard = await screen.findByRole(
      "article",
      { name: "Total incidents" },
    );

    expect(
      within(totalCard).getByText("4"),
    ).toBeInTheDocument();
    expect(
      testState.getDashboardSummary,
    ).toHaveBeenCalledTimes(2);
  });
});
