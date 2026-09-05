/**
 * Route guard for pages intended only for signed-out visitors.
 */

import { Navigate, Outlet } from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";
import {
  AuthenticationLoading,
  SessionError,
} from "../components/RouteStatus.jsx";


export function PublicOnlyRoute() {
  const {
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

  if (status === "authenticated") {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
