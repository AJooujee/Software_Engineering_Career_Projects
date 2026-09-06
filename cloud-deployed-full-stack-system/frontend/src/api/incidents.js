/**
 * Incident-management requests sent to the FastAPI backend.
 */

import { apiRequest } from "./client.js";


const INCIDENTS_PATH = "/api/incidents";

export const INCIDENT_SEVERITIES = [
  "low",
  "medium",
  "high",
  "critical",
];

export const INCIDENT_STATUSES = [
  "open",
  "investigating",
  "resolved",
  "closed",
];


/**
 * Convert frontend Incident form fields into the backend schema.
 */
function createIncidentPayload(incidentData) {
  const payload = {};

  if (incidentData.title !== undefined) {
    payload.title = incidentData.title.trim();
  }

  if (incidentData.description !== undefined) {
    payload.description = incidentData.description.trim();
  }

  if (incidentData.serviceName !== undefined) {
    payload.service_name = incidentData.serviceName.trim();
  }

  if (incidentData.severity !== undefined) {
    payload.severity = incidentData.severity;
  }

  if (incidentData.status !== undefined) {
    payload.status = incidentData.status;
  }

  return payload;
}


/**
 * Add a non-empty normalized string to an API query.
 */
function addQueryValue(query, name, value) {
  if (typeof value !== "string") {
    return;
  }

  const normalizedValue = value.trim();

  if (normalizedValue) {
    query.set(name, normalizedValue);
  }
}


/**
 * Return a filtered, paginated collection of Incidents.
 */
export function listIncidents(
  accessToken,
  {
    search = "",
    status = "",
    severity = "",
    serviceName = "",
    offset = 0,
    limit = 20,
    signal,
  } = {},
) {
  const query = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  });

  // Keep frontend field names readable while matching backend parameters.
  addQueryValue(query, "search", search);
  addQueryValue(query, "status", status);
  addQueryValue(query, "severity", severity);
  addQueryValue(query, "service_name", serviceName);

  return apiRequest(`${INCIDENTS_PATH}?${query}`, {
    accessToken,
    signal,
  });
}


/**
 * Return one Incident by identifier.
 */
export function getIncident(
  accessToken,
  incidentId,
  { signal } = {},
) {
  return apiRequest(
    `${INCIDENTS_PATH}/${encodeURIComponent(incidentId)}`,
    {
      accessToken,
      signal,
    },
  );
}


/**
 * Create a new operational Incident.
 */
export function createIncident(accessToken, incidentData) {
  return apiRequest(INCIDENTS_PATH, {
    method: "POST",
    accessToken,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(
      createIncidentPayload(incidentData),
    ),
  });
}


/**
 * Apply selected changes to an existing Incident.
 */
export function updateIncident(
  accessToken,
  incidentId,
  incidentData,
) {
  return apiRequest(
    `${INCIDENTS_PATH}/${encodeURIComponent(incidentId)}`,
    {
      method: "PATCH",
      accessToken,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(
        createIncidentPayload(incidentData),
      ),
    },
  );
}


/**
 * Delete an Incident as an administrator.
 */
export function deleteIncident(accessToken, incidentId) {
  return apiRequest(
    `${INCIDENTS_PATH}/${encodeURIComponent(incidentId)}`,
    {
      method: "DELETE",
      accessToken,
    },
  );
}
