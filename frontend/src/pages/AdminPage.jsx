import { useEffect, useState } from "react";

import {
  approveRequest,
  createUser,
  declineRequest,
  deleteUser,
  fetchAdminData,
  fetchUsers,
  updateUser,
} from "../services/analyticsApi";

const CACHE_KEY = "la_admin_data";

function parseError(err) {
  const detail = err?.response?.data?.detail;
  if (!detail) return err?.message ?? "Request failed. Make sure the backend is running.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg ?? JSON.stringify(d)).join("; ");
  return JSON.stringify(detail);
}

function applyData(data, setUserRows, setReqRows) {
  setUserRows((data.users ?? []).map((u) => ({ ...u, _type: "user" })));
  setReqRows((data.requests ?? []).map((r) => ({ ...r, _type: "request" })));
}

export default function AdminPage() {
  const [userRows, setUserRows] = useState([]);
  const [reqRows, setReqRows] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingReqs] = useState(false);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);

  async function load() {
    setError("");

    // Show cached data instantly if available
    try {
      const cached = sessionStorage.getItem(CACHE_KEY);
      if (cached) {
        applyData(JSON.parse(cached), setUserRows, setReqRows);
        setLoadingUsers(false);
      }
    } catch { /* ignore */ }

    // Fetch fresh data (single round-trip, both queries parallel on backend)
    try {
      const data = await fetchAdminData();
      applyData(data, setUserRows, setReqRows);
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoadingUsers(false);
    }
  }

  useEffect(() => { load(); }, []);

  const rows = [...userRows, ...reqRows];

  async function handleApprove(r) {
    try {
      await approveRequest(r.request_id);
      // Optimistic: remove request row, then refresh both in background
      setReqRows((prev) => prev.filter((row) => row.request_id !== r.request_id));
      fetchAdminData().then((data) => {
        applyData(data, setUserRows, setReqRows);
        sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
      });
    } catch (err) { alert(parseError(err)); }
  }

  async function handleDecline(r) {
    try {
      await declineRequest(r.request_id);
      setReqRows((prev) => prev.map((row) =>
        row.request_id === r.request_id ? { ...row, status: "declined" } : row
      ));
    } catch (err) { alert(parseError(err)); }
  }

  async function handleDelete(username) {
    if (!window.confirm(`Delete user "${username}"? This cannot be undone.`)) return;
    try {
      await deleteUser(username);
      setUserRows((prev) => prev.filter((r) => r.username !== username));
    } catch (err) { alert(parseError(err)); }
  }

  const closeModal = () => setModal(null);

  const pendingCount = reqRows.filter((r) => r.status === "pending").length;

  return (
    <div className="admin-page">
      <div className="admin-header">
        <div>
          <h1 className="admin-title">User Management</h1>
          <p className="admin-subtitle">
            {loadingUsers ? "Loading…" : `${userRows.length} user${userRows.length !== 1 ? "s" : ""}`}
            {!loadingReqs && pendingCount > 0 && <span className="admin-pending-badge">{pendingCount} pending</span>}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setModal({ type: "create" })}>
          + New User
        </button>
      </div>

      {error && <p className="admin-error">{error}</p>}

      {loadingUsers ? (
        <p className="admin-loading">Loading users…</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Type</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                if (row._type === "user") {
                  return (
                    <tr key={`user-${row.username}`}>
                      <td className="admin-td-user">{row.username}</td>
                      <td className="admin-td-dim">—</td>
                      <td><span className={`role-badge role-${row.role}`}>{row.role}</span></td>
                      <td><span className="status-badge status-active">active</span></td>
                      <td className="admin-td-dim">
                        {row.source === "builtin" ? "built-in" : "user"}
                      </td>
                      <td className="admin-td-date">
                        {row.created_at ? new Date(row.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="admin-td-actions">
                        {row.source === "builtin" ? (
                          <span className="admin-builtin-tag">built-in</span>
                        ) : (
                          <>
                            <button type="button" className="btn-link" onClick={() => setModal({ type: "editRole", user: row })}>Edit role</button>
                            <button type="button" className="btn-link" onClick={() => setModal({ type: "resetPw", user: row })}>Reset password</button>
                            <button type="button" className="btn-link btn-link-danger" onClick={() => handleDelete(row.username)}>Delete</button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                }

                /* registration request row */
                return (
                  <tr key={`req-${row.request_id}`} className={row.status === "pending" ? "admin-row-pending" : ""}>
                    <td className="admin-td-user">{row.username}</td>
                    <td>{row.email || "—"}</td>
                    <td><span className={`role-badge role-${row.role}`}>{row.role}</span></td>
                    <td><span className={`status-badge status-${row.status}`}>{row.status}</span></td>
                    <td className="admin-td-dim">request</td>
                    <td className="admin-td-date">
                      {row.created_at ? new Date(row.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="admin-td-actions">
                      {row.status === "pending" ? (
                        <>
                          <button type="button" className="btn-link btn-link-success" onClick={() => handleApprove(row)}>Approve</button>
                          <button type="button" className="btn-link btn-link-danger" onClick={() => handleDecline(row)}>Decline</button>
                        </>
                      ) : (
                        <span className="admin-td-dim">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {modal?.type === "create" && (
        <CreateUserModal onClose={closeModal} onCreated={() => { closeModal(); load(); }} />
      )}
      {modal?.type === "editRole" && (
        <EditRoleModal
          user={modal.user}
          onClose={closeModal}
          onUpdated={(username, role) => {
            setRows((prev) => prev.map((r) => r._type === "user" && r.username === username ? { ...r, role } : r));
            closeModal();
          }}
        />
      )}
      {modal?.type === "resetPw" && (
        <ResetPasswordModal user={modal.user} onClose={closeModal} onDone={closeModal} />
      )}
    </div>
  );
}

/* ── Create User ──────────────────────────────────────────── */
function CreateUserModal({ onClose, onCreated }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role] = useState("admin");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim()) { setError("Username is required."); return; }
    if (!password.trim()) { setError("Password is required."); return; }
    try {
      setLoading(true);
      setError("");
      await createUser(username.trim(), password, role);
      onCreated();
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>New User</h3>
          <button type="button" className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form className="modal-form" onSubmit={handleSubmit}>
          <label className="modal-label">
            Username
            <input className="modal-input" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="off" required />
          </label>
          <label className="modal-label">
            Password
            <input className="modal-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />
          </label>
          <label className="modal-label">
            Role
            <input className="modal-input" value="Admin" readOnly style={{ color: "#94a3b8", cursor: "default" }} />
          </label>
          {error && <p className="admin-error" style={{ margin: 0 }}>{error}</p>}
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Creating…" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Edit Role ────────────────────────────────────────────── */
function EditRoleModal({ user, onClose, onUpdated }) {
  const [role, setRole] = useState(user.role);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (role === user.role) { onClose(); return; }
    try {
      setLoading(true);
      setError("");
      await updateUser(user.username, null, role);
      onUpdated(user.username, role);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Edit role — {user.username}</h3>
          <button type="button" className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form className="modal-form" onSubmit={handleSubmit}>
          <label className="modal-label">
            Role
            <select className="modal-input" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="admin">Admin</option>
            </select>
          </label>
          {error && <p className="admin-error" style={{ margin: 0 }}>{error}</p>}
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Reset Password ───────────────────────────────────────── */
function ResetPasswordModal({ user, onClose, onDone }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!password.trim()) { setError("Enter a new password."); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }
    try {
      setLoading(true);
      setError("");
      await updateUser(user.username, password, null);
      setSuccess(true);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Reset password — {user.username}</h3>
          <button type="button" className="modal-close" onClick={onClose}>✕</button>
        </div>
        {success ? (
          <div className="modal-form">
            <p style={{ color: "#16a34a", margin: 0, fontSize: "0.9rem" }}>Password updated successfully.</p>
            <div className="modal-actions">
              <button type="button" className="btn btn-primary" onClick={onDone}>Done</button>
            </div>
          </div>
        ) : (
          <form className="modal-form" onSubmit={handleSubmit}>
            <label className="modal-label">
              New password
              <input className="modal-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />
            </label>
            <label className="modal-label">
              Confirm password
              <input className="modal-input" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required />
            </label>
            {error && <p className="admin-error" style={{ margin: 0 }}>{error}</p>}
            <div className="modal-actions">
              <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "Saving…" : "Reset Password"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
