import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function StockPrediction({ symbol }) {
  const [predictionData, setPredictionData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

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
  
  // Add predictions for both models
  for (let i = 0; i < predictionData.multi_day_predictions.linear_regression.length; i++) {
    const predictionDate = new Date(lastDate);
    predictionDate.setDate(predictionDate.getDate() + i + 1);
    
    predictionChartData.push({
      date: predictionDate.toLocaleDateString(),
      linear: predictionData.multi_day_predictions.linear_regression[i],
      ransac: predictionData.multi_day_predictions.ransac[i]
    });
  }

  // Combine historical and prediction data (last 14 days of historical)
  const chartData = [
    ...historicalData.slice(-14).map(item => ({ 
      date: item.date, 
      historical: item.price,
      linear: null,
      ransac: null
    })),
    ...predictionChartData.map(item => ({
      date: item.date,
      historical: null,
      linear: item.linear,
      ransac: item.ransac
    }))
  ];

  // Function to calculate percent change
  const percentChange = (newValue, oldValue) => {
    return ((newValue - oldValue) / oldValue * 100).toFixed(2);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">{symbol} - Price Prediction</h2>
        <p className="text-gray-600">Current Price: ${predictionData.current_price.toFixed(2)}</p>
        <p className="text-gray-600">Prediction Date: {predictionData.prediction_date}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-50 p-4 rounded-md shadow">
          <h3 className="text-lg font-semibold mb-2">Linear Regression Model</h3>
          <p className="text-lg">
            Next Day: <span className="font-bold">${predictionData.next_day_predictions.linear_regression.toFixed(2)}</span>
            <span className={`ml-2 ${predictionData.next_day_predictions.linear_regression > predictionData.current_price ? 'text-green-500' : 'text-red-500'}`}>
              ({percentChange(predictionData.next_day_predictions.linear_regression, predictionData.current_price)}%)
            </span>
          </p>
          <p className="text-sm text-gray-500">RMSE: {predictionData.model_performance.linear_regression_rmse.toFixed(2)}</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-md shadow">
          <h3 className="text-lg font-semibold mb-2">RANSAC Model</h3>
          <p className="text-lg">
            Next Day: <span className="font-bold">${predictionData.next_day_predictions.ransac.toFixed(2)}</span>
            <span className={`ml-2 ${predictionData.next_day_predictions.ransac > predictionData.current_price ? 'text-green-500' : 'text-red-500'}`}>
              ({percentChange(predictionData.next_day_predictions.ransac, predictionData.current_price)}%)
            </span>
          </p>
          <p className="text-sm text-gray-500">RMSE: {predictionData.model_performance.ransac_rmse.toFixed(2)}</p>
        </div>
      </div>

      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-4">Price Prediction Chart</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="historical" 
                stroke="#8884d8" 
                name="Historical Price" 
                strokeWidth={2} 
                dot={{ r: 2 }}
                connectNulls
              />
              <Line 
                type="monotone" 
                dataKey="linear" 
                stroke="#82ca9d" 
                name="Linear Regression"
                strokeWidth={2}
                strokeDasharray="5 5"
                connectNulls 
              />
              <Line 
                type="monotone" 
                dataKey="ransac" 
                stroke="#ff7300" 
                name="RANSAC"
                strokeWidth={2}
                strokeDasharray="3 3"
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

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
                <th className="px-4 py-2 border">Avg. Prediction</th>
              </tr>
            </thead>
            <tbody>
              {predictionChartData.map((item, index) => {
                const avgPrice = (item.linear + item.ransac) / 2;
                return (
                  <tr key={index}>
                    <td className="px-4 py-2 border">{index + 1}</td>
                    <td className="px-4 py-2 border">{item.date}</td>
                    <td className="px-4 py-2 border">${item.linear.toFixed(2)}</td>
                    <td className="px-4 py-2 border">${item.ransac.toFixed(2)}</td>
                    <td className="px-4 py-2 border">${avgPrice.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default StockPrediction;