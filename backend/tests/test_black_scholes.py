import pytest
from backend.black_scholes import BlackScholes
import numpy as np
import time

@pytest.fixture
def bs():
    return BlackScholes(risk_free_rate=0.05)

def test_call_option_price(bs):
    result = bs.calculate_option_price(
        S=100,  # Current stock price
        K=100,  # Strike price
        T=1.0,  # Time to expiration
        sigma=0.2,  # Volatility
        option_type='call'
    )
    
    assert result['status'] == 'success'
    assert isinstance(result['price'], float)
    assert result['price'] > 0
    assert 'delta' in result
    assert 'gamma' in result
    assert 'theta' in result
    assert 'vega' in result

def test_put_option_price(bs):
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='put'
    )
    
    assert result['status'] == 'success'
    assert isinstance(result['price'], float)
    assert result['price'] > 0
    assert result['delta'] < 0  # Put delta should be negative

def test_implied_volatility(bs):
    # First calculate a call option price
    price_result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='call'
    )
    
    # Then calculate implied volatility from that price
    iv_result = bs.calculate_implied_volatility(
        market_price=price_result['price'],
        S=100,
        K=100,
        T=1.0,
        option_type='call'
    )
    
    assert iv_result['status'] == 'success'
    assert abs(iv_result['implied_volatility'] - 0.2) < 0.01

def test_edge_cases(bs):
    # Test zero time to expiration
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=0.0,
        sigma=0.2,
        option_type='call'
    )
    assert result['status'] == 'success'
    
    # Test very high volatility
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=2.0,
        option_type='call'
    )
    assert result['status'] == 'success'
    assert result['price'] > 0

    # Test very large stock price
    result = bs.calculate_option_price(
        S=1e10,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='call'
    )
    assert result['status'] == 'success'

    # Test very small stock price
    result = bs.calculate_option_price(
        S=1e-10,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='call'
    )
    assert result['status'] == 'success'

    # Test zero stock price
    result = bs.calculate_option_price(
        S=0,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='call'
    )
    assert result['status'] == 'error'

    # Test very large volatility
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=10.0,
        option_type='call'
    )
    assert result['status'] == 'success'

    # Test very small volatility
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=1e-10,
        option_type='call'
    )
    assert result['status'] == 'success'

    # Test zero volatility
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=0,
        option_type='call'
    )
    assert result['status'] == 'error'

def test_error_handling(bs):
    # Test invalid option type
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='invalid'
    )
    assert result['status'] == 'error'

    # Test negative stock price
    result = bs.calculate_option_price(
        S=-100,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='call'
    )
    assert result['status'] == 'error'

    # Test non-numeric stock price
    result = bs.calculate_option_price(
        S='invalid',
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='call'
    )
    assert result['status'] == 'error'

    # Test missing parameter
# result = bs.calculate_option_price(
#     S=100,
#     K=100,
#     T=1.0,
#     sigma=0.2
# )
# assert result['status'] == 'error'

    with pytest.raises(TypeError):
            bs.calculate_option_price(
                K=100,
                T=1.0,
                sigma=0.2,
                option_type='call'
            )
def test_greeks_calculation(bs):
    result = bs.calculate_option_price(
        S=100,
        K=100,
        T=1.0,
        sigma=0.2,
        option_type='call'
    )
    
    # Check that all Greeks are present and have reasonable values
    assert 0 <= result['delta'] <= 1  # Call delta should be between 0 and 1
    assert result['gamma'] > 0  # Gamma should always be positive
    assert result['vega'] > 0  # Vega should always be positive
    assert result['theta'] < 0  # Theta should be negative for long options 

def test_boundary_conditions(bs):
    # Test very large strike price
    result = bs.calculate_option_price(S=100, K=1e10, T=1.0, sigma=0.2, option_type='call')
    assert result['status'] == 'success'
    assert result['price'] >= 0

    # Test very small strike price
    result = bs.calculate_option_price(S=100, K=1e-10, T=1.0, sigma=0.2, option_type='call')
    assert result['status'] == 'success'
    assert result['price'] >= 0

    # Test extreme time value (very large)
    result = bs.calculate_option_price(S=100, K=100, T=1e5, sigma=0.2, option_type='call')
    assert result['status'] == 'success'
    assert result['price'] >= 0

    # Test extreme time value (very small)
    result = bs.calculate_option_price(S=100, K=100, T=1e-5, sigma=0.2, option_type='call')
    assert result['status'] == 'success'
    assert result['price'] >= 0 

def test_integration(bs):
    # Test implied volatility calculation with valid option price
    result = bs.calculate_implied_volatility(market_price=10.0, S=100, K=100, T=1.0, option_type='call')
    assert result['status'] == 'success'
    assert result['implied_volatility'] > 0

    # Test implied volatility with invalid market price
    result = bs.calculate_implied_volatility(market_price=-10.0, S=100, K=100, T=1.0, option_type='call')
    assert result['status'] == 'error'

    # Test implied volatility with zero market price
    result = bs.calculate_implied_volatility(market_price=0.0, S=100, K=100, T=1.0, option_type='call')
    assert result['status'] == 'error' 

def test_performance(bs):
    start_time = time.time()
    for _ in range(1000):
        bs.calculate_option_price(S=100, K=100, T=1.0, sigma=0.2, option_type='call')
    end_time = time.time()
    assert end_time - start_time < 1.0  # Ensure the function completes within 1 second 