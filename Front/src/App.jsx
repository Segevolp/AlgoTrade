console.log("✅ App.jsx loaded");


import React from 'react';
import { useState } from 'react';

function App() {
  const [forecast, setForecast] = useState([]);
  const [dates, setDates] = useState([]);

  const fetchForecast = async () => {
    const res = await fetch('/api/predict?days=20');
    const data = await res.json();
    setForecast(data.forecast || []);
    setDates(data.dates || []);
  };

  const trainModel = async () => {
    const res = await fetch('/api/train', { method: 'POST' });
    const data = await res.json();
    alert(data.message || data.error);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>S&P 500 LSTM Forecast</h1>
      <button onClick={trainModel}>Train Model</button>
      <button onClick={fetchForecast} style={{ marginLeft: '10px' }}>
        Get Forecast
      </button>
      <ul>
        {forecast.map((price, idx) => (
          <li key={idx}>
            {dates[idx]}: {price.toFixed(2)}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
