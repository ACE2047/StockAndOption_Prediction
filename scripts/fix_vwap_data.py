#!/usr/bin/env python3
"""
Script to fix the VWAP data issue in AAPL_2years_data.csv
The volume and vwap columns are swapped in the current file.
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_vwap_data():
    """Fix the VWAP data by swapping volume and vwap columns and fixing timestamps."""
    
    # Read the CSV file
    logger.info("Reading AAPL_2years_data.csv...")
    df = pd.read_csv('AAPL_2years_data.csv')
    
    logger.info(f"Original data shape: {df.shape}")
    logger.info(f"Original columns: {list(df.columns)}")
    
    # Display first few rows to confirm the issue
    logger.info("First 3 rows of original data:")
    print(df.head(3))
    
    # Swap the volume and vwap columns
    logger.info("Swapping volume and vwap columns...")
    df_fixed = df.copy()
    df_fixed['volume'] = df['vwap']  # What was labeled as vwap is actually volume
    df_fixed['vwap'] = df['volume']  # What was labeled as volume is actually vwap
    
    # Fix the timestamps - convert from Unix timestamp (milliseconds) to readable format
    logger.info("Converting timestamps...")
    # The timestamps in the file appear to be Unix timestamps in milliseconds
    # Let's check if the volume column (which should contain large numbers) contains timestamp-like values
    
    # First, let's examine what's in the volume column after our swap
    sample_volume = df_fixed['volume'].iloc[0]
    logger.info(f"Sample volume value after swap: {sample_volume}")
    
    # If the volume values are very large (like Unix timestamps), we need to fix this
    if sample_volume > 1000000000:  # This would be a timestamp, not volume
        logger.info("Volume values appear to be timestamps. Need to investigate data structure...")
        
        # Let's look at the actual API response structure
        # Based on Polygon API docs, the order should be:
        # [timestamp, open, high, low, close, volume, vwap, transactions]
        # But our data seems to have volume and vwap swapped
        
        # The correct mapping should be:
        df_corrected = pd.DataFrame()
        df_corrected['timestamp'] = pd.to_datetime(df['volume'], unit='ms')  # volume column contains timestamps
        df_corrected['open'] = df['open']
        df_corrected['high'] = df['high'] 
        df_corrected['low'] = df['low']
        df_corrected['close'] = df['close']
        df_corrected['volume'] = df['transactions']  # transactions column contains volume
        df_corrected['vwap'] = df['vwap']  # this was correct
        df_corrected['transactions'] = df['volume']  # volume column contains transactions
        
        logger.info("Applied corrected column mapping")
        df_fixed = df_corrected
    
    # Display first few rows of fixed data
    logger.info("First 3 rows of fixed data:")
    print(df_fixed.head(3))
    
    # Save the fixed data
    output_filename = 'AAPL_2years_data_fixed.csv'
    df_fixed.to_csv(output_filename, index=False)
    logger.info(f"Fixed data saved to {output_filename}")
    
    # Also backup the original file
    backup_filename = 'AAPL_2years_data_backup.csv'
    df.to_csv(backup_filename, index=False)
    logger.info(f"Original data backed up to {backup_filename}")
    
    return df_fixed

if __name__ == "__main__":
    fixed_df = fix_vwap_data()
    print("\nData fixing completed!")
    print(f"Fixed data shape: {fixed_df.shape}")
    print(f"Date range: {fixed_df['timestamp'].min()} to {fixed_df['timestamp'].max()}")