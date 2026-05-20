import { useState } from "react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Analytics", hint: "Dashboard & charts" },
  { to: "/compare", label: "Compare", hint: "Side-by-side students" },
];

export default function SidebarLayout({ children, user, onLogout }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`app-layout ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar" aria-label="Main navigation">
        <div className="sidebar-brand">
          <span className="sidebar-logo">LA</span>
          {!collapsed && (
            <div>
              <p className="sidebar-title">Learning Analytics</p>
              <p className="sidebar-caption">Interpretable dashboards</p>
            </div>
          )}
          <button
            type="button"
            className="sidebar-collapse-btn"
            onClick={() => setCollapsed((prev) => !prev)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
          >
            {collapsed ? "»" : "«"}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const linkClass = ({ isActive }) =>
              ["sidebar-nav-item", isActive && "sidebar-nav-active"].filter(Boolean).join(" ");

            return (
              <NavLink key={item.to} to={item.to} end={Boolean(item.end)} className={linkClass}>
                {!collapsed ? (
                  <span className="sidebar-nav-copy">
                    <span className="sidebar-nav-label">{item.label}</span>
                    <span className="sidebar-nav-hint">{item.hint}</span>
                  </span>
                ) : (
                  <span className="sidebar-short">{item.label[0]}</span>
                )}
              </NavLink>
            );
          })}

          {user?.role === "admin" && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                ["sidebar-nav-item sidebar-nav-admin", isActive && "sidebar-nav-active"].filter(Boolean).join(" ")
              }
            >
              {!collapsed ? (
                <span className="sidebar-nav-copy">
                  <span className="sidebar-nav-label">User Management</span>
                  <span className="sidebar-nav-hint">Users & requests</span>
                </span>
              ) : (
                <span className="sidebar-short">A</span>
              )}
            </NavLink>
          )}

          {!user ? (
            !collapsed ? (
              <NavLink to="/login" className={({ isActive }) => `sidebar-auth ${isActive ? "sidebar-auth-active" : ""}`}>
                Sign in
              </NavLink>
            ) : (
              <NavLink to="/login" className="sidebar-auth-mini" title="Sign in">
                ⋯
              </NavLink>
            )
          ) : null}
        </nav>

        <div className="sidebar-footer">
          {user ? (
            collapsed ? (
              <button type="button" className="sidebar-logout-compact" onClick={onLogout}>
                Exit
              </button>
            ) : (
              <div className="sidebar-account">
                <p className="sidebar-user">{user.username}</p>
                <p className="sidebar-role">{user.role}</p>
                <button type="button" className="sidebar-logout" onClick={onLogout}>
                  Log out
                </button>
              </div>
            )
          ) : collapsed ? null : (
            <p className="sidebar-microcopy">Transparent analytics aligned with publicly shared learning logs.</p>
          )}
        </div>
      </aside>

      <div className="layout-main">
        <main className="layout-content">{children}</main>
      </div>
    </div>
  );
}
