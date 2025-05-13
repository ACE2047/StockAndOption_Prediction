import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Import configuration
try:
    from config import AppConfig
    POLYGON_API_KEY = AppConfig.POLYGON_API_KEY
except ImportError:
    # Fallback if config is not available
    from dotenv import load_dotenv
    load_dotenv()
    POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")

def get_all_tickers():
    """Get a list of all active stock tickers from Polygon.io.
    
    Returns:
        List of ticker objects
    """
    url = f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit=1000&apiKey={POLYGON_API_KEY}"
    
    all_tickers = []
    next_url = url
    
    # Paginate through results (limited to 5 pages to avoid rate limits)
    for _ in range(5):
        if not next_url:
            break
            
        response = requests.get(next_url)
        if response.status_code != 200:
            break
            
        data = response.json()
        all_tickers.extend(data.get('results', []))
        
        # Get next page URL if available
        next_url = data.get('next_url')
        if next_url:
            next_url = f"{next_url}&apiKey={POLYGON_API_KEY}"
    
    return all_tickers

def get_options_chain(symbol: str) -> List[Dict[str, Any]]:
    """Get options chain for a specific stock symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        List of option contract objects
    """
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={symbol}&limit=1000&apiKey={POLYGON_API_KEY}"
    
    all_options = []
    next_url = url
    
    # Paginate through results (limited to 5 pages to avoid rate limits)
    for _ in range(5):
        if not next_url:
            break
            
        response = requests.get(next_url)
        if response.status_code != 200:
            break
            
        data = response.json()
        all_options.extend(data.get('results', []))
        
        # Get next page URL if available
        next_url = data.get('next_url')
        if next_url:
            next_url = f"{next_url}&apiKey={POLYGON_API_KEY}"
    
    return all_options

def get_stock_price(symbol: str) -> float:
    """Get the current stock price for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Current stock price
    """
    url = f"https://api.polygon.io/v2/last/trade/{symbol}?apiKey={POLYGON_API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            result = data.get('results', {})
            
            if result:
                return float(result.get('p', 0))
        
        # If we couldn't get the price, try the previous close
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?apiKey={POLYGON_API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('results', [{}])[0]
            
            if result:
                return float(result.get('c', 0))
        
        return 0.0
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return 0.0

def get_historical_prices(symbol: str, days: int = 90) -> pd.DataFrame:
    """Get historical daily prices for a stock.
    
    Args:
        symbol: Stock ticker symbol
        days: Number of days of historical data to fetch
        
    Returns:
        DataFrame with historical price data
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for API (YYYY-MM-DD)
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}?adjusted=true&sort=asc&limit=5000&apiKey={POLYGON_API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                # Convert to DataFrame
                df = pd.DataFrame(results)
                
                # Rename columns to more readable names
                df = df.rename(columns={
                    'v': 'volume',
                    'o': 'open',
                    'c': 'close',
                    'h': 'high',
                    'l': 'low',
                    't': 'timestamp',
                    'n': 'transactions'
                })
                
                # Convert timestamp to datetime
                df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Set date as index
                df = df.set_index('date')
                
                return df
        
        # Return empty DataFrame if no data
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching historical prices for {symbol}: {e}")
        return pd.DataFrame()

def get_stock_volatility(symbol: str, days: int = 30) -> float:
    """Calculate historical volatility for a stock.
    
    Args:
        symbol: Stock ticker symbol
        days: Number of days to use for volatility calculation
        
    Returns:
        Annualized volatility as a decimal (e.g., 0.25 for 25%)
    """
    try:
        # Get historical prices
        df = get_historical_prices(symbol, days=days)
        
        if df.empty:
            return 0.2  # Default volatility if no data
        
        # Calculate daily returns
        df['return'] = df['close'].pct_change()
        
        # Calculate volatility (standard deviation of returns)
        daily_volatility = df['return'].std()
        
        # Annualize volatility (approximately 252 trading days in a year)
        annualized_volatility = daily_volatility * np.sqrt(252)
        
        return annualized_volatility
    except Exception as e:
        print(f"Error calculating volatility for {symbol}: {e}")
        return 0.2  # Default volatility
