import React, { useState, useEffect } from "react";
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  CircularProgress,
  LinearProgress,
  Grid,
  Alert,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
} from "@mui/material";
import { trainARIMA, predictARIMA, getARIMAModels } from "../api/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const ArimaPage = () => {
  const [params, setParams] = useState({
    ticker: "^GSPC",
    start: "2020-01-01",
    end: "2025-04-08",
    exog_tickers: "GLD,QQQ,^TNX",
    predict_days: 10,
  });

  const [trainResult, setTrainResult] = useState(null);
  const [predictResult, setPredictResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");

  useEffect(() => {
    const fetchModels = async () => {
      const result = await getARIMAModels(); // Assuming this API function exists
      if (result.success) {
        setModels(result.tickers);
      }
    };
    fetchModels();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setParams((prev) => ({
      ...prev,
      [name]: name === "predict_days" ? parseInt(value) : value,
    }));
  };

  const handleTrain = async () => {
    setLoading(true);
    setTrainResult(null);
    const result = await trainARIMA({
      ...params,
      exog_tickers: params.exog_tickers.split(",").map((s) => s.trim()),
    });
    setTrainResult(result);
    setLoading(false);
  };

  const handlePredict = async () => {
    setLoading(true);
    const result = await predictARIMA(params.predict_days);
    setPredictResult(result);
    setLoading(false);
  };

  const handlePredictModel = async ticker => {
    setLoading(true);
    // use your axios wrapper which knows about API_BASE
    const result = await predictARIMA(ticker, params.predict_days);
    setPredictResult(result);
    setLoading(false);
  };


  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        ARIMA Training & Prediction
      </Typography>

      {loading && (
        <Box my={2}>
          <Typography variant="body1" color="textSecondary">
            Processing, please wait...
          </Typography>
          <LinearProgress />
        </Box>
      )}

      <Box component="form" noValidate autoComplete="off">
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Ticker"
              name="ticker"
              value={params.ticker}
              onChange={handleChange}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              label="Start Date"
              name="start"
              type="date"
              value={params.start}
              onChange={handleChange}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              label="End Date"
              name="end"
              type="date"
              value={params.end}
              onChange={handleChange}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Exogenous Tickers (comma-separated)"
              name="exog_tickers"
              value={params.exog_tickers}
              onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Days to Predict"
              name="predict_days"
              type="number"
              value={params.predict_days}
              onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12}>
            <Box display="flex" gap={2}>
              <Button
                variant="contained"
                color="primary"
                onClick={handleTrain}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : "Train"}
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                onClick={handlePredict}
                disabled={loading || !trainResult?.success}
              >
                Predict
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>

      <Box mt={4}>
        <FormControl fullWidth>
          <InputLabel>Select a trained model to predict</InputLabel>
          <Select
            value={selectedModel}
            onChange={(e) => {
              setSelectedModel(e.target.value);
              handlePredictModel(e.target.value);
            }}
          >
            {models.map((ticker) => (
              <MenuItem key={ticker} value={ticker}>
                {ticker}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {trainResult && (
        <Box mt={3}>
          <Alert severity={trainResult.success ? "success" : "error"}>
            {trainResult.success
              ? "Training completed successfully."
              : trainResult.error}
          </Alert>
        </Box>
      )}

      {predictResult?.success &&
        Array.isArray(predictResult.data?.dates) &&
        Array.isArray(predictResult.data?.forecast_mean) && (
          <Box mt={4}>
            <Typography variant="h6" gutterBottom>
              10-Day Forecast with Confidence Intervals
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={predictResult.data.dates.map((date, idx) => ({
                  date,
                  forecast: predictResult.data.forecast_mean[idx],
                  lower: predictResult.data.forecast_ci_lower[idx],
                  upper: predictResult.data.forecast_ci_upper[idx],
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke="#1976d2"
                  strokeWidth={2}
                  name="Forecast"
                />
                <Line
                  type="monotone"
                  dataKey="lower"
                  stroke="#8884d8"
                  strokeDasharray="5 5"
                  name="95% CI Lower"
                />
                <Line
                  type="monotone"
                  dataKey="upper"
                  stroke="#8884d8"
                  strokeDasharray="5 5"
                  name="95% CI Upper"
                />
                {/* Optional: shaded area between upper and lower CI (Recharts doesn't natively support area-between-lines) */}
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}
    </Container>
  );
};

export default ArimaPage;
