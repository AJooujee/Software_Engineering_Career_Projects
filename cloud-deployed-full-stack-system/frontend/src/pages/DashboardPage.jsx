/**
 * Authenticated operational metrics and audit overview.
 */

import {
  useEffect,
  useState,
} from "react";

import { ApiError } from "../api/client.js";
import { listAuditEvents } from "../api/audit-events.js";
import { getDashboardSummary } from "../api/dashboard.js";
import { getBackendHealth } from "../api/health.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { PageHeader } from "../components/PageHeader.jsx";


const roleInformation = {
  viewer: {
    label: "Viewer",
    capability: "Read Incident and operational information.",
  },
  operator: {
    label: "Operator",
    capability: "Read, create, and update operational Incidents.",
  },
  admin: {
    label: "Administrator",
    capability: "Manage Incidents, users, roles, and account access.",
  },
};

const metricDefinitions = [
  {
    key: "total_incidents",
    label: "Total incidents",
    detail: "All recorded operational events.",
  },
  {
    key: "active_incidents",
    label: "Active incidents",
    detail: "Open or currently under investigation.",
  },
  {
    key: "critical_incidents",
    label: "Critical incidents",
    detail: "Events with critical severity.",
  },
  {
    key: "affected_services",
    label: "Affected services",
    detail: "Services with an active Incident.",
  },
];

const statusDefinitions = [
  ["open", "Open"],
  ["investigating", "Investigating"],
  ["resolved", "Resolved"],
  ["closed", "Closed"],
];

const severityDefinitions = [
  ["critical", "Critical"],
  ["high", "High"],
  ["medium", "Medium"],
  ["low", "Low"],
];

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});


/**
 * Return whether an API error invalidates the current session.
 */
function isAuthorizationError(error) {
  return (
    error instanceof ApiError
    && (error.status === 401 || error.status === 403)
  );
}


/**
 * Convert an enum or audit action segment into readable text.
 */
function formatLabel(value = "") {
  return value
    .replace(/[._]+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word, index) => (
      index === 0
        ? word.charAt(0).toUpperCase() + word.slice(1)
        : word.toLowerCase()
    ))
    .join(" ");
}


/**
 * Format an audit timestamp for the current browser locale.
 */
function formatDate(timestamp) {
  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }

  return dateFormatter.format(date);
}


/**
 * Summarize changed fields without exposing verbose audit payloads.
 */
function formatChangedFields(changes = {}) {
  const fields = Object.keys(changes);

  if (!fields.length) {
    return "Operation recorded";
  }

  return `Changed ${fields
    .map((field) => formatLabel(field).toLowerCase())
    .join(", ")}`;
}


/**
 * Present one primary operational metric.
 */
function MetricCard({
  label,
  value,
  detail,
}) {
  return (
    <article
      className="metric-card dashboard-metric"
      aria-label={label}
    >
      <div className="metric-card__heading">
        <p>{label}</p>
      </div>

      <p className="metric-card__value">
        {Number(value ?? 0).toLocaleString()}
      </p>

      <p className="metric-card__detail">
        {detail}
      </p>
    </article>
  );
}


/**
 * Present a stable set of lifecycle or severity counts.
 */
