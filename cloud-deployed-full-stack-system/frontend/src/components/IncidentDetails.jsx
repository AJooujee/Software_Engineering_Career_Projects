/**
 * Detailed view of one selected operational Incident.
 */

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});


/**
 * Convert an enum-style value into a readable label.
 */
function formatLabel(value = "") {
  return value
    .split("_")
    .map((word) => (
      word.charAt(0).toUpperCase() + word.slice(1)
    ))
    .join(" ");
}


/**
 * Format an API timestamp for display.
 */
function formatDate(timestamp) {
  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return dateFormatter.format(date);
}


export function IncidentDetails({
  incident,
  canEdit,
  canDelete,
  onEdit,
  onDelete,
}) {
  return (
    <article className="incident-details">
      <header className="incident-details__header">
        <div>
          <p className="eyebrow">Selected incident</p>
          <h2>{incident.title}</h2>
        </div>

        {(canEdit || canDelete) && (
          <div className="incident-details__actions">
            {canEdit && (
              <button
                type="button"
                className="button-secondary"
                onClick={onEdit}
              >
                Edit
              </button>
            )}

            {canDelete && (
              <button
                type="button"
                className="button-danger button-danger--subtle"
                onClick={onDelete}
              >
                Delete
              </button>
            )}
          </div>
        )}
      </header>

      <dl className="incident-details__summary">
        <div>
          <dt>Severity</dt>
          <dd>
            <span
              className={
                `severity-badge severity-badge--`
                + incident.severity
              }
            >
              {formatLabel(incident.severity)}
            </span>
          </dd>
        </div>

        <div>
          <dt>Status</dt>
          <dd>
            <span
              className={
                `incident-status incident-status--`
                + incident.status
              }
            >
              {formatLabel(incident.status)}
            </span>
          </dd>
        </div>

        <div>
          <dt>Service</dt>
          <dd>{incident.service_name}</dd>
        </div>
      </dl>

      <section className="incident-details__description">
        <h3>Description</h3>
        <p>{incident.description}</p>
      </section>

      <dl className="incident-details__metadata">
        <div>
          <dt>Created</dt>
          <dd>{formatDate(incident.created_at)}</dd>
        </div>

        <div>
          <dt>Last updated</dt>
          <dd>{formatDate(incident.updated_at)}</dd>
        </div>

        <div>
          <dt>Incident ID</dt>
          <dd className="incident-details__identifier">
            {incident.id}
          </dd>
        </div>
      </dl>
    </article>
  );
}
