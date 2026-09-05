/**
 * Role-aware placeholder for the Phase 5 incident workflow.
 */

import { useAuth } from "../auth/AuthContext.jsx";
import { PageHeader } from "../components/PageHeader.jsx";


export function IncidentsPage() {
  const { user } = useAuth();

  const canModifyIncidents = ["operator", "admin"].includes(user?.role);
  const canDeleteIncidents = user?.role === "admin";

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Incident management"
        title="Operational incidents"
        description={
          "Review your current incident permissions before the "
          + "complete workflow arrives in Phase 5."
        }
      />

      <section className="content-panel">
        <div className="content-panel__heading">
          <div>
            <p className="eyebrow">Access summary</p>
            <h2>Your incident permissions</h2>
          </div>

          <span className="status-pill">Phase 5</span>
        </div>

        <div className="permission-list">
          <div className="permission-list__item">
            <div>
              <strong>View incidents</strong>
              <p>List and inspect operational incidents.</p>
            </div>

            <span className="status-pill status-pill--success">
              Available
            </span>
          </div>

          <div className="permission-list__item">
            <div>
              <strong>Create and update incidents</strong>
              <p>Requires operator or administrator access.</p>
            </div>

            <span
              className={
                canModifyIncidents
                  ? "status-pill status-pill--success"
                  : "status-pill status-pill--restricted"
              }
            >
              {canModifyIncidents ? "Available" : "Restricted"}
            </span>
          </div>

          <div className="permission-list__item">
            <div>
              <strong>Delete incidents</strong>
              <p>Requires administrator access.</p>
            </div>

            <span
              className={
                canDeleteIncidents
                  ? "status-pill status-pill--success"
                  : "status-pill status-pill--restricted"
              }
            >
              {canDeleteIncidents ? "Available" : "Restricted"}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