function MetricBreakdown({
  title,
  eyebrow,
  definitions,
  counts,
  modifier,
}) {
  return (
    <section
      className="content-panel dashboard-breakdown"
      aria-label={title}
    >
      <header className="dashboard-section-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
      </header>

      <dl className="dashboard-breakdown__list">
        {definitions.map(([key, label]) => (
          <div key={key}>
            <dt>
              <span
                className={`${modifier} ${modifier}--${key}`}
              >
                {label}
              </span>
            </dt>

            <dd>
              {Number(counts?.[key] ?? 0).toLocaleString()}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}


/**
 * Present administrator-only immutable activity records.
 */
function AuditActivity({
  events,
  status,
  error,
  onRetry,
}) {
  return (
    <section
      className="content-panel audit-activity"
      aria-label="Recent audit activity"
      aria-busy={status === "loading"}
    >
      <header className="dashboard-section-heading">
        <div>
          <p className="eyebrow">Administrator visibility</p>
          <h2>Recent audit activity</h2>
        </div>

        <span className="status-pill">
          Latest 8
        </span>
      </header>

      {status === "loading" && (
        <p className="dashboard-request-state">
          Loading audit activity...
        </p>
      )}

      {status === "error" && (
        <div
          className="form-alert form-alert--error"
          role="alert"
        >
          <p>{error}</p>

          <button
            type="button"
            className="button-secondary"
            onClick={onRetry}
          >
            Retry audit activity
          </button>
        </div>
      )}

      {status === "ready" && events.length === 0 && (
        <p className="dashboard-request-state">
          No audited changes have been recorded yet.
        </p>
      )}

      {status === "ready" && events.length > 0 && (
        <ol className="audit-activity__list">
          {events.map((event) => (
            <li key={event.id}>
              <div className="audit-activity__marker">
                <span aria-hidden="true" />
              </div>

              <div className="audit-activity__content">
                <div className="audit-activity__heading">
                  <strong>{formatLabel(event.action)}</strong>
                  <time dateTime={event.created_at}>
                    {formatDate(event.created_at)}
                  </time>
                </div>

                <p className="audit-activity__resource">
                  {event.resource_label}
                </p>

                <p className="audit-activity__metadata">
                  {/* Keep audit metadata independently accessible. */}
                  <span>{event.actor_email}</span>
                  <span aria-hidden="true"> · </span>
                  <span>
                    {formatChangedFields(event.changes)}
                  </span>
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}


export function DashboardPage() {
  const {
    accessToken,
    user,
    logout,
  } = useAuth();

  const [connection, setConnection] = useState({
    status: "checking",
    message: "Checking backend connection...",
  });

  const [metrics, setMetrics] = useState({
    status: "loading",
    data: null,
    error: null,
  });
  const [metricsReloadVersion, setMetricsReloadVersion] = useState(0);

  const [auditActivity, setAuditActivity] = useState({
    status: "idle",
    events: [],
    error: null,
  });
  const [auditReloadVersion, setAuditReloadVersion] = useState(0);

  const isAdministrator = user?.role === "admin";

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
          message: requestError.message
            ?? "Unable to check backend availability.",
        });
      }
    }

    checkBackendHealth();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadMetrics() {
      setMetrics({
        status: "loading",
        data: null,
        error: null,
      });

      try {
        const summary = await getDashboardSummary(
          accessToken,
          {
            signal: controller.signal,
          },
        );

        setMetrics({
          status: "ready",
          data: summary,
          error: null,
        });
      } catch (requestError) {
        if (requestError.name === "AbortError") {
          return;
        }

        if (isAuthorizationError(requestError)) {
          logout();
          return;
        }

        setMetrics({
          status: "error",
          data: null,
          error: requestError.message
            ?? "Unable to load operational metrics.",
        });
      }
    }

    loadMetrics();

    return () => controller.abort();
  }, [
    accessToken,
    logout,
    metricsReloadVersion,
  ]);

  useEffect(() => {
    if (!isAdministrator) {
      setAuditActivity({
        status: "idle",
        events: [],
        error: null,
      });
      return undefined;
    }

    const controller = new AbortController();

    async function loadAuditActivity() {
      setAuditActivity({
        status: "loading",
        events: [],
        error: null,
      });

      try {
        const events = await listAuditEvents(
          accessToken,
          {
            limit: 8,
            signal: controller.signal,
          },
        );

        setAuditActivity({
          status: "ready",
          events,
          error: null,
        });
      } catch (requestError) {
        if (requestError.name === "AbortError") {
          return;
        }

        if (isAuthorizationError(requestError)) {
          logout();
          return;
        }

        setAuditActivity({
          status: "error",
          events: [],
          error: requestError.message
            ?? "Unable to load recent audit activity.",
        });
      }
    }

    loadAuditActivity();

    return () => controller.abort();
  }, [
    accessToken,
    auditReloadVersion,
    isAdministrator,
    logout,
  ]);

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
          "Monitor current Incident volume, service impact, "
          + "and operational activity."
        }
      />

      <section
        className="dashboard-context"
        aria-label="Workspace context"
      >
        <div>
          <span
            className={
              `status-indicator `
              + `status-indicator--${connection.status}`
            }
            aria-hidden="true"
          />

          <div>
            <strong>Backend API</strong>
            <p aria-live="polite">{connection.message}</p>
          </div>
        </div>

        <div>
          <span className={`role-badge role-badge--${user?.role}`}>
            {currentRole.label}
          </span>

          <p>{currentRole.capability}</p>
        </div>
      </section>

      <section
        className="dashboard-metrics-section"
        aria-labelledby="operational-metrics-heading"
        aria-busy={metrics.status === "loading"}
      >
        <header className="dashboard-section-heading">
          <div>
            <p className="eyebrow">Current workload</p>
            <h2 id="operational-metrics-heading">
              Operational metrics
            </h2>
          </div>
        </header>

        {metrics.status === "loading" && (
          <div className="content-panel dashboard-request-state">
            Loading operational metrics...
          </div>
        )}

        {metrics.status === "error" && (
          <div
            className="content-panel dashboard-request-error"
            role="alert"
          >
            <div>
              <p className="eyebrow">Metrics unavailable</p>
              <h2>Unable to load the operational summary</h2>
              <p>{metrics.error}</p>
            </div>

            <button
              type="button"
              className="button-secondary"
              onClick={() => {
                setMetricsReloadVersion(
                  (currentVersion) => currentVersion + 1,
                );
              }}
            >
              Retry metrics
            </button>
          </div>
        )}

        {metrics.status === "ready" && (
          <>
            <div className="dashboard-metrics-grid">
              {metricDefinitions.map((metric) => (
                <MetricCard
                  key={metric.key}
                  label={metric.label}
                  value={metrics.data?.[metric.key]}
                  detail={metric.detail}
                />
              ))}
            </div>

            <div className="dashboard-breakdown-grid">
              <MetricBreakdown
                title="Incident lifecycle"
                eyebrow="Status distribution"
                definitions={statusDefinitions}
                counts={metrics.data?.status_counts}
                modifier="incident-status"
              />

              <MetricBreakdown
                title="Severity distribution"
                eyebrow="Impact profile"
                definitions={severityDefinitions}
                counts={metrics.data?.severity_counts}
                modifier="severity-badge"
              />
            </div>
          </>
        )}
      </section>

      {isAdministrator && (
        <AuditActivity
          events={auditActivity.events}
          status={auditActivity.status}
          error={auditActivity.error}
          onRetry={() => {
            setAuditReloadVersion(
              (currentVersion) => currentVersion + 1,
            );
          }}
        />
      )}
    </div>
  );
}
