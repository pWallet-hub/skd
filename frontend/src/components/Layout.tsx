import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { get } from "../api/client";
import type { NotificationItem, Signal, UserRole } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABEL } from "../utils/format";
import {
  Bell,
  BookOpen,
  ClipboardList,
  FileText,
  HeartPulse,
  Hospital,
  LayoutDashboard,
  LogOut,
  MapIcon,
  MapPin,
  Megaphone,
  Menu,
  Radar,
  Settings,
  Smile,
  Stethoscope,
  TrendingUp,
  UserCog,
  Users,
} from "./icons";
import { Avatar } from "./ui";

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  roles: UserRole[];
  badge?: "signals";
}

const STAFF: UserRole[] = ["health_reviewer", "analyst", "institution", "admin"];
const HEALTH_TEAM: UserRole[] = ["health_reviewer", "analyst", "admin"];
const ADMIN: UserRole[] = ["admin"];

const SECTIONS: { label: string; items: NavItem[] }[] = [
  {
    label: "My family",
    items: [
      { to: "/family", label: "Dashboard", icon: <LayoutDashboard size={18} />, roles: ["parent"] },
      { to: "/report", label: "Report a concern", icon: <Stethoscope size={18} />, roles: ["parent"] },
      { to: "/care", label: "Find care", icon: <Hospital size={18} />, roles: ["parent"] },
      { to: "/learn", label: "Guidance", icon: <BookOpen size={18} />, roles: ["parent"] },
    ],
  },
  {
    label: "Community health",
    items: [
      { to: "/insights", label: "Overview", icon: <TrendingUp size={18} />, roles: STAFF },
      { to: "/map", label: "Map", icon: <MapIcon size={18} />, roles: STAFF },
      { to: "/signals", label: "Signals", icon: <Radar size={18} />, roles: STAFF, badge: "signals" },
      { to: "/review", label: "Report review", icon: <ClipboardList size={18} />, roles: ["health_reviewer", "admin"] },
      { to: "/alerts", label: "Alerts", icon: <Megaphone size={18} />, roles: HEALTH_TEAM },
    ],
  },
  {
    label: "Administration",
    items: [
      { to: "/admin", label: "Admin dashboard", icon: <LayoutDashboard size={18} />, roles: ADMIN },
      { to: "/admin/users", label: "Users", icon: <Users size={18} />, roles: ADMIN },
      { to: "/admin/places", label: "Places", icon: <MapPin size={18} />, roles: ADMIN },
      { to: "/admin/content", label: "Content", icon: <FileText size={18} />, roles: ADMIN },
      { to: "/admin/audit", label: "Audit log", icon: <ClipboardList size={18} />, roles: ADMIN },
      { to: "/admin/settings", label: "Settings", icon: <Settings size={18} />, roles: ADMIN },
    ],
  },
];

export function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isStaff = !!user && STAFF.includes(user.role);
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: () => get<NotificationItem[]>("/notifications"),
    refetchInterval: 60_000,
    enabled: !!user,
  });
  const signals = useQuery({
    queryKey: ["signals"],
    queryFn: () => get<Signal[]>("/signals"),
    enabled: isStaff,
    refetchInterval: 60_000,
  });
  const unread = notifications.data?.filter((n) => !n.read_at).length ?? 0;
  const newSignals = signals.data?.filter((s) => s.status === "detected").length ?? 0;

  useEffect(() => {
    setNavOpen(false);
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  if (!user) return null;

  return (
    <div className="shell">
      <aside className={`sidebar ${navOpen ? "open" : ""}`}>
        <Link to="/" className="sidebar-brand" style={{ textDecoration: "none" }}>
          <div className="logo">
            <Smile size={20} />
          </div>
          <div>
            <div className="brand-name">SmartKids</div>
            <div className="brand-sub">Smile &amp; Grow</div>
          </div>
        </Link>

        {SECTIONS.map((section) => {
          const items = section.items.filter((i) => i.roles.includes(user.role));
          if (items.length === 0) return null;
          return (
            <nav className="nav-section" key={section.label} aria-label={section.label}>
              <div className="nav-label">{section.label}</div>
              {items.map((item) => (
                <NavLink key={item.to} to={item.to} end={item.to === "/admin"} className="nav-link">
                  {item.icon}
                  {item.label}
                  {item.badge === "signals" && newSignals > 0 && (
                    <span className="nav-count" title={`${newSignals} new signals`}>
                      {newSignals}
                    </span>
                  )}
                </NavLink>
              ))}
            </nav>
          );
        })}

        <div className="sidebar-foot">
          <div className="demo-note">
            <HeartPulse size={14} style={{ verticalAlign: "-2px", marginRight: 6 }} />
            Prototype · fictional data. Parent reports are observations, not diagnoses.
          </div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <button className="icon-btn menu-toggle" onClick={() => setNavOpen((o) => !o)} aria-label="Open menu">
            <Menu size={18} />
          </button>
          <div className="topbar-spacer" />
          <Link to="/notifications" className="icon-btn" aria-label={`Notifications (${unread} unread)`}>
            <Bell size={18} />
            {unread > 0 && <span className="dot-count">{unread > 9 ? "9+" : unread}</span>}
          </Link>
          <div className="user-menu" ref={menuRef}>
            <button className="user-chip" onClick={() => setMenuOpen((o) => !o)} aria-haspopup="menu">
              <Avatar name={user.full_name} />
              <div className="who">
                <strong>{user.full_name}</strong>
                <span>{ROLE_LABEL[user.role]}</span>
              </div>
            </button>
            {menuOpen && (
              <div className="dropdown" role="menu">
                <div className="meta">{user.email}</div>
                <Link to="/account">
                  <UserCog size={16} /> My account
                </Link>
                <Link to="/notifications">
                  <Bell size={16} /> Notifications
                </Link>
                <button onClick={logout}>
                  <LogOut size={16} /> Sign out
                </button>
              </div>
            )}
          </div>
        </header>
        <main className={`content ${user.role === "parent" ? "has-tabbar" : ""}`}>
          <Outlet />
        </main>
        {user.role === "parent" && (
          <nav className="tabbar" aria-label="Main">
            <NavLink to="/family"><LayoutDashboard size={20} /><span>Home</span></NavLink>
            <NavLink to="/report"><Stethoscope size={20} /><span>Report</span></NavLink>
            <NavLink to="/care"><Hospital size={20} /><span>Care</span></NavLink>
            <NavLink to="/learn"><BookOpen size={20} /><span>Guidance</span></NavLink>
            <NavLink to="/notifications"><Bell size={20} /><span>Alerts{unread > 0 ? ` (${unread})` : ""}</span></NavLink>
          </nav>
        )}
      </div>
      {navOpen && <div className="modal-backdrop" style={{ zIndex: 25 }} onClick={() => setNavOpen(false)} />}
    </div>
  );
}
