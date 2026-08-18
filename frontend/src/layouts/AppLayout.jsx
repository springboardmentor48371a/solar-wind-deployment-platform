import { Outlet } from "react-router-dom";

import AppHeader from "../components/AppHeader.jsx";
import Sidebar from "../components/Sidebar.jsx";

export default function AppLayout() {
  return (
    <div className="shell">
      <Sidebar />
      <div className="shell-main">
        <AppHeader />
        <main className="content-area">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

