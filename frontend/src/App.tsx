import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "./auth/AuthContext";
import { homeFor } from "./auth/home";
import { Layout } from "./components/Layout";
import { Loading } from "./components/ui";
import AlertsPage from "./pages/AlertsPage";
import FamilyPage from "./pages/FamilyPage";
import InsightsPage from "./pages/InsightsPage";
import LearnPage from "./pages/LearnPage";
import LoginPage from "./pages/LoginPage";
import MapPage from "./pages/MapPage";
import NotificationsPage from "./pages/NotificationsPage";
import ReportSymptomsPage from "./pages/ReportSymptomsPage";
import SignalDetailPage from "./pages/SignalDetailPage";
import SignalsPage from "./pages/SignalsPage";

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function Home() {
  const { user } = useAuth();
  return <Navigate to={user ? homeFor(user.role) : "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Home />} />
        <Route path="family" element={<FamilyPage />} />
        <Route path="report" element={<ReportSymptomsPage />} />
        <Route path="learn" element={<LearnPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="map" element={<MapPage />} />
        <Route path="signals" element={<SignalsPage />} />
        <Route path="signals/:id" element={<SignalDetailPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
