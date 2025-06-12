import axios from "axios";

export const API_BASE = "http://localhost:5555";

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
    return { success: false, error: err.message };
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
    return { success: false, error: err.message };
  }
};

export const getLSTMModels = async () => {
  try {
    const response = await axios.get(`${API_BASE}/lstm/models`);
    return response.data;
  } catch (err) {
    console.error("Get LSTM models error:", err);
    return { success: false, error: err.message };
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
    return { success: false, error: err.message };
  }
};

export const predictARIMA = async (days = 10) => {
  try {
    const response = await axios.get(`${API_BASE}/arima/predict`, {
      params: { days },
    });
    return response.data;
  } catch (err) {
    console.error("Predict ARIMA error:", err);
    return { success: false, error: err.message };
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
    return { success: false, error: err.message };
  }
};

export const predictProphet = async (days = 10) => {
  try {
    const response = await axios.get(`${API_BASE}/prophet/predict`, {
      params: { days },
    });
    return response.data;
  } catch (err) {
    console.error("Predict Prophet error:", err);
    return { success: false, error: err.message };
  }
};

