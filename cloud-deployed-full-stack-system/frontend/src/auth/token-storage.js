/**
 * Session-scoped storage for the JWT access token.
 */

const ACCESS_TOKEN_KEY = "cloud-operations-access-token";


/**
 * Return browser session storage when running in a browser.
 */
function getSessionStorage() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.sessionStorage;
}


/**
 * Load the access token for the current browser tab.
 */
export function loadAccessToken() {
  return getSessionStorage()?.getItem(ACCESS_TOKEN_KEY) ?? null;
}


/**
 * Save an access token for the lifetime of the current browser tab.
 */
export function saveAccessToken(accessToken) {
  getSessionStorage()?.setItem(ACCESS_TOKEN_KEY, accessToken);
}


/**
 * Remove the access token during logout or failed authentication.
 */
export function removeAccessToken() {
  getSessionStorage()?.removeItem(ACCESS_TOKEN_KEY);
}
