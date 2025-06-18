#!/usr/bin/env python3
"""
Test script to check the actual structure of Polygon API response
"""

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

def test_polygon_api_structure():
    """Test the actual structure of Polygon API response."""
    
    if not POLYGON_API_KEY:
        print("Polygon API key not found in .env file.")
        return
    
    # Test with a single day of AAPL data
    ticker = "AAPL"
    test_date = "2023-06-20"  # A date we know has data
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{test_date}/{test_date}?apiKey={POLYGON_API_KEY}"
    
    print(f"Testing API call: {url}")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("API Response structure:")
        print(json.dumps(data, indent=2))
        
        if data.get('results'):
            result = data['results'][0]
            print(f"\nFirst result keys: {list(result.keys())}")
            print(f"First result values: {list(result.values())}")
            
            # Check what each field contains
            for key, value in result.items():
                print(f"{key}: {value}")
                
    else:
        print(f"API Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_polygon_api_structure()