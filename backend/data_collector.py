import os
import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

if not POLYGON_API_KEY:
    logger.error("Polygon API key not found in .env file. Please add it and retry.")
    exit(1)

def daterange(start_date, end_date, delta=timedelta(days=30)):
    """Yield start and end date tuples of max `delta` days until end_date."""
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + delta, end_date)
        yield current_start, current_end
        current_start = current_end + timedelta(days=1)

def fetch_stock_data_chunk(ticker, start_date, end_date):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}?apiKey={POLYGON_API_KEY}"
    logger.info(f"Fetching data chunk for {ticker} from {start_date.date()} to {end_date.date()}...")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            return pd.DataFrame(data['results'])
        else:
            logger.warning(f"No data found for {ticker} in range {start_date.date()} to {end_date.date()}")
            return pd.DataFrame()
    else:
        logger.error(f"Error fetching data: {response.status_code} - {response.text}")
        return None

def fetch_stock_data(ticker, overall_start_date, overall_end_date):
    all_data = []
    for start, end in daterange(overall_start_date, overall_end_date):
        df_chunk = fetch_stock_data_chunk(ticker, start, end)
        if df_chunk is None:
            logger.error("Stopping data fetch due to error.")
            break
        all_data.append(df_chunk)
        time.sleep(12)  # Sleep 12 seconds to keep under 5 calls/min limit
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        # Rename columns and convert timestamp
        # Based on actual Polygon API response structure:
        # API returns: [v, vw, o, c, h, l, t, n]
        # Which means: [volume, vwap, open, close, high, low, timestamp, transactions]
        full_df.columns = ['volume', 'vwap', 'open', 'close', 'high', 'low', 'timestamp', 'transactions']
        
        # Reorder to standard format: [timestamp, open, high, low, close, volume, vwap, transactions]
        full_df = full_df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap', 'transactions']]
        
        # Convert timestamp from milliseconds to datetime
        full_df['timestamp'] = pd.to_datetime(full_df['timestamp'], unit='ms')
        return full_df
    else:
        return pd.DataFrame()

def main():
    ticker = "AAPL"
    start_date = datetime.now() - timedelta(days=365*2)  # 2 years ago
    end_date = datetime.now()
    
    logger.info(f"Starting fetch for {ticker} from {start_date.date()} to {end_date.date()}")

    df = fetch_stock_data(ticker, start_date, end_date)
    
    if not df.empty:
        filename = f"{ticker}_2years_data.csv"
        df.to_csv(filename, index=False)
        logger.info(f"Data saved to {filename}")
    else:
        logger.error("No data fetched.")

if __name__ == "__main__":
    main()
