import requests

POLYGON_API_KEY = "YOUR_API_KEY"  # Replace with your actual API key

def get_all_tickers():
    url = f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&apiKey={POLYGON_API_KEY}"
    response = requests.get(url)
    return response.json().get('results', [])

def get_options_chain(symbol):
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={symbol}&apiKey={POLYGON_API_KEY}"
    response = requests.get(url)
    return response.json().get('results', [])
