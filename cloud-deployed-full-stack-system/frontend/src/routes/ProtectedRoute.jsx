/**
 * Route guard for authenticated and role-restricted pages.
 */

import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";
import {
  AuthenticationLoading,
  SessionError,
} from "../components/RouteStatus.jsx";


export function ProtectedRoute({ allowedRoles = [] }) {
  const location = useLocation();
  const {
    user,
    status,
    error,
    retrySession,
    logout,
  } = useAuth();

  if (status === "checking") {
    return <AuthenticationLoading />;
  }

  if (status === "error") {
    return (
      <SessionError
        message={error}
        onRetry={retrySession}
        onLogout={logout}
      />
    );
  }

  if (status !== "authenticated" || !user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location }}
      />
    );
  }

  if (
    allowedRoles.length > 0
    && !allowedRoles.includes(user.role)
  ) {
    return <Navigate to="/forbidden" replace />;
  }

  return <Outlet />;
}
