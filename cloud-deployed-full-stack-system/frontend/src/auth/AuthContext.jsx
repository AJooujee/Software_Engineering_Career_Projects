/**
 * Application-wide authentication state and actions.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { ApiError } from "../api/client.js";
import {
  getCurrentUser,
  loginUser,
  registerUser,
} from "../api/auth.js";
import {
  loadAccessToken,
  removeAccessToken,
  saveAccessToken,
} from "./token-storage.js";


const AuthContext = createContext(null);


/**
 * Return whether the API rejected the stored authentication token.
 */
function isRejectedToken(error) {
  return (
    error instanceof ApiError
    && (error.status === 401 || error.status === 403)
  );
}


/**
 * Provide authentication state and actions to the React application.
 */
export function AuthProvider({ children }) {
  const [initialAccessToken] = useState(loadAccessToken);
  const [accessToken, setAccessToken] = useState(initialAccessToken);
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(
    initialAccessToken ? "checking" : "anonymous",
  );
  const [error, setError] = useState(null);

  const clearSession = useCallback(() => {
    removeAccessToken();
    setAccessToken(null);
    setUser(null);
    setError(null);
    setStatus("anonymous");
  }, []);

  const verifyStoredSession = useCallback(
    async (token, { signal } = {}) => {
      setStatus("checking");
      setError(null);

      try {
        const currentUser = await getCurrentUser(token, { signal });

        setAccessToken(token);
        setUser(currentUser);
        setStatus("authenticated");

        return currentUser;
      } catch (requestError) {
        if (requestError.name === "AbortError") {
          return null;
        }

        if (isRejectedToken(requestError)) {
          clearSession();
          return null;
        }

        setUser(null);
        setError(requestError.message);
        setStatus("error");

        return null;
      }
    },
    [clearSession],
  );

  useEffect(() => {
    if (!initialAccessToken) {
      return undefined;
    }

    const controller = new AbortController();

    verifyStoredSession(initialAccessToken, {
      signal: controller.signal,
    });

    return () => controller.abort();
  }, [initialAccessToken, verifyStoredSession]);

  const login = useCallback(async ({ email, password }) => {
    setError(null);

    const tokenResponse = await loginUser({
      email,
      password,
    });

    const currentUser = await getCurrentUser(
      tokenResponse.access_token,
    );

    saveAccessToken(tokenResponse.access_token);
    setAccessToken(tokenResponse.access_token);
    setUser(currentUser);
    setStatus("authenticated");

    return currentUser;
  }, []);

  const register = useCallback(
    async ({ email, fullName, password }) => {
      await registerUser({
        email,
        fullName,
        password,
      });

      return login({
        email,
        password,
      });
    },
    [login],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const retrySession = useCallback(async () => {
    const storedToken = loadAccessToken();

    if (!storedToken) {
      clearSession();
      return null;
    }

    return verifyStoredSession(storedToken);
  }, [clearSession, verifyStoredSession]);

  const contextValue = useMemo(
    () => ({
      accessToken,
      user,
      status,
      error,
      isAuthenticated: status === "authenticated",
      login,
      register,
      logout,
      retrySession,
    }),
    [
      accessToken,
      user,
      status,
      error,
      login,
      register,
      logout,
      retrySession,
    ],
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}


/**
 * Return the authentication context for a descendant component.
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
