import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";
import { getGoogleLoginUrl } from "../services/apiClient.js";

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [error, setError] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("oauth_error")
      ? "Google sign in was cancelled or failed."
      : "";
  });
  const [submitting, setSubmitting] = useState(false);

  const redirectTo = location.state?.from?.pathname ?? "/app";

  if (isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  function updateField(event) {
    setFormData((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(formData.email, formData.password);
      navigate(redirectTo, { replace: true });
    } catch (requestError) {
      setError("Unable to log in. Check your email and password.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleGoogleLogin() {
    window.location.assign(getGoogleLoginUrl());
  }

  return (
    <main className="auth-layout">
      <section className="auth-visual" aria-label="Renewable energy platform">
        <div className="energy-mark large" aria-hidden="true">
          <span />
        </div>
        <p className="eyebrow">Solar, wind and site planning</p>
        <h1>Renewable Energy Deployment Platform</h1>
        <p>
          Plan smarter. Harness renewable energy. Build a sustainable future.
        </p>
        <div className="energy-motifs" aria-hidden="true">
          <span className="motif solar-motif">Solar</span>
          <span className="motif wind-motif">Wind</span>
          <span className="motif location-motif">Site planning</span>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-card-brand">
          <div className="energy-mark" aria-hidden="true">
            <span />
          </div>
          <div>
            <strong>RENEWGRID</strong>
            <small>Deployment workspace</small>
          </div>
        </div>
        <p className="eyebrow">Welcome back</p>
        <h2>Sign in to your workspace</h2>
        <form onSubmit={handleSubmit}>
          <label>
            Email / Username
            <input
              name="email"
              type="email"
              value={formData.email}
              onChange={updateField}
              autoComplete="email"
              required
            />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              value={formData.password}
              onChange={updateField}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <div className="auth-divider">or</div>
        <button type="button" className="google-button" onClick={handleGoogleLogin}>
          Continue with Google
        </button>
        <p className="form-link">
          Need an account? <Link to="/register">Register</Link>
        </p>
      </section>
    </main>
  );
}
