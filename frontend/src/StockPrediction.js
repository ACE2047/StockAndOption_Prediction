import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function StockPrediction({ symbol }) {
  const [predictionData, setPredictionData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedHorizon, setSelectedHorizon] = useState('short_term');

  useEffect(() => {
    if (!symbol) return;

    setLoading(true);
    axios.get(`/api/stock_prediction/${symbol}`)
      .then(response => {
        setPredictionData(response.data);
        setError(null);
      })
      .catch(err => {
        console.error("Error fetching prediction data:", err);
        setError("Failed to fetch prediction data");
        setPredictionData(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [symbol]);

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading prediction data...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  if (!predictionData) {
    return <div className="p-4">No prediction data available for {symbol}</div>;
  }

  // Prepare historical data for chart
  const historicalData = Object.entries(predictionData.historical_data || {}).map(([date, price]) => ({
    date: new Date(parseInt(date)).toLocaleDateString(),
    price
  }));

  // Sort by date
  historicalData.sort((a, b) => new Date(a.date) - new Date(b.date));

  // Prepare prediction data for chart
  const predictionChartData = [];
  
  // Last historical date to start predictions
  const lastDate = new Date(historicalData[historicalData.length - 1].date);
  
  // Add predictions for the selected horizon
  const horizonPredictions = predictionData.horizons[selectedHorizon].multi_day;
  
  for (let i = 0; i < horizonPredictions.linear_regression.length; i++) {
    const predictionDate = new Date(lastDate);
    predictionDate.setDate(predictionDate.getDate() + i + 1);
    
    predictionChartData.push({
      date: predictionDate.toLocaleDateString(),
      linear: horizonPredictions.linear_regression[i],
      ransac: horizonPredictions.ransac[i],
      random_forest: horizonPredictions.random_forest[i],
      gradient_boosting: horizonPredictions.gradient_boosting[i],
      ensemble: horizonPredictions.ensemble[i]
    });
  }

  // Combine historical and prediction data (last 14 days of historical)
  const chartData = [
    ...historicalData.slice(-14).map(item => ({ 
      date: item.date, 
      historical: item.price,
      linear: null,
      ransac: null,
      random_forest: null,
      gradient_boosting: null,
      ensemble: null
    })),
    ...predictionChartData.map(item => ({
      date: item.date,
      historical: null,
      linear: item.linear,
      ransac: item.ransac,
      random_forest: item.random_forest,
      gradient_boosting: item.gradient_boosting,
      ensemble: item.ensemble
    }))
  ];

  // Function to calculate percent change
  const percentChange = (newValue, oldValue) => {
    return ((newValue - oldValue) / oldValue * 100).toFixed(2);
  };

  // Function to get horizon display name
  const getHorizonDisplayName = (horizon) => {
    switch (horizon) {
      case 'short_term': return 'Short Term (1-5 days)';
      case 'medium_term': return 'Medium Term (1-3 months)';
      case 'long_term': return 'Long Term (3-12 months)';
      default: return horizon;
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">{symbol} - Price Prediction</h2>
        <p className="text-gray-600">Current Price: ${predictionData.current_price.toFixed(2)}</p>
        <p className="text-gray-600">Prediction Date: {predictionData.prediction_date}</p>
        
        {/* Horizon selector */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700">Prediction Horizon</label>
          <select
            value={selectedHorizon}
            onChange={(e) => setSelectedHorizon(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="short_term">Short Term (1-5 days)</option>
            <option value="medium_term">Medium Term (1-3 months)</option>
            <option value="long_term">Long Term (3-12 months)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-50 p-4 rounded-md shadow">
          <h3 className="text-lg font-semibold mb-2">Next Day Predictions</h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(predictionData.horizons[selectedHorizon].next_day).map(([model, price]) => (
              <div key={model}>
                <p className="text-sm text-gray-500">{model.replace('_', ' ').toUpperCase()}</p>
                <p className="text-lg font-bold">${price.toFixed(2)}</p>
                <p className={`text-sm ${price > predictionData.current_price ? 'text-green-500' : 'text-red-500'}`}>
                  ({percentChange(price, predictionData.current_price)}%)
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Price Chart */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Price Prediction Chart</h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="historical" stroke="#000000" name="Historical" />
              <Line type="monotone" dataKey="linear" stroke="#4CAF50" name="Linear Regression" />
              <Line type="monotone" dataKey="ransac" stroke="#F44336" name="RANSAC" />
              <Line type="monotone" dataKey="random_forest" stroke="#2196F3" name="Random Forest" />
              <Line type="monotone" dataKey="gradient_boosting" stroke="#9C27B0" name="Gradient Boosting" />
              <Line type="monotone" dataKey="ensemble" stroke="#FF9800" name="Ensemble" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Multi-day predictions table */}
      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-4">Multi-Day Predictions</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead>
              <tr>
                <th className="px-4 py-2 border">Day</th>
                <th className="px-4 py-2 border">Date</th>
                <th className="px-4 py-2 border">Linear Regression</th>
                <th className="px-4 py-2 border">RANSAC</th>
                <th className="px-4 py-2 border">Random Forest</th>
                <th className="px-4 py-2 border">Gradient Boosting</th>
                <th className="px-4 py-2 border">Ensemble</th>
              </tr>
            </thead>
            <tbody>
              {predictionChartData.map((item, index) => (
                <tr key={index}>
                  <td className="px-4 py-2 border">{index + 1}</td>
                  <td className="px-4 py-2 border">{item.date}</td>
                  <td className="px-4 py-2 border">${item.linear.toFixed(2)}</td>
                  <td className="px-4 py-2 border">${item.ransac.toFixed(2)}</td>
                  <td className="px-4 py-2 border">${item.random_forest.toFixed(2)}</td>
                  <td className="px-4 py-2 border">${item.gradient_boosting.toFixed(2)}</td>
                  <td className="px-4 py-2 border">${item.ensemble.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default StockPrediction;