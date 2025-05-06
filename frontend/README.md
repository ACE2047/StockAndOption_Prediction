# Stock and Option Prediction Frontend

This is the frontend application for the Stock and Option Prediction project.

## Project Structure

```
frontend/
├── public/                # Static files
├── src/                   # Source code
│   ├── components/        # React components
│   │   ├── analysis/      # Analysis-related components
│   │   │   ├── StockPrediction.js
│   │   │   ├── OptionsAnalysis.js
│   │   │   ├── CombinedAnalysis.js
│   │   │   ├── NewsAnalysis.js
│   │   │   └── index.js
│   │   ├── common/        # Common UI components
│   │   │   ├── Dropdowns.js
│   │   │   └── index.js
│   │   ├── tools/         # Tool-related components
│   │   │   ├── BlackScholesCalculator.js
│   │   │   ├── RealTimeData.js
│   │   │   └── index.js
│   │   └── Toggle.css     # Shared styles
│   ├── App.js             # Main application component
│   └── index.js           # Entry point
└── README.md              # This file
```

## Component Overview

### Analysis Components

- **StockPrediction**: Displays stock price predictions using various models
- **OptionsAnalysis**: Analyzes options data for a selected stock
- **CombinedAnalysis**: Combines stock and options analysis
- **NewsAnalysis**: Analyzes news sentiment for a selected stock

### Common Components

- **Dropdowns**: Provides stock and option selection functionality

### Tool Components

- **BlackScholesCalculator**: Calculates option prices using the Black-Scholes model
- **RealTimeData**: Displays real-time stock data

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Build for production:
   ```
   npm run build
   ```