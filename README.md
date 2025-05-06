# Stock and Options Trading Prediction System

This project implements a stock and options trading prediction system using the Black-Scholes model for options pricing and RANSAC & Linear Regression for stock predictions. It leverages the Polygon.io API for market data, integrates with a News API for sentiment analysis, and uses LLM for processing information.

## Features

- **Stock Price Prediction**: Uses RANSAC and Linear Regression models to predict future stock prices
- **Options Pricing**: Implements the Black-Scholes model for theoretical options pricing
- **Options Analysis**: Analyzes options contracts to identify potentially undervalued options
- **Combined Analysis**: Integrates stock predictions with options analysis for comprehensive trading insights
- **News Analysis**: Categorizes news articles by topic and analyzes their potential impact on stocks
- **LLM Integration**: Uses Large Language Models to process news and generate trading insights
- **Real-Time Data**: Provides real-time stock price updates via WebSocket connection
- **Interactive Dashboard**: Visualizes predictions and analysis through an intuitive web interface

## Tech Stack

### Backend
- Python
- Flask
- pandas, numpy, scikit-learn
- Polygon.io API for market data
- News API for financial news
- OpenAI API for LLM processing
- WebSockets for real-time data streaming

### Frontend
- React.js
- Tailwind CSS
- Recharts for data visualization
- WebSocket client for real-time updates

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 14+
- Polygon.io API key

### Backend Setup

1. Clone the repository:
```
git clone <repository-url>
cd StockAndOption_Prediction
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Set up your API keys:
   - Create a `.env` file in the root directory
   - Add your API keys:
     ```
     POLYGON_API_KEY=your_polygon_api_key_here
     NEWS_API_KEY=your_newsapi_key_here
     OPENAI_API_KEY=your_openai_api_key_here
     ```

5. Start the Flask server:
```
cd backend
python app.py
```

### Frontend Setup

1. Install dependencies:
```
cd frontend
npm install
```

2. Start the development server:
```
npm start
```

3. Access the application at `http://localhost:3000`

## Usage

1. Select a stock from the dropdown menu
2. View stock price predictions using RANSAC and Linear Regression models
3. Explore options analysis to identify potentially profitable options contracts
4. Use the Black-Scholes calculator to price options with custom parameters
5. Check the combined analysis for comprehensive trading insights

## Project Structure

```
StockAndOption_Prediction/
├── backend/                   # Backend Flask application
│   ├── blueprints/            # API route blueprints
│   ├── models/                # Machine learning models
│   ├── app.py                 # Main Flask application
│   ├── black_scholes.py       # Black-Scholes model implementation
│   ├── data_fetcher.py        # API integration with Polygon.io
│   ├── stock_predictior.py    # Stock prediction models
│   └── README.md              # Backend documentation
├── frontend/                  # Frontend React application
│   ├── public/                # Static files
│   ├── src/                   # Source code
│   │   ├── components/        # React components
│   │   │   ├── analysis/      # Analysis components
│   │   │   ├── common/        # Common UI components
│   │   │   └── tools/         # Tool components
│   │   ├── App.js             # Main application component
│   │   └── index.js           # Entry point
│   └── README.md              # Frontend documentation
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

For more detailed information about the project structure, see the README files in the [backend](./backend/README.md) and [frontend](./frontend/README.md) directories.

## Future Enhancements

- Implement more advanced prediction models (LSTM, ARIMA)
- Add portfolio management features
- Integrate with trading platforms via APIs
- Implement backtesting functionality
- Add user authentication and personalized watchlists

## License

[MIT License](LICENSE)