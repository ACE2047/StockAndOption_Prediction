import React, { useState, useEffect, useRef } from 'react';
import { Card, Container, Alert, Badge, Spinner, Table } from 'react-bootstrap';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8765';

const RealTimeData = ({ symbols = [] }) => {
  const [connected, setConnected] = useState(false);
  const [stockData, setStockData] = useState({});
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket server
    connectWebSocket();

    // Clean up on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    // Subscribe to symbols when connection is established
    if (connected && symbols.length > 0) {
      symbols.forEach(symbol => {
        subscribeToSymbol(symbol);
      });
    }
  }, [connected, symbols]);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);
        
        // Send a ping every 30 seconds to keep the connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'ping' }));
          }
        }, 30000);
        
        // Clear interval when connection closes
        ws.onclose = () => {
          clearInterval(pingInterval);
          handleDisconnect();
        };
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'stock_update') {
            setStockData(prevData => ({
              ...prevData,
              [data.symbol]: {
                ...data.data,
                lastUpdate: new Date()
              }
            }));
          } else if (data.type === 'pong') {
            // Received pong response, connection is alive
            console.log('Received pong from server');
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('WebSocket connection error. Attempting to reconnect...');
      };

    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      setError('Failed to connect to real-time data server. Attempting to reconnect...');
      handleDisconnect();
    }
  };

  const handleDisconnect = () => {
    setConnected(false);
    
    // Attempt to reconnect after 5 seconds
    reconnectTimeoutRef.current = setTimeout(() => {
      console.log('Attempting to reconnect WebSocket...');
      connectWebSocket();
    }, 5000);
  };

  const subscribeToSymbol = (symbol) => {
    if (!symbol || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    wsRef.current.send(JSON.stringify({
      action: 'subscribe',
      symbol: symbol
    }));
    
    console.log(`Subscribed to ${symbol}`);
  };

  const formatPrice = (price) => {
    return typeof price === 'number' ? price.toFixed(2) : 'N/A';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const getPriceChangeClass = (symbol) => {
    if (!stockData[symbol] || !stockData[symbol].previousPrice) return '';
    
    const currentPrice = stockData[symbol].price;
    const previousPrice = stockData[symbol].previousPrice;
    
    if (currentPrice > previousPrice) return 'text-success';
    if (currentPrice < previousPrice) return 'text-danger';
    return '';
  };

  return (
    <Container className="mt-4">
      <Card>
        <Card.Header>
          <h4>
            Real-Time Stock Data
            {connected ? (
              <Badge bg="success" className="ms-2">Connected</Badge>
            ) : (
              <Badge bg="danger" className="ms-2">Disconnected</Badge>
            )}
          </h4>
        </Card.Header>
        <Card.Body>
          {error && (
            <Alert variant="warning">{error}</Alert>
          )}
          
          {!connected && (
            <div className="text-center mb-3">
              <Spinner animation="border" role="status" size="sm" className="me-2" />
              <span>Connecting to real-time data server...</span>
            </div>
          )}
          
          {symbols.length === 0 ? (
            <Alert variant="info">No symbols selected for real-time tracking.</Alert>
          ) : (
            <Table striped bordered hover>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Price</th>
                  <th>Size</th>
                  <th>Exchange</th>
                  <th>Last Update</th>
                </tr>
              </thead>
              <tbody>
                {symbols.map(symbol => (
                  <tr key={symbol}>
                    <td>{symbol}</td>
                    <td className={getPriceChangeClass(symbol)}>
                      {stockData[symbol] ? formatPrice(stockData[symbol].price) : (
                        <Spinner animation="border" size="sm" />
                      )}
                    </td>
                    <td>{stockData[symbol] ? stockData[symbol].size : '-'}</td>
                    <td>{stockData[symbol] ? stockData[symbol].exchange : '-'}</td>
                    <td>
                      {stockData[symbol] ? formatTimestamp(stockData[symbol].lastUpdate) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
        <Card.Footer className="text-muted">
          Data updates in real-time via WebSocket connection
        </Card.Footer>
      </Card>
    </Container>
  );
};

export default RealTimeData;