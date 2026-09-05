/**
 * Tests for authenticated and role-restricted frontend routes.
 */

import {
  render,
  screen,
} from "@testing-library/react";
import {
  MemoryRouter,
  Route,
  Routes,
} from "react-router";
import {
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { useAuth } from "../auth/AuthContext.jsx";
import { ProtectedRoute } from "./ProtectedRoute.jsx";
import { PublicOnlyRoute } from "./PublicOnlyRoute.jsx";


vi.mock("../auth/AuthContext.jsx", () => ({
  useAuth: vi.fn(),
}));


function createAuthState(overrides = {}) {
  return {
    user: null,
    status: "anonymous",
    error: null,
    retrySession: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  };
}


function renderProtectedRoute({ allowedRoles = [] } = {}) {
  render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route path="/login" element={<p>Login page</p>} />
        <Route path="/forbidden" element={<p>Forbidden page</p>} />

        <Route
          element={
            <ProtectedRoute allowedRoles={allowedRoles} />
          }
        >
          <Route
            path="/protected"
            element={<p>Protected content</p>}
          />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}


function renderPublicRoute() {
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<p>Login page</p>} />
        </Route>

        <Route
          path="/dashboard"
          element={<p>Dashboard page</p>}
        />
      </Routes>
    </MemoryRouter>,
  );
}


describe("ProtectedRoute", () => {
  beforeEach(() => {
    useAuth.mockReset();
  });

  test("redirects an anonymous visitor to login", async () => {
    useAuth.mockReturnValue(createAuthState());

    renderProtectedRoute();

    expect(await screen.findByText("Login page")).toBeInTheDocument();
  });

  test("redirects a viewer away from an admin route", async () => {
    useAuth.mockReturnValue(
      createAuthState({
        status: "authenticated",
        user: {
          role: "viewer",
        },
      }),
    );

    renderProtectedRoute({
      allowedRoles: ["admin"],
    });

    expect(
      await screen.findByText("Forbidden page"),
    ).toBeInTheDocument();
  });

  test("allows an administrator to open an admin route", () => {
    useAuth.mockReturnValue(
      createAuthState({
        status: "authenticated",
        user: {
          role: "admin",
        },
      }),
    );

    renderProtectedRoute({
      allowedRoles: ["admin"],
    });

    expect(
      screen.getByText("Protected content"),
    ).toBeInTheDocument();
  });
});


describe("PublicOnlyRoute", () => {
  beforeEach(() => {
    useAuth.mockReset();
  });

  test("allows an anonymous visitor to open login", () => {
    useAuth.mockReturnValue(createAuthState());

    renderPublicRoute();

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  test("redirects an authenticated user to dashboard", async () => {
    useAuth.mockReturnValue(
      createAuthState({
        status: "authenticated",
        user: {
          role: "operator",
        },
      }),
    );

    renderPublicRoute();

    expect(
      await screen.findByText("Dashboard page"),
    ).toBeInTheDocument();
  });
});
