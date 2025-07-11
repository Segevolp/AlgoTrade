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
import { trainLSTM, predictLSTM, getLSTMModels } from "../api/api";
import TickerAutocomplete from "../components/TickerAutocomplete";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const LSTMPage = () => {
  const [params, setParams] = useState({
    ticker: "^GSPC",
    start: "2010-01-01",
    end: "2025-05-22",
    sequence_length: 60,
    predict_days: 20,
  });

  const [trainResult, setTrainResult] = useState(null);
  const [predictResult, setPredictResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");

  useEffect(() => {
    const fetchModels = async () => {
      const result = await getLSTMModels();
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
      [name]:
        name === "sequence_length" || name === "predict_days"
          ? parseInt(value)
          : value,
    }));
  };

  const handleTrain = async () => {
    setLoading(true);
    setTrainResult(null);
    const result = await trainLSTM(params);
    setTrainResult(result);
    setLoading(false);
  };

  const handlePredict = async (ticker) => {
    setLoading(true);
    const result = await predictLSTM(
      ticker,
      params.predict_days,
      params.sequence_length
    );
    setPredictResult(result);
    setLoading(false);
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        LSTM Training & Prediction
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
            <TickerAutocomplete
              name="ticker"
              label="Ticker"
              value={params.ticker}
              onChange={handleChange}
              placeholder="e.g., AAPL, ^GSPC, TSLA"
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
          <Grid item xs={6}>
            <TextField
              fullWidth
              label="Sequence Length"
              name="sequence_length"
              type="number"
              value={params.sequence_length}
              onChange={handleChange}
            />
          </Grid>
          <Grid item xs={6}>
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
              handlePredict(e.target.value);
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

      {predictResult?.success && (
        <Box mt={4}>
          <Typography variant="h6" gutterBottom>
            Forecast Results (Line Chart):
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={predictResult.data.dates.map((date, idx) => ({
                date,
                price: predictResult.data.forecast[idx],
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#1976d2"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Container>
  );
};

export default LSTMPage;
