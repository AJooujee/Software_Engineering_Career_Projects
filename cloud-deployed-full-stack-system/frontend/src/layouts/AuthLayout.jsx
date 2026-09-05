/**
 * Shared presentation for public authentication pages.
 */

import { Link, Outlet } from "react-router";


export function AuthLayout() {
  return (
    <main className="auth-layout">
      <section className="auth-layout__brand">
        <Link className="brand-link" to="/">
          <span className="brand-mark" aria-hidden="true">
            CO
          </span>

          <span>Cloud Operations</span>
        </Link>

        <div className="auth-layout__introduction">
          <p className="eyebrow">Operational intelligence</p>
          <h1>Keep every service visible and every response coordinated.</h1>
          <p>
            A secure workspace for monitoring system health,
            managing incidents, and coordinating operational teams.
          </p>
        </div>

        <ul className="auth-layout__features">
          <li>Role-based workspace access</li>
          <li>Persistent incident management</li>
          <li>Cloud-ready service monitoring</li>
        </ul>
      </section>

      <section className="auth-layout__content">
        <div className="auth-card">
          <Outlet />
        </div>

        <p className="auth-layout__footer">
          Cloud Operations Platform
        </p>
      </section>
    </main>
  );
}
