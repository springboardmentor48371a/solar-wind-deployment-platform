import React, { useState } from "react";

import Login from "./login";
import Dashboard from "./Dashboard";
import SolarAnalysis from "./SolarAnalysis";
import WindAnalysis from "./windanalysis";
import SiteSelection from "./siteselection";
import Predictions from "./predictions";
import Reports from "./reports";

function App() {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const [path, setPath] = useState(window.location.pathname);

  const navigate = (newPath) => {
    window.history.pushState({}, "", newPath);
    setPath(newPath);
  };

  const handleLogin = (loggedInUser) => {
    const currentUser = loggedInUser || {
      name: "User",
      email: "user@example.com",
    };

    localStorage.setItem("user", JSON.stringify(currentUser));
    setUser(currentUser);
    navigate("/dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    sessionStorage.clear();
    setUser(null);
    navigate("/");
  };

  // LOGIN
  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  // DASHBOARD
  if (path === "/" || path === "/dashboard") {
    return <Dashboard user={user} onLogout={handleLogout} />;
  }

  // SOLAR
  if (path === "/solar-analysis") {
    return <SolarAnalysis user={user} onBack={() => navigate("/dashboard")} />;
  }

  // WIND
  if (path === "/wind-analysis") {
    return <WindAnalysis user={user} onBack={() => navigate("/dashboard")} />;
  }

  // SITE SELECTION
  if (path === "/site-selection") {
    return <SiteSelection user={user} onBack={() => navigate("/dashboard")} />;
  }

  // PREDICTIONS
  if (path === "/predictions") {
    return <Predictions user={user} onBack={() => navigate("/dashboard")} />;
  }

  // REPORTS
  if (path === "/reports") {
    return <Reports user={user} onBack={() => navigate("/dashboard")} />;
  }

  return <Dashboard user={user} onLogout={handleLogout} />;
}

export default App;