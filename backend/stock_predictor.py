import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, RANSACRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import requests
from datetime import datetime, timedelta

POLYGON_API_KEY = "YOUR_API_KEY"  # Replace with your actual API key

def fetch_historical_data(symbol, days=60):
    """Fetch historical daily price data for a given stock symbol."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}?apiKey={POLYGON_API_KEY}"
    
    response = requests.get(url)
    if response.status_code != 200:
        return None
    
    data = response.json()
    if 'results' not in data:
        return None
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(data['results'])
    df['date'] = pd.to_datetime(df['t'], unit='ms')
    df = df.rename(columns={'c': 'close', 'h': 'high', 'l': 'low', 'o': 'open', 'v': 'volume'})
    df = df.set_index('date')
    return df[['close', 'open', 'high', 'low', 'volume']]

def prepare_features(df, window_size=14):
    """Prepare features for the ML models."""
    # Technical indicators
    df['ma_5'] = df['close'].rolling(window=5).mean()
    df['ma_20'] = df['close'].rolling(window=20).mean()
    df['rsi'] = compute_rsi(df['close'], window_size)
    df['daily_return'] = df['close'].pct_change()
    df['volatility'] = df['close'].rolling(window=window_size).std()
    
    # Add day of week and month features
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    
    # Create target variable (next day's closing price)
    df['target'] = df['close'].shift(-1)
    
    # Drop NaN values
    df = df.dropna()
    
    return df

def compute_rsi(prices, window=14):
    """Compute Relative Strength Index."""
    deltas = np.diff(prices)
    seed = deltas[:window+1]
    up = seed[seed >= 0].sum()/window
    down = -seed[seed < 0].sum()/window
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:window] = 100. - 100./(1. + rs)
    
    for i in range(window, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
            
        up = (up * (window - 1) + upval) / window
        down = (down * (window - 1) + downval) / window
        rs = up/down
        rsi[i] = 100. - 100./(1. + rs)
    
    return rsi

def train_models(df):
    """Train RANSAC and Linear Regression models."""
    # Features
    features = ['open', 'high', 'low', 'volume', 'ma_5', 'ma_20', 'rsi', 'daily_return', 'volatility', 'day_of_week', 'month']
    X = df[features]
    y = df['target']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    # Linear Regression Model
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    lr_pred = lr_model.predict(X_test)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))
    
    # RANSAC Model
    ransac_model = RANSACRegressor(random_state=42)
    ransac_model.fit(X_train, y_train)
    ransac_pred = ransac_model.predict(X_test)
    ransac_rmse = np.sqrt(mean_squared_error(y_test, ransac_pred))
    
    return {
        'linear_regression': {
            'model': lr_model,
            'rmse': lr_rmse,
            'test_predictions': lr_pred,
            'actual_values': y_test
        },
        'ransac': {
            'model': ransac_model,
            'rmse': ransac_rmse,
            'test_predictions': ransac_pred,
            'actual_values': y_test
        }
    }

def predict_next_price(symbol, days_to_predict=5):
    """Predict stock prices for the next few days."""
    # Fetch historical data
    df = fetch_historical_data(symbol, days=90)
    if df is None:
        return {"error": "Could not fetch data for this symbol"}
    
    # Prepare features
    df = prepare_features(df)
    
    # Train models
    models = train_models(df)
    
    # Last available data point for prediction
    last_data = df[['open', 'high', 'low', 'volume', 'ma_5', 'ma_20', 'rsi', 
                   'daily_return', 'volatility', 'day_of_week', 'month']].iloc[-1:]
    
    # Make predictions for the next day
    next_price_lr = models['linear_regression']['model'].predict(last_data)[0]
    next_price_ransac = models['ransac']['model'].predict(last_data)[0]
    
    # Make predictions for multiple days
    multi_day_predictions = {
        'linear_regression': [],
        'ransac': []
    }
    
    current_data = last_data.copy()
    
    for i in range(days_to_predict):
        # Linear Regression prediction
        lr_pred = float(models['linear_regression']['model'].predict(current_data)[0])
        multi_day_predictions['linear_regression'].append(lr_pred)
        
        # RANSAC prediction
        ransac_pred = float(models['ransac']['model'].predict(current_data)[0])
        multi_day_predictions['ransac'].append(ransac_pred)
        
        # Update current data for next prediction
        # This is a simplification - in reality you'd need to update all features
        current_data.iloc[0]['close'] = lr_pred  # Just for demonstration
    
    # Calculate model performance
    model_performance = {
        'linear_regression_rmse': float(models['linear_regression']['rmse']),
        'ransac_rmse': float(models['ransac']['rmse'])
    }
    
    # Results
    return {
        'symbol': symbol,
        'current_price': float(df['close'].iloc[-1]),
        'next_day_predictions': {
            'linear_regression': float(next_price_lr),
            'ransac': float(next_price_ransac)
        },
        'multi_day_predictions': multi_day_predictions,
        'model_performance': model_performance,
        'historical_data': df['close'].tail(30).to_dict(),
        'prediction_date': datetime.now().strftime('%Y-%m-%d')
    }