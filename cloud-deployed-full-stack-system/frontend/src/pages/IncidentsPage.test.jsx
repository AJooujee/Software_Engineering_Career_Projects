/**
 * Integration-style component tests for the Incident workspace.
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
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { IncidentsPage } from "./IncidentsPage.jsx";


const authContext = vi.hoisted(() => ({
  current: null,
}));


// Replace application authentication with a controllable test user.
vi.mock("../auth/AuthContext.jsx", () => ({
  useAuth: () => authContext.current,
}));


const incidentId = "e7c55154-16a7-4877-a2b1-b46335942a43";

const exampleIncident = {
  id: incidentId,
  title: "Orders API error rate",
  description: "Customer requests are returning server errors.",
  service_name: "orders-api",
  severity: "critical",
  status: "open",
  created_at: "2026-09-05T18:53:00Z",
  updated_at: "2026-09-05T18:53:00Z",
};


/**
 * Create a mocked JSON response with an API-compatible content type.
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
 * Configure the current authenticated role for one test.
 */
function useTestRole(role) {
  authContext.current = {
    accessToken: `${role}-access-token`,
    user: {
      id: `${role}-user-id`,
      email: `${role}@example.com`,
      full_name: `Phase Five ${role}`,
      role,
      is_active: true,
    },
    logout: vi.fn(),
  };
}


