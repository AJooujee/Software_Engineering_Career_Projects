/**
 * Authenticated application shell with role-aware navigation.
 */

import { NavLink, Outlet } from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";


const primaryNavigation = [
  {
    label: "Dashboard",
    shortLabel: "D",
    to: "/dashboard",
  },
  {
    label: "Incidents",
    shortLabel: "I",
    to: "/incidents",
  },
];

const roleLabels = {
  viewer: "Viewer",
  operator: "Operator",
  admin: "Administrator",
};


/**
 * Return a navigation class that reflects the active route.
 */
function navigationClassName({ isActive }) {
  return [
    "app-navigation__link",
    isActive ? "app-navigation__link--active" : "",
  ]
    .filter(Boolean)
    .join(" ");
}


/**
 * Create a short avatar label from the user's full name.
 */
function getInitials(fullName = "") {
  return fullName
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((namePart) => namePart.charAt(0))
    .join("")
    .toUpperCase() || "U";
}


export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="application-layout">
      <aside className="application-sidebar">
        <NavLink className="brand-link" to="/dashboard">
          <span className="brand-mark" aria-hidden="true">
            CO
          </span>

          <span>Cloud Operations</span>
        </NavLink>

        <nav
          className="app-navigation"
          aria-label="Primary navigation"
        >
          <p className="app-navigation__label">Workspace</p>

          {primaryNavigation.map((navigationItem) => (
            <NavLink
              key={navigationItem.to}
              className={navigationClassName}
              to={navigationItem.to}
              end={navigationItem.to === "/dashboard"}
            >
              <span
                className="app-navigation__icon"
                aria-hidden="true"
              >
                {navigationItem.shortLabel}
              </span>

              <span>{navigationItem.label}</span>
            </NavLink>
          ))}

          {user?.role === "admin" && (
            <NavLink
              className={navigationClassName}
              to="/users"
            >
              <span
                className="app-navigation__icon"
                aria-hidden="true"
              >
                U
              </span>

              <span>User access</span>
            </NavLink>
          )}
        </nav>

        <div className="user-summary">
          <span className="user-summary__avatar" aria-hidden="true">
            {getInitials(user?.full_name)}
          </span>

          <div className="user-summary__details">
            <p>{user?.full_name}</p>
            <span>{roleLabels[user?.role] ?? user?.role}</span>
          </div>

          <button
            type="button"
            className="user-summary__logout"
            onClick={logout}
            title="Sign out"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="application-workspace">
        <header className="application-header">
          <div>
            <p className="application-header__label">
              Secure workspace
            </p>
            <p className="application-header__email">
              {user?.email}
            </p>
          </div>

          <span className={`role-badge role-badge--${user?.role}`}>
            {roleLabels[user?.role] ?? user?.role}
          </span>
        </header>

        <main className="application-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
