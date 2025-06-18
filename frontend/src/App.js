import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography } from '@mui/material';
import Dropdowns from './components/Dropdowns';
import ChatInterface from './components/ChatInterface';
import StockPrediction from './StockPrediction';
import OptionsAnalysis from './OptionsAnalysis';
import axios from 'axios';

function App() {
  const [selectedStock, setSelectedStock] = useState('');
  const [selectedOption, setSelectedOption] = useState('');
  const [stockData, setStockData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (selectedStock) {
      fetchStockData(selectedStock);
    }
  }, [selectedStock]);

  const fetchStockData = async (symbol) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/stock/${symbol}`);
      setStockData(response.data);
    } catch (err) {
      setError('Failed to fetch stock data');
      console.error('Error fetching stock data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl">
      <Typography variant="h3" component="h1" gutterBottom align="center" sx={{ my: 4 }}>
        Stock & Options Trading Prediction
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Dropdowns
              onStockSelect={setSelectedStock}
              onOptionSelect={setSelectedOption}
            />
          </Paper>
        </Grid>

        {selectedStock && (
          <>
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 2 }}>
                <StockPrediction
                  symbol={selectedStock}
                  stockData={stockData}
                  loading={loading}
                  error={error}
                />
              </Paper>
            </Grid>

            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2 }}>
                <ChatInterface
                  symbol={selectedStock}
                  stockData={stockData}
                />
              </Paper>
            </Grid>

            {selectedOption && (
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <OptionsAnalysis
                    symbol={selectedStock}
                    selectedOption={selectedOption}
                  />
                </Paper>
              </Grid>
            )}
          </>
        )}
      </Grid>
    </Container>
  );
}

export default App;