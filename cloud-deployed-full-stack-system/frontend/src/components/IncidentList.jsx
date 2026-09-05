/**
 * Selectable list of operational Incidents.
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
 * Format an API timestamp for the current browser locale.
 */
function formatDate(timestamp) {
  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return dateFormatter.format(date);
}


export function IncidentList({
  incidents,
  selectedIncidentId,
  onSelect,
}) {
  return (
    <ul
      className="incident-list"
      aria-label="Operational incidents"
    >
      {incidents.map((incident) => {
        const isSelected = incident.id === selectedIncidentId;

        return (
          <li key={incident.id}>
            <button
              type="button"
              className={[
                "incident-list__item",
                isSelected
                  ? "incident-list__item--selected"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-pressed={isSelected}
              onClick={() => onSelect(incident)}
            >
              <div className="incident-list__heading">
                <span
                  className={
                    `severity-badge severity-badge--`
                    + incident.severity
                  }
                >
                  {formatLabel(incident.severity)}
                </span>

                <span
                  className={
                    `incident-status incident-status--`
                    + incident.status
                  }
                >
                  {formatLabel(incident.status)}
                </span>
              </div>

              <strong className="incident-list__title">
                {incident.title}
              </strong>

              <span className="incident-list__service">
                {incident.service_name}
              </span>

              <span className="incident-list__date">
                Created {formatDate(incident.created_at)}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
