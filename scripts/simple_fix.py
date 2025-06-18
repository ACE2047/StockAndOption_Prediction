#!/usr/bin/env python3
"""
Simple direct fix based on known API values
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_fix():
    """Apply a simple fix by correctly mapping the columns."""
    
    # Read current data
    df = pd.read_csv('AAPL_2years_data.csv')
    
    logger.info("Current problematic data sample:")
    print(df[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(3))
    
    # From our API test, we know the first row should be:
    # Expected: open=184.41, high=186.1, low=184.41, close=185.01, vwap=185.2709
    # Current:  open=185.2709, high=185.01, low=184.41, close=186.1, vwap=184.41
    
    # So the mapping should be:
    # current_open -> expected_vwap (185.2709 -> 185.2709) ✓
    # current_high -> expected_close (185.01 -> 185.01) ✓  
    # current_low -> expected_open (184.41 -> 184.41) ✓
    # current_close -> expected_high (186.1 -> 186.1) ✓
    # current_vwap -> expected_low (184.41 -> 184.41) ✓
    
    logger.info("Applying correct column mapping...")
    df_fixed = df.copy()
    
    # Store original values
    orig_open = df['open'].copy()
    orig_high = df['high'].copy() 
    orig_low = df['low'].copy()
    orig_close = df['close'].copy()
    orig_vwap = df['vwap'].copy()
    
    # Apply correct mapping
    df_fixed['open'] = orig_low      # low -> open
    df_fixed['high'] = orig_close    # close -> high  
    df_fixed['low'] = orig_vwap      # vwap -> low
    df_fixed['close'] = orig_high    # high -> close
    df_fixed['vwap'] = orig_open     # open -> vwap
    
    logger.info("Fixed data sample:")
    print(df_fixed[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(3))
    
    # Validate the fix
    logger.info("Validating the fix...")
    vwap_issues = 0
    high_low_issues = 0
    
    for idx, row in df_fixed.iterrows():
        # Check if high >= low
        if row['high'] < row['low']:
            high_low_issues += 1
        
        # Check if VWAP is within high-low range
        if not (row['low'] <= row['vwap'] <= row['high']):
            vwap_issues += 1
    
    logger.info(f"High < Low issues: {high_low_issues} (should be 0)")
    logger.info(f"VWAP outside range issues: {vwap_issues} (should be 0 or very few)")
    
    # Save the fixed data
    df_fixed.to_csv('AAPL_2years_data.csv', index=False)
    logger.info("Fixed data saved to AAPL_2years_data.csv")
    
    return df_fixed

if __name__ == "__main__":
    fixed_df = simple_fix()
    print(f"\nSimple fix completed!")
    print(f"Data shape: {fixed_df.shape}")
    
    # Show expected vs actual for first row
    print(f"\nValidation for first row:")
    row = fixed_df.iloc[0]
    print(f"Expected: open=184.41, high=186.1, low=184.41, close=185.01, vwap=185.2709")
    print(f"Actual:   open={row['open']}, high={row['high']}, low={row['low']}, close={row['close']}, vwap={row['vwap']}")