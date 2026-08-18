import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";

export default function UnauthorizedPage() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <section className="empty-state">
      <p className="eyebrow">Access denied</p>
      <h2>You do not have permission to view this page.</h2>
      {currentUser && (
        <p>
          Signed in as {currentUser.full_name} with the {currentUser.role} role.
        </p>
      )}
      <div className="action-row">
        <Link className="button-link" to="/app/dashboard">
          Back to dashboard
        </Link>
        <button type="button" className="secondary-button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </section>
  );
}

