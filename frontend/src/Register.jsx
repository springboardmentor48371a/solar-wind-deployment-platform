import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function Register({ onSuccess }) {
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "Renewable Energy Planner",
  });
  const [message, setMessage] = useState("");

  const handleChange = (event) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      if (response.ok) {
        setMessage("Registration successful!");
        onSuccess?.();
      } else {
        setMessage(data.detail || "Registration failed");
      }
    } catch {
      setMessage("Unable to connect to backend");
    }
  };

  return (
    <section className="panel panel-register auth-card">
      <div className="auth-card-heading">
        <h2>Solar &amp; Wind Platform</h2>
        <p>Renewable energy intelligence</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="field-grid">
          <label className="field field-wide">Full name
            <input type="text" name="full_name" placeholder="Your full name" value={formData.full_name} onChange={handleChange} required />
          </label>
          <label className="field field-wide">Email address
            <input type="email" name="email" placeholder="you@example.com" value={formData.email} onChange={handleChange} required />
          </label>
          <label className="field field-wide">Password
            <input type="password" name="password" placeholder="Create a password" value={formData.password} onChange={handleChange} required />
          </label>
          <label className="field field-wide">Role
            <select name="role" value={formData.role} onChange={handleChange} required>
              <option>Renewable Energy Planner</option>
              <option>GIS Analyst</option>
              <option>Project Manager</option>
              <option>Administrator</option>
            </select>
          </label>
        </div>
        <button className="button button-primary" type="submit">Create account <span aria-hidden="true">→</span></button>
      </form>

      <p className="helper-text">Already have an account? <button type="button" className="text-button" onClick={onSuccess}>Sign in</button></p>

      {message && <p className="form-message" aria-live="polite">{message}</p>}
    </section>
  );
}

export default Register;
