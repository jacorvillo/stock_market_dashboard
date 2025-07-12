#!/usr/bin/env python3
"""
Test script for the new scanner functionality
"""

import pandas as pd
import numpy as np
from scanner_functions import StockScanner

def test_scanner_functionality():
    """Test the new scanner functionality"""
    print("Testing new scanner functionality...")
    
    # Initialize scanner
    scanner = StockScanner()
    
    # Test divergence detection
    print("\n1. Testing divergence detection...")
    
    # Create sample data for testing
    dates = pd.date_range('2024-01-01', periods=20, freq='D')
    close_prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
                              110, 109, 111, 113, 112, 114, 116, 115, 117, 119], index=dates)
    
    # Create RSI data with divergence (price going up, RSI going down)
    rsi_data = pd.Series([50, 52, 51, 53, 55, 54, 56, 58, 57, 59,
                          60, 59, 61, 63, 62, 64, 66, 65, 67, 69], index=dates)
    
    # Create MACD data with divergence (price going up, MACD going down)
    macd_data = pd.Series([0.1, 0.2, 0.15, 0.25, 0.3, 0.25, 0.3, 0.35, 0.3, 0.35,
                           0.4, 0.35, 0.4, 0.45, 0.4, 0.45, 0.5, 0.45, 0.5, 0.55], index=dates)
    
    # Test divergence detection
    divergences = scanner._detect_divergences(close_prices, rsi_data, macd_data)
    print(f"Detected divergences: {divergences}")
    
    # Test RSI extremes detection
    print("\n2. Testing RSI extremes detection...")
    
    # Test overbought RSI
    overbought_rsi = pd.Series([75, 76, 77, 78, 79, 80, 81, 82, 83, 84], index=dates[:10])
    extreme = scanner._detect_rsi_extremes(overbought_rsi)
    print(f"Overbought RSI detection: {extreme}")
    
    # Test oversold RSI
    oversold_rsi = pd.Series([25, 24, 23, 22, 21, 20, 19, 18, 17, 16], index=dates[:10])
    extreme = scanner._detect_rsi_extremes(oversold_rsi)
    print(f"Oversold RSI detection: {extreme}")
    
    # Test neutral RSI
    neutral_rsi = pd.Series([45, 46, 47, 48, 49, 50, 51, 52, 53, 54], index=dates[:10])
    extreme = scanner._detect_rsi_extremes(neutral_rsi)
    print(f"Neutral RSI detection: {extreme}")
    
    print("\n3. Testing scanner with sample data...")
    
    # Test the scanner with a small sample
    try:
        results = scanner.scan_stocks(
            filters={'macd_divergence': 'bullish'},
            universes=['sp500'],
            max_results=5,
            sort_by='volume'
        )
        print(f"Scanner results shape: {results.shape if not results.empty else 'Empty'}")
        if not results.empty:
            print("Sample columns:", list(results.columns))
    except Exception as e:
        print(f"Scanner test error: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_scanner_functionality() 