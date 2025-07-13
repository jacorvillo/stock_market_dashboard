"""
Impulse System Functions for Stock Market Dashboard

The Impulse System combines EMA trend and MACD Histogram momentum to generate signals.
Key components:
- Trend: EMA slope direction (rising/falling)
- Momentum: MACD-Histogram movement (rising/falling)

Color signals:
- Green: EMA rising + MACD-Histogram rising (especially below zero)
- Red: EMA falling + MACD-Histogram falling (especially below zero)
- Blue: All other conditions
"""

import pandas as pd
import numpy as np

def calculate_impulse_system(df, ema_period=13):
    """
    Calculate Impulse System signals based on EMA trend and MACD Histogram momentum
    
    Parameters:
    - df: DataFrame with OHLC data and indicators (must have EMA_{ema_period} and MACD_hist columns)
    - ema_period: The EMA period to use for trend direction (default: 13)
    
    Returns:
    - DataFrame with added 'impulse_color' column containing 'green', 'red', or 'blue'
    """
    try:
        df = df.copy()
        
        # Check if we have the required indicators
        ema_col = f'EMA_{ema_period}'
        if ema_col not in df.columns or 'MACD_hist' not in df.columns:
            # Default to 'blue' if indicators are missing
            df['impulse_color'] = 'blue'
            return df
        
        # Calculate EMA slope (trend direction)
        df['ema_slope'] = df[ema_col].diff()
        
        # Calculate MACD Histogram change (momentum)
        df['macd_hist_change'] = df['MACD_hist'].diff()
        
        # Initialize the impulse color column with default 'blue'
        df['impulse_color'] = 'blue'
        
        # Green: EMA rising + MACD-Histogram rising (especially below zero)
        green_condition = (df['ema_slope'] > 0) & (df['macd_hist_change'] > 0)
        # Additional emphasis if MACD-Histogram is below zero (stronger signal)
        strong_green_condition = green_condition & (df['MACD_hist'] < 0)
        
        # Red: EMA falling + MACD-Histogram falling (especially below zero)
        red_condition = (df['ema_slope'] < 0) & (df['macd_hist_change'] < 0)
        # Additional emphasis if MACD-Histogram is below zero (stronger signal)
        strong_red_condition = red_condition & (df['MACD_hist'] < 0)
        
        # Apply the conditions to set the colors
        df.loc[green_condition | strong_green_condition, 'impulse_color'] = 'green'
        df.loc[red_condition | strong_red_condition, 'impulse_color'] = 'red'
        
        # Clean up temporary columns
        df = df.drop(['ema_slope', 'macd_hist_change'], axis=1)
        
        return df
    
    except Exception as e:
        print(f"Error in calculate_impulse_system: {e}")
        df['impulse_color'] = 'blue'  # Default to blue on error
        return df

def get_impulse_colors(impulse_color):
    """
    Get the appropriate colors for candlesticks based on impulse color
    
    Parameters:
    - impulse_color: 'green', 'red', or 'blue'
    
    Returns:
    - Dictionary with line and fill colors for increasing and decreasing candles
    """
    colors = {
        'green': {
            'increasing_line_color': '#00ff88',  # Bright green
            'increasing_fillcolor': 'rgba(0, 255, 136, 0.4)',
            'decreasing_line_color': '#00ff88',  # Same green for decreasing
            'decreasing_fillcolor': 'rgba(0, 255, 136, 0.2)'  # Lighter fill for decreasing
        },
        'red': {
            'increasing_line_color': '#ff4444',  # Bright red
            'increasing_fillcolor': 'rgba(255, 68, 68, 0.2)',  # Lighter fill for increasing
            'decreasing_line_color': '#ff4444',  # Same red for decreasing
            'decreasing_fillcolor': 'rgba(255, 68, 68, 0.4)'
        },
        'blue': {
            'increasing_line_color': '#00d4ff',  # Bright blue
            'increasing_fillcolor': 'rgba(0, 212, 255, 0.4)',
            'decreasing_line_color': '#00d4ff',  # Same blue for decreasing
            'decreasing_fillcolor': 'rgba(0, 212, 255, 0.2)'  # Lighter fill for decreasing
        }
    }
    
    # Default to blue if color not found
    return colors.get(impulse_color, colors['blue'])
