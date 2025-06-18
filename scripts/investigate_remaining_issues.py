#!/usr/bin/env python3
"""
Investigate remaining VWAP issues
"""

import pandas as pd

def investigate_issues():
    """Investigate what's still wrong with the data."""
    
    df = pd.read_csv('AAPL_2years_data.csv')
    
    print("=== Current Data Analysis ===")
    print("Sample rows:")
    print(df[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(10))
    
    print(f"\nHigh range: ${df['high'].min():.2f} - ${df['high'].max():.2f}")
    print(f"Low range: ${df['low'].min():.2f} - ${df['low'].max():.2f}")
    
    # Check for impossible conditions
    impossible_rows = df[df['high'] < df['low']]
    print(f"\nRows where high < low: {len(impossible_rows)}")
    
    if len(impossible_rows) > 0:
        print("Sample impossible rows:")
        print(impossible_rows[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(5))
    
    # Let's go back to the original API response and map it correctly
    print("\n=== API Response Mapping ===")
    print("From our API test, the response structure is:")
    print("{'v': volume, 'vw': vwap, 'o': open, 'c': close, 'h': high, 'l': low, 't': timestamp, 'n': transactions}")
    print("Values: [49799092.0, 185.2709, 184.41, 185.01, 186.1, 184.41, 1687233600000, 577495]")
    print("So the correct order should be: [volume, vwap, open, close, high, low, timestamp, transactions]")
    
    # Let's check what our current data looks like vs what it should be
    print("\n=== Checking Current vs Expected ===")
    sample_row = df.iloc[0]
    print(f"Current row 0:")
    print(f"  timestamp: {sample_row['timestamp']}")
    print(f"  open: {sample_row['open']}")
    print(f"  high: {sample_row['high']}")
    print(f"  low: {sample_row['low']}")
    print(f"  close: {sample_row['close']}")
    print(f"  volume: {sample_row['volume']}")
    print(f"  vwap: {sample_row['vwap']}")
    print(f"  transactions: {sample_row['transactions']}")
    
    print(f"\nExpected from API (for 2023-06-20):")
    print(f"  volume: 49799092.0")
    print(f"  vwap: 185.2709")
    print(f"  open: 184.41")
    print(f"  close: 185.01")
    print(f"  high: 186.1")
    print(f"  low: 184.41")
    print(f"  timestamp: 1687233600000 (2023-06-20)")
    print(f"  transactions: 577495")
    
    # The issue might be that we're still not mapping correctly
    # Let me check if the VWAP value matches what we expect
    print(f"\nComparison:")
    print(f"  Current VWAP: {sample_row['vwap']} vs Expected: 185.2709")
    print(f"  Current Open: {sample_row['open']} vs Expected: 184.41")
    print(f"  Current High: {sample_row['high']} vs Expected: 186.1")
    print(f"  Current Low: {sample_row['low']} vs Expected: 184.41")

if __name__ == "__main__":
    investigate_issues()