import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { login, register, setAuthToken } from "../services/analyticsApi";

export default function LoginPage({ onLogin }) {
  const [tab, setTab] = useState("signin");
  const navigate = useNavigate();

  return (
    <div className="auth-page">
      <div className="auth-bg-glow auth-glow-1" />
      <div className="auth-bg-glow auth-glow-2" />

      <div className="auth-container">
        <Link to="/" className="auth-brand">
          <span className="auth-brand-logo">LA</span>
          <span className="auth-brand-name">Learning Analytics</span>
        </Link>

        <div className="auth-card">
          <div className="auth-tabs">
            <button
              type="button"
              className={`auth-tab ${tab === "signin" ? "auth-tab-active" : ""}`}
              onClick={() => setTab("signin")}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`auth-tab ${tab === "register" ? "auth-tab-active" : ""}`}
              onClick={() => setTab("register")}
            >
              Register
            </button>
          </div>

          {tab === "signin" ? (
            <SignInForm onLogin={onLogin} navigate={navigate} />
          ) : (
            <RegisterForm onSwitchTab={() => setTab("signin")} />
          )}
        </div>

        <p className="auth-footer-note">
          Default account: <code>admin / admin123</code>
        </p>
      </div>
    </div>
  );
}

function SignInForm({ onLogin, navigate }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      setLoading(true);
      setError("");
      const data = await login(username, password);
      localStorage.setItem("la_token", data.access_token);
      localStorage.setItem("la_user", JSON.stringify(data.user));
      setAuthToken(data.access_token);
      onLogin(data.user);
      navigate("/dashboard");
    } catch {
      setError("Invalid username or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="auth-field">
        <label className="auth-label">Username</label>
        <input
          className="auth-input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
      </div>
      <div className="auth-field">
        <label className="auth-label">Password</label>
        <input
          className="auth-input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
      </div>
      {error && <p className="auth-error">{error}</p>}
      <button className="auth-submit" type="submit" disabled={loading}>
        {loading ? "Signing in…" : "Sign In"}
      </button>
    </form>
  );
}

function RegisterForm({ onSwitchTab }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("admin");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      setLoading(true);
      setError("");
      setSuccess("");
      await register(username, password, email, role);
      setSuccess("Registration request submitted. An admin will review it shortly.");
      setUsername("");
      setEmail("");
      setPassword("");
    } catch (err) {
      setError(err?.response?.data?.detail ?? "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="auth-field">
        <label className="auth-label">Username</label>
        <input
          className="auth-input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
      </div>
      <div className="auth-field">
        <label className="auth-label">Email <span className="auth-optional">(optional)</span></label>
        <input
          className="auth-input"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
      </div>
      <div className="auth-field">
        <label className="auth-label">Password</label>
        <input
          className="auth-input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          required
        />
      </div>
      <div className="auth-field">
        <label className="auth-label">Role</label>
        <select className="auth-input auth-select" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="admin">Admin</option>
        </select>
      </div>
      {error && <p className="auth-error">{error}</p>}
      {success && <p className="auth-success">{success}</p>}
      <button className="auth-submit" type="submit" disabled={loading}>
        {loading ? "Submitting…" : "Request Access"}
      </button>
      {success && (
        <button type="button" className="auth-switch-link" onClick={onSwitchTab}>
          Back to Sign In
        </button>
      )}
    </form>
  );
}
