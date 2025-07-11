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
import { trainProphet, predictProphet, getProphetModels } from "../api/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const ProphetPage = () => {
  const [params, setParams] = useState({
    ticker: "^GSPC",
    start: "2015-01-01",
    end: "2025-05-22",
    predict_days: 20,
  });

  const [loading, setLoading] = useState(false);
  const [trainResult, setTrainResult] = useState(null);
  const [predictResult, setPredictResult] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");

  useEffect(() => {
    const fetchModels = async () => {
      const result = await getProphetModels();
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
    const result = await trainProphet(params);
    setTrainResult(result);
    setLoading(false);
  };

  const handlePredict = async () => {
    setLoading(true);
    const result = await predictProphet(params.ticker, params.predict_days);
    setPredictResult(result);
    setLoading(false);
  };

  const handlePredictModel = async (ticker) => {
    setLoading(true);
    const result = await predictProphet(params.predict_days, ticker);
    setPredictResult(result);
    setLoading(false);
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Prophet Forecasting
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
              label="Days to Predict"
              name="predict_days"
              type="number"
              value={params.predict_days}
              onChange={handleChange}
            />
          </Grid>
          <Grid item xs={6}>
            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={handleTrain}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : "Train"}
            </Button>
          </Grid>
          <Grid item xs={6}>
            <Button
              variant="contained"
              color="secondary"
              fullWidth
              onClick={handlePredict}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : "Predict"}
            </Button>
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
            disabled={loading}
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

      {predictResult?.success && (
        <Box mt={4}>
          <Typography variant="h6" gutterBottom>
            Prophet Forecast Results:
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={predictResult.data.dates.map((date, idx) => ({
                date,
                forecast: predictResult.data.forecast[idx],
                upper: predictResult.data.forecast_upper[idx],
                lower: predictResult.data.forecast_lower[idx],
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="forecast" stroke="#1976d2" />
              <Line type="monotone" dataKey="upper" stroke="#2e7d32" />
              <Line type="monotone" dataKey="lower" stroke="#c62828" />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Container>
  );
};

export default ProphetPage;
