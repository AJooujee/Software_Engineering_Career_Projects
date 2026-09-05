/**
 * Authentication requests sent to the FastAPI backend.
 */

import { apiRequest } from "./client.js";


/**
 * Register a new viewer account.
 */
export function registerUser({
  email,
  fullName,
  password,
}) {
  return apiRequest("/api/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      full_name: fullName.trim(),
      password,
    }),
  });
}


/**
 * Exchange an email and password for an access token.
 */
export function loginUser({ email, password }) {
  const loginForm = new URLSearchParams();

  // FastAPI's OAuth2 form expects the email in the username field.
  loginForm.set("username", email.trim().toLowerCase());
  loginForm.set("password", password);

  return apiRequest("/api/auth/token", {
    method: "POST",
    body: loginForm,
  });
}


/**
 * Load the authenticated user's current database-backed profile.
 */
export function getCurrentUser(accessToken, { signal } = {}) {
  return apiRequest("/api/auth/me", {
    accessToken,
    signal,
  });
}
