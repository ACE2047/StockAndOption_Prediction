import React, { useState } from 'react';
import { Dropdowns } from './components/common';
import { 
  StockPrediction, 
  OptionsAnalysis, 
  CombinedAnalysis, 
  NewsAnalysis 
} from './components/analysis';
import { 
  BlackScholesCalculator, 
  RealTimeData 
} from './components/tools';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';

function App() {
  const [selectedStock, setSelectedStock] = useState('');
  const [selectedOption, setSelectedOption] = useState('');
  const [loading, setLoading] = useState(false);
  const [trackedStocks, setTrackedStocks] = useState([]);

  const handleStockSelect = (symbol) => {
    setSelectedStock(symbol);
    setLoading(true);
    // Simulating API load time
    setTimeout(() => setLoading(false), 1000);
    
    // Add to tracked stocks for real-time data if not already there
    if (symbol && !trackedStocks.includes(symbol)) {
      setTrackedStocks([...trackedStocks, symbol]);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">
        Stock & Option Prediction Dashboard
      </h1>
      
      <div className="bg-gray-100 p-4 rounded-md mb-6">
        <h2 className="text-xl font-semibold mb-3">Select Stock and Option</h2>
        <Dropdowns
          onStockSelect={handleStockSelect}
          onOptionSelect={setSelectedOption}
        />
      </div>

      {selectedStock && (
        <Tabs>
          <TabList>
            <Tab>Stock Prediction</Tab>
            <Tab>Options Analysis</Tab>
            <Tab>Combined Analysis</Tab>
            <Tab>News & Insights</Tab>
            <Tab>Real-Time Data</Tab>
            <Tab>Black-Scholes Calculator</Tab>
          </TabList>

          <TabPanel>
            {loading ? (
              <div className="text-center p-10">Loading predictions...</div>
            ) : (
              <StockPrediction symbol={selectedStock} />
            )}
          </TabPanel>
          
          <TabPanel>
            {loading ? (
              <div className="text-center p-10">Loading options data...</div>
            ) : (
              <OptionsAnalysis symbol={selectedStock} selectedOption={selectedOption} />
            )}
          </TabPanel>
          
          <TabPanel>
            {loading ? (
              <div className="text-center p-10">Loading combined analysis...</div>
            ) : (
              <CombinedAnalysis symbol={selectedStock} />
            )}
          </TabPanel>
          
          <TabPanel>
            {loading ? (
              <div className="text-center p-10">Loading news and insights...</div>
            ) : (
              <NewsAnalysis symbol={selectedStock} />
            )}
          </TabPanel>
          
          <TabPanel>
            <RealTimeData symbols={trackedStocks} />
          </TabPanel>
          
          <TabPanel>
            <BlackScholesCalculator currentPrice={100} />
          </TabPanel>
        </Tabs>
      )}
    </div>
  );
}

export default App;