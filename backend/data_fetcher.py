import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import time
from functools import lru_cache
import logging
import redis
import json

logger = logging.getLogger(__name__)

# Import configuration
try:
    from config import AppConfig
    POLYGON_API_KEY = AppConfig.POLYGON_API_KEY
except ImportError:
    # Fallback if config is not available
    from dotenv import load_dotenv
    load_dotenv()
    POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")

class PolygonDataFetcher:
    def __init__(self, api_key: str, cache_ttl: int = 300):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.session = requests.Session()
        self.rate_limit = 5  # requests per minute
        self.last_request_time = 0
        self.cache_ttl = cache_ttl
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        except redis.ConnectionError:
            logger.warning("Redis not available, using in-memory cache")
            self.redis_client = None

    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < (60 / self.rate_limit):
            time.sleep((60 / self.rate_limit) - time_since_last)
        self.last_request_time = time.time()

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate a cache key for the request."""
        return f"polygon:{endpoint}:{json.dumps(params, sort_keys=True)}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if available."""
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Cache error: {str(e)}")
        return None

    def _set_cache(self, cache_key: str, data: Dict):
        """Store data in cache."""
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(data)
                )
            except Exception as e:
                logger.error(f"Cache error: {str(e)}")

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make an API request with rate limiting and caching."""
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            return cached_data

        self._rate_limit()
        params['apiKey'] = self.api_key
        
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def get_all_tickers(self) -> List[Dict]:
        """Get all active stock tickers."""
        return self._make_request("/v3/reference/tickers", {
            "market": "stocks",
            "active": "true",
            "limit": 1000
        }).get("results", [])

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current stock price and details."""
        return self._make_request(f"/v2/last/trade/{symbol}", {})

    def get_options_chain(self, symbol: str) -> List[Dict]:
        """Get options chain for a symbol."""
        return self._make_request("/v3/reference/options/contracts", {
            "underlying_ticker": symbol,
            "limit": 1000
        }).get("results", [])

    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timespan: str = "day"
    ) -> List[Dict]:
        """Get historical price data."""
        return self._make_request(f"/v2/aggs/ticker/{symbol}/range/1/{timespan}/{start_date}/{end_date}", {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000
        }).get("results", [])

    def get_market_status(self) -> Dict:
        """Get current market status."""
        return self._make_request("/v1/marketstatus/now", {})

    def get_company_info(self, symbol: str) -> Dict:
        """Get company information."""
        return self._make_request(f"/v3/reference/tickers/{symbol}", {})

    def get_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get news articles for a symbol."""
        return self._make_request("/v2/reference/news", {
            "ticker": symbol,
            "limit": limit
        }).get("results", [])

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

def fetch_stock_data(symbol, start_date=None, end_date=None):
    logger.info(f"Fetching stock data for {symbol} from {start_date} to {end_date}")
    # ... existing code ...

def fetch_news_data(symbol):
    logger.info(f"Fetching news data for {symbol}")
    # ... existing code ...

def fetch_training_data(symbol, start_date=None, end_date=None):
    logger.info(f"Fetching training data for {symbol} from {start_date} to {end_date}")
    # ... existing code ...
