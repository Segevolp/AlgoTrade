import axios from "axios";

export const API_BASE = "http://localhost:5555";

// Auth token management
let authToken = localStorage.getItem("authToken");

const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    localStorage.setItem("authToken", token);
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    console.log("Token set successfully:", token.substring(0, 20) + "...");
  } else {
    localStorage.removeItem("authToken");
    delete axios.defaults.headers.common["Authorization"];
    console.log("Token cleared");
  }
};

// Initialize auth token if exists
if (authToken) {
  setAuthToken(authToken);
  console.log("Token loaded from localStorage");
}

// Add axios interceptor to handle token expiry
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only logout on 401 Unauthorized, not 422
      console.log("Authentication error (401), clearing token");
      setAuthToken(null);
      // Redirect to home page
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// ==================== AUTHENTICATION ====================

export const register = async (userData) => {
  try {
    const response = await axios.post(`${API_BASE}/register`, userData);
    return response.data;
  } catch (err) {
    console.error("Register error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const login = async (credentials) => {
  try {
    const response = await axios.post(`${API_BASE}/login`, credentials);
    console.log("Login response:", response.data);

    if (response.data.success && response.data.access_token) {
      setAuthToken(response.data.access_token);
      console.log("Login successful, token set");
    }
    return response.data;
  } catch (err) {
    console.error("Login error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const logout = () => {
  setAuthToken(null);
  return { success: true };
};

export const getProfile = async () => {
  try {
    console.log(
      "Getting profile with token:",
      authToken ? "Token present" : "No token"
    );
    const response = await axios.get(`${API_BASE}/profile`);
    return response.data;
  } catch (err) {
    console.error("Get profile error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const isAuthenticated = () => {
  const hasToken = !!authToken;
  console.log("Is authenticated:", hasToken);
  return hasToken;
};

// ==================== PORTFOLIO MANAGEMENT ====================

export const getPortfolios = async () => {
  try {
    console.log(
      "Getting portfolios with token:",
      authToken ? "Token present" : "No token"
    );
    const response = await axios.get(`${API_BASE}/portfolios`);
    return response.data;
  } catch (err) {
    console.error("Get portfolios error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const createPortfolio = async (portfolioData) => {
  try {
    const response = await axios.post(`${API_BASE}/portfolios`, portfolioData);
    return response.data;
  } catch (err) {
    console.error("Create portfolio error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const deletePortfolio = async (portfolioId) => {
  try {
    const response = await axios.delete(
      `${API_BASE}/portfolios/${portfolioId}`
    );
    return response.data;
  } catch (err) {
    console.error("Delete portfolio error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const addPortfolioItem = async (portfolioId, itemData) => {
  try {
    const response = await axios.post(
      `${API_BASE}/portfolios/${portfolioId}/items`,
      itemData
    );
    return response.data;
  } catch (err) {
    console.error("Add portfolio item error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const updatePortfolioItem = async (portfolioId, itemId, itemData) => {
  try {
    const response = await axios.put(
      `${API_BASE}/portfolios/${portfolioId}/items/${itemId}`,
      itemData
    );
    return response.data;
  } catch (err) {
    console.error("Update portfolio item error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const deletePortfolioItem = async (portfolioId, itemId) => {
  try {
    const response = await axios.delete(
      `${API_BASE}/portfolios/${portfolioId}/items/${itemId}`
    );
    return response.data;
  } catch (err) {
    console.error("Delete portfolio item error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const predictPortfolioEarnings = async (portfolioId, predictionData) => {
  try {
    const response = await axios.post(
      `${API_BASE}/portfolios/${portfolioId}/predict`,
      predictionData
    );
    return response.data;
  } catch (err) {
    console.error("Predict portfolio earnings error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

// ==================== EXISTING API ENDPOINTS ====================

export const hello = async () => {
  const response = await axios.get(`${API_BASE}/hello`);
  return response;
};

export const trainLSTM = async (params = {}) => {
  try {
    const response = await axios.post(`${API_BASE}/lstm/train`, {
      ticker: params.ticker || "^GSPC",
      start: params.start || "2010-01-01",
      end: params.end || "2025-05-22",
      sequence_length: params.sequence_length || 60,
    });
    return response.data;
  } catch (err) {
    console.error("Train LSTM error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const predictLSTM = async (
  ticker = "^GSPC",
  days = 20,
  sequence_length = 60
) => {
  try {
    const response = await axios.get(`${API_BASE}/lstm/predict`, {
      params: { ticker, days, sequence_length },
    });
    return response.data;
  } catch (err) {
    console.error("Predict LSTM error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const getLSTMModels = async () => {
  try {
    const response = await axios.get(`${API_BASE}/lstm/models`);
    return response.data;
  } catch (err) {
    console.error("Get LSTM models error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const trainARIMA = async (params = {}) => {
  try {
    const response = await axios.post(`${API_BASE}/arima/train`, {
      ticker: params.ticker || "^GSPC",
      start: params.start || "2020-01-01",
      end: params.end || "2025-04-08",
      exog_tickers: params.exog_tickers || ["GLD", "QQQ", "^TNX"],
    });
    return response.data;
  } catch (err) {
    console.error("Train ARIMA error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const predictARIMA = async (tickerOrDays = 10, days = null) => {
  try {
    let params = {};

    // If days is provided, first parameter is ticker
    if (days !== null) {
      params = { ticker: tickerOrDays, days };
    } else {
      // If only one parameter, it's days (backward compatibility)
      params = { days: tickerOrDays };
    }

    const response = await axios.get(`${API_BASE}/arima/predict`, {
      params,
    });
    return response.data;
  } catch (err) {
    console.error("Predict ARIMA error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const getARIMAModels = async () => {
  try {
    const response = await axios.get(`${API_BASE}/arima/models`);
    return response.data;
  } catch (err) {
    console.error("Get LSTM models error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const trainProphet = async (params = {}) => {
  try {
    const response = await axios.post(`${API_BASE}/prophet/train`, {
      ticker: params.ticker || "^GSPC",
      start: params.start || "2015-01-01",
      end: params.end || "2025-05-22",
    });
    return response.data;
  } catch (err) {
    console.error("Train Prophet error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const predictProphet = async (ticker = "^GSPC", days = 10) => {
  try {
    const response = await axios.get(`${API_BASE}/prophet/predict`, {
      params: { ticker, days },
    });
    return response.data;
  } catch (err) {
    console.error("Predict Prophet error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};

export const getProphetModels = async () => {
  try {
    const response = await axios.get(`${API_BASE}/prophet/models`);
    return response.data;
  } catch (err) {
    console.error("Get Prophet models error:", err);
    return { success: false, error: err.response?.data?.error || err.message };
  }
};
