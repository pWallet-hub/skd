import { NavLink, Outlet } from "react-router-dom";
import type { UserRole } from "../api/types";
import { useAuth } from "../auth/AuthContext";

interface NavItem {
  to: string;
  label: string;
  roles: UserRole[];
}

const STAFF: UserRole[] = ["health_reviewer", "analyst", "institution", "admin"];
const HEALTH_TEAM: UserRole[] = ["health_reviewer", "analyst", "admin"];

const NAV: NavItem[] = [
  { to: "/family", label: "My family", roles: ["parent"] },
  { to: "/report", label: "Report symptoms", roles: ["parent"] },
  { to: "/learn", label: "Guidance", roles: ["parent"] },
  { to: "/insights", label: "Overview", roles: STAFF },
  { to: "/map", label: "Map", roles: STAFF },
  { to: "/signals", label: "Signals", roles: STAFF },
  { to: "/alerts", label: "Alerts", roles: HEALTH_TEAM },
  { to: "/notifications", label: "Notifications", roles: [...STAFF, "parent"] },
];

export function Layout() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          SmartKids <span>Smile &amp; Grow</span>
        </div>
        <nav>
          {NAV.filter((n) => n.roles.includes(user.role)).map((n) => (
            <NavLink key={n.to} to={n.to}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="user">
          <span>
            {user.full_name} · <em>{user.role.replace("_", " ")}</em>
          </span>
          <button className="link" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="footer">
        Prototype with fictional demo data. Parent reports are observations, not diagnoses.
      </footer>
    </div>
  );
}
