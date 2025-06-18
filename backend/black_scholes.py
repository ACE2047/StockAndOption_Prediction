import numpy as np
from scipy.stats import norm
from typing import Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class BlackScholes:
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate

    def calculate_option_price(
        self,
        S: float,  # Current stock price
        K: float,  # Strike price
        T: float,  # Time to expiration in years
        r: Optional[float] = None,  # Risk-free rate
        sigma: float = 0.2,  # Volatility
        option_type: str = 'call',  # 'call' or 'put'
        dividend_yield: float = 0.0  # Dividend yield
    ) -> Dict[str, Union[float, str]]:
        """
        Calculate option price using Black-Scholes model with dividend adjustment.
        Returns a dictionary with price and additional metrics.
        """
        # Robust input validation
        try:
            S = float(S)
            K = float(K)
            T = float(T)
            sigma = float(sigma)
            if r is not None:
                r = float(r)
            dividend_yield = float(dividend_yield)
        except (ValueError, TypeError):
            return {'status': 'error', 'message': 'Invalid input type'}

        if option_type not in ['call', 'put']:
            return {'status': 'error', 'message': 'Invalid option type'}
        if S <= 0 or K <= 0 or T < 0 or sigma <= 0:
            return {'status': 'error', 'message': 'Inputs must be positive and non-zero'}
        try:
            r = r if r is not None else self.risk_free_rate
            T = max(T, 0.0001)  # Prevent division by zero
            
            d1 = (np.log(S / K) + (r - dividend_yield + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type.lower() == 'call':
                price = S * np.exp(-dividend_yield * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
                delta = np.exp(-dividend_yield * T) * norm.cdf(d1)
            else:
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-dividend_yield * T) * norm.cdf(-d1)
                delta = -np.exp(-dividend_yield * T) * norm.cdf(-d1)
            
            # Calculate Greeks
            gamma = np.exp(-dividend_yield * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
            theta = (-S * sigma * np.exp(-dividend_yield * T) * norm.pdf(d1)) / (2 * np.sqrt(T))
            vega = S * np.sqrt(T) * np.exp(-dividend_yield * T) * norm.pdf(d1)
            
            return {
                'price': float(price),
                'delta': float(delta),
                'gamma': float(gamma),
                'theta': float(theta),
                'vega': float(vega),
                'type': option_type,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error calculating option price: {str(e)}")
            return {
                'price': 0.0,
                'status': 'error',
                'message': str(e)
            }

    def calculate_implied_volatility(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: Optional[float] = None,
        option_type: str = 'call',
        dividend_yield: float = 0.0,
        max_iterations: int = 100,
        precision: float = 0.00001
    ) -> Dict[str, Union[float, str]]:
        """
        Calculate implied volatility using Newton-Raphson method.
        """
        try:
            r = r if r is not None else self.risk_free_rate
            sigma = 0.5  # Initial guess
            
            if option_type is None:
                return {'status': 'error', 'message': 'Option type is required'}
            
            for i in range(max_iterations):
                price = self.calculate_option_price(S, K, T, r, sigma, option_type, dividend_yield)['price']
                diff = market_price - price
                
                if abs(diff) < precision:
                    return {
                        'implied_volatility': float(sigma),
                        'status': 'success'
                    }
                
                vega = self.calculate_option_price(S, K, T, r, sigma, option_type, dividend_yield)['vega']
                if abs(vega) < precision:
                    break
                    
                sigma = sigma + diff/vega
                
            return {
                'implied_volatility': float(sigma),
                'status': 'warning',
                'message': 'Maximum iterations reached'
            }
            
        except Exception as e:
            logger.error(f"Error calculating implied volatility: {str(e)}")
            return {
                'implied_volatility': 0.0,
                'status': 'error',
                'message': str(e)
            }
