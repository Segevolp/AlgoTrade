import React, { useState, useEffect } from "react";
import {
  getPortfolios,
  createPortfolio,
  deletePortfolio,
  addPortfolioItem,
  updatePortfolioItem,
  deletePortfolioItem,
  predictPortfolioEarnings,
} from "../api/api";
import { useAuth } from "../contexts/AuthContext";
import TickerAutocomplete from "../components/TickerAutocomplete";
import "./PortfolioPage.css";

const PortfolioPage = () => {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddItemModal, setShowAddItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { user } = useAuth();

  // Prediction states
  const [showPredictionModal, setShowPredictionModal] = useState(false);
  const [predictionMethod, setPredictionMethod] = useState("average");
  const [predictionDays, setPredictionDays] = useState(30);
  const [predictionResult, setPredictionResult] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);

  const [newPortfolioName, setNewPortfolioName] = useState("");
  const [newItem, setNewItem] = useState({
    ticker: "",
    quantity: "",
    purchase_price: "",
    notes: "",
  });

  useEffect(() => {
    fetchPortfolios();
  }, []);

  const fetchPortfolios = async () => {
    try {
      const response = await getPortfolios();
      if (response.success) {
        setPortfolios(response.portfolios);
        if (response.portfolios.length > 0 && !selectedPortfolio) {
          setSelectedPortfolio(response.portfolios[0]);
        }
      } else {
        setError(response.error || "Failed to fetch portfolios");
      }
    } catch (error) {
      setError("Failed to fetch portfolios");
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePortfolio = async (e) => {
    e.preventDefault();
    if (!newPortfolioName.trim()) return;

    try {
      const response = await createPortfolio({ name: newPortfolioName });
      if (response.success) {
        setPortfolios([...portfolios, response.portfolio]);
        setNewPortfolioName("");
        setShowCreateModal(false);
        setSelectedPortfolio(response.portfolio);
      } else {
        setError(response.error || "Failed to create portfolio");
      }
    } catch (error) {
      setError("Failed to create portfolio");
    }
  };

  const handleDeletePortfolio = async (portfolioId) => {
    if (!confirm("Are you sure you want to delete this portfolio?")) return;

    try {
      const response = await deletePortfolio(portfolioId);
      if (response.success) {
        const updatedPortfolios = portfolios.filter(
          (p) => p.id !== portfolioId
        );
        setPortfolios(updatedPortfolios);
        if (selectedPortfolio?.id === portfolioId) {
          setSelectedPortfolio(updatedPortfolios[0] || null);
        }
      } else {
        setError(response.error || "Failed to delete portfolio");
      }
    } catch (error) {
      setError("Failed to delete portfolio");
    }
  };

  const handleAddItem = async (e) => {
    e.preventDefault();
    if (
      !selectedPortfolio ||
      !newItem.ticker ||
      !newItem.quantity ||
      !newItem.purchase_price
    ) {
      return;
    }

    try {
      const response = await addPortfolioItem(selectedPortfolio.id, {
        ticker: newItem.ticker.toUpperCase(),
        quantity: parseFloat(newItem.quantity),
        purchase_price: parseFloat(newItem.purchase_price),
        notes: newItem.notes,
      });

      if (response.success) {
        const updatedPortfolios = portfolios.map((p) =>
          p.id === selectedPortfolio.id
            ? { ...p, items: [...p.items, response.item] }
            : p
        );
        setPortfolios(updatedPortfolios);
        setSelectedPortfolio(
          updatedPortfolios.find((p) => p.id === selectedPortfolio.id)
        );
        setNewItem({ ticker: "", quantity: "", purchase_price: "", notes: "" });
        setShowAddItemModal(false);
      } else {
        setError(response.error || "Failed to add item");
      }
    } catch (error) {
      setError("Failed to add item");
    }
  };

  const handleUpdateItem = async (e) => {
    e.preventDefault();
    if (!editingItem || !selectedPortfolio) return;

    try {
      const response = await updatePortfolioItem(
        selectedPortfolio.id,
        editingItem.id,
        {
          ticker: editingItem.ticker.toUpperCase(),
          quantity: parseFloat(editingItem.quantity),
          purchase_price: parseFloat(editingItem.purchase_price),
          notes: editingItem.notes,
        }
      );

      if (response.success) {
        const updatedPortfolios = portfolios.map((p) =>
          p.id === selectedPortfolio.id
            ? {
                ...p,
                items: p.items.map((item) =>
                  item.id === editingItem.id ? response.item : item
                ),
              }
            : p
        );
        setPortfolios(updatedPortfolios);
        setSelectedPortfolio(
          updatedPortfolios.find((p) => p.id === selectedPortfolio.id)
        );
        setEditingItem(null);
      } else {
        setError(response.error || "Failed to update item");
      }
    } catch (error) {
      setError("Failed to update item");
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!confirm("Are you sure you want to delete this item?")) return;

    try {
      const response = await deletePortfolioItem(selectedPortfolio.id, itemId);
      if (response.success) {
        const updatedPortfolios = portfolios.map((p) =>
          p.id === selectedPortfolio.id
            ? { ...p, items: p.items.filter((item) => item.id !== itemId) }
            : p
        );
        setPortfolios(updatedPortfolios);
        setSelectedPortfolio(
          updatedPortfolios.find((p) => p.id === selectedPortfolio.id)
        );
      } else {
        setError(response.error || "Failed to delete item");
      }
    } catch (error) {
      setError("Failed to delete item");
    }
  };

  const handlePredictEarnings = async () => {
    if (!selectedPortfolio) return;

    setPredictionLoading(true);
    setError("");

    try {
      const response = await predictPortfolioEarnings(selectedPortfolio.id, {
        method: predictionMethod,
        days: predictionDays,
      });

      if (response.success) {
        setPredictionResult(response);
        setShowPredictionModal(true);
      } else {
        setPredictionResult(response); // Contains error and missing models info
        setShowPredictionModal(true);
      }
    } catch (error) {
      setError("Failed to predict portfolio earnings");
    } finally {
      setPredictionLoading(false);
    }
  };

  const closePredictionModal = () => {
    setShowPredictionModal(false);
    setPredictionResult(null);
  };

  const calculatePortfolioValue = (portfolio) => {
    if (!portfolio || !portfolio.items) return 0;
    return portfolio.items.reduce(
      (total, item) => total + item.quantity * item.purchase_price,
      0
    );
  };

  if (loading) {
    return <div className="portfolio-loading">Loading portfolios...</div>;
  }

  return (
    <div className="portfolio-page">
      <div className="portfolio-header">
        <h1>My Portfolios</h1>
        <p>Welcome back, {user?.username}!</p>
        <button
          className="create-portfolio-btn"
          onClick={() => setShowCreateModal(true)}
        >
          Create New Portfolio
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="portfolio-content">
        <div className="portfolio-sidebar">
          <h3>Your Portfolios</h3>
          {portfolios.length === 0 ? (
            <p className="no-portfolios">
              No portfolios yet. Create your first one!
            </p>
          ) : (
            <div className="portfolio-list">
              {portfolios.map((portfolio) => (
                <div
                  key={portfolio.id}
                  className={`portfolio-item ${
                    selectedPortfolio?.id === portfolio.id ? "active" : ""
                  }`}
                  onClick={() => setSelectedPortfolio(portfolio)}
                >
                  <h4>{portfolio.name}</h4>
                  <p>{portfolio.items.length} stocks</p>
                  <p>${calculatePortfolioValue(portfolio).toFixed(2)}</p>
                  <button
                    className="delete-portfolio-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeletePortfolio(portfolio.id);
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="portfolio-main">
          {selectedPortfolio ? (
            <>
              <div className="portfolio-details">
                <h2>{selectedPortfolio.name}</h2>
                <div className="portfolio-stats">
                  <div className="stat">
                    <span>Total Value</span>
                    <span>
                      ${calculatePortfolioValue(selectedPortfolio).toFixed(2)}
                    </span>
                  </div>
                  <div className="stat">
                    <span>Total Stocks</span>
                    <span>{selectedPortfolio.items.length}</span>
                  </div>
                  <div className="stat">
                    <span>Created</span>
                    <span>
                      {new Date(
                        selectedPortfolio.created_at
                      ).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <button
                  className="add-item-btn"
                  onClick={() => setShowAddItemModal(true)}
                >
                  Add Stock
                </button>
              </div>

              <div className="portfolio-prediction">
                <h3>Earnings Prediction</h3>
                <div className="prediction-controls">
                  <div className="prediction-inputs">
                    <div className="input-group">
                      <label htmlFor="predictionMethod">Method:</label>
                      <select
                        id="predictionMethod"
                        value={predictionMethod}
                        onChange={(e) => setPredictionMethod(e.target.value)}
                      >
                        <option value="average">
                          Average (All Algorithms)
                        </option>
                        <option value="lstm">LSTM Neural Network</option>
                        <option value="arima">ARIMA Model</option>
                        <option value="prophet">Prophet Forecasting</option>
                      </select>
                    </div>
                    <div className="input-group">
                      <label htmlFor="predictionDays">Days to Predict:</label>
                      <input
                        type="number"
                        id="predictionDays"
                        value={predictionDays}
                        onChange={(e) =>
                          setPredictionDays(parseInt(e.target.value))
                        }
                        min="1"
                        max="365"
                      />
                    </div>
                  </div>
                  <button
                    className="predict-btn"
                    onClick={handlePredictEarnings}
                    disabled={
                      predictionLoading || !selectedPortfolio?.items?.length
                    }
                  >
                    {predictionLoading ? "Predicting..." : "Predict Earnings"}
                  </button>
                </div>
              </div>

              <div className="portfolio-items">
                <h3>Holdings</h3>
                {selectedPortfolio.items.length === 0 ? (
                  <p className="no-items">No stocks in this portfolio yet.</p>
                ) : (
                  <div className="items-table">
                    <div className="table-header">
                      <span>Ticker</span>
                      <span>Quantity</span>
                      <span>Purchase Price</span>
                      <span>Total Value</span>
                      <span>Notes</span>
                      <span>Actions</span>
                    </div>
                    {selectedPortfolio.items.map((item) => (
                      <div key={item.id} className="table-row">
                        <span className="ticker">{item.ticker}</span>
                        <span>{item.quantity}</span>
                        <span>${item.purchase_price.toFixed(2)}</span>
                        <span>
                          ${(item.quantity * item.purchase_price).toFixed(2)}
                        </span>
                        <span className="notes">{item.notes || "-"}</span>
                        <span className="actions">
                          <button
                            className="edit-btn"
                            onClick={() => setEditingItem(item)}
                          >
                            Edit
                          </button>
                          <button
                            className="delete-btn"
                            onClick={() => handleDeleteItem(item.id)}
                          >
                            Delete
                          </button>
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="no-portfolio-selected">
              <h2>Select a portfolio to view details</h2>
              <p>Choose a portfolio from the sidebar or create a new one.</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Portfolio Modal */}
      {showCreateModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowCreateModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Create New Portfolio</h3>
            <form onSubmit={handleCreatePortfolio}>
              <div className="form-group">
                <label htmlFor="portfolioName">Portfolio Name</label>
                <input
                  type="text"
                  id="portfolioName"
                  value={newPortfolioName}
                  onChange={(e) => setNewPortfolioName(e.target.value)}
                  placeholder="Enter portfolio name"
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit">Create Portfolio</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Item Modal */}
      {showAddItemModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowAddItemModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Add Stock to Portfolio</h3>
            <form onSubmit={handleAddItem}>
              <div className="form-group">
                <label htmlFor="ticker">Ticker Symbol</label>
                <TickerAutocomplete
                  name="ticker"
                  value={newItem.ticker}
                  onChange={(e) =>
                    setNewItem({ ...newItem, ticker: e.target.value })
                  }
                  placeholder="e.g., AAPL, GOOGL, ^GSPC"
                  size="small"
                  fullWidth={false}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="quantity">Quantity</label>
                <input
                  type="number"
                  id="quantity"
                  value={newItem.quantity}
                  onChange={(e) =>
                    setNewItem({ ...newItem, quantity: e.target.value })
                  }
                  placeholder="Number of shares"
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="purchasePrice">Purchase Price</label>
                <input
                  type="number"
                  id="purchasePrice"
                  value={newItem.purchase_price}
                  onChange={(e) =>
                    setNewItem({ ...newItem, purchase_price: e.target.value })
                  }
                  placeholder="Price per share"
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="notes">Notes (Optional)</label>
                <textarea
                  id="notes"
                  value={newItem.notes}
                  onChange={(e) =>
                    setNewItem({ ...newItem, notes: e.target.value })
                  }
                  placeholder="Any notes about this investment"
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setShowAddItemModal(false)}
                >
                  Cancel
                </button>
                <button type="submit">Add Stock</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Item Modal */}
      {editingItem && (
        <div className="modal-overlay" onClick={() => setEditingItem(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Stock</h3>
            <form onSubmit={handleUpdateItem}>
              <div className="form-group">
                <label htmlFor="editTicker">Ticker Symbol</label>
                <TickerAutocomplete
                  name="ticker"
                  value={editingItem.ticker}
                  onChange={(e) =>
                    setEditingItem({ ...editingItem, ticker: e.target.value })
                  }
                  placeholder="e.g., AAPL, GOOGL, ^GSPC"
                  size="small"
                  fullWidth={false}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="editQuantity">Quantity</label>
                <input
                  type="number"
                  id="editQuantity"
                  value={editingItem.quantity}
                  onChange={(e) =>
                    setEditingItem({ ...editingItem, quantity: e.target.value })
                  }
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="editPurchasePrice">Purchase Price</label>
                <input
                  type="number"
                  id="editPurchasePrice"
                  value={editingItem.purchase_price}
                  onChange={(e) =>
                    setEditingItem({
                      ...editingItem,
                      purchase_price: e.target.value,
                    })
                  }
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="editNotes">Notes</label>
                <textarea
                  id="editNotes"
                  value={editingItem.notes || ""}
                  onChange={(e) =>
                    setEditingItem({ ...editingItem, notes: e.target.value })
                  }
                  placeholder="Any notes about this investment"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setEditingItem(null)}>
                  Cancel
                </button>
                <button type="submit">Update Stock</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Prediction Results Modal */}
      {showPredictionModal && predictionResult && (
        <div className="modal-overlay" onClick={closePredictionModal}>
          <div
            className="modal-content prediction-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <button className="modal-close" onClick={closePredictionModal}>
              ×
            </button>

            {predictionResult.success ? (
              <div className="prediction-success">
                <h3>📈 Portfolio Earnings Prediction</h3>
                <div className="prediction-summary">
                  <div className="prediction-info">
                    <span>
                      <strong>Method:</strong>{" "}
                      {predictionResult.method.toUpperCase()}
                    </span>
                    <span>
                      <strong>Prediction Period:</strong>{" "}
                      {predictionResult.days} days
                    </span>
                  </div>

                  <div className="total-prediction">
                    <div className="metric">
                      <span className="label">Current Portfolio Value:</span>
                      <span className="value">
                        $
                        {predictionResult.total_metrics.current_value.toFixed(
                          2
                        )}
                      </span>
                    </div>
                    <div className="metric">
                      <span className="label">Predicted Portfolio Value:</span>
                      <span className="value">
                        $
                        {predictionResult.total_metrics.predicted_value.toFixed(
                          2
                        )}
                      </span>
                    </div>
                    <div className="metric main-metric">
                      <span className="label">Expected Profit/Loss:</span>
                      <span
                        className={`value ${
                          predictionResult.total_metrics.profit_loss >= 0
                            ? "profit"
                            : "loss"
                        }`}
                      >
                        ${predictionResult.total_metrics.profit_loss.toFixed(2)}
                        (
                        {predictionResult.total_metrics.profit_loss_percent.toFixed(
                          2
                        )}
                        %)
                      </span>
                    </div>
                  </div>
                </div>

                <div className="stock-predictions">
                  <h4>Individual Stock Predictions:</h4>
                  <div className="predictions-table">
                    <div className="table-header">
                      <span>Stock</span>
                      <span>Current Price</span>
                      <span>Predicted Price</span>
                      <span>Expected P&L</span>
                    </div>
                    {predictionResult.stock_predictions.map((stock, index) => (
                      <div key={index} className="table-row">
                        <span className="ticker">{stock.ticker}</span>
                        <span>${stock.purchase_price.toFixed(2)}</span>
                        <span>${stock.predicted_price.toFixed(2)}</span>
                        <span
                          className={stock.profit_loss >= 0 ? "profit" : "loss"}
                        >
                          ${stock.profit_loss.toFixed(2)} (
                          {stock.profit_loss_percent.toFixed(2)}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="prediction-error">
                <h3>⚠️ Missing Trained Models</h3>
                <p className="error-description">
                  To predict earnings using{" "}
                  <strong>
                    {predictionResult.required_algorithms?.join(", ")}
                  </strong>
                  , you need trained models for all stocks in your portfolio.
                </p>

                <div className="missing-models">
                  <h4>Missing Models:</h4>
                  {Object.entries(predictionResult.missing_models || {}).map(
                    ([ticker, algorithms]) => (
                      <div key={ticker} className="missing-model-item">
                        <span className="ticker">{ticker}</span>
                        <span className="algorithms">
                          Missing: {algorithms.join(", ")}
                        </span>
                        <div className="train-links">
                          {algorithms.includes("lstm") && (
                            <a href="/lstm" className="train-link">
                              Train LSTM
                            </a>
                          )}
                          {algorithms.includes("arima") && (
                            <a href="/arima" className="train-link">
                              Train ARIMA
                            </a>
                          )}
                          {algorithms.includes("prophet") && (
                            <a href="/prophet" className="train-link">
                              Train Prophet
                            </a>
                          )}
                        </div>
                      </div>
                    )
                  )}
                </div>

                <p className="help-text">
                  Train the missing models first, then return to predict your
                  portfolio earnings.
                </p>
              </div>
            )}

            <div className="modal-actions">
              <button type="button" onClick={closePredictionModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioPage;
