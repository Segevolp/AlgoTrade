import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import AuthModal from "../Auth/AuthModal";

const Navbar = () => {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState("login");

  const handleAuthClick = (mode) => {
    setAuthMode(mode);
    setShowAuthModal(true);
  };

  const handleLogout = () => {
    logout();
  };

  const navItems = [
    { path: "/", label: "Home", requiresAuth: false },
    { path: "/portfolio", label: "Portfolio", requiresAuth: true },
    { path: "/lstm", label: "LSTM", requiresAuth: true },
    { path: "/arima", label: "ARIMA", requiresAuth: true },
    { path: "/prophet", label: "Prophet", requiresAuth: true },
  ];

  const filteredNavItems = navItems.filter(
    (item) => !item.requiresAuth || isAuthenticated
  );

  return (
    <>
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/" className="navbar-logo">
            <h2>AlgoTrade</h2>
          </Link>

          <div className="navbar-menu">
            {filteredNavItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`navbar-item ${
                  location.pathname === item.path ? "active" : ""
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>

          <div className="navbar-auth">
            {isAuthenticated ? (
              <div className="user-menu">
                <div className="user-info">
                  <span className="username">Welcome, {user?.username}</span>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            ) : (
              <div className="auth-buttons">
                <button
                  className="login-btn"
                  onClick={() => handleAuthClick("login")}
                >
                  Login
                </button>
                <button
                  className="register-btn"
                  onClick={() => handleAuthClick("register")}
                >
                  Sign Up
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialMode={authMode}
      />
    </>
  );
};

export default Navbar;
