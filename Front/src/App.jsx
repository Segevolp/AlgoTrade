import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/NavBar/Navbar";
import HomePage from "./pages/HomePage";
import LSTMPage from "./pages/LSTMPage";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/lstm" element={<LSTMPage />} />
        <Route path="/algo2" element={<div>Algo 2 Page</div>} />
        <Route path="/algo3" element={<div>Algo 3 Page</div>} />
        <Route path="/algo4" element={<div>Algo 4 Page</div>} />
      </Routes>
    </Router>
  );
}

export default App;
