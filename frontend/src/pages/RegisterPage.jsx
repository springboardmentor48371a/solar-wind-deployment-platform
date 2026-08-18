import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import RoleSelect from "../components/RoleSelect.jsx";
import { useAuth } from "../auth/AuthContext.jsx";

const initialFormData = {
  full_name: "",
  email: "",
  password: "",
  role: "",
  phone_number: "",
  organization: "",
};

export default function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState(initialFormData);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [validationError, setValidationError] = useState("");
  const [submitting, setSubmitting] = useState(false);

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
    setSuccess("");
    setValidationError("");

    if (!formData.role) {
      setValidationError("Role is required.");
      return;
    }

    setSubmitting(true);

    try {
      await register({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        role: formData.role,
        phone_number: formData.phone_number || null,
        organization: formData.organization || null,
      });
      setSuccess("Registration successful. Redirecting to login...");
      setTimeout(() => navigate("/login", { replace: true }), 900);
    } catch (requestError) {
      setError(requestError.message || "Registration failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-visual" aria-label="Renewable energy planning">
        <div className="energy-mark large" aria-hidden="true">
          <span />
        </div>
        <p className="eyebrow">Clean energy operations</p>
        <h1>Build your renewable deployment workspace</h1>
        <p>
          Coordinate projects, evaluate candidate sites and prepare clean-energy
          assets from one professional workspace.
        </p>
        <div className="energy-motifs" aria-hidden="true">
          <span className="motif solar-motif">Solar</span>
          <span className="motif wind-motif">Wind</span>
          <span className="motif location-motif">Location</span>
        </div>
      </section>

      <section className="auth-panel wide">
        <div className="auth-card-brand">
          <div className="energy-mark" aria-hidden="true">
            <span />
          </div>
          <div>
            <strong>RENEWGRID</strong>
            <small>Renewable Energy Deployment Platform</small>
          </div>
        </div>
        <p className="eyebrow">Create your account</p>
        <h2>Start planning renewable sites</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              Full Name
              <input
                name="full_name"
                value={formData.full_name}
                onChange={updateField}
                autoComplete="name"
                maxLength="100"
                required
              />
            </label>
            <label>
              Email
              <input
                name="email"
                type="email"
                value={formData.email}
                onChange={updateField}
                autoComplete="email"
                maxLength="150"
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
                autoComplete="new-password"
                minLength="8"
                maxLength="72"
                required
              />
            </label>
            <label>
              Phone
              <input
                name="phone_number"
                value={formData.phone_number}
                onChange={updateField}
                autoComplete="tel"
                maxLength="20"
              />
            </label>
            <label>
              Organization
              <input
                name="organization"
                value={formData.organization}
                onChange={updateField}
                autoComplete="organization"
                maxLength="150"
              />
            </label>
            <label>
              Role
              <RoleSelect
                name="role"
                value={formData.role}
                onChange={updateField}
                required
              />
            </label>
          </div>
          <p className="helper-text">
            Your role determines the tools and workspace available to you.
          </p>
          {(validationError || error) && (
            <p className="form-error">{validationError || error}</p>
          )}
          {success && <p className="form-success">{success}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Creating account..." : "Create account"}
          </button>
        </form>
        <p className="form-link">
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
