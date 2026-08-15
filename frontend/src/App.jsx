import { useState } from "react";

import Login from "./login";
import Dashboard from "./Dashboard";

import SolarAnalysis from "./SolarAnalysis";
import WindAnalysis from "./windanalysis";
import SiteSelection from "./siteselection";
import Predictions from "./predictions";
import Reports from "./reports";

import "./App.css";

function App() {

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("solarWindUser");

    return savedUser
      ? JSON.parse(savedUser)
      : null;
  });

  const [page, setPage] = useState("dashboard");


  // =========================
  // LOGIN
  // =========================

  const handleLogin = (loggedInUser) => {

    setUser(loggedInUser);

    localStorage.setItem(
      "solarWindUser",
      JSON.stringify(loggedInUser)
    );

    setPage("dashboard");
  };


  // =========================
  // LOGOUT
  // =========================

  const handleLogout = () => {

    localStorage.removeItem("solarWindUser");

    setUser(null);

    setPage("dashboard");
  };


  // =========================
  // NOT LOGGED IN
  // =========================

  if (!user) {

    return (
      <Login
        onLogin={handleLogin}
      />
    );
  }


  // =========================
  // PAGE NAVIGATION
  // =========================

  const renderPage = () => {

    switch (page) {

      case "solar":

        return (
          <SolarAnalysis
            user={user}
            onBack={() => setPage("dashboard")}
          />
        );


      case "wind":

        return (
          <WindAnalysis
            user={user}
            onBack={() => setPage("dashboard")}
          />
        );


      case "sites":

        return (
          <SiteSelection
            user={user}
            onBack={() => setPage("dashboard")}
          />
        );


      case "predictions":

        return (
          <Predictions
            user={user}
            onBack={() => setPage("dashboard")}
          />
        );


      case "reports":

        return (
          <Reports
            user={user}
            onBack={() => setPage("dashboard")}
          />
        );


      case "dashboard":

      default:

        return (
          <Dashboard
            user={user}
            onLogout={handleLogout}
            onNavigate={setPage}
          />
        );
    }
  };


  return (
    <div className="app">

      {renderPage()}

    </div>
  );
}

export default App;