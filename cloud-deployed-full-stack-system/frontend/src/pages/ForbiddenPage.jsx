/**
 * Explain when an authenticated user lacks a required role.
 */

import { Link } from "react-router";

import { PageHeader } from "../components/PageHeader.jsx";


export function ForbiddenPage() {
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Access restricted"
        title="You do not have permission to view this page"
        description={
          "Your account is authenticated, but your current role "
          + "does not include access to this resource."
        }
      />

      <section className="content-panel">
        <p>
          Contact an administrator if you believe your role should
          include this permission.
        </p>

        <Link
          className="button-primary button-inline"
          to="/dashboard"
        >
          Return to dashboard
        </Link>
      </section>
    </div>
  );
}
