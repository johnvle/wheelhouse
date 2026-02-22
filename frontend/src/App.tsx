import { BrowserRouter, Routes, Route } from "react-router";
import AuthGuard from "@/components/AuthGuard";
import Layout from "@/components/Layout";
import OpenPositions from "@/pages/OpenPositions";
import History from "@/pages/History";
import Dashboard from "@/pages/Dashboard";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<AuthGuard />}>
          <Route element={<Layout />}>
            <Route index element={<OpenPositions />} />
            <Route path="history" element={<History />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
