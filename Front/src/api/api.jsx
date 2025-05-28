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


export const predictLSTM = async (days = 20, sequence_length = 60) => {
  try {
    const response = await axios.get(`${API_BASE}/lstm/predict`, {
      params: { days, sequence_length }
    });
    return response.data;
  } catch (err) {
    console.error("Predict LSTM error:", err);
    return { success: false, error: err.message };
  }
};
