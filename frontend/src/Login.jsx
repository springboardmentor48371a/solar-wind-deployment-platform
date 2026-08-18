import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function Login({ onSuccess, onSwitchToRegister }) {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("access_token", data.access_token);
        setMessage("Login successful!");
        onSuccess?.();
      } else {
        setMessage(data.detail || "Login failed");
      }
    } catch {
      setMessage("Unable to connect to backend");
    }
  };

  return (
    <section className="panel panel-login auth-card">
      <div className="auth-card-heading">
        <h2>Solar &amp; Wind Platform</h2>
        <p>Welcome back</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="field-grid">
          <label className="field field-wide">Email address
            <input type="email" name="email" placeholder="you@example.com" value={formData.email} onChange={handleChange} required />
          </label>
          <label className="field field-wide">Password
            <input type="password" name="password" placeholder="Enter your password" value={formData.password} onChange={handleChange} required />
          </label>
        </div>
        <button className="button button-secondary" type="submit">Sign in <span aria-hidden="true">→</span></button>
      </form>

      <p className="helper-text">Need an account? <button type="button" className="text-button" onClick={onSwitchToRegister}>Create one here</button></p>

      {message && <p className="form-message" aria-live="polite">{message}</p>}
    </section>
  );
}

export default Login;
