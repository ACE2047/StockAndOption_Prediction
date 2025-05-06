import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, RANSACRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import joblib
import os
from optimized_data_fetcher import get_historical_prices

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory for storing trained models
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

class StockPredictor:
    def __init__(self, symbol, days=90, prediction_days=5, use_cache=True):
        """
        Initialize Stock Predictor
        
        Args:
            symbol (str): Stock ticker symbol
            days (int): Number of days of historical data to use
            prediction_days (int): Number of days to predict into the future
            use_cache (bool): Whether to use cached models
        """
        self.symbol = symbol
        self.days = days
        self.prediction_days = prediction_days
        self.use_cache = use_cache
        self.models = {}
        self.scaler = StandardScaler()
        self.latest_data = None
        self.features = ['open', 'high', 'low', 'volume', 'ma_5', 'ma_20', 'rsi', 
                         'daily_return', 'volatility', 'day_of_week', 'month']
        
    def _get_model_path(self, model_name):
        """Get path for model file"""
        return os.path.join(MODEL_DIR, f"{self.symbol}_{model_name}.joblib")
    
    def _check_cached_model(self, model_name):
        """Check if a cached model exists and is recent enough to use"""
        model_path = self._get_model_path(model_name)
        if not os.path.exists(model_path):
            return None
        
        # Check if model was trained recently (within the last 24 hours)
        mod_time = os.path.getmtime(model_path)
        if datetime.fromtimestamp(mod_time) < datetime.now() - timedelta(days=1):
            logger.info(f"Cached model for {self.symbol} is too old, will retrain")
            return None
            
        try:
            model = joblib.load(model_path)
            logger.info(f"Loaded cached {model_name} model for {self.symbol}")
            return model
        except Exception as e:
            logger.error(f"Error loading cached model: {e}")
            return None
    
    def fetch_data(self):
        """Fetch historical price data and prepare it for modeling"""
        try:
            logger.info(f"Fetching historical data for {self.symbol}")
            df = get_historical_prices(self.symbol, days=self.days)
            
            if df is None or df.empty:
                logger.error(f"Failed to get data for {self.symbol}")
                return None
                
            df = self._prepare_features(df)
            logger.info(f"Data prepared for {self.symbol}, shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {self.symbol}: {e}")
            return None
    
    def _prepare_features(self, df):
        """Prepare features for the ML models"""
        # Technical indicators
        df['ma_5'] = df['close'].rolling(window=5).mean()
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['rsi'] = self._compute_rsi(df['close'])
        df['daily_return'] = df['close'].pct_change()
        df['volatility'] = df['close'].rolling(window=14).std()
        
        # Add day of week and month features
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        
        # Create target variable (next day's closing price)
        df['target'] = df['close'].shift(-1)
        
        # Drop NaN values
        df = df.dropna()
        
        # Save the latest data point for future predictions
        self.latest_data = df.iloc[-1].copy()
        
        return df
    
    def _compute_rsi(self, prices, window=14):
        """Compute Relative Strength Index"""
        deltas = np.diff(prices)
        seed = deltas[:window+1]
        up = seed[seed >= 0].sum()/window
        down = -seed[seed < 0].sum()/window
        rs = up/down if down != 0 else float('inf')
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
            rs = up/down if down != 0 else float('inf')
            rsi[i] = 100. - 100./(1. + rs)
        
        return rsi
    
    def train_models(self, df=None):
        """Train or load various prediction models"""
        if df is None:
            df = self.fetch_data()
            
        if df is None or df.empty:
            logger.error("No data available for training")
            return False
            
        # Extract features and target
        X = df[self.features]
        y = df['target']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Use time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Initialize performance metrics
        performance = {}
        
        # Train Linear Regression model
        lr_model = self._train_or_load_model('linear_regression', LinearRegression, X_scaled, y, tscv)
        
        # Train RANSAC model
        ransac_model = self._train_or_load_model('ransac', RANSACRegressor, X_scaled, y, tscv, 
                                                random_state=42, min_samples=self.days//10)
        
        # Train Random Forest model
        rf_model = self._train_or_load_model('random_forest', RandomForestRegressor, X_scaled, y, tscv,
                                            n_estimators=100, random_state=42)
        
        # Train Gradient Boosting model
        gb_model = self._train_or_load_model('gradient_boosting', GradientBoostingRegressor, X_scaled, y, tscv,
                                           n_estimators=100, learning_rate=0.1, random_state=42)
        
        logger.info(f"All models trained for {self.symbol}")
        return True
    
    def _train_or_load_model(self, model_name, model_class, X, y, cv, **kwargs):
        """Train a model or load from cache if available"""
        # Check cache first
        if self.use_cache:
            cached_model = self._check_cached_model(model_name)
            if cached_model is not None:
                self.models[model_name] = cached_model
                return cached_model
        
        # Train a new model
        logger.info(f"Training {model_name} model for {self.symbol}")
        model = model_class(**kwargs)
        
        # Use cross-validation to evaluate
        cv_scores = []
        for train_idx, test_idx in cv.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            cv_scores.append(rmse)
        
        avg_rmse = np.mean(cv_scores)
        logger.info(f"{model_name} cross-validation RMSE: {avg_rmse:.2f}")
        
        # Retrain on full dataset
        model.fit(X, y)
        
        # Save model and performance metrics
        self.models[model_name] = model
        joblib.dump(model, self._get_model_path(model_name))
        
        return model
    
    def predict_next_days(self):
        """Generate predictions for the next several days"""
        if not self.models or not self.latest_data:
            logger.error("Models not trained or no data available")
            return None
        
        # Container for predictions
        predictions = {
            'symbol': self.symbol,
            'prediction_date': datetime.now().strftime('%Y-%m-%d'),
            'current_price': float(self.latest_data['close']),
            'next_day_predictions': {},
            'multi_day_predictions': {
                'linear_regression': [],
                'ransac': [],
                'random_forest': [],
                'gradient_boosting': [],
                'ensemble': []
            },
            'model_performance': {}
        }
        
        # Prepare the latest data point
        last_features = self.latest_data[self.features].values.reshape(1, -1)
        last_features_scaled = self.scaler.transform(last_features)
        
        # Next day predictions for each model
        for model_name, model in self.models.items():
            try:
                next_day_pred = float(model.predict(last_features_scaled)[0])
                predictions['next_day_predictions'][model_name] = next_day_pred
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
                predictions['next_day_predictions'][model_name] = None
        
        # Calculate ensemble prediction (average of all models)
        valid_preds = [pred for pred in predictions['next_day_predictions'].values() if pred is not None]
        if valid_preds:
            predictions['next_day_predictions']['ensemble'] = sum(valid_preds) / len(valid_preds)
        
        # Multi-day predictions
        current_data = self.latest_data.copy()
        
        for day in range(self.prediction_days):
            # Make predictions with each model
            day_predictions = {}
            
            for model_name, model in self.models.items():
                try:
                    features = current_data[self.features].values.reshape(1, -1)
                    features_scaled = self.scaler.transform(features)
                    pred = float(model.predict(features_scaled)[0])
                    predictions['multi_day_predictions'][model_name].append(pred)
                    day_predictions[model_name] = pred
                except Exception as e:
                    logger.error(f"Error in multi-day prediction with {model_name}: {e}")
            
            # Calculate ensemble prediction for this day
            valid_day_preds = [p for p in day_predictions.values() if p is not None]
            if valid_day_preds:
                ensemble_pred = sum(valid_day_preds) / len(valid_day_preds)
                predictions['multi_day_predictions']['ensemble'].append(ensemble_pred)
            
            # Update current data for next iteration
            # In a real scenario, we would update all the features more accurately
            if 'ensemble' in day_predictions:
                current_data['close'] = ensemble_pred
                current_data['open'] = ensemble_pred * 0.99  # Simplified
                current_data['high'] = ensemble_pred * 1.01  # Simplified
                current_data['low'] = ensemble_pred * 0.98   # Simplified
                # Update other features...
        
        return predictions
    
    def evaluate_models(self, df=None):
        """Evaluate model performance on test data"""
        if df is None:
            df = self.fetch_data()
            
        if df is None or df.empty:
            logger.error("No data available for evaluation")
            return None
            
        # Extract features and target
        X = df[self.features]
        y = df['target']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, shuffle=False
        )
        
        performance = {}
        
        # Evaluate each model
        for model_name, model in self.models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            performance[model_name] = {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2)
            }
            
            logger.info(f"{model_name} - RMSE: {rmse:.2f}, MAE: {mae:.2f}, R²: {r2:.2f}")
        
        return performance
    
    def plot_predictions(self, predictions=None, save_path=None):
        """Plot historical data and predictions"""
        if predictions is None:
            predictions = self.predict_next_days()
            
        if predictions is None:
            logger.error("No predictions available to plot")
            return
            
        # Get historical data for plotting
        df = self.fetch_data()
        if df is None or df.empty:
            logger.error("No historical data available for plotting")
            return
            
        # Create figure and axis
        plt.figure(figsize=(12, 6))
        
        # Plot historical data (last 30 days)
        historical = df['close'].iloc[-30:].reset_index()
        plt.plot(historical.index, historical['close'], label='Historical', color='blue')
        
        # Plot prediction for each model
        colors = {'linear_regression': 'green', 'ransac': 'red', 'random_forest': 'purple', 
                 'gradient_boosting': 'orange', 'ensemble': 'black'}
        
        # Start index for predictions (after historical data)
        start_idx = len(historical)
        
        for model_name, preds in predictions['multi_day_predictions'].items():
            if preds:  # Check if we have predictions for this model
                indices = range(start_idx, start_idx + len(preds))
                plt.plot(indices, preds, label=f"{model_name.replace('_', ' ').title()}", 
                         color=colors.get(model_name, 'gray'), linestyle='--')
        
        # Add labels and title
        plt.title(f"{self.symbol} Stock Price Prediction")
        plt.xlabel("Days")
        plt.ylabel("Price ($)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
            
        plt.close()
    
    def run_full_analysis(self):
        """Run a complete analysis and return all results"""
        # Fetch data
        df = self.fetch_data()
        if df is None or df.empty:
            return {"error": f"Failed to fetch data for {self.symbol}"}
            
        # Train models
        training_success = self.train_models(df)
        if not training_success:
            return {"error": f"Failed to train models for {self.symbol}"}
            
        # Evaluate models
        performance = self.evaluate_models(df)
        
        # Generate predictions
        predictions = self.predict_next_days()
        if predictions:
            predictions['model_performance'] = performance
            
            # Generate a plot and save it
            plot_path = os.path.join(os.path.dirname(__file__), 'static', 'plots')
            os.makedirs(plot_path, exist_ok=True)
            plot_file = os.path.join(plot_path, f"{self.symbol}_prediction.png")
            self.plot_predictions(predictions, save_path=plot_file)
            
            predictions['plot_path'] = plot_file
            
        return predictions

# Helper function to quickly get predictions for a symbol
def quick_predict(symbol, days=90, prediction_days=5, use_cache=True):
    """Quick helper function to get predictions for a symbol"""
    predictor = StockPredictor(symbol, days, prediction_days, use_cache)
    return predictor.run_full_analysis()

# If run directly
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Stock Price Prediction')
    parser.add_argument('--symbol', '-s', type=str, required=True, help='Stock ticker symbol')
    parser.add_argument('--days', '-d', type=int, default=90, help='Days of historical data')
    parser.add_argument('--predict', '-p', type=int, default=5, help='Days to predict')
    parser.add_argument('--no-cache', action='store_true', help='Disable model caching')
    
    args = parser.parse_args()
    
    # Run prediction
    predictor = StockPredictor(args.symbol, args.days, args.predict, not args.no_cache)
    results = predictor.run_full_analysis()
    
    # Print results
    if 'error' in results:
        print(f"Error: {results['error']}")
    else:
        print(f"=== {args.symbol} Stock Prediction ===")
        print(f"Current Price: ${results['current_price']:.2f}")
        print(f"Next Day Predictions:")
        for model, price in results['next_day_predictions'].items():
            if price is not None:
                print(f"  {model.replace('_', ' ').title()}: ${price:.2f}")
                
        print("\nModel Performance (RMSE):")
        for model, metrics in results['model_performance'].items():
            print(f"  {model.replace('_', ' ').title()}: {metrics['rmse']:.4f}")
            
        print(f"\nPrediction plot saved to {results.get('plot_path', 'N/A')}")