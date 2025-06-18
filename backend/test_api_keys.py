import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

logger = logging.getLogger(__name__)

def test_polygon_api_key():
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        logger.error("Polygon API key not found in .env file.")
        return False
    response = requests.get(f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2023-01-01/2023-01-02?apiKey={api_key}")
    if response.status_code == 200:
        logger.info("Polygon API key is valid.")
        return True
    else:
        logger.error(f"Polygon API key is invalid. Status code: {response.status_code}")
        return False

def test_news_api_key():
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        logger.error("News API key not found in .env file.")
        return False
    response = requests.get(f"https://newsapi.org/v2/everything?q=Apple&apiKey={api_key}")
    if response.status_code == 200:
        logger.info("News API key is valid.")
        return True
    else:
        logger.error(f"News API key is invalid. Status code: {response.status_code}")
        return False

if __name__ == "__main__":
    test_polygon_api_key()
    test_news_api_key() 