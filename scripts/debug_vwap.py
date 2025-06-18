#!/usr/bin/env python3
"""
Debug script to investigate VWAP issues
"""

import pandas as pd

def debug_vwap_issues():
    """Debug VWAP values that are outside high-low range."""
    
    df = pd.read_csv('AAPL_2years_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print("=== VWAP Debug Analysis ===\n")
    
    # Find rows where VWAP is outside high-low range
    vwap_issues = df[~((df['low'] <= df['vwap']) & (df['vwap'] <= df['high']))]
    
    print(f"Found {len(vwap_issues)} rows with VWAP outside high-low range")
    print("\nFirst 10 problematic rows:")
    print(vwap_issues[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(10))
    
    # Check if the issue is with high/low values being swapped
    print("\n=== Checking for potential high/low swap ===")
    high_low_swapped = df[df['high'] < df['low']]
    print(f"Rows where high < low: {len(high_low_swapped)}")
    
    if len(high_low_swapped) > 0:
        print("Sample of high/low swapped rows:")
        print(high_low_swapped[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(5))
    
    # Let's also check the original API response to see what we should expect
    print("\n=== Comparing with expected API structure ===")
    print("From our API test, we know the structure should be:")
    print("v (volume), vw (vwap), o (open), c (close), h (high), l (low), t (timestamp), n (transactions)")
    
    # Let's check if we need to swap high and low
    print("\nChecking if high and low are swapped...")
    
    # Sample a few rows to manually verify
    sample_rows = df.head(5)
    print("\nSample rows for manual verification:")
    for idx, row in sample_rows.iterrows():
        print(f"Row {idx}: open={row['open']}, high={row['high']}, low={row['low']}, close={row['close']}, vwap={row['vwap']}")
        
        # Check if VWAP makes sense
        if row['low'] <= row['vwap'] <= row['high']:
            print(f"  ✓ VWAP {row['vwap']} is within range [{row['low']}, {row['high']}]")
        else:
            print(f"  ✗ VWAP {row['vwap']} is OUTSIDE range [{row['low']}, {row['high']}]")
            
            # Check if swapping high/low would fix it
            if row['high'] <= row['vwap'] <= row['low']:
                print(f"  → Swapping high/low would fix this: VWAP {row['vwap']} would be in [{row['high']}, {row['low']}]")

if __name__ == "__main__":
    debug_vwap_issues()