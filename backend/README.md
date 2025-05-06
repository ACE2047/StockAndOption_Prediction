# Stock and Option Prediction Backend

This is the backend application for the Stock and Option Prediction project.

## Project Structure

```
backend/
├── blueprints/           # Flask blueprints for API routes
│   ├── __init__.py
│   └── news_api_blueprint.py
├── models/               # Machine learning models
├── app.py                # Main Flask application
├── black_scholes.py      # Black-Scholes option pricing model
├── config.py             # Configuration settings
├── data_fetcher.py       # Data fetching utilities
├── enhanced_black_scholes.py  # Enhanced option pricing model
├── EnhancedStockPredictor.py  # Enhanced stock prediction model
├── llm_processor.py      # Language model processor for news analysis
├── news_api.py           # News API integration
├── optimized_data_fetcher.py  # Optimized data fetching
├── stock_predictior.py   # Stock prediction model
├── websocket_manager.py  # WebSocket manager for real-time data
├── websocket_server.py   # WebSocket server implementation
└── README.md             # This file
```

## API Endpoints

- `/api/tickers` - Get list of available stock tickers
- `/api/options/:symbol` - Get options data for a specific stock
- `/api/stock_prediction/:symbol` - Get stock price predictions
- `/api/option_analysis/:symbol` - Get options analysis
- `/api/combined_analysis/:symbol` - Get combined stock and options analysis
- `/api/option_price` - Calculate option price using Black-Scholes model
- `/api/news/:symbol` - Get news and sentiment analysis

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Start the Flask server:
   ```
   python app.py
   ```

3. Start the WebSocket server (in a separate terminal):
   ```
   python websocket_server.py
   ```