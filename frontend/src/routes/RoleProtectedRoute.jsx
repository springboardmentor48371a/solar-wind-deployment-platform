import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";

export default function RoleProtectedRoute({ allowedRoles, children }) {
  const { currentUser, isAuthenticated, loading } = useAuth();
  const location = useLocation();
  const roleIsAllowed = allowedRoles?.includes(currentUser?.role);

  if (loading) {
    return <main className="page-shell">Loading...</main>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!roleIsAllowed) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children ?? <Outlet />;
}