describe("IncidentsPage", () => {
  beforeEach(() => {
    useTestRole("viewer");

    // Each test defines the exact sequence returned by the backend.
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("allows a viewer to read without mutation controls", async () => {
    globalThis.fetch.mockResolvedValueOnce(
      jsonResponse([exampleIncident]),
    );

    render(<IncidentsPage />);

    expect(
      await screen.findAllByText("Orders API error rate"),
    ).toHaveLength(2);

    expect(
      screen.getByRole("button", { name: "Refresh" }),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("button", {
        name: "Create incident",
      }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Edit" }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Delete" }),
    ).not.toBeInTheDocument();
  });

  it("allows an operator to create an Incident", async () => {
    useTestRole("operator");
    const user = userEvent.setup();

    const createdIncident = {
      ...exampleIncident,
      title: "Inventory synchronization delay",
      description: "Warehouse updates are delayed.",
      service_name: "inventory-worker",
      severity: "high",
    };

    // Return the empty page, creation result, and refreshed page.
    globalThis.fetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse(createdIncident, 201),
      )
      .mockResolvedValueOnce(
        jsonResponse([createdIncident]),
      );

    render(<IncidentsPage />);

    await screen.findByRole("heading", {
      name: "No incidents have been reported",
    });

    await user.click(
      screen.getByRole("button", {
        name: "Create incident",
      }),
    );

    await user.type(
      screen.getByLabelText("Title"),
      "Inventory synchronization delay",
    );
    await user.type(
      screen.getByLabelText("Service name"),
      "inventory-worker",
    );
    await user.selectOptions(
      screen.getByLabelText("Severity"),
      "high",
    );
    await user.type(
      screen.getByLabelText("Description"),
      "Warehouse updates are delayed.",
    );

    await user.click(
      within(
        // Scope the submit query to the active modal.
        screen.getByRole(
          "dialog",
          { name: "Create incident" },
        ),
      ).getByRole(
        "button",
        { name: "Create incident" },
      ),
    );

    expect(
      await screen.findByText(
        'Created "Inventory synchronization delay".',
      ),
    ).toBeInTheDocument();

    expect(
      await screen.findAllByText(
        "Inventory synchronization delay",
      ),
    ).toHaveLength(2);

    // The second request is the POST sent by the form.
    const createOptions = globalThis.fetch.mock.calls[1][1];

    expect(createOptions.method).toBe("POST");
    expect(JSON.parse(createOptions.body)).toEqual({
      title: "Inventory synchronization delay",
      description: "Warehouse updates are delayed.",
      service_name: "inventory-worker",
      severity: "high",
    });

    expect(
      screen.queryByRole("button", { name: "Delete" }),
    ).not.toBeInTheDocument();
  });

  it("allows an operator to update an Incident", async () => {
    useTestRole("operator");
    const user = userEvent.setup();

    const updatedIncident = {
      ...exampleIncident,
      description: "The operations team is investigating.",
      severity: "high",
      status: "investigating",
      updated_at: "2026-09-05T19:00:00Z",
    };

    globalThis.fetch
      .mockResolvedValueOnce(
        jsonResponse([exampleIncident]),
      )
      .mockResolvedValueOnce(
        jsonResponse(updatedIncident),
      );

    render(<IncidentsPage />);

    await screen.findAllByText("Orders API error rate");

    await user.click(
      screen.getByRole("button", { name: "Edit" }),
    );

    await user.clear(
      screen.getByLabelText("Description"),
    );
    await user.type(
      screen.getByLabelText("Description"),
      "The operations team is investigating.",
    );
    await user.selectOptions(
      screen.getByLabelText("Severity"),
      "high",
    );
    await user.selectOptions(
      screen.getByLabelText("Status"),
      "investigating",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save changes",
      }),
    );

    expect(
      await screen.findByText(
        'Updated "Orders API error rate".',
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "The operations team is investigating.",
      ),
    ).toBeInTheDocument();

    const updateOptions = globalThis.fetch.mock.calls[1][1];

    expect(updateOptions.method).toBe("PATCH");
    expect(JSON.parse(updateOptions.body)).toMatchObject({
      description: "The operations team is investigating.",
      severity: "high",
      status: "investigating",
    });

    expect(
      screen.queryByRole("button", { name: "Delete" }),
    ).not.toBeInTheDocument();
  });

  it("allows an administrator to confirm Incident deletion", async () => {
    useTestRole("admin");
    const user = userEvent.setup();

    // Return the Incident, successful deletion, and empty refresh.
    globalThis.fetch
      .mockResolvedValueOnce(
        jsonResponse([exampleIncident]),
      )
      .mockResolvedValueOnce(
        new Response(null, {
          status: 204,
        }),
      )
      .mockResolvedValueOnce(jsonResponse([]));

    render(<IncidentsPage />);

    await screen.findAllByText("Orders API error rate");

    await user.click(
      screen.getByRole("button", { name: "Delete" }),
    );

    const dialog = screen.getByRole("dialog", {
      name: "Delete incident?",
    });

    expect(
      within(dialog).getByText("Orders API error rate"),
    ).toBeInTheDocument();

    await user.click(
      within(dialog).getByRole("button", {
        name: "Delete incident",
      }),
    );

    expect(
      await screen.findByText(
        'Deleted "Orders API error rate".',
      ),
    ).toBeInTheDocument();

    expect(
      await screen.findByRole("heading", {
        name: "No incidents have been reported",
      }),
    ).toBeInTheDocument();

    expect(globalThis.fetch.mock.calls[1][1].method).toBe(
      "DELETE",
    );
  });

  it("allows a failed Incident list request to be retried", async () => {
    const user = userEvent.setup();

    globalThis.fetch
      .mockResolvedValueOnce(
        jsonResponse(
          {
            detail: "Database temporarily unavailable.",
          },
          500,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse([exampleIncident]),
      );

    render(<IncidentsPage />);

    expect(
      await screen.findByText(
        "Database temporarily unavailable.",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Try again" }),
    );

    expect(
      await screen.findAllByText("Orders API error rate"),
    ).toHaveLength(2);
  });

  it("moves between Incident result pages", async () => {
    useTestRole("viewer");

    // A complete page enables navigation when the API has no total count.
    const firstPage = Array.from(
      { length: 10 },
      (_, index) => ({
        ...exampleIncident,
        id: `incident-${index + 1}`,
        title: `Incident ${index + 1}`,
      }),
    );
    const secondPage = [
      {
        ...exampleIncident,
        id: "incident-11",
        title: "Incident 11",
      },
    ];

    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockReset();
    fetchMock
      .mockResolvedValueOnce(jsonResponse(firstPage))
      .mockResolvedValueOnce(jsonResponse(secondPage))
      .mockResolvedValueOnce(jsonResponse(firstPage));

    const user = userEvent.setup();

    render(<IncidentsPage />);

    const firstPageList = await screen.findByRole(
      "list",
      { name: "Operational incidents" },
    );

    expect(
      within(firstPageList).getByText("Incident 1"),
    ).toBeInTheDocument();

    const nextButton = screen.getByRole(
      "button",
      { name: "Next" },
    );

    expect(nextButton).toBeEnabled();

    await user.click(nextButton);

    expect(
      await screen.findByText("Page 2"),
    ).toBeInTheDocument();

    const secondPageList = screen.getByRole(
      "list",
      { name: "Operational incidents" },
    );

    expect(
      within(secondPageList).getByText("Incident 11"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Next" }),
    ).toBeDisabled();

    expect(fetchMock.mock.calls[1][0]).toContain(
      "offset=10",
    );
    expect(fetchMock.mock.calls[1][0]).toContain(
      "limit=10",
    );

    await user.click(
      screen.getByRole("button", { name: "Previous" }),
    );

    expect(
      await screen.findByText("Page 1"),
    ).toBeInTheDocument();

    expect(fetchMock.mock.calls[2][0]).toContain(
      "offset=0",
    );
  });
});
