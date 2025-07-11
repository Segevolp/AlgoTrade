import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Navbar from "./components/NavBar/Navbar";
import "./components/NavBar/Navbar.css";
import HomePage from "./pages/HomePage";
import PortfolioPage from "./pages/PortfolioPage";
import LSTMPage from "./pages/LSTMPage";
import ArimaPage from "./pages/ArimaPage";
import ProphetPage from "./pages/ProphetPage";

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="loading-spinner">Loading...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/" replace />;
};

// Main App Component
const AppContent = () => {
  const { loading } = useAuth();

  if (loading) {
    return <div className="loading-spinner">Loading...</div>;
  }

  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/portfolio"
          element={
            <ProtectedRoute>
              <PortfolioPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/lstm"
          element={
            <ProtectedRoute>
              <LSTMPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/arima"
          element={
            <ProtectedRoute>
              <ArimaPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/prophet"
          element={
            <ProtectedRoute>
              <ProphetPage />
            </ProtectedRoute>
          }
        />
        <Route path="/algo4" element={<div>Algo 4 Page</div>} />
      </Routes>
    </Router>
  );
};

// Root App Component with AuthProvider
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
