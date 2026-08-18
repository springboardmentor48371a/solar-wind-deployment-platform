import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./routes/ProtectedRoute.jsx";
import RoleProtectedRoute from "./routes/RoleProtectedRoute.jsx";
import AppLayout from "./layouts/AppLayout.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import GoogleCallbackPage from "./pages/GoogleCallbackPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import CreateProjectPage from "./pages/CreateProjectPage.jsx";
import EditProjectPage from "./pages/EditProjectPage.jsx";
import ProjectDetailPage from "./pages/ProjectDetailPage.jsx";
import ProjectsPage from "./pages/ProjectsPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import RoleCheckPage from "./pages/RoleCheckPage.jsx";
import CreateSitePage from "./pages/CreateSitePage.jsx";
import EditSitePage from "./pages/EditSitePage.jsx";
import SiteDetailPage from "./pages/SiteDetailPage.jsx";
import UnauthorizedPage from "./pages/UnauthorizedPage.jsx";
import {
  ALL_ROLES,
  ROLE_ADMIN,
  ROLE_GIS_ANALYST,
  ROLE_PLANNER,
  ROLE_PROJECT_MANAGER,
} from "./config/roles.js";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/app" element={<DashboardPage />} />
          <Route path="/app/dashboard" element={<DashboardPage />} />
          <Route path="/app/projects" element={<ProjectsPage />} />
          <Route path="/app/projects/new" element={<CreateProjectPage />} />
          <Route path="/app/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/app/projects/:projectId/edit" element={<EditProjectPage />} />
          <Route
            path="/app/projects/:projectId/sites/new"
            element={<CreateSitePage />}
          />
          <Route
            path="/app/projects/:projectId/sites/:siteId"
            element={<SiteDetailPage />}
          />
          <Route
            path="/app/projects/:projectId/sites/:siteId/edit"
            element={<EditSitePage />}
          />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route element={<RoleProtectedRoute allowedRoles={[ROLE_PLANNER]} />}>
            <Route
              path="/app/planner-check"
              element={<RoleCheckPage roleName={ROLE_PLANNER} />}
            />
          </Route>
          <Route element={<RoleProtectedRoute allowedRoles={[ROLE_GIS_ANALYST]} />}>
            <Route
              path="/app/gis-check"
              element={<RoleCheckPage roleName={ROLE_GIS_ANALYST} />}
            />
          </Route>
          <Route
            element={<RoleProtectedRoute allowedRoles={[ROLE_PROJECT_MANAGER]} />}
          >
            <Route
              path="/app/project-manager-check"
              element={<RoleCheckPage roleName={ROLE_PROJECT_MANAGER} />}
            />
          </Route>
          <Route element={<RoleProtectedRoute allowedRoles={[ROLE_ADMIN]} />}>
            <Route
              path="/app/admin-check"
              element={<RoleCheckPage roleName={ROLE_ADMIN} />}
            />
          </Route>
          <Route element={<RoleProtectedRoute allowedRoles={ALL_ROLES} />}>
            <Route
              path="/app/role-check"
              element={<RoleCheckPage roleName="Any authenticated role" />}
            />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
