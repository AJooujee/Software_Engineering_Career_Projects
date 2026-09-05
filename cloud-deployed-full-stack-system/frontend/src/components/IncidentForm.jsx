/**
 * Shared form for creating and editing operational Incidents.
 */

import { useEffect, useState } from "react";

import {
  INCIDENT_SEVERITIES,
  INCIDENT_STATUSES,
} from "../api/incidents.js";


/**
 * Convert an enum-style value into a readable option label.
 */
function formatOptionLabel(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}


/**
 * Create form state from an existing Incident or blank defaults.
 */
function createFormData(incident) {
  return {
    title: incident?.title ?? "",
    description: incident?.description ?? "",
    serviceName: incident?.service_name ?? "",
    severity: incident?.severity ?? "medium",
    status: incident?.status ?? "open",
  };
}


export function IncidentForm({
  incident = null,
  error = null,
  isSubmitting = false,
  onSubmit,
  onCancel,
}) {
  const isEditing = Boolean(incident);
  const [formData, setFormData] = useState(
    () => createFormData(incident),
  );

  useEffect(() => {
    setFormData(createFormData(incident));
  }, [incident]);

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((currentFormData) => ({
      ...currentFormData,
      [name]: value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();

    const incidentData = {
      title: formData.title,
      description: formData.description,
      serviceName: formData.serviceName,
      severity: formData.severity,
    };

    if (isEditing) {
      incidentData.status = formData.status;
    }

    onSubmit(incidentData);
  }

  return (
    <form className="incident-form" onSubmit={handleSubmit}>
      {error && (
        <div
          id="incident-form-error"
          className="form-alert form-alert--error"
          role="alert"
        >
          {error}
        </div>
      )}

      <fieldset
        className="incident-form__fields"
        disabled={isSubmitting}
        aria-describedby={
          error ? "incident-form-error" : undefined
        }
      >
        <label className="form-field">
          <span>Title</span>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            minLength={3}
            maxLength={200}
            autoFocus
            required
          />
        </label>

        <label className="form-field">
          <span>Service name</span>
          <input
            type="text"
            name="serviceName"
            value={formData.serviceName}
            onChange={handleChange}
            minLength={2}
            maxLength={120}
            placeholder="payment-api"
            required
          />
        </label>

        <div className="incident-form__row">
          <label className="form-field">
            <span>Severity</span>
            <select
              name="severity"
              value={formData.severity}
              onChange={handleChange}
              required
            >
              {INCIDENT_SEVERITIES.map((severity) => (
                <option key={severity} value={severity}>
                  {formatOptionLabel(severity)}
                </option>
              ))}
            </select>
          </label>

          {isEditing && (
            <label className="form-field">
              <span>Status</span>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                required
              >
                {INCIDENT_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {formatOptionLabel(status)}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>

        <label className="form-field">
          {/* Keep helper copy separate from the field's accessible name. */}
          <span id="incident-description-label">
            Description
          </span>
          <textarea
            id="incident-description"
            name="description"
            aria-labelledby="incident-description-label"
            aria-describedby="incident-description-help"
            value={formData.description}
            onChange={handleChange}
            minLength={1}
            maxLength={5000}
            rows={7}
            required
          />
          <small id="incident-description-help">
            Describe the impact, symptoms, and current response.
          </small>
        </label>
      </fieldset>

      <div className="incident-form__actions">
        <button
          type="button"
          className="button-secondary"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </button>

        <button
          type="submit"
          className="button-primary"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? "Saving..."
            : isEditing
              ? "Save changes"
              : "Create incident"}
        </button>
      </div>
    </form>
  );
}
