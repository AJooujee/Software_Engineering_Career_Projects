/**
 * Tests for the frontend authentication API contract.
 */

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import {
  getCurrentUser,
  loginUser,
  registerUser,
} from "./auth.js";


function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}


describe("authentication API", () => {
  let fetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("sends normalized registration data as JSON", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: "user-id",
        email: "aj@example.com",
        full_name: "AJ Pipattanakun",
        role: "viewer",
      }, 201),
    );

    await registerUser({
      email: "  AJ@Example.com ",
      fullName: "  AJ Pipattanakun  ",
      password: "SecurePassword123!",
    });

    const [requestUrl, requestOptions] = fetchMock.mock.calls[0];

    expect(requestUrl).toBe(
      "http://127.0.0.1:8000/api/auth/register",
    );
    expect(requestOptions.method).toBe("POST");
    expect(requestOptions.headers.get("Content-Type")).toBe(
      "application/json",
    );
    expect(JSON.parse(requestOptions.body)).toEqual({
      email: "aj@example.com",
      full_name: "AJ Pipattanakun",
      password: "SecurePassword123!",
    });
  });

  test("sends login credentials using the OAuth2 form contract", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        access_token: "signed-token",
        token_type: "bearer",
        expires_in: 1800,
      }),
    );

    const tokenResponse = await loginUser({
      email: " AJ@Example.com ",
      password: "SecurePassword123!",
    });

    const [requestUrl, requestOptions] = fetchMock.mock.calls[0];

    expect(requestUrl).toBe(
      "http://127.0.0.1:8000/api/auth/token",
    );
    expect(requestOptions.method).toBe("POST");
    expect(requestOptions.body).toBeInstanceOf(URLSearchParams);
    expect(requestOptions.body.get("username")).toBe(
      "aj@example.com",
    );
    expect(requestOptions.body.get("password")).toBe(
      "SecurePassword123!",
    );
    expect(tokenResponse.access_token).toBe("signed-token");
  });

  test("uses a bearer token when loading the current user", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: "user-id",
        email: "aj@example.com",
        full_name: "AJ Pipattanakun",
        role: "admin",
      }),
    );

    await getCurrentUser("signed-token");

    const [requestUrl, requestOptions] = fetchMock.mock.calls[0];

    expect(requestUrl).toBe(
      "http://127.0.0.1:8000/api/auth/me",
    );
    expect(requestOptions.headers.get("Authorization")).toBe(
      "Bearer signed-token",
    );
  });

  test("returns the backend message for invalid credentials", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          detail: "Incorrect email or password.",
        },
        401,
      ),
    );

    await expect(
      loginUser({
        email: "aj@example.com",
        password: "incorrect-password",
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      message: "Incorrect email or password.",
    });
  });
});
