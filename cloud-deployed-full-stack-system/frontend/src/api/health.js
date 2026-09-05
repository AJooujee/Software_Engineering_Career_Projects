/**
 * Backend health-check requests.
 */

import { apiRequest } from "./client.js";


/**
 * Return the current health information from the FastAPI service.
 */
export function getBackendHealth({ signal } = {}) {
  return apiRequest("/health", {
    signal,
  });
}
