/**
 * Shared HTTP client for the Cloud Operations backend API.
 */

// Use the configured backend address or the local FastAPI server.
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");


/**
 * Represent an unsuccessful response from the backend API.
 */
export class ApiError extends Error {
  constructor(message, { status = 0, details = null, cause } = {}) {
    super(message, { cause });

    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}


/**
 * Read JSON or text content without failing on an empty response body.
 */
async function readResponsePayload(response) {
  if (response.status === 204) {
    return null;
  }

  const responseText = await response.text();

  if (!responseText) {
    return null;
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(responseText);
    } catch {
      return responseText;
    }
  }

  return responseText;
}


/**
 * Convert FastAPI error responses into a message suitable for the UI.
 */
function getErrorMessage(payload, statusCode) {
  if (typeof payload === "string" && payload) {
    return payload;
  }

  if (typeof payload?.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload?.detail)) {
    return payload.detail
      .map((issue) => {
        const field = Array.isArray(issue.loc)
          ? issue.loc.filter((item) => item !== "body").join(".")
          : "";

        return field ? `${field}: ${issue.msg}` : issue.msg;
      })
      .join(" ");
  }

  return `The API request failed with status ${statusCode}.`;
}


/**
 * Send one request to the backend and return its parsed response body.
 */
export async function apiRequest(
  path,
  {
    accessToken,
    headers: suppliedHeaders,
    ...requestOptions
  } = {},
) {
  const headers = new Headers(suppliedHeaders);

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...requestOptions,
      headers,
    });
  } catch (error) {
    if (error.name === "AbortError") {
      throw error;
    }

    throw new ApiError("Unable to connect to the backend API.", {
      cause: error,
    });
  }

  const payload = await readResponsePayload(response);

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(payload, response.status),
      {
        status: response.status,
        details: payload,
      },
    );
  }

  return payload;
}
