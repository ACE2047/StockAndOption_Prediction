import numpy as np
from scipy.stats import norm

def calculate_option_price(S, K, T, r, sigma, option_type='call'):
    # S: current stock price
    # K: strike price
    # T: time to expiration in years
    # r: risk-free rate
    # sigma: volatility
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return price
