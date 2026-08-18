import { NavLink } from "react-router-dom";

import { navigationItems } from "../config/navigation.js";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Sidebar() {
  const { currentUser } = useAuth();
  const visibleItems = navigationItems.filter((item) =>
    item.allowedRoles.includes(currentUser.role),
  );

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="energy-mark" aria-hidden="true">
          <span />
        </span>
        <div>
          <strong>RENEWGRID</strong>
          <small>Renewable Energy Deployment Platform</small>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Application navigation">
        {visibleItems.map((item) =>
          item.path ? (
            <NavLink
              key={item.label}
              to={item.path}
              className={({ isActive }) => (isActive ? "active" : undefined)}
            >
              {item.label}
            </NavLink>
          ) : (
            <span key={item.label} className="sidebar-nav-disabled" aria-disabled="true">
              {item.label}
              <small>{item.disabledText}</small>
            </span>
          ),
        )}
      </nav>
    </aside>
  );
}
