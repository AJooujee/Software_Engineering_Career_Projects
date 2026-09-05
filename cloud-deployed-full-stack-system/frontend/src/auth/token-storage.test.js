/**
 * Tests for session-scoped JWT storage.
 */

import {
  beforeEach,
  describe,
  expect,
  test,
} from "vitest";

import {
  loadAccessToken,
  removeAccessToken,
  saveAccessToken,
} from "./token-storage.js";


describe("access token storage", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  test("returns null when the browser session has no token", () => {
    expect(loadAccessToken()).toBeNull();
  });

  test("saves and reloads the token from session storage", () => {
    saveAccessToken("signed-access-token");

    expect(loadAccessToken()).toBe("signed-access-token");
  });

  test("removes the token during logout", () => {
    saveAccessToken("signed-access-token");

    removeAccessToken();

    expect(loadAccessToken()).toBeNull();
  });
});
