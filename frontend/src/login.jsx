import { useState } from "react";
import "./login.css";

function Login({ onLogin }) {
  const [mode, setMode] = useState("login");

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const endpoint =
        mode === "login"
          ? "http://127.0.0.1:8000/login"
          : "http://127.0.0.1:8000/register";

      const body =
        mode === "login"
          ? {
              email: form.email.trim(),
              password: form.password,
            }
          : {
              name: form.name.trim(),
              email: form.email.trim(),
              password: form.password,
            };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      // =========================
      // LOGIN SUCCESS
      // =========================
      if (mode === "login") {
        const loggedUser = data.user;

        // Save complete user information
        localStorage.setItem(
          "user",
          JSON.stringify(loggedUser)
        );

        localStorage.setItem(
          "user_id",
          String(loggedUser.id)
        );

        localStorage.setItem(
          "user_name",
          loggedUser.name
        );

        localStorage.setItem(
          "user_email",
          loggedUser.email
        );

        // Send user to App
        onLogin(loggedUser);
      }

      // =========================
      // REGISTER SUCCESS
      // =========================
      else {
        alert("Registration successful. Please login.");

        setMode("login");

        setForm({
          name: "",
          email: form.email,
          password: "",
        });

        setShowPassword(false);
      }
    } catch (err) {
      console.error("LOGIN ERROR:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">

      <div className="login-card">

        {/* LOGO */}
        <div className="login-logo">
          <span>☀️</span>
          <span>🌬️</span>
        </div>

        <h1>Solar & Wind</h1>

        <p className="login-subtitle">
          Deployment Intelligence Platform
        </p>

        {/* TABS */}
        <div className="login-tabs">

          <button
            type="button"
            className={
              mode === "login"
                ? "tab active"
                : "tab"
            }
            onClick={() => {
              setMode("login");
              setError("");
            }}
          >
            Login
          </button>

          <button
            type="button"
            className={
              mode === "register"
                ? "tab active"
                : "tab"
            }
            onClick={() => {
              setMode("register");
              setError("");
            }}
          >
            Register
          </button>

        </div>

        {/* FORM */}
        <form onSubmit={handleSubmit}>

          {/* NAME */}
          {mode === "register" && (
            <div className="form-group">

              <label>Full Name</label>

              <input
                type="text"
                name="name"
                placeholder="Enter your name"
                value={form.name}
                onChange={handleChange}
                required
              />

            </div>
          )}

          {/* EMAIL */}
          <div className="form-group">

            <label>Email</label>

            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={form.email}
              onChange={handleChange}
              required
            />

          </div>

          {/* PASSWORD */}
          <div className="form-group">

            <label>Password</label>

            <div className="password-container">

              <input
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                name="password"
                placeholder="Enter your password"
                value={form.password}
                onChange={handleChange}
                required
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword(!showPassword)
                }
              >
                {showPassword ? "🙈" : "👁️"}
              </button>

            </div>

          </div>

          {/* ERROR */}
          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          {/* SUBMIT */}
          <button
            type="submit"
            className="login-submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : mode === "login"
              ? "Login"
              : "Create Account"}
          </button>

        </form>

        {/* FOOTER */}
        <div className="login-footer">

          {mode === "login" ? (
            <>
              Don't have an account?{" "}

              <button
                type="button"
                onClick={() => {
                  setMode("register");
                  setError("");
                }}
              >
                Register
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}

              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setError("");
                }}
              >
                Login
              </button>
            </>
          )}

        </div>

      </div>

    </div>
  );
}

export default Login;