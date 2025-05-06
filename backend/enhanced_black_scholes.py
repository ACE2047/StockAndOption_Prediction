import numpy as np
from scipy.stats import norm
from scipy import optimize
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_option_price(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option price using Black-Scholes formula
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration in years
        r (float): Risk-free interest rate (decimal)
        sigma (float): Volatility (decimal)
        option_type (str): Type of option - 'call' or 'put'
        
    Returns:
        float: Option price
    """
    try:
        # Validate inputs
        if S <= 0 or K <= 0 or T <= 0:
            raise ValueError("Stock price, strike price, and time must be positive")
        
        if sigma <= 0:
            raise ValueError("Volatility must be positive")
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Calculate price based on option type
        if option_type.lower() == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type.lower() == 'put':
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("Option type must be 'call' or 'put'")
        
        return price
    
    except Exception as e:
        logger.error(f"Error calculating option price: {str(e)}")
        raise

def calculate_implied_volatility(option_price, S, K, T, r, option_type='call'):
    """
    Calculate implied volatility using an iterative approach
    
    Args:
        option_price (float): Market price of the option
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration in years
        r (float): Risk-free interest rate (decimal)
        option_type (str): Type of option - 'call' or 'put'
        
    Returns:
        float: Implied volatility
    """
    try:
        # Validation
        if option_price <= 0 or S <= 0 or K <= 0 or T <= 0:
            raise ValueError("Prices, strike price, and time must be positive")
        
        # Define the objective function (difference between BS price and market price)
        def objective(sigma):
            return calculate_option_price(S, K, T, r, sigma, option_type) - option_price
        
        # Initial guess and bounds for volatility
        initial_sigma = 0.2  # Start with 20% volatility
        bounds = (0.001, 5.0)  # Reasonable bounds for volatility
        
        # Find implied volatility where the objective function equals zero
        result = optimize.root_scalar(objective, bracket=bounds, method='brentq')
        
        if not result.converged:
            raise RuntimeError("Implied volatility calculation did not converge")
            
        return result.root
        
    except Exception as e:
        logger.error(f"Error calculating implied volatility: {str(e)}")
        raise

def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option Greeks: Delta, Gamma, Theta, Vega, and Rho
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration in years
        r (float): Risk-free interest rate (decimal)
        sigma (float): Volatility (decimal)
        option_type (str): Type of option - 'call' or 'put'
        
    Returns:
        dict: Dictionary containing the Greeks
    """
    try:
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Common calculations
        phi = norm.pdf(d1)  # Standard normal density function
        
        # Calculate Greeks
        if option_type.lower() == 'call':
            delta = norm.cdf(d1)
            theta = -((S * sigma * phi) / (2 * np.sqrt(T))) - r * K * np.exp(-r * T) * norm.cdf(d2)
            rho = T * K * np.exp(-r * T) * norm.cdf(d2)
        else:  # Put option
            delta = -norm.cdf(-d1)
            theta = -((S * sigma * phi) / (2 * np.sqrt(T))) + r * K * np.exp(-r * T) * norm.cdf(-d2)
            rho = -T * K * np.exp(-r * T) * norm.cdf(-d2)
        
        # Common Greeks for both call and put
        gamma = phi / (S * sigma * np.sqrt(T))  # Rate of change of delta
        vega = S * np.sqrt(T) * phi / 100  # Divided by 100 for 1% change in volatility
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta / 365,  # Daily theta (per calendar day)
            'vega': vega,
            'rho': rho / 100,  # For a 1% change in interest rate
        }
    
    except Exception as e:
        logger.error(f"Error calculating Greeks: {str(e)}")
        raise

def option_strategy_analyzer(strategy, S, r, sigma, days_to_analyze=30):
    """
    Analyze an options strategy across stock prices and time
    
    Args:
        strategy (list): List of dicts with option details:
            - count (int): Number of contracts (negative for sold options)
            - type (str): 'call' or 'put'
            - K (float): Strike price
            - T (float): Time to expiration in years
            - premium (float): Option premium paid/received
        S (float): Current stock price
        r (float): Risk-free interest rate
        sigma (float): Volatility
        days_to_analyze (int): Number of days to analyze
    
    Returns:
        dict: Analysis results with profit/loss at different prices and times
    """
    try:
        # Generate range of stock prices to analyze (±30% from current price)
        price_range = np.linspace(S * 0.7, S * 1.3, 50)
        
        # Generate range of days to analyze
        days_range = np.linspace(0, days_to_analyze, 6)
        
        results = {
            'price_range': price_range.tolist(),
            'days_range': days_range.tolist(),
            'profit_matrix': []
        }
        
        # Calculate profit/loss at each price point and time point
        for days in days_range:
            profit_at_time = []
            
            for price in price_range:
                total_profit = 0
                
                for option in strategy:
                    # Adjust time to expiration
                    adjusted_T = max(0, option['T'] - (days / 365))
                    
                    if adjusted_T == 0:
                        # At expiration, calculate intrinsic value
                        if option['type'] == 'call':
                            option_value = max(0, price - option['K'])
                        else:  # put
                            option_value = max(0, option['K'] - price)
                    else:
                        # Before expiration, use Black-Scholes
                        option_value = calculate_option_price(
                            price, option['K'], adjusted_T, r, sigma, option['type']
                        )
                    
                    # Calculate profit from this option (premium - current value)
                    # For sold options (negative count), profit increases when value decreases
                    option_profit = option['count'] * (option['premium'] - option_value)
                    total_profit += option_profit
                
                profit_at_time.append(round(total_profit, 2))
            
            results['profit_matrix'].append(profit_at_time)
        
        return results
    
    except Exception as e:
        logger.error(f"Error in option strategy analyzer: {str(e)}")
        raise

# Example usage of strategy analyzer:
#
# iron_condor = [
#     {'count': -1, 'type': 'call', 'K': 105, 'T': 0.25, 'premium': 2.5},  # Sold call
#     {'count': 1, 'type': 'call', 'K': 110, 'T': 0.25, 'premium': 1.2},   # Bought call
#     {'count': -1, 'type': 'put', 'K': 95, 'T': 0.25, 'premium': 2.0},    # Sold put
#     {'count': 1, 'type': 'put', 'K': 90, 'T': 0.25, 'premium': 0.8}      # Bought put
# ]
#
# analysis = option_strategy_analyzer(iron_condor, 100, 0.03, 0.2)