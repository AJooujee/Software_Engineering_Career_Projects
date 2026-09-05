/**
 * Authenticated overview of the Cloud Operations workspace.
 */

import { useEffect, useState } from "react";

import { getBackendHealth } from "../api/health.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { PageHeader } from "../components/PageHeader.jsx";


const roleInformation = {
  viewer: {
    label: "Viewer",
    capability: "Read incident and operational information.",
  },
  operator: {
    label: "Operator",
    capability: "Read, create, and update operational incidents.",
  },
  admin: {
    label: "Administrator",
    capability: "Manage incidents, users, roles, and account access.",
  },
};


export function DashboardPage() {
  const { user } = useAuth();

  const [connection, setConnection] = useState({
    status: "checking",
    message: "Checking backend connection...",
  });

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackendHealth() {
      try {
        const health = await getBackendHealth({
          signal: controller.signal,
        });

        setConnection({
          status: health.status === "healthy" ? "healthy" : "error",
          message: `Connected to ${health.service}`,
        });
      } catch (requestError) {
        if (requestError.name === "AbortError") {
          return;
        }

        setConnection({
          status: "error",
          message: requestError.message,
        });
      }
    }

    checkBackendHealth();

    return () => controller.abort();
  }, []);

  const currentRole = roleInformation[user?.role] ?? {
    label: user?.role ?? "Unknown",
    capability: "Account permissions are unavailable.",
  };

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Operations overview"
        title={`Welcome, ${user?.full_name}`}
        description={
          "Monitor platform availability and review your current "
          + "workspace access."
        }
      />

      <section
        className="dashboard-grid"
        aria-label="Workspace status"
      >
        <article className="metric-card">
          <div className="metric-card__heading">
            <p>Backend API</p>

            <span
              className={
                `status-indicator `
                + `status-indicator--${connection.status}`
              }
              aria-hidden="true"
            />
          </div>

          <p
            className="metric-card__value"
            aria-live="polite"
          >
            {connection.status === "healthy"
              ? "Operational"
              : connection.status === "checking"
                ? "Checking"
                : "Unavailable"}
          </p>

          <p className="metric-card__detail">
            {connection.message}
          </p>
        </article>

        <article className="metric-card">
          <div className="metric-card__heading">
            <p>Current role</p>
          </div>

          <p className="metric-card__value">
            {currentRole.label}
          </p>

          <p className="metric-card__detail">
            {currentRole.capability}
          </p>
        </article>

        <article className="metric-card">
          <div className="metric-card__heading">
            <p>Authentication</p>
          </div>

          <p className="metric-card__value">Protected</p>

          <p className="metric-card__detail">
            Your active session is validated by the FastAPI backend.
          </p>
        </article>
      </section>

      <section className="content-panel">
        <div className="content-panel__heading">
          <div>
            <p className="eyebrow">Phase 4 workspace</p>
            <h2>Frontend foundation is active</h2>
          </div>

          <span className="status-pill status-pill--success">
            Connected
          </span>
        </div>

        <p>
          Routing, authentication state, protected navigation,
          and role-aware application layouts are now being integrated.
          Incident workflow screens will be completed in Phase 5.
        </p>
      </section>
    </div>
  );
}
