import React, { useState, useEffect } from 'react';
import axios from 'axios';

function BlackScholesCalculator({ currentPrice = 100 }) {
  const [formData, setFormData] = useState({
    S: currentPrice, // Current stock price
    K: currentPrice, // Strike price
    T: 0.25, // Time to expiration in years (default: 3 months)
    r: 0.03, // Risk-free interest rate (default: 3%)
    sigma: 0.2, // Volatility (default: 20%)
    type: 'call' // Option type (call or put)
  });

  const [optionPrice, setOptionPrice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Update stock price when currentPrice prop changes
  useEffect(() => {
    setFormData(prev => ({ ...prev, S: currentPrice }));
  }, [currentPrice]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'type' ? value : parseFloat(value)
    }));
  };

  const calculatePrice = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/option_price', formData);
      setOptionPrice(response.data.price);
    } catch (err) {
      console.error("Error calculating option price:", err);
      setError("Failed to calculate option price. Please check your inputs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Black-Scholes Option Calculator</h2>
        <p className="text-gray-600">
          Calculate theoretical option prices using the Black-Scholes model
        </p>
      </div>

      <form onSubmit={calculatePrice} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stock Price (S)
          </label>
          <input
            type="number"
            name="S"
            value={formData.S}
            onChange={handleInputChange}
            className="border rounded w-full px-3 py-2"
            min="0.01"
            step="0.01"
            required
          />
          <p className="text-xs text-gray-500 mt-1">Current market price of the stock</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Strike Price (K)
          </label>
          <input
            type="number"
            name="K"
            value={formData.K}
            onChange={handleInputChange}
            className="border rounded w-full px-3 py-2"
            min="0.01"
            step="0.01"
            required
          />
          <p className="text-xs text-gray-500 mt-1">The price at which the option can be exercised</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Time to Expiration (T) in Years
          </label>
          <input
            type="number"
            name="T"
            value={formData.T}
            onChange={handleInputChange}
            className="border rounded w-full px-3 py-2"
            min="0.01"
            max="10"
            step="0.01"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Time until expiration in years (e.g., 0.25 = 3 months)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Risk-Free Rate (r)
          </label>
          <input
            type="number"
            name="r"
            value={formData.r}
            onChange={handleInputChange}
            className="border rounded w-full px-3 py-2"
            min="0"
            max="1"
            step="0.001"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Annual risk-free interest rate as a decimal (e.g., 0.03 = 3%)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Volatility (σ)
          </label>
          <input
            type="number"
            name="sigma"
            value={formData.sigma}
            onChange={handleInputChange}
            className="border rounded w-full px-3 py-2"
            min="0.01"
            max="2"
            step="0.01"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Annual volatility of the stock as a decimal (e.g., 0.2 = 20%)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Option Type
          </label>
          <select
            name="type"
            value={formData.type}
            onChange={handleInputChange}
            className="border rounded w-full px-3 py-2"
            required
          >
            <option value="call">Call Option</option>
            <option value="put">Put Option</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Call option (right to buy) or put option (right to sell)
          </p>
        </div>

        <div className="col-span-1 md:col-span-2">
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            disabled={loading}
          >
            {loading ? 'Calculating...' : 'Calculate Option Price'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-6 p-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {optionPrice !== null && !error && (
        <div className="mt-6 p-6 bg-green-50 rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Option Type</p>
              <p className="font-medium capitalize">{formData.type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Theoretical Price</p>
              <p className="text-2xl font-bold">${optionPrice.toFixed(2)}</p>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-green-200">
            <h4 className="font-medium mb-2">Interpretation</h4>
            <p className="text-sm">
              This theoretical price of <strong>${optionPrice.toFixed(2)}</strong> for 
              a {formData.type} option with strike price ${formData.K.toFixed(2)} on a stock 
              trading at ${formData.S.toFixed(2)} is based on the Black-Scholes model.
            </p>
            <p className="text-sm mt-2">
              The model assumes a risk-free rate of {(formData.r * 100).toFixed(1)}%, 
              volatility of {(formData.sigma * 100).toFixed(1)}%, and 
              time to expiration of {formData.T.toFixed(2)} years 
              ({Math.round(formData.T * 365)} days).
            </p>
          </div>
        </div>
      )}

      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-2">About Black-Scholes Model</h3>
        <p className="text-sm text-gray-700">
          The Black-Scholes model is a mathematical model used to estimate the price of European-style options. 
          It takes into account the current stock price, expected volatility, time to expiration, 
          risk-free interest rate, and strike price.
        </p>
        <p className="text-sm text-gray-700 mt-2">
          While the model makes several simplifying assumptions, it provides a widely-used baseline for 
          evaluating option prices in financial markets.
        </p>
      </div>
    </div>
  );
}

export default BlackScholesCalculator;