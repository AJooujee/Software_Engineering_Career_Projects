/**
 * Operational dashboard requests sent to the FastAPI backend.
 */

import { apiRequest } from "./client.js";


const DASHBOARD_SUMMARY_PATH = "/api/dashboard/summary";


/**
 * Return the current Incident metrics for an authenticated user.
 */
export function getDashboardSummary(
  accessToken,
  { signal } = {},
) {
  return apiRequest(DASHBOARD_SUMMARY_PATH, {
    accessToken,
    signal,
  });
}
