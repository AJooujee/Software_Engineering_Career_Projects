/**
 * Fallback page for an unknown frontend route.
 */

import { Link } from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";


export function NotFoundPage() {
  const { isAuthenticated } = useAuth();

  return (
    <main className="route-status">
      <div className="route-status__card">
        <p className="eyebrow">Error 404</p>
        <h1>Page not found</h1>
        <p>
          The requested page does not exist in the Cloud Operations
          application.
        </p>

        <Link
          className="button-primary button-inline"
          to={isAuthenticated ? "/dashboard" : "/login"}
        >
          {isAuthenticated ? "Return to dashboard" : "Go to sign in"}
        </Link>
      </div>
    </main>
  );
}
