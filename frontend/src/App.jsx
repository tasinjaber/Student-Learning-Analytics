import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import SidebarLayout from "./components/SidebarLayout";
import AdminPage from "./pages/AdminPage";
import ComparisonPage from "./pages/ComparisonPage";
import DashboardPage from "./pages/DashboardPage";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import StudentProfilePage from "./pages/StudentProfilePage";
import { setAuthToken } from "./services/analyticsApi";

const DEFAULT_DATASET = { dataset_id: null, name: "Default (Kaggle / MongoDB)" };

function AppRoutes() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [activeDataset, setActiveDataset] = useState(DEFAULT_DATASET);

  useEffect(() => {
    const savedToken = localStorage.getItem("la_token");
    const savedUser = localStorage.getItem("la_user");
    if (savedToken && savedUser) {
      setAuthToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    const savedDs = localStorage.getItem("la_dataset");
    if (savedDs) setActiveDataset(JSON.parse(savedDs));
  }, []);

  function logout() {
    localStorage.removeItem("la_token");
    localStorage.removeItem("la_user");
    setAuthToken(null);
    setUser(null);
    navigate("/");
  }

  function handleDatasetChange(ds) {
    setActiveDataset(ds);
    localStorage.setItem("la_dataset", JSON.stringify(ds));
  }

  return (
    <Routes>
      {/* Standalone pages — no sidebar */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage onLogin={setUser} />} />

      {/* App pages — wrapped in sidebar */}
      <Route path="/*" element={
        <SidebarLayout user={user} onLogout={logout}>
          <Routes>
            <Route
              path="/dashboard"
              element={
                user
                  ? <DashboardPage user={user} activeDataset={activeDataset} onDatasetChange={handleDatasetChange} />
                  : <Navigate to="/login" replace />
              }
            />
            <Route
              path="/student/:id"
              element={user ? <StudentProfilePage activeDataset={activeDataset} /> : <Navigate to="/login" replace />}
            />
            <Route
              path="/compare"
              element={user ? <ComparisonPage activeDataset={activeDataset} /> : <Navigate to="/login" replace />}
            />
            <Route
              path="/admin"
              element={
                user?.role === "admin"
                  ? <AdminPage />
                  : <Navigate to="/dashboard" replace />
              }
            />
          </Routes>
        </SidebarLayout>
      } />
    </Routes>
  );
}

export default function App() {
  return <AppRoutes />;
}
