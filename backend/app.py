from flask import Flask, jsonify, request, abort
from data_fetcher import (
    get_all_tickers, 
    get_options_chain, 
    get_stock_price, 
    get_stock_volatility
)
from black_scholes import calculate_option_price
from stock_predictior import predict_next_price
from enhanced_black_scholes import calculate_option_price as enhanced_calculate_option_price
from enhanced_black_scholes import calculate_greeks, calculate_implied_volatility
try:
    from optimized_data_fetcher import get_historical_prices
    from EnhancedStockPredictor import StockPredictor
    ENHANCED_MODELS_AVAILABLE = True
except ImportError:
    ENHANCED_MODELS_AVAILABLE = False
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from flask_cors import CORS

# Import configuration
from config import AppConfig

# Import our WebSocket manager
from websocket_manager import websocket_manager

# Import blueprints
from blueprints.news_api_blueprint import news_api_bp

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(AppConfig)
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(news_api_bp)

# Start WebSocket server if enabled
if os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true':
    websocket_manager.start_server()

@app.route('/api/tickers')
def tickers():
    return jsonify(get_all_tickers())

@app.route('/api/options/<symbol>')
def options(symbol):
    return jsonify(get_options_chain(symbol))

@app.route('/api/option_price', methods=['POST'])
def option_price():
    """
    Calculate option price using Black-Scholes model
    
    Request body:
        S: Current stock price
        K: Strike price
        T: Time to expiration in years
        r: Risk-free rate
        sigma: Volatility
        type: Option type (call or put)
    
    Returns:
        JSON with calculated option price and Greeks
    """
    try:
        data = request.json
        
        # Validate required parameters
        required_params = ['S', 'K', 'T', 'r', 'sigma']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        S = float(data['S'])
        K = float(data['K'])
        T = float(data['T'])
        r = float(data['r'])
        sigma = float(data['sigma'])
        option_type = data.get('type', 'call').lower()
        
        # Validate parameter values
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            return jsonify({'error': 'Parameters must be positive values'}), 400
        
        if option_type not in ['call', 'put']:
            return jsonify({'error': 'Option type must be "call" or "put"'}), 400
        
        # Calculate option price
        price = calculate_option_price(
            S=S,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        
        # Calculate Greeks (simplified approach)
        # Delta - option price change per $1 stock price change
        delta_shift = 0.01 * S
        delta_price = calculate_option_price(
            S=S + delta_shift,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        delta = (delta_price - price) / delta_shift
        
        # Gamma - rate of change of delta per $1 stock price change
        gamma_price_up = calculate_option_price(
            S=S + delta_shift,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        gamma_price_down = calculate_option_price(
            S=S - delta_shift,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        gamma = (gamma_price_up - 2*price + gamma_price_down) / (delta_shift**2)
        
        # Theta - option price change per day (time decay)
        theta_shift = 1/365.0  # One day
        theta_price = calculate_option_price(
            S=S,
            K=K,
            T=max(0.001, T - theta_shift),  # Prevent negative time
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        theta = (theta_price - price) / theta_shift
        
        # Vega - option price change per 1% volatility change
        vega_shift = 0.01  # 1% volatility
        vega_price = calculate_option_price(
            S=S,
            K=K,
            T=T,
            r=r,
            sigma=sigma + vega_shift,
            option_type=option_type
        )
        vega = (vega_price - price) / vega_shift
        
        # Calculate intrinsic and time value
        intrinsic_value = max(0, S - K if option_type == 'call' else K - S)
        time_value = price - intrinsic_value
        
        return jsonify({
            'price': round(price, 2),
            'greeks': {
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'vega': round(vega, 4)
            },
            'intrinsic_value': round(intrinsic_value, 2),
            'time_value': round(time_value, 2)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock_prediction/<symbol>')
def stock_prediction(symbol):
    # Get prediction days from query parameter, default to 5
    days = request.args.get('days', default=5, type=int)
    use_enhanced = request.args.get('enhanced', default=False, type=bool)
    
    try:
        if use_enhanced and ENHANCED_MODELS_AVAILABLE:
            # Use enhanced predictor if available and requested
            predictor = StockPredictor(symbol, prediction_days=days)
            if predictor.train_models():
                predictions = predictor.predict_next_days()
                return jsonify(predictions)
            else:
                # Fall back to basic predictor if enhanced fails
                predictions = predict_next_price(symbol, days_to_predict=days)
                return jsonify(predictions)
        else:
            # Use basic predictor
            predictions = predict_next_price(symbol, days_to_predict=days)
            return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/option_analysis/<symbol>')
def option_analysis(symbol):
    """
    Analyze options for a given stock symbol using Black-Scholes model
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        JSON with options analysis including theoretical prices and valuation
    """
    try:
        # Get options chain
        options_data = get_options_chain(symbol)
        
        if not options_data:
            return jsonify({"error": f"No options data available for {symbol}"}), 404
        
        # Get current stock price from API
        current_price = get_stock_price(symbol)
        
        # Get historical volatility
        volatility = get_stock_volatility(symbol)
        
        # Current risk-free rate (Treasury yield)
        risk_free_rate = 0.03  # 3% - this could be fetched from an API in a production app
        
        # Filter and analyze options
        today = datetime.now()
        analyzed_options = []
        
        # Group options by expiration date
        expiration_groups = {}
        
        for option in options_data:
            # Parse expiration date
            try:
                exp_date = option.get('expiration_date', '')
                if not exp_date in expiration_groups:
                    expiration_groups[exp_date] = []
                expiration_groups[exp_date].append(option)
            except:
                continue
        
        # Process each expiration date group
        for exp_date, options in expiration_groups.items():
            try:
                exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
                days_to_expiry = (exp_datetime - today).days
                
                # Skip expired options
                if days_to_expiry <= 0:
                    continue
                
                T = days_to_expiry / 365.0  # Convert to years
                
                # Process each option in this expiration group
                for option in options:
                    strike = float(option.get('strike_price', 0))
                    option_type = option.get('contract_type', 'call').lower()
                    
                    # Calculate theoretical price using Black-Scholes
                    theoretical_price = calculate_option_price(
                        S=current_price,
                        K=strike,
                        T=T,
                        r=risk_free_rate,
                        sigma=volatility,
                        option_type=option_type
                    )
                    
                    # Get market price (or use a default if not available)
                    market_price = float(option.get('last_price', 0))
                    
                    # Calculate implied volatility (simplified approach)
                    implied_vol = volatility
                    if market_price > 0:
                        # In a real app, you would solve for implied volatility
                        # This is a placeholder calculation
                        vol_adjustment = (market_price / theoretical_price - 1) * 0.1
                        implied_vol = max(0.05, min(1.0, volatility + vol_adjustment))
                    
                    # Add analysis data to the option
                    analyzed_option = {
                        **option,
                        'days_to_expiry': days_to_expiry,
                        'theoretical_price': round(theoretical_price, 2),
                        'market_price': market_price,
                        'price_difference': round(theoretical_price - market_price, 2),
                        'is_undervalued': theoretical_price > market_price,
                        'implied_volatility': round(implied_vol, 4),
                        'historical_volatility': round(volatility, 4),
                        'intrinsic_value': round(max(0, current_price - strike if option_type == 'call' else strike - current_price), 2),
                        'time_value': round(theoretical_price - max(0, current_price - strike if option_type == 'call' else strike - current_price), 2),
                        'current_stock_price': current_price
                    }
                    
                    analyzed_options.append(analyzed_option)
            except Exception as e:
                print(f"Error processing expiration date {exp_date}: {e}")
                continue
        
        # Sort by expiration date and then by strike price
        analyzed_options.sort(key=lambda x: (x.get('expiration_date', ''), x.get('strike_price', 0)))
        
        return jsonify(analyzed_options)
    
    except Exception as e:
        print(f"Error in option_analysis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/combined_analysis/<symbol>')
def combined_analysis(symbol):
    """
    Combine stock prediction with options analysis for a comprehensive view
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        JSON with combined stock predictions and options analysis
    """
    try:
        # Get stock prediction
        stock_pred = predict_next_price(symbol)
        
        if 'error' in stock_pred:
            return jsonify({"error": stock_pred['error']}), 404
        
        # Get options chain
        options_data = get_options_chain(symbol)
        
        # Get current stock price and volatility
        current_price = stock_pred.get('current_price', get_stock_price(symbol))
        volatility = get_stock_volatility(symbol)
        
        # Risk-free rate
        risk_free_rate = 0.03  # 3% - could be fetched from an API
        
        # Get predicted prices for different time horizons
        predicted_prices = {
            'next_day': stock_pred['next_day_predictions']['ransac'],
            'week': stock_pred['multi_day_predictions']['ransac'][min(4, len(stock_pred['multi_day_predictions']['ransac'])-1)],
            'month': stock_pred['multi_day_predictions']['ransac'][-1] if stock_pred['multi_day_predictions']['ransac'] else current_price
        }
        
        # Calculate implied volatility and other metrics for options
        analyzed_options = []
        today = datetime.now()
        
        # Group options by expiration date for better organization
        expiration_groups = {}
        
        for option in options_data:
            try:
                exp_date = option.get('expiration_date', '')
                if not exp_date:
                    continue
                    
                if exp_date not in expiration_groups:
                    expiration_groups[exp_date] = []
                    
                expiration_groups[exp_date].append(option)
            except:
                continue
        
        # Process each expiration date
        for exp_date, options_list in expiration_groups.items():
            try:
                exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
                days_to_expiry = (exp_datetime - today).days
                
                # Skip expired options
                if days_to_expiry <= 0:
                    continue
                
                T = days_to_expiry / 365.0  # Convert to years
                
                # Choose which predicted price to use based on expiration timeframe
                if days_to_expiry <= 1:
                    predicted_price = predicted_prices['next_day']
                elif days_to_expiry <= 7:
                    predicted_price = predicted_prices['week']
                else:
                    predicted_price = predicted_prices['month']
                
                # Process each option in this expiration group
                for option in options_list:
                    # Basic option info
                    option_data = {
                        'contract': option.get('ticker', ''),
                        'strike': float(option.get('strike_price', 0)),
                        'expiration': exp_date,
                        'type': option.get('contract_type', 'call').lower(),
                        'days_to_expiry': days_to_expiry
                    }
                    
                    # Use Black-Scholes to calculate theoretical price
                    theoretical_price = calculate_option_price(
                        S=current_price,
                        K=option_data['strike'],
                        T=T,
                        r=risk_free_rate,
                        sigma=volatility,
                        option_type=option_data['type']
                    )
                    option_data['theoretical_price'] = round(theoretical_price, 2)
                    
                    # Market price
                    market_price = float(option.get('last_price', 0))
                    option_data['market_price'] = market_price
                    
                    # Calculate potential profit/loss based on predicted stock price
                    if option_data['type'] == 'call':
                        potential_value = max(0, predicted_price - option_data['strike'])
                    else:  # Put
                        potential_value = max(0, option_data['strike'] - predicted_price)
                    
                    # Calculate Greeks (simplified)
                    # Delta - option price change per $1 stock price change
                    delta_shift = 0.01 * current_price
                    delta_price = calculate_option_price(
                        S=current_price + delta_shift,
                        K=option_data['strike'],
                        T=T,
                        r=risk_free_rate,
                        sigma=volatility,
                        option_type=option_data['type']
                    )
                    delta = (delta_price - theoretical_price) / delta_shift
                    
                    # Add analysis data
                    option_data.update({
                        'potential_value': round(potential_value, 2),
                        'profit_potential': round(potential_value - theoretical_price, 2),
                        'profit_percentage': round((potential_value / theoretical_price - 1) * 100, 2) if theoretical_price > 0 else 0,
                        'is_undervalued': theoretical_price > market_price if market_price > 0 else None,
                        'price_difference': round(theoretical_price - market_price, 2) if market_price > 0 else None,
                        'implied_volatility': round(volatility, 4),
                        'delta': round(delta, 4),
                        'predicted_stock_price': round(predicted_price, 2),
                        'current_stock_price': round(current_price, 2)
                    })
                    
                    analyzed_options.append(option_data)
            except Exception as e:
                print(f"Error processing expiration date {exp_date}: {e}")
                continue
        
        # Sort options by expiration date and then by strike price
        analyzed_options.sort(key=lambda x: (x.get('expiration', ''), x.get('strike', 0)))
        
        # Group options by expiration date for the response
        grouped_options = {}
        for option in analyzed_options:
            exp = option.get('expiration', 'unknown')
            if exp not in grouped_options:
                grouped_options[exp] = []
            grouped_options[exp].append(option)
        
        # Add trading recommendations based on model predictions and option analysis
        recommendations = []
        
        # Bullish scenario - stock predicted to go up
        if predicted_prices['week'] > current_price * 1.02:  # 2% increase predicted
            # Find undervalued call options
            for option in analyzed_options:
                if option['type'] == 'call' and option.get('is_undervalued', False) and option['profit_percentage'] > 20:
                    recommendations.append({
                        'type': 'BUY_CALL',
                        'contract': option['contract'],
                        'reason': f"Stock predicted to rise {round((predicted_prices['week']/current_price-1)*100, 1)}% in a week. This call option has {option['profit_percentage']}% potential profit.",
                        'option': option
                    })
                    break
        
        # Bearish scenario - stock predicted to go down
        elif predicted_prices['week'] < current_price * 0.98:  # 2% decrease predicted
            # Find undervalued put options
            for option in analyzed_options:
                if option['type'] == 'put' and option.get('is_undervalued', False) and option['profit_percentage'] > 20:
                    recommendations.append({
                        'type': 'BUY_PUT',
                        'contract': option['contract'],
                        'reason': f"Stock predicted to fall {round((1-predicted_prices['week']/current_price)*100, 1)}% in a week. This put option has {option['profit_percentage']}% potential profit.",
                        'option': option
                    })
                    break
        
        # Neutral scenario - stock predicted to stay flat
        else:
            recommendations.append({
                'type': 'HOLD',
                'reason': f"Stock predicted to remain relatively flat (within ±2%) in the coming week."
            })
        
        return jsonify({
            'stock_prediction': stock_pred,
            'options_analysis': {
                'grouped_by_expiration': grouped_options,
                'all_options': analyzed_options
            },
            'trading_recommendations': recommendations,
            'market_data': {
                'current_price': round(current_price, 2),
                'historical_volatility': round(volatility * 100, 2),
                'risk_free_rate': risk_free_rate * 100,
                'prediction_date': datetime.now().strftime('%Y-%m-%d')
            }
        })
    
    except Exception as e:
        print(f"Error in combined_analysis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/enhanced_option_price', methods=['POST'])
def enhanced_option_price():
    """
    Calculate option price and Greeks using enhanced Black-Scholes model
    
    Request body:
        S: Current stock price
        K: Strike price
        T: Time to expiration in years
        r: Risk-free rate
        sigma: Volatility
        type: Option type (call or put)
    
    Returns:
        JSON with calculated option price, Greeks, and additional metrics
    """
    try:
        data = request.json
        
        # Validate required parameters
        required_params = ['S', 'K', 'T', 'r', 'sigma']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        S = float(data['S'])
        K = float(data['K'])
        T = float(data['T'])
        r = float(data['r'])
        sigma = float(data['sigma'])
        option_type = data.get('type', 'call').lower()
        
        # Validate parameter values
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            return jsonify({'error': 'Parameters must be positive values'}), 400
        
        if option_type not in ['call', 'put']:
            return jsonify({'error': 'Option type must be "call" or "put"'}), 400
        
        # Calculate option price
        price = enhanced_calculate_option_price(
            S=S,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        
        # Calculate Greeks
        greeks = calculate_greeks(
            S=S,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        
        # Calculate intrinsic and time value
        intrinsic_value = max(0, S - K if option_type == 'call' else K - S)
        time_value = price - intrinsic_value
        
        # Calculate breakeven price
        if option_type == 'call':
            breakeven = K + price
        else:
            breakeven = K - price
        
        return jsonify({
            'price': round(price, 2),
            'greeks': {
                'delta': round(greeks['delta'], 4),
                'gamma': round(greeks['gamma'], 4),
                'theta': round(greeks['theta'], 4),
                'vega': round(greeks['vega'], 4),
                'rho': round(greeks['rho'], 4)
            },
            'intrinsic_value': round(intrinsic_value, 2),
            'time_value': round(time_value, 2),
            'breakeven_price': round(breakeven, 2),
            'implied_volatility': round(sigma * 100, 2),
            'days_to_expiration': round(T * 365, 0)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# News and LLM endpoints are now handled by the news_api_blueprint

def cleanup():
    """Cleanup resources before application exit."""
    print("Cleaning up resources...")
    if os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true':
        websocket_manager.stop_server()

if __name__ == "__main__":
    try:
        # Run the app
        app.run(
            host='0.0.0.0', 
            port=AppConfig.PORT, 
            debug=AppConfig.DEBUG
        )
    except KeyboardInterrupt:
        print("Application interrupted by user")
    finally:
        cleanup()