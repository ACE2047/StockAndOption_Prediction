import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function OptionsAnalysis({ symbol, selectedOption }) {
  const [optionsData, setOptionsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'call', 'put'
  const [sortBy, setSortBy] = useState('expiration'); // 'strike', 'expiration', 'price_difference'
  const [selectedOptionData, setSelectedOptionData] = useState(null);

  useEffect(() => {
    if (!symbol) return;

    setLoading(true);
    axios.get(`/api/option_analysis/${symbol}`)
      .then(response => {
        setOptionsData(response.data || []);
        setError(null);
        
        // If a specific option is selected, find its data
        if (selectedOption) {
          const option = response.data.find(opt => opt.id === selectedOption);
          setSelectedOptionData(option || null);
        } else {
          setSelectedOptionData(null);
        }
      })
      .catch(err => {
        console.error("Error fetching options data:", err);
        setError("Failed to fetch options data");
        setOptionsData([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [symbol, selectedOption]);

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading options data...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  if (optionsData.length === 0) {
    return <div className="p-4">No options data available for {symbol}</div>;
  }

  // Filter options based on selected filter
  const filteredOptions = optionsData.filter(option => {
    if (filter === 'all') return true;
    return option.type && option.type.toLowerCase() === filter;
  });

  // Sort options based on selected sorting criteria
  const sortedOptions = [...filteredOptions].sort((a, b) => {
    switch (sortBy) {
      case 'strike':
        return a.strike_price - b.strike_price;
      case 'expiration':
        return new Date(a.expiration_date) - new Date(b.expiration_date);
      case 'price_difference':
        // Sort by largest price difference (potentially most mispriced options)
        return (b.price_difference || 0) - (a.price_difference || 0);
      default:
        return 0;
    }
  });

  // Prepare data for the chart
  const chartData = sortedOptions
    .filter(option => option.price_difference !== undefined)
    .slice(0, 10) // Take top 10 for clarity
    .map(option => ({
      contract: option.ticker,
      priceDifference: option.price_difference,
      type: option.type || 'unknown',
      strike: option.strike_price || 0,
      expiration: option.expiration_date || 'unknown'
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">{symbol} - Options Analysis</h2>
        <p className="text-gray-600">Analyzing options for potential mispricing based on Black-Scholes model</p>
      </div>

      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Type</label>
          <select 
            className="border rounded px-3 py-2"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Options</option>
            <option value="call">Calls Only</option>
            <option value="put">Puts Only</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
          <select 
            className="border rounded px-3 py-2"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="expiration">Expiration Date</option>
            <option value="strike">Strike Price</option>
            <option value="price_difference">Price Difference</option>
          </select>
        </div>
      </div>

      {selectedOptionData && (
        <div className="bg-blue-50 p-4 rounded-md mb-6">
          <h3 className="text-lg font-semibold mb-2">Selected Option: {selectedOptionData.ticker}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Type</p>
              <p className="font-medium">{selectedOptionData.type || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Strike Price</p>
              <p className="font-medium">${selectedOptionData.strike_price || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Expiration</p>
              <p className="font-medium">{selectedOptionData.expiration_date || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Market Price</p>
              <p className="font-medium">${selectedOptionData.last_price || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Theoretical Price</p>
              <p className="font-medium">${selectedOptionData.theoretical_price?.toFixed(2) || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Mispricing</p>
              <p className={`font-medium ${selectedOptionData.is_undervalued ? 'text-green-600' : 'text-red-600'}`}>
                ${Math.abs(selectedOptionData.price_difference || 0).toFixed(2)} 
                {selectedOptionData.is_undervalued ? ' (Undervalued)' : ' (Overvalued)'}
              </p>
            </div>
          </div>
        </div>
      )}

      {chartData.length > 0 && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-4">Price Difference Analysis</h3>
          <p className="text-sm text-gray-600 mb-2">
            This chart shows the difference between Black-Scholes theoretical price and market price.
            Positive values indicate potentially undervalued options.
          </p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="contract" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [`${value.toFixed(2)}`, 'Price Difference']}
                  labelFormatter={(label) => `Contract: ${label}`}
                />
                <Legend />
                <Bar 
                  dataKey="priceDifference" 
                  name="Price Difference" 
                  // Color bars based on positive (undervalued) or negative (overvalued)
                  fill={(data) => (data.priceDifference >= 0 ? '#82ca9d' : '#ff7300')}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-4">Options Table</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead>
              <tr>
                <th className="px-4 py-2 border">Contract</th>
                <th className="px-4 py-2 border">Type</th>
                <th className="px-4 py-2 border">Strike</th>
                <th className="px-4 py-2 border">Expiration</th>
                <th className="px-4 py-2 border">Market Price</th>
                <th className="px-4 py-2 border">Theoretical</th>
                <th className="px-4 py-2 border">Difference</th>
                <th className="px-4 py-2 border">Analysis</th>
              </tr>
            </thead>
            <tbody>
              {sortedOptions.map((option, index) => (
                <tr key={index} className={selectedOption === option.id ? 'bg-blue-50' : ''}>
                  <td className="px-4 py-2 border">{option.ticker}</td>
                  <td className="px-4 py-2 border capitalize">{option.type || 'N/A'}</td>
                  <td className="px-4 py-2 border">${option.strike_price || 'N/A'}</td>
                  <td className="px-4 py-2 border">{option.expiration_date || 'N/A'}</td>
                  <td className="px-4 py-2 border">${option.last_price || 'N/A'}</td>
                  <td className="px-4 py-2 border">${option.theoretical_price?.toFixed(2) || 'N/A'}</td>
                  <td className={`px-4 py-2 border ${option.is_undervalued ? 'text-green-600' : 'text-red-600'}`}>
                    ${Math.abs(option.price_difference || 0).toFixed(2)}
                  </td>
                  <td className={`px-4 py-2 border font-medium ${option.is_undervalued ? 'text-green-600' : 'text-red-600'}`}>
                    {option.is_undervalued ? 'Undervalued' : 'Overvalued'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}