/**
 * Administrator-only placeholder for user access management.
 */

import { PageHeader } from "../components/PageHeader.jsx";


export function UsersPage() {
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Administration"
        title="User access"
        description={
          "Manage account roles and active status through the "
          + "administrator-only workspace."
        }
      />

      <section className="content-panel">
        <div className="content-panel__heading">
          <div>
            <p className="eyebrow">Protected route</p>
            <h2>Administrator access verified</h2>
          </div>

          <span className="status-pill status-pill--success">
            Admin
          </span>
        </div>

        <p>
          The backend user-management API is ready. A complete user
          management table will be added after the core frontend
          application layout is established.
        </p>
      </section>
    </div>
  );
}
