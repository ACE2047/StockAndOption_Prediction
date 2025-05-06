import React, { useState, useEffect } from 'react';

function Dropdowns({ onStockSelect, onOptionSelect }) {
  const [stocks, setStocks] = useState([]);
  const [options, setOptions] = useState([]);
  const [selectedStock, setSelectedStock] = useState('');
  const [loadingStocks, setLoadingStocks] = useState(true);
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [error, setError] = useState(null);

  // Fetch list of stocks on component mount
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        setLoadingStocks(true);
        const response = await fetch('/api/tickers');
        
        if (!response.ok) {
          throw new Error('Failed to fetch stock tickers');
        }
        
        const data = await response.json();
        
        // Sort tickers alphabetically
        const sortedStocks = data
          .filter(ticker => ticker.ticker && ticker.name)
          .sort((a, b) => a.ticker.localeCompare(b.ticker));
        
        setStocks(sortedStocks);
        setError(null);
      } catch (err) {
        console.error('Error fetching stocks:', err);
        setError('Failed to load stock list');
        setStocks([]);
      } finally {
        setLoadingStocks(false);
      }
    };

    fetchStocks();
  }, []);

  // Fetch options for selected stock
  useEffect(() => {
    if (!selectedStock) return;
    
    const fetchOptions = async () => {
      try {
        setLoadingOptions(true);
        const response = await fetch(`/api/options/${selectedStock}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch options data');
        }
        
        const data = await response.json();
        
        setOptions(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching options:', err);
        setError('Failed to load options data');
        setOptions([]);
      } finally {
        setLoadingOptions(false);
      }
    };

    fetchOptions();
  }, [selectedStock]);

  // Handle stock selection
  const handleStockChange = (e) => {
    const symbol = e.target.value;
    setSelectedStock(symbol);
    onStockSelect(symbol);
    // Clear selected option when stock changes
    onOptionSelect('');
  };

  // Handle option selection
  const handleOptionChange = (e) => {
    const optionId = e.target.value;
    onOptionSelect(optionId);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Select Stock
        </label>
        {loadingStocks ? (
          <div className="animate-pulse h-10 bg-gray-200 rounded"></div>
        ) : (
          <select
            value={selectedStock}
            onChange={handleStockChange}
            className="w-full p-2 border rounded-md"
            disabled={loadingStocks}
          >
            <option value="">Select a stock...</option>
            {stocks.map(stock => (
              <option key={stock.ticker} value={stock.ticker}>
                {stock.ticker} - {stock.name}
              </option>
            ))}
          </select>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Select Option
        </label>
        {loadingOptions ? (
          <div className="animate-pulse h-10 bg-gray-200 rounded"></div>
        ) : (
          <select
            onChange={handleOptionChange}
            className="w-full p-2 border rounded-md"
            disabled={!selectedStock || loadingOptions}
          >
            <option value="">Select an option contract...</option>
            {options.map(option => (
              <option key={option.id || option.ticker} value={option.id || option.ticker}>
                {option.ticker} - {option.type?.toUpperCase()} ${option.strike_price} 
                {option.expiration_date ? ` - Exp: ${option.expiration_date}` : ''}
              </option>
            ))}
          </select>
        )}
      </div>

      {error && <div className="col-span-2 text-red-500 text-sm">{error}</div>}
    </div>
  );
}

export default Dropdowns;