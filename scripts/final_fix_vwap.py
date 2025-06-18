#!/usr/bin/env python3
"""
Final fix for VWAP data - swap high and low columns
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def final_fix_vwap():
    """Apply the final fix by swapping high and low columns."""
    
    logger.info("Reading current AAPL_2years_data.csv...")
    df = pd.read_csv('AAPL_2years_data.csv')
    
    logger.info("Current data sample:")
    print(df[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(3))
    
    # Swap high and low columns
    logger.info("Swapping high and low columns...")
    df_fixed = df.copy()
    df_fixed['high'] = df['low']  # What was labeled as 'low' is actually 'high'
    df_fixed['low'] = df['high']  # What was labeled as 'high' is actually 'low'
    
    logger.info("Fixed data sample:")
    print(df_fixed[['timestamp', 'open', 'high', 'low', 'close', 'vwap']].head(3))
    
    # Validate the fix
    logger.info("Validating the fix...")
    vwap_issues = 0
    for idx, row in df_fixed.iterrows():
        if not (row['low'] <= row['vwap'] <= row['high']):
            vwap_issues += 1
    
    logger.info(f"VWAP validation: {vwap_issues} issues found (should be 0 or very few)")
    
    # Save the final corrected data
    df_fixed.to_csv('AAPL_2years_data.csv', index=False)
    logger.info("Final corrected data saved to AAPL_2years_data.csv")
    
    # Also save a backup
    df_fixed.to_csv('AAPL_2years_data_final.csv', index=False)
    logger.info("Backup saved to AAPL_2years_data_final.csv")
    
    return df_fixed

if __name__ == "__main__":
    fixed_df = final_fix_vwap()
    print(f"\nFinal fix completed!")
    print(f"Data shape: {fixed_df.shape}")
    print(f"Date range: {fixed_df['timestamp'].min()} to {fixed_df['timestamp'].max()}")