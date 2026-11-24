import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import type { UserRole } from "./api/types";
import { useAuth } from "./auth/AuthContext";
import { homeFor } from "./auth/home";
import { Layout } from "./components/Layout";
import { Loading } from "./components/ui";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AuditLogPage from "./pages/admin/AuditLogPage";
import ContentPage from "./pages/admin/ContentPage";
import PlacesPage from "./pages/admin/PlacesPage";
import SettingsPage from "./pages/admin/SettingsPage";
import UsersPage from "./pages/admin/UsersPage";
import AccountPage from "./pages/AccountPage";
import AlertsPage from "./pages/AlertsPage";
import ChildPage from "./pages/ChildPage";
import FindCarePage from "./pages/FindCarePage";
import HealthCardPage from "./pages/HealthCardPage";
import RegisterPage from "./pages/RegisterPage";
import ReviewQueuePage from "./pages/ReviewQueuePage";
import FamilyPage from "./pages/FamilyPage";
import InsightsPage from "./pages/InsightsPage";
import LearnPage from "./pages/LearnPage";
import LoginPage from "./pages/LoginPage";
import MapPage from "./pages/MapPage";
import NotificationsPage from "./pages/NotificationsPage";
import ReportSymptomsPage from "./pages/ReportSymptomsPage";
import SignalDetailPage from "./pages/SignalDetailPage";
import SignalsPage from "./pages/SignalsPage";

const STAFF: UserRole[] = ["health_reviewer", "analyst", "institution", "admin"];
const HEALTH_TEAM: UserRole[] = ["health_reviewer", "analyst", "admin"];

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ padding: 40 }}><Loading rows={4} /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/** UI-level guard. The API enforces the same rules; this just avoids dead-end pages. */
function RequireRole({ roles, children }: { roles: UserRole[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) return <Navigate to={user ? homeFor(user.role) : "/login"} replace />;
  return <>{children}</>;
}

function Home() {
  const { user } = useAuth();
  return <Navigate to={user ? homeFor(user.role) : "/login"} replace />;
}

const only = (roles: UserRole[], el: ReactNode) => <RequireRole roles={roles}>{el}</RequireRole>;

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/card/:token" element={<HealthCardPage />} />
      <Route element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Home />} />
        <Route path="family" element={only(["parent"], <FamilyPage />)} />
        <Route path="report" element={only(["parent"], <ReportSymptomsPage />)} />
        <Route path="children/:id" element={only(["parent"], <ChildPage />)} />
        <Route path="care" element={only(["parent"], <FindCarePage />)} />
        <Route path="learn" element={<LearnPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="account" element={<AccountPage />} />

        <Route path="insights" element={only(STAFF, <InsightsPage />)} />
        <Route path="map" element={only(STAFF, <MapPage />)} />
        <Route path="signals" element={only(STAFF, <SignalsPage />)} />
        <Route path="signals/:id" element={only(STAFF, <SignalDetailPage />)} />
        <Route path="alerts" element={only(HEALTH_TEAM, <AlertsPage />)} />
        <Route path="review" element={only(["health_reviewer", "admin"], <ReviewQueuePage />)} />

        <Route path="admin" element={only(["admin"], <AdminDashboardPage />)} />
        <Route path="admin/users" element={only(["admin"], <UsersPage />)} />
        <Route path="admin/places" element={only(["admin"], <PlacesPage />)} />
        <Route path="admin/content" element={only(["admin"], <ContentPage />)} />
        <Route path="admin/audit" element={only(["admin"], <AuditLogPage />)} />
        <Route path="admin/settings" element={only(["admin"], <SettingsPage />)} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
