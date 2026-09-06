/**
 * Search and classification filters for the Incident queue.
 */

import {
  INCIDENT_SEVERITIES,
  INCIDENT_STATUSES,
} from "../api/incidents.js";


/**
 * Convert an enum-style value into a readable option label.
 */
function formatOptionLabel(value = "") {
  return value
    .split("_")
    .map((word) => (
      word.charAt(0).toUpperCase() + word.slice(1)
    ))
    .join(" ");
}


/**
 * Return whether the draft contains at least one filter value.
 */
function containsFilterValue(filters) {
  return Object.values(filters).some(
    (value) => value.trim().length > 0,
  );
}


export function IncidentFilters({
  value,
  hasActiveFilters,
  isLoading,
  onChange,
  onApply,
  onClear,
}) {
  const hasDraftValues = containsFilterValue(value);

  function handleChange(event) {
    const {
      name,
      value: fieldValue,
    } = event.target;

    onChange({
      ...value,
      [name]: fieldValue,
    });
  }

  function handleSubmit(event) {
    event.preventDefault();
    onApply();
  }

  return (
    <form
      className="incident-filters"
      aria-label="Incident filters"
      onSubmit={handleSubmit}
    >
      <div className="incident-filters__heading">
        <div>
          <p className="eyebrow">Queue controls</p>
          <h2>Filter incidents</h2>
        </div>

        {hasActiveFilters && (
          <span className="status-pill status-pill--success">
            Filters active
          </span>
        )}
      </div>

      <fieldset
        className="incident-filters__fields"
        disabled={isLoading}
      >
        <label className="form-field incident-filters__search">
          <span>Search incidents</span>
          <input
            type="search"
            name="search"
            value={value.search}
            placeholder="Title, description, or service"
            autoComplete="off"
            onChange={handleChange}
          />
        </label>

        <label className="form-field">
          <span>Filter by status</span>
          <select
            name="status"
            value={value.status}
            onChange={handleChange}
          >
            <option value="">All statuses</option>

            {INCIDENT_STATUSES.map((status) => (
              <option key={status} value={status}>
                {formatOptionLabel(status)}
              </option>
            ))}
          </select>
        </label>

        <label className="form-field">
          <span>Filter by severity</span>
          <select
            name="severity"
            value={value.severity}
            onChange={handleChange}
          >
            <option value="">All severities</option>

            {INCIDENT_SEVERITIES.map((severity) => (
              <option key={severity} value={severity}>
                {formatOptionLabel(severity)}
              </option>
            ))}
          </select>
        </label>

        <label className="form-field">
          <span>Filter by service</span>
          <input
            type="text"
            name="serviceName"
            value={value.serviceName}
            placeholder="payment-api"
            autoComplete="off"
            onChange={handleChange}
          />
        </label>
      </fieldset>

      <div className="incident-filters__actions">
        <button
          type="button"
          className="button-secondary"
          disabled={isLoading || !hasDraftValues}
          onClick={onClear}
        >
          Clear filters
        </button>

        <button
          type="submit"
          className="button-primary"
          disabled={isLoading}
        >
          {isLoading ? "Filtering..." : "Apply filters"}
        </button>
      </div>
    </form>
  );
}
