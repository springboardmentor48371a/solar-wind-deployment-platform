import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";

export default function GoogleCallbackPage() {
  const { loginWithToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const hasStarted = useRef(false);

  useEffect(() => {
    async function completeLogin() {
      if (hasStarted.current) {
        return;
      }
      hasStarted.current = true;

      const params = new URLSearchParams(window.location.hash.slice(1));
      const accessToken = params.get("access_token");

      if (!accessToken) {
        setError("Google authentication did not return an application token.");
        return;
      }

      try {
        await loginWithToken(accessToken);
        window.history.replaceState(null, "", "/auth/google/callback");
        navigate("/app", { replace: true });
      } catch (requestError) {
        setError("Unable to complete Google authentication.");
      }
    }

    completeLogin();
  }, [loginWithToken, navigate]);

  if (error) {
    return (
      <main className="auth-layout">
        <section className="auth-panel">
          <p className="eyebrow">Google authentication</p>
          <h1>Sign in failed</h1>
          <p className="form-error">{error}</p>
          <p className="form-link">
            <Link to="/login">Back to login</Link>
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <p>Completing Google sign in...</p>
    </main>
  );
}
