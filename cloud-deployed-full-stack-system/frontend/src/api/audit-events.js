/**
 * Administrator audit-history requests sent to the FastAPI backend.
 */

import { apiRequest } from "./client.js";


const AUDIT_EVENTS_PATH = "/api/audit-events";


/**
 * Return a paginated collection of immutable audit events.
 */
export function listAuditEvents(
  accessToken,
  {
    offset = 0,
    limit = 50,
    signal,
  } = {},
) {
  const query = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  });

  return apiRequest(`${AUDIT_EVENTS_PATH}?${query}`, {
    accessToken,
    signal,
  });
}
