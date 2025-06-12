import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/NavBar/Navbar";
import HomePage from "./pages/HomePage";
import LSTMPage from "./pages/LSTMPage";
import ArimaPage from "./pages/ArimaPage";
import ProphetPage from "./pages/ProphetPage";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/lstm" element={<LSTMPage />} />
        <Route path="/arima" element={<ArimaPage />} />
        <Route path="/prophet" element={<ProphetPage />} />
        <Route path="/algo4" element={<div>Algo 4 Page</div>} />
      </Routes>
    </Router>
  );
}

export default App;
