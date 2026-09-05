/**
 * Route configuration for the Cloud Operations frontend.
 */

import {
  Navigate,
  Route,
  Routes,
} from "react-router";

import { AppLayout } from "./layouts/AppLayout.jsx";
import { AuthLayout } from "./layouts/AuthLayout.jsx";
import { DashboardPage } from "./pages/DashboardPage.jsx";
import { ForbiddenPage } from "./pages/ForbiddenPage.jsx";
import { IncidentsPage } from "./pages/IncidentsPage.jsx";
import { LoginPage } from "./pages/LoginPage.jsx";
import { NotFoundPage } from "./pages/NotFoundPage.jsx";
import { RegisterPage } from "./pages/RegisterPage.jsx";
import { UsersPage } from "./pages/UsersPage.jsx";
import { ProtectedRoute } from "./routes/ProtectedRoute.jsx";
import { PublicOnlyRoute } from "./routes/PublicOnlyRoute.jsx";


function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route
            index
            element={<Navigate to="/dashboard" replace />}
          />

          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="forbidden" element={<ForbiddenPage />} />

          <Route
            element={
              <ProtectedRoute allowedRoles={["admin"]} />
            }
          >
            <Route path="users" element={<UsersPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}


export default App;
