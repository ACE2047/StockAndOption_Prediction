import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, ReferenceLine } from 'recharts';

function CombinedAnalysis({ symbol }) {
  const [combinedData, setCombinedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [displayMode, setDisplayMode] = useState('comprehensive'); // 'comprehensive', 'prediction', 'options'

  useEffect(() => {
    if (!symbol) return;

    setLoading(true);
    axios.get(`/api/combined_analysis/${symbol}`)
      .then(response => {
        setCombinedData(response.data);
        setError(null);
      })
      .catch(err => {
        console.error("Error fetching combined data:", err);
        setError("Failed to fetch combined analysis data");
        setCombinedData(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [symbol]);

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading combined analysis...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  if (!combinedData) {
    return <div className="p-4">No combined analysis data available for {symbol}</div>;
  }

  // Extract stock prediction and options data
  const stockPrediction = combinedData.stock_prediction;
  const optionsAnalysis = combinedData.options_analysis;

  // Prepare chart data for stock predictions
  const historicalData = Object.entries(stockPrediction.historical_data || {}).map(([date, price]) => ({
    date: new Date(parseInt(date)).toLocaleDateString(),
    price
  })).sort((a, b) => new Date(a.date) - new Date(b.date));

  const predictionChartData = [];
  const lastDate = new Date(historicalData[historicalData.length - 1].date);
  
  for (let i = 0; i < stockPrediction.multi_day_predictions.linear_regression.length; i++) {
    const predictionDate = new Date(lastDate);
    predictionDate.setDate(predictionDate.getDate() + i + 1);
    
    predictionChartData.push({
      date: predictionDate.toLocaleDateString(),
      linear: stockPrediction.multi_day_predictions.linear_regression[i],
      ransac: stockPrediction.multi_day_predictions.ransac[i]
    });
  }

  // Combine historical and prediction data
  const chartData = [
    ...historicalData.slice(-10).map(item => ({ 
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

  // Group options by expiration date
  const optionsByExpiry = {};
  optionsAnalysis.forEach(option => {
    const expiry = option.expiration;
    if (!optionsByExpiry[expiry]) {
      optionsByExpiry[expiry] = [];
    }
    optionsByExpiry[expiry].push(option);
  });

  // Find options with best profit potential
  const sortedOptions = [...optionsAnalysis].sort((a, b) => b.profit_potential - a.profit_potential);
  const topOptions = sortedOptions.slice(0, 5);

  // Risk-return scatter plot data
  const riskReturnData = optionsAnalysis.map(option => ({
    id: option.contract,
    x: option.days_to_expiry,
    y: option.profit_potential,
    z: option.type,
    strike: option.strike
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">{symbol} - Combined Analysis</h2>
        <p className="text-gray-600">
          Current Price: ${stockPrediction.current_price.toFixed(2)} | 
          Prediction Date: {stockPrediction.prediction_date}
        </p>
        
        <div className="mt-4 flex space-x-2">
          <button 
            className={`px-4 py-2 rounded ${displayMode === 'comprehensive' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setDisplayMode('comprehensive')}
          >
            Comprehensive View
          </button>
          <button 
            className={`px-4 py-2 rounded ${displayMode === 'prediction' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setDisplayMode('prediction')}
          >
            Stock Prediction
          </button>
          <button 
            className={`px-4 py-2 rounded ${displayMode === 'options' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setDisplayMode('options')}
          >
            Options Analysis
          </button>
        </div>
      </div>

      {(displayMode === 'comprehensive' || displayMode === 'prediction') && (
        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Stock Price Prediction</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-md shadow">
              <h3 className="text-lg font-semibold mb-2">Next Day Predictions</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Linear Regression</p>
                  <p className="text-lg font-bold">${stockPrediction.next_day_predictions.linear_regression.toFixed(2)}</p>
                  <p className={`text-sm ${stockPrediction.next_day_predictions.linear_regression > stockPrediction.current_price ? 'text-green-500' : 'text-red-500'}`}>
                    {((stockPrediction.next_day_predictions.linear_regression - stockPrediction.current_price) / stockPrediction.current_price * 100).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">RANSAC</p>
                  <p className="text-lg font-bold">${stockPrediction.next_day_predictions.ransac.toFixed(2)}</p>
                  <p className={`text-sm ${stockPrediction.next_day_predictions.ransac > stockPrediction.current_price ? 'text-green-500' : 'text-red-500'}`}>
                    {((stockPrediction.next_day_predictions.ransac - stockPrediction.current_price) / stockPrediction.current_price * 100).toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded-md shadow">
              <h3 className="text-lg font-semibold mb-2">Model Performance</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Linear Regression RMSE</p>
                  <p className="text-lg">{stockPrediction.model_performance.linear_regression_rmse.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">RANSAC RMSE</p>
                  <p className="text-lg">{stockPrediction.model_performance.ransac_rmse.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="h-64 md:h-80">
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
                <ReferenceLine y={stockPrediction.current_price} stroke="red" strokeDasharray="3 3" label="Current" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {(displayMode === 'comprehensive' || displayMode === 'options') && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-4">Options Analysis</h3>
          
          <div className="mb-6">
            <h4 className="text-lg font-semibold mb-2">Top Opportunities</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white">
                <thead>
                  <tr>
                    <th className="px-4 py-2 border">Contract</th>
                    <th className="px-4 py-2 border">Type</th>
                    <th className="px-4 py-2 border">Strike</th>
                    <th className="px-4 py-2 border">Expiration</th>
                    <th className="px-4 py-2 border">Days Left</th>
                    <th className="px-4 py-2 border">Theoretical</th>
                    <th className="px-4 py-2 border">Potential Value</th>
                    <th className="px-4 py-2 border">Profit Potential</th>
                  </tr>
                </thead>
                <tbody>
                  {topOptions.map((option, idx) => (
                    <tr key={idx} className={idx === 0 ? 'bg-green-50' : ''}>
                      <td className="px-4 py-2 border">{option.contract}</td>
                      <td className="px-4 py-2 border capitalize">{option.type}</td>
                      <td className="px-4 py-2 border">${option.strike.toFixed(2)}</td>
                      <td className="px-4 py-2 border">{option.expiration}</td>
                      <td className="px-4 py-2 border">{option.days_to_expiry}</td>
                      <td className="px-4 py-2 border">${option.theoretical_price.toFixed(2)}</td>
                      <td className="px-4 py-2 border">${option.potential_value.toFixed(2)}</td>
                      <td className={`px-4 py-2 border font-medium ${option.profit_potential > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${option.profit_potential.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-lg font-semibold mb-2">Risk-Return Analysis</h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid />
                    <XAxis 
                      type="number" 
                      dataKey="x" 
                      name="Days to Expiry" 
                      label={{ value: 'Days to Expiry', position: 'insideBottomRight', offset: -5 }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="y" 
                      name="Profit Potential" 
                      label={{ value: 'Profit Potential ($)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      cursor={{ strokeDasharray: '3 3' }}
                      formatter={(value, name, props) => {
                        if (name === 'x') return [`${value} days`, 'Time to Expiry'];
                        if (name === 'y') return [`$${value.toFixed(2)}`, 'Profit Potential'];
                        return [value, name];
                      }}
                      labelFormatter={(value) => null}
                      content={({active, payload}) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-white p-2 border rounded shadow">
                              <p>{payload[0].payload.id}</p>
                              <p className="capitalize">{payload[0].payload.z} - Strike: ${payload[0].payload.strike}</p>
                              <p>Days: {payload[0].payload.x}</p>
                              <p>Potential: ${payload[0].payload.y.toFixed(2)}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter 
                      name="Call Options" 
                      data={riskReturnData.filter(d => d.z === 'call')} 
                      fill="#8884d8" 
                      shape="circle"
                    />
                    <Scatter 
                      name="Put Options" 
                      data={riskReturnData.filter(d => d.z === 'put')} 
                      fill="#82ca9d" 
                      shape="triangle"
                    />
                    <Legend />
                    <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold mb-2">Options by Expiration</h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={Object.keys(optionsByExpiry).map(expiry => ({
                    expiry,
                    calls: optionsByExpiry[expiry].filter(o => o.type === 'call').length,
                    puts: optionsByExpiry[expiry].filter(o => o.type === 'put').length
                  }))} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="expiry" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="calls" name="Call Options" fill="#8884d8" />
                    <Bar dataKey="puts" name="Put Options" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 p-4 bg-blue-50 rounded-md">
        <h3 className="text-lg font-semibold mb-2">Analysis Summary</h3>
        <p className="mb-2">
          Based on our models, {symbol} is predicted to 
          {stockPrediction.next_day_predictions.linear_regression > stockPrediction.current_price ? 
            ' increase' : ' decrease'} in value over the next trading day.
        </p>
        <p className="mb-2">
          The most promising option contract is {topOptions[0]?.contract || 'not available'} with a potential profit of 
          ${topOptions[0]?.profit_potential.toFixed(2) || '0.00'}.
        </p>
        <p>
          Recommendation: {
            stockPrediction.next_day_predictions.linear_regression > stockPrediction.current_price && topOptions[0]?.profit_potential > 0 ?
              'Consider both stock purchase and options strategy for maximum potential.' :
            stockPrediction.next_day_predictions.linear_regression > stockPrediction.current_price ?
              'Stock purchase may be favorable, but exercise caution with options.' :
            topOptions[0]?.profit_potential > 0 ?
              'Stock may decline, but selected options strategy could be profitable.' :
              'Exercise caution with both stock and options positions at this time.'
          }
        </p>
      </div>
    </div>
  );
}

export default CombinedAnalysis;