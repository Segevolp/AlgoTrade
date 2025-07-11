import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import AuthModal from "../components/Auth/AuthModal";
import "./HomePage.css";

const HomePage = () => {
  const { user, isAuthenticated } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState("login");

  const handleAuthClick = (mode) => {
    setAuthMode(mode);
    setShowAuthModal(true);
  };

  const features = [
    {
      title: "LSTM Neural Networks",
      description:
        "Advanced deep learning models for time series prediction using Long Short-Term Memory networks.",
      icon: "🧠",
      path: "/lstm",
      color: "#667eea",
    },
    {
      title: "ARIMA Models",
      description:
        "AutoRegressive Integrated Moving Average models for statistical forecasting.",
      icon: "📊",
      path: "/arima",
      color: "#764ba2",
    },
    {
      title: "Prophet Forecasting",
      description:
        "Facebook's Prophet algorithm for robust time series forecasting.",
      icon: "🔮",
      path: "/prophet",
      color: "#f093fb",
    },
    {
      title: "Portfolio Management",
      description:
        "Track and manage your stock portfolios with detailed analytics.",
      icon: "💼",
      path: "/portfolio",
      color: "#f5576c",
    },
  ];

  return (
    <div className="home-page">
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Welcome to <span className="brand-name">AlgoTrade</span>
          </h1>
          <p className="hero-subtitle">
            Advanced algorithmic trading platform with machine learning-powered
            predictions
          </p>

          {isAuthenticated ? (
            <div className="welcome-back">
              <h2>Welcome back, {user?.username}! 👋</h2>
              <p>Ready to explore your trading algorithms and portfolios?</p>
              <div className="quick-actions">
                <Link to="/portfolio" className="btn btn-primary">
                  View My Portfolio
                </Link>
                <Link to="/lstm" className="btn btn-secondary">
                  Train Models
                </Link>
              </div>
            </div>
          ) : (
            <div className="cta-section">
              <p className="cta-text">
                Join thousands of traders using AI-powered predictions
              </p>
              <div className="cta-buttons">
                <button
                  className="btn btn-primary btn-lg"
                  onClick={() => handleAuthClick("register")}
                >
                  Get Started Free
                </button>
                <button
                  className="btn btn-outline btn-lg"
                  onClick={() => handleAuthClick("login")}
                >
                  Sign In
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="features-section">
        <div className="container">
          <h2 className="section-title">Powerful Trading Tools</h2>
          <p className="section-subtitle">
            Everything you need to make informed trading decisions
          </p>

          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-card">
                <div className="feature-icon" style={{ color: feature.color }}>
                  {feature.icon}
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
                {isAuthenticated ? (
                  <Link to={feature.path} className="feature-link">
                    Explore →
                  </Link>
                ) : (
                  <button
                    className="feature-link"
                    onClick={() => handleAuthClick("register")}
                  >
                    Get Access →
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="stats-section">
        <div className="container">
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-number">95%</div>
              <div className="stat-label">Prediction Accuracy</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">10K+</div>
              <div className="stat-label">Active Traders</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">$50M+</div>
              <div className="stat-label">Assets Under Management</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">24/7</div>
              <div className="stat-label">Market Monitoring</div>
            </div>
          </div>
        </div>
      </div>

      {!isAuthenticated && (
        <div className="final-cta">
          <div className="container">
            <h2>Ready to start your trading journey?</h2>
            <p>
              Join AlgoTrade today and get access to advanced trading algorithms
            </p>
            <button
              className="btn btn-primary btn-lg"
              onClick={() => handleAuthClick("register")}
            >
              Create Free Account
            </button>
          </div>
        </div>
      )}

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialMode={authMode}
      />
    </div>
  );
};

export default HomePage;
