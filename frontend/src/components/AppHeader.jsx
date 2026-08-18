import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";

export default function AppHeader() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Operations workspace</p>
        <h1>Renewable Energy Deployment</h1>
      </div>
      <div className="user-menu">
        <div>
          <strong>{currentUser.full_name}</strong>
          <span>{currentUser.role}</span>
        </div>
        <button type="button" className="secondary-button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}
