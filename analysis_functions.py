import pandas as pd
import numpy as np
import datetime as dt
from datetime import datetime, timedelta
import yfinance as yf
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.subplots import make_subplots

# Simple cache for recently viewed tickers (speeds up repeated requests)
_ticker_cache = {}
_cache_expiry = {}
CACHE_DURATION_SECONDS = 60  # Cache data for 1 minute

def _is_cache_valid(symbol, timeframe):
    """Check if cached data is still valid"""
    cache_key = f"{symbol}_{timeframe}"
    if cache_key not in _ticker_cache or cache_key not in _cache_expiry:
        return False
    
    # Check if cache has expired
    from datetime import datetime
    return datetime.now().timestamp() < _cache_expiry[cache_key]

def _get_cached_data(symbol, timeframe):
    """Get cached data if available and valid"""
    cache_key = f"{symbol}_{timeframe}"
    if _is_cache_valid(symbol, timeframe):
        return _ticker_cache[cache_key]
    return None

def _cache_data(symbol, timeframe, data, start_date, end_date, is_minute_data):
    """Cache data for fast retrieval"""
    cache_key = f"{symbol}_{timeframe}"
    from datetime import datetime
    _ticker_cache[cache_key] = (data.copy(), start_date, end_date, is_minute_data)
    _cache_expiry[cache_key] = datetime.now().timestamp() + CACHE_DURATION_SECONDS

# Function to fetch stock data with lookback for indicators
def get_stock_data(symbol="SPY", period="1y", frequency=None, ema_periods=[13, 26]):
    """Fetch stock data from yfinance with caching for faster ticker switching, with extended lookback for intraday EMA warmup."""
    try:
        # Check cache first for non-intraday data (intraday needs real-time updates)
        if period != "1d":
            cached_result = _get_cached_data(symbol, period)
            if cached_result is not None:
                return cached_result
        
        # Sanitize symbol for safety
        symbol = symbol.strip().upper()
        if not symbol or not all(c.isalnum() or c in ['-', '.'] for c in symbol):
            symbol = "SPY"
            
        # Check if intraday (1d or yesterday) data is requested
        is_intraday = period in ["1d", "yesterday"]
        
        # Get current time in CEST (user's timezone)
        now_cest = datetime.now()
        
        # Convert CEST to UTC first
        # CEST is UTC+2, so subtract 2 hours to get UTC
        now_utc = now_cest - timedelta(hours=2)
        
        # Convert UTC to Eastern Time (EDT is UTC-4 in summer, EST is UTC-5 in winter)
        # For July 2025, we're in EDT (summer time), so UTC-4
        now_et = now_utc - timedelta(hours=4)
        
        # Check if we are in market hours (9:30AM - 4:00PM ET)
        is_market_open = (now_et.hour > 9 or (now_et.hour == 9 and now_et.minute >= 30)) and now_et.hour < 16
        is_pre_market = now_et.hour < 9 or (now_et.hour == 9 and now_et.minute < 30)
        is_after_market = now_et.hour >= 16
        is_weekend = now_et.weekday() >= 5  # Saturday=5, Sunday=6
        
        # Handle "yesterday" period first - always fetch previous trading day data
        if period == "yesterday":
            
            # Calculate the previous trading day (skip weekends and go back to last business day)
            current_date = now_cest.date()
            
            # Go back one day and find the previous business day
            prev_day = current_date - pd.Timedelta(days=1)
            while prev_day.weekday() > 4:  # 5=Saturday, 6=Sunday
                prev_day = prev_day - pd.Timedelta(days=1)
                
            # Fetch minute data for a period that includes multiple previous trading days for indicator calculation
            # Use "7d" period to ensure we get enough data for accurate indicator calculations
            ticker = yf.Ticker(symbol)
            try:
                data = ticker.history(period="7d", interval="1m", timeout=5)
                
                if data.empty:
                    # Fallback to daily data and then filter
                    data = ticker.history(period="7d", interval="1d", timeout=5)
                    if data.empty:
                        raise Exception(f"No data available for {symbol}")
                
                data.reset_index(inplace=True)
                
                # Handle the Date/Datetime column and convert to CEST
                if 'Datetime' in data.columns:
                    data = data.rename(columns={'Datetime': 'Date'})
                
                # Convert from ET to CEST (add 6 hours for summer time)
                data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
                data['Date'] = data['Date'] + timedelta(hours=6)  # Convert EDT to CEST
                
                # Keep the full dataset for indicator calculation
                full_data_for_indicators = data.copy()
                
                # Filter to only show data from the previous trading day in CEST for display
                display_data = data[data['Date'].dt.date == prev_day]
                
                # Replace the display data with filtered data but keep full dataset for indicator calculation
                data = display_data
                
                if data.empty:
                    # Return empty dataset if no data for yesterday
                    empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    start_date = pd.Timestamp(prev_day)
                    end_date = pd.Timestamp(prev_day)
                    is_minute_data = True
                    return empty_df, start_date, end_date, is_minute_data
                
                # Filter to market hours (15:30 to 22:00 CEST, which is 9:30 AM to 4:00 PM ET)
                data = data[
                    (data['Date'].dt.time >= pd.Timestamp('15:30:00').time()) &
                    (data['Date'].dt.time <= pd.Timestamp('22:00:00').time())
                ]
                
                if data.empty:
                    empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    start_date = pd.Timestamp(prev_day)
                    end_date = pd.Timestamp(prev_day)
                    is_minute_data = True
                    return empty_df, start_date, end_date, is_minute_data
                
                # Set start and end dates for the display
                start_date = data['Date'].min()
                end_date = data['Date'].max()
                is_minute_data = True
                
                return data, start_date, end_date, is_minute_data
                
            except Exception as e:
                # Return empty dataset on error
                empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                start_date = pd.Timestamp(prev_day)
                end_date = pd.Timestamp(prev_day)
                is_minute_data = True
                return empty_df, start_date, end_date, is_minute_data
        
        # Handle intraday data differently - get minute data for 1-day period
        if is_intraday:
            # Special handling for "yesterday" period - always fetch previous trading day data
            if period == "yesterday":
                # Skip to the "yesterday" handling logic later in the function
                pass
            else:
                # For 1D view: Show empty chart when market is closed, real-time data when open
                
                if is_weekend:
                    # Return empty dataset when it's weekend
                    empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    start_date = now_cest
                    end_date = now_cest
                    is_minute_data = True
                    return empty_df, start_date, end_date, is_minute_data
                elif is_pre_market or is_after_market:
                    # During trading days but outside market hours, return empty dataset
                    # This ensures we only show data during active market hours
                    empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    start_date = now_cest
                    end_date = now_cest
                    is_minute_data = True
                    return empty_df, start_date, end_date, is_minute_data
            
            # Market is open - fetch real-time minute data for today only
            
            # Fetch minute data using yfinance - Include PREVIOUS DAYS' data for proper indicator calculation
            ticker = yf.Ticker(symbol)
            try:
                # For intraday, fetch 5 days of minute data to include previous market periods
                # This ensures indicators have enough historical data to calculate properly from market open
                interval_arg = frequency if frequency else "1m"
                data = ticker.history(period="5d", interval=interval_arg, timeout=5)  # Extended period for indicators
                
                # Convert timestamps to CEST timezone for display
                data.reset_index(inplace=True)
                
                # Handle the Date/Datetime column and convert to CEST
                if 'Datetime' in data.columns:
                    data = data.rename(columns={'Datetime': 'Date'})
                
                # Convert from ET to CEST
                # yfinance intraday data comes in ET timezone
                # EDT is UTC-4, so to convert to CEST (UTC+2): add 6 hours
                # EST is UTC-5, so to convert to CEST (UTC+1): add 6 hours (winter)
                # For July 2025, we're in summer time, so EDT to CEST = +6 hours
                data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
                data['Date'] = data['Date'] + timedelta(hours=6)  # Convert EDT to CEST
                
                # Store the full dataset for indicator calculation
                full_data_for_indicators = data.copy()
                
                # Filter to only show data from today in CEST for display
                today_cest = now_cest.date()
                display_data = data[data['Date'].dt.date == today_cest]
                
                # If today's data is empty, return empty dataset
                if display_data.empty:
                    empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    start_date = now_cest
                    end_date = now_cest
                    is_minute_data = True
                    return empty_df, start_date, end_date, is_minute_data
                    
                # Use display_data for UI but keep all data for indicator calculation
                data = display_data
                
                if data.empty:
                    empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    start_date = now_cest
                    end_date = now_cest
                    is_minute_data = True
                    return empty_df, start_date, end_date, is_minute_data
                
                # Set start and end dates for the display
                start_date = data['Date'].min()
                end_date = data['Date'].max()
                is_minute_data = True
                
                return data, start_date, end_date, is_minute_data
                
            except Exception as e:
                # Return empty dataset on error
                empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                start_date = now_cest
                end_date = now_cest
                is_minute_data = True
                return empty_df, start_date, end_date, is_minute_data
        else:
            # Calculate optimized period for faster loading while maintaining indicator accuracy
            # Reduced extended periods for faster ticker switching
            extended_period = period
            if period == "1mo":
                extended_period = "3mo"  # Reduced from 6mo for faster loading
            elif period == "6mo":
                extended_period = "1y"   # Keep as is (reasonable)
            elif period == "ytd":
                extended_period = "1y"   # Reduced from 2y for faster loading
            elif period == "1y":
                extended_period = "2y"   # Reduced from 3y for faster loading
            elif period == "5y":
                extended_period = "7y"   # Reduced from 10y for faster loading
            
            # Try to fetch real stock data with reduced timeout for faster response
            ticker = yf.Ticker(symbol)
            interval_arg = frequency if frequency else None
            if interval_arg:
                data = ticker.history(period=extended_period, interval=interval_arg, timeout=3)  # Reduced timeout for faster switching
            else:
                data = ticker.history(period=extended_period, timeout=3)  # Reduced timeout for faster switching
        
        if data.empty or len(data) < 5:  # Consider requiring minimum number of data points
            # Fallback to SPY if current symbol fails
            if symbol != "SPY":
                ticker = yf.Ticker("SPY")
                interval_arg = frequency if frequency else None
                if interval_arg:
                    data = ticker.history(period=extended_period, interval=interval_arg, timeout=3)  # Reduced timeout
                else:
                    data = ticker.history(period=extended_period, timeout=3)  # Reduced timeout
                if data.empty:
                    raise Exception(f"Could not fetch data for {symbol} or SPY fallback")
            else:
                raise Exception(f"Could not fetch data for {symbol}")
            
        data.reset_index(inplace=True)
        
        # Handle the Date/Datetime column
        # YFinance may return 'Date' for daily data or 'Datetime' for intraday data
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)  # Remove timezone info
        elif 'Datetime' in data.columns:
            # For intraday data, rename Datetime to Date for consistency
            data = data.rename(columns={'Datetime': 'Date'})
            data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)  # Remove timezone info
        
        # Exclude weekends
        # Only keep business days (Monday=0 to Friday=4)
        data = data[data['Date'].dt.weekday < 5]
        
        # Calculate the target end date and start date for the requested period
        end_date = data['Date'].max()
        
        # Calculate start date based on requested period
        if period == "1d":
            # For intraday data, calculate precise 1 day window
            if is_intraday:
                # For 1d intraday view, show just one full trading day (9:30AM - 4:00PM)
                # Get today's market date
                trading_day = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                # Calculate market opening and closing times
                market_open = trading_day.replace(hour=9, minute=30)
                market_close = trading_day.replace(hour=16, minute=0)
                
                # For intraday data, we'll restrict to market hours on the display date
                start_date = market_open
                
                # If we're showing yesterday's data (pre-market), ensure we get correct market hours
                if is_pre_market:
                    # We're viewing previous day's data, so use that date's market session
                    start_date = trading_day.replace(hour=9, minute=30)
                    end_date = trading_day.replace(hour=16, minute=0)
                
            else:
                start_date = end_date - pd.Timedelta(days=1)
        elif period == "1mo":
            start_date = end_date - pd.DateOffset(months=1)
        elif period == "6mo":
            start_date = end_date - pd.DateOffset(months=6)
        elif period == "ytd":
            # For YTD, exclude today from the data if we're in pre-market hours
            # Using ET (market time) for the determination
            if is_pre_market:
                # Adjust end_date to previous day's end
                end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0) - pd.Timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59)
                
            # Create a naive datetime object for January 1st of the current year
            start_date = pd.Timestamp(end_date.year, 1, 1)
        elif period == "1y":
            start_date = end_date - pd.DateOffset(years=1)
        elif period == "5y":
            start_date = end_date - pd.DateOffset(years=5)
        else:  # max
            start_date = data['Date'].min()
        
        # Store the full data for indicator calculation
        full_data = data.copy()
        
        # For intraday data, add a marker to identify this as minute-level data
        is_minute_data = False
        if period in ["1d", "yesterday"] and is_intraday and len(data) > 0:
            # Check if the data has minute granularity (check time differences)
            time_diffs = pd.Series(data['Date'].diff().dropna())
            if len(time_diffs) > 0:
                # If the median time difference is less than 10 minutes, it's likely minute data
                median_diff_seconds = time_diffs.median().total_seconds()
                is_minute_data = median_diff_seconds < 600  # 10 minutes in seconds
        
        # Cache non-intraday data for faster ticker switching (don't cache intraday as it needs real-time updates)
        if period not in ["1d", "yesterday"]:
            _cache_data(symbol, period, full_data, start_date, end_date, is_minute_data)
        
        # After indicator calculation, we'll trim to the requested period
        return full_data, start_date, end_date, is_minute_data
        
    except Exception as e:
        # Try SPY as fallback
        try:
            if symbol != "SPY":
                ticker = yf.Ticker("SPY")
                data = ticker.history(period="1y", timeout=5)
                if not data.empty:
                    data.reset_index(inplace=True)
                    if 'Date' in data.columns:
                        data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
                    elif 'Datetime' in data.columns:
                        data = data.rename(columns={'Datetime': 'Date'})
                        data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
                    
                    end_date = data['Date'].max()
                    start_date = end_date - pd.DateOffset(months=1)  # Default to 1 month
                    is_minute_data = False
                    return data, start_date, end_date, is_minute_data
            
            # If SPY also fails, raise error
            raise Exception(f"Could not fetch data for {symbol} or SPY fallback")
            
        except Exception as fallback_error:
            raise Exception(f"No data available for {symbol}")

# Function to calculate technical indicators with custom parameters
def calculate_indicators(df, ema_periods=[13, 26], macd_fast=12, macd_slow=26, macd_signal=9, force_smoothing=2, adx_period=13, stoch_period=5, rsi_period=13, fast_mode=False):
    """Calculate technical indicators for the stock data with custom parameters
    fast_mode: If True, calculates only essential indicators for faster ticker switching"""
    try:
        df = df.copy()
        
        # Handle empty dataframes (e.g., when market is closed for 1D view)
        if df.empty:
            # Return empty dataframe with indicator columns
            for period in ema_periods:
                df[f'EMA_{period}'] = []
            df['MACD'] = []
            df['MACD_signal'] = []
            df['MACD_hist'] = []
            df['Force_Index'] = []
            df['AD_Line'] = []
            df['ADX'] = []
            df['DI_plus'] = []
            df['DI_minus'] = []
            df['ATR'] = []
            df['Stoch_K'] = []
            df['Stoch_D'] = []
            df['RSI'] = []
            df['OBV'] = []
            return df
        
        # Only calculate indicators if we have enough data
        min_length = len(df)
        
        if fast_mode:
            # In fast mode, only calculate the most essential indicators
            ema_periods = ema_periods[:2] if len(ema_periods) > 2 else ema_periods  # Limit to 2 EMAs max
        
        # Track unreliable rows for warning (for intraday)
        unreliable_mask = pd.Series(False, index=df.index)
        indicator_columns = []

        # Custom EMA periods (optimized for speed)
        for period in ema_periods:
            col = f'EMA_{period}'
            if min_length >= max(period, 10):
                ema_series = ta.trend.EMAIndicator(df['Close'], window=period).ema_indicator()
                df[col] = ema_series
                indicator_columns.append(col)
                unreliable_mask |= ema_series.isna()
            else:
                df[col] = df['Close'].ffill()
                indicator_columns.append(col)

        # MACD with custom parameters
        macd_cols = ['MACD', 'MACD_signal', 'MACD_hist']
        if min_length >= max(macd_fast, macd_slow):
            macd = ta.trend.MACD(df['Close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal)
            macd_macd = macd.macd().fillna(method='bfill')
            macd_signal = macd.macd_signal().fillna(method='bfill')
            macd_hist = macd.macd_diff().fillna(method='bfill')
            df['MACD'] = macd_macd
            df['MACD_signal'] = macd_signal
            df['MACD_hist'] = macd_hist
            unreliable_mask |= macd.macd().isna() | macd.macd_signal().isna() | macd.macd_diff().isna()
        else:
            df['MACD'] = 0
            df['MACD_signal'] = 0
            df['MACD_hist'] = 0

        # Force Index with smoothing
        if min_length >= 2:
            force_raw = ta.volume.ForceIndexIndicator(df['Close'], df['Volume']).force_index()
            if force_smoothing > 1 and min_length >= force_smoothing:
                df['Force_Index'] = force_raw.rolling(window=force_smoothing).mean()
            else:
                df['Force_Index'] = force_raw
        else:
            df['Force_Index'] = 0

        # A/D Line (Accumulation/Distribution)
        if min_length >= 1:
            ad_line = ta.volume.AccDistIndexIndicator(df['High'], df['Low'], df['Close'], df['Volume']).acc_dist_index()
            df['AD'] = ad_line
            df['AD_Line'] = ad_line
        else:
            df['AD'] = 0
            df['AD_Line'] = 0

        # ADX, DI+, and DI- indicators
        adx_cols = ['ADX', 'DI_plus', 'DI_minus']
        adx_period = max(1, min(adx_period, 50))
        if min_length >= max(14, adx_period):
            adx_indicator = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=adx_period)
            adx = adx_indicator.adx().fillna(method='bfill')
            di_plus = adx_indicator.adx_pos().fillna(method='bfill')
            di_minus = adx_indicator.adx_neg().fillna(method='bfill')
            df['ADX'] = adx
            df['DI_plus'] = di_plus
            df['DI_minus'] = di_minus
            unreliable_mask |= adx_indicator.adx().isna() | adx_indicator.adx_pos().isna() | adx_indicator.adx_neg().isna()
        else:
            df['ADX'] = 25
            df['DI_plus'] = 25
            df['DI_minus'] = 25

        # ATR for bands calculation
        if min_length >= 14:
            df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        else:
            df['ATR'] = (df['High'] - df['Low']).rolling(window=min(14, min_length)).mean()

        # Slow Stochastic (%K and %D)
        stoch_cols = ['Stoch_K', 'Stoch_D']
        stoch_period = max(1, min(stoch_period, 50))
        if min_length >= max(14, stoch_period):
            stoch_indicator = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=stoch_period, smooth_window=3)
            stoch_k = stoch_indicator.stoch().fillna(method='bfill')
            stoch_d = stoch_indicator.stoch_signal().fillna(method='bfill')
            df['Stoch_K'] = stoch_k
            df['Stoch_D'] = stoch_d
            unreliable_mask |= stoch_indicator.stoch().isna() | stoch_indicator.stoch_signal().isna()
        else:
            df['Stoch_K'] = 50
            df['Stoch_D'] = 50

        # Relative Strength Index (RSI)
        rsi_period = max(1, min(rsi_period, 50))
        if min_length >= max(14, rsi_period):
            rsi_indicator = ta.momentum.RSIIndicator(df['Close'], window=rsi_period)
            rsi = rsi_indicator.rsi().fillna(method='bfill')
            df['RSI'] = rsi
            unreliable_mask |= rsi_indicator.rsi().isna()
        else:
            df['RSI'] = 50

        # On Balance Volume (OBV)
        if min_length >= 1:
            obv_indicator = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume'])
            df['OBV'] = obv_indicator.on_balance_volume()
        else:
            df['OBV'] = 0

        # Fill any remaining NaN values with 0 or forward fill
        numeric_columns = [col for col in df.columns if col.startswith('EMA_') or col in ['MACD', 'MACD_signal', 'MACD_hist', 'Force_Index', 'AD_Line', 'ATR', 'ADX', 'DI_plus', 'DI_minus', 'Stoch_K', 'Stoch_D', 'RSI', 'OBV']]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].ffill().fillna(0)

        # Add unreliable flag to DataFrame for UI warning
        df['unreliable_indicators'] = unreliable_mask.values
        
        return df
        
    except Exception as e:
        # Return dataframe with zero-filled indicator columns
        for period in ema_periods:
            df[f'EMA_{period}'] = df['Close']
        df['MACD'] = 0
        df['MACD_signal'] = 0
        df['MACD_hist'] = 0
        df['Force_Index'] = 0
        df['AD_Line'] = 0
        df['ADX'] = 25  # Default neutral value
        df['DI_plus'] = 25
        df['DI_minus'] = 25
        df['ATR'] = (df['High'] - df['Low']) * 0.1  # Simple ATR estimate
        return df
    
def update_lower_chart_settings(chart_type):
    """Update the settings panel based on the selected lower chart type"""
    if chart_type == 'macd':
        return [
            html.H6("MACD Settings", style={'color': '#00d4aa'}),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Fast Period:", style={'color': '#fff', 'fontSize': '12px'}),
                    dbc.Input(id='macd-fast', type='number', value=12, min=1, max=50, size='sm')
                ], width=4),
                dbc.Col([
                    dbc.Label("Slow Period:", style={'color': '#fff', 'fontSize': '12px'}),
                    dbc.Input(id='macd-slow', type='number', value=26, min=1, max=100, size='sm')
                ], width=4),
                dbc.Col([
                    dbc.Label("Signal:", style={'color': '#fff', 'fontSize': '12px'}),
                    dbc.Input(id='macd-signal', type='number', value=9, min=1, max=50, size='sm')
                ], width=4)
            ], className="mb-2")
        ]
    elif chart_type == 'force':
        return [
            html.H6("Force Index Settings", style={'color': '#00d4aa'}),
            dbc.Label("Smoothing Period:", style={'color': '#fff', 'fontSize': '12px'}),
            dbc.Input(id='force-smoothing', type='number', value=2, min=1, max=20, className="mb-3")
        ]
    elif chart_type == 'ad':
        return [
            html.H6("A/D Line Settings", style={'color': '#00d4aa'}),
            html.P("The Accumulation/Distribution Line uses price and volume data with no additional parameters.", 
                  style={'color': '#ccc', 'fontSize': '12px'})
        ]
    elif chart_type == 'adx':
        return [
            html.H6("ADX/DI Settings", style={'color': '#00d4aa'}),
            dbc.Label("ADX Period:", style={'color': '#fff', 'fontSize': '12px'}),
            dbc.Input(id='adx-period', type='number', value=13, min=1, max=50, className="mb-3"),
            dbc.Label("Display:", style={'color': '#fff', 'fontSize': '12px'}),
            dbc.Checklist(
                id='adx-components',
                options=[
                    {'label': 'ADX Line', 'value': 'adx'},
                    {'label': 'DI+ Line', 'value': 'di_plus'},
                    {'label': 'DI- Line', 'value': 'di_minus'}
                ],
                value=['adx', 'di_plus', 'di_minus'],
                inline=True,
                style={'color': '#fff'}
            )
        ]
    elif chart_type == 'stochastic':
        return [
            html.H6("Slow Stochastic Settings", style={'color': '#00d4aa'}),
            dbc.Label("Stochastic Period:", style={'color': '#fff', 'fontSize': '12px'}),
            dbc.Input(id='stochastic-period', type='number', value=5, min=1, max=50, className="mb-3"),
            html.P("Displays %K (green) and %D (red) oscillators with overbought (80%) and oversold (20%) levels.", 
                  style={'color': '#ccc', 'fontSize': '12px'})
        ]
    elif chart_type == 'rsi':
        return [
            html.H6("RSI Settings", style={'color': '#00d4aa'}),
            dbc.Label("RSI Period:", style={'color': '#fff', 'fontSize': '12px'}),
            dbc.Input(id='rsi-period', type='number', value=13, min=1, max=50, className="mb-3"),
            html.P("Displays RSI oscillator with overbought (70) and oversold (30) levels. Areas below 30 and above 70 are highlighted.", 
                  style={'color': '#ccc', 'fontSize': '12px'})
        ]
    elif chart_type == 'obv':
        return [
            html.H6("OBV Settings", style={'color': '#00d4aa'}),
            html.P("On Balance Volume (OBV) uses volume flow to predict changes in stock price. No additional parameters required.", 
                  style={'color': '#ccc', 'fontSize': '12px'})
        ]
    else:  # Volume
        return [
            html.H6("Volume Settings", style={'color': '#00d4aa'}),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Compare with another stock or ETF:", style={'color': '#fff', 'fontSize': '12px'}),
                    dbc.Select(
                        id='volume-comparison-select',
                        options=[
                            {'label': 'None', 'value': 'none'},
                            {'label': 'SPY - S&P 500 ETF', 'value': 'SPY'},
                            {'label': 'QQQ - Nasdaq ETF', 'value': 'QQQ'},
                            {'label': 'IWM - Russell 2000 ETF', 'value': 'IWM'},
                            {'label': 'DIA - Dow Jones ETF', 'value': 'DIA'}
                        ],
                        value='none',
                        style={'backgroundColor': '#2b3035', 'color': '#fff'}
                    )
                ], width=12)
            ], className="mb-2")
        ]
    
def update_symbol(n_clicks, symbol):
    """Update the current symbol when search button is clicked with the value from the input"""
    if symbol:
        # Strip whitespace and convert to uppercase for consistency
        symbol = symbol.upper().strip()
        # Replace any potential special characters that shouldn't be in a ticker
        symbol = ''.join(c for c in symbol if c.isalnum() or c in ['-', '.'])
        return symbol
    return 'SPY'

def format_symbol_input(value):
    """Format the symbol input as the user types"""
    if value:
        # Convert to uppercase
        value = value.upper().strip()
        # Only allow alphanumeric, dash, and dot characters
        value = ''.join(c for c in value if c.isalnum() or c in ['-', '.'])
    return value

def update_macd_stores(fast, slow, signal):
    """Update store values when MACD parameters change in UI"""
    return fast or 12, slow or 26, signal or 9

def update_force_store(smoothing):
    """Update store value when Force Index parameter changes in UI"""
    return smoothing or 2

def update_adx_stores(period, components):
    """Update store values when ADX parameters change in UI"""
    adx_period = period or 13
    components = components or ['adx', 'di_plus', 'di_minus']
    return adx_period, components

def update_stochastic_store(period):
    """Update store value when Stochastic parameter changes in UI"""
    return period or 5

def update_rsi_store(period):
    """Update store value when RSI parameter changes in UI"""
    return period or 13

def get_comparison_volume(comparison_symbol, timeframe, start_date, end_date):
    """Fetch volume data for comparison stock"""
    if comparison_symbol == 'none':
        return None
        
    try:
        ticker = yf.Ticker(comparison_symbol)
        
        # Use a slightly extended period to ensure we get enough data
        if isinstance(start_date, pd.Timestamp):
            start_str = (start_date - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
        else:
            start_str = (pd.Timestamp(start_date) - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
            
        if isinstance(end_date, pd.Timestamp):
            end_str = (end_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            end_str = (pd.Timestamp(end_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            
        # Fetch the data
        comp_data = ticker.history(start=start_str, end=end_str, interval='1d')
        
        if comp_data.empty:
            return None
            
        comp_data.reset_index(inplace=True)
        
        # Handle Date/Datetime column
        if 'Date' in comp_data.columns:
            comp_data['Date'] = pd.to_datetime(comp_data['Date']).dt.tz_localize(None)
        elif 'Datetime' in comp_data.columns:
            comp_data = comp_data.rename(columns={'Datetime': 'Date'})
            comp_data['Date'] = pd.to_datetime(comp_data['Date']).dt.tz_localize(None)
            
        # Return only Date and Volume columns
        return comp_data[['Date', 'Volume']].copy()
    except Exception as e:
        return None

def update_data(n, symbol, timeframe, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, adx_period, stoch_period, rsi_period, frequency=None):
    """Update stock data periodically or when symbol/timeframe/parameters change"""
    error_msg = []
    error_class = "alert alert-warning fade show d-none"  # Hidden by default
    
    try:
        symbol = symbol or 'SPY'
        timeframe = timeframe or '1mo'
        ema_periods = ema_periods or [13, 26]
        # Use default values if the components don't exist in the layout
        macd_fast = 12 if macd_fast is None else macd_fast
        macd_slow = 26 if macd_slow is None else macd_slow
        macd_signal = 9 if macd_signal is None else macd_signal
        force_smoothing = 2 if force_smoothing is None else force_smoothing
        adx_period = 13 if adx_period is None else adx_period
        stoch_period = 5 if stoch_period is None else stoch_period
        rsi_period = 13 if rsi_period is None else rsi_period
        
        # Track if we're using sample data
        using_sample_data = False
        
        # Get extended data for proper indicator calculation
        try:
            # Check cache first
            cached_result = _get_cached_data(symbol, timeframe)
            if cached_result is not None:
                full_data, start_date, end_date, is_minute_data = cached_result
            else:
                full_data, start_date, end_date, is_minute_data = get_stock_data(symbol, timeframe, frequency)
                _cache_data(symbol, timeframe, full_data, start_date, end_date, is_minute_data)  # Cache the result
        except Exception as data_error:
            full_data, start_date, end_date, is_minute_data = get_stock_data("SPY", timeframe, frequency)  # Fall back to SPY
            error_msg = [
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Could not fetch data for symbol '{symbol}'. Using sample data instead. ",
                html.Span("Please check if the symbol is valid and try again.", className="small")
            ]
            error_class = "alert alert-warning fade show"
            using_sample_data = True
        
        # Check if we have empty data for 1D or yesterday view (market closed) - this is normal, don't show errors
        if timeframe in ["1d", "yesterday"] and len(full_data) == 0:
            return [], [], "alert alert-warning fade show d-none"  # Hidden error class
        
        # Calculate indicators on full dataset (use fast mode for quicker ticker switching)
        fast_mode = len(full_data) > 1000  # Use fast mode for large datasets to speed up calculations
        
        # For intraday data (1d and yesterday), we need to separate display data from indicator calculation data
        # This ensures all indicators have sufficient historical data to calculate properly from market open
        if timeframe in ["1d", "yesterday"]:
            # Calculate indicators using the extended historical dataset (multiple days)
            df_with_indicators = calculate_indicators(full_data, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, adx_period, stoch_period, rsi_period, fast_mode)
            # After calculation, filter to just today or yesterday for display
            display_date = None
            now_cest = datetime.now()
            if timeframe == "1d":
                display_date = now_cest.date()
            else:
                display_date = now_cest.date() - pd.Timedelta(days=1)
                while pd.Timestamp(display_date).weekday() > 4:
                    display_date = (pd.Timestamp(display_date) - pd.Timedelta(days=1)).date()
            df_final = df_with_indicators[pd.to_datetime(df_with_indicators['Date']).dt.date == display_date].copy()
        else:
            # For non-intraday views, just calculate normally
            df_with_indicators = calculate_indicators(full_data, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, adx_period, stoch_period, rsi_period, fast_mode)
            df_final = df_with_indicators[df_with_indicators['Date'] >= start_date].copy()
        
        # Ensure both the Date column and start_date have the same timezone status (both naive)
        # Make sure the Date column is timezone-naive for comparison
        df_with_indicators['Date'] = pd.to_datetime(df_with_indicators['Date']).dt.tz_localize(None)
        
        # Convert start_date to a timezone-naive datetime if it has timezone info
        if hasattr(start_date, 'tz') and start_date.tz is not None:
            start_date = start_date.tz_localize(None)
        
        # Now trim to the requested period - for intraday, this will show only today's data
        # but the indicators will be calculated using the extended historical data
        df_final = df_with_indicators[df_with_indicators['Date'] >= start_date].copy()
        
        if not using_sample_data and (len(df_final) < 5):
            # For 1D or yesterday view, if we have no data it's likely because market is closed - don't show error
            if timeframe in ["1d", "yesterday"]:
                return [], [], "alert alert-warning fade show d-none"  # Hidden error class
            
            full_data, start_date, end_date, is_minute_data = get_stock_data("SPY", timeframe, frequency)
            df_with_indicators = calculate_indicators(full_data, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, fast_mode=True)
            
            # Ensure timezone-naive comparison
            df_with_indicators['Date'] = pd.to_datetime(df_with_indicators['Date']).dt.tz_localize(None)
            if hasattr(start_date, 'tz') and start_date.tz is not None:
                start_date = start_date.tz_localize(None)
                
            df_final = df_with_indicators[df_with_indicators['Date'] >= start_date].copy()
            error_msg = [
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Insufficient data available for symbol '{symbol}'. Using sample data instead. ",
                html.Span("The symbol may be too new, delisted, or incorrectly entered.", className="small")
            ]
            error_class = "alert alert-warning fade show"
            
        return df_final.to_dict('records'), error_msg, error_class
        
    except Exception as e:
        # Return error state instead of sample data
        error_msg = [
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"An error occurred: {str(e)}. Please check your internet connection and try again."
        ]
        error_class = "alert alert-danger fade show"
        return [], error_msg, error_class

def update_main_chart(data, symbol, chart_type, show_ema, ema_periods, atr_bands, timeframe=None, use_impulse_system=False):
    """Update the main chart with different visualization types and indicators
    Returns: (figure, is_in_value_zone)"""
    try:
        if not data:
            return go.Figure(), False
        
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        symbol = symbol or 'SPY'
        chart_type = chart_type or 'candlestick'
        show_ema = show_ema or []
        ema_periods = ema_periods or [13, 26]
        atr_bands = atr_bands or []
        
        # Process Impulse System if enabled (for candlestick charts only)
        impulse_df = None
        if use_impulse_system and chart_type == 'candlestick' and len(df) > 1:
            # Import here to avoid circular imports
            from impulse_functions import calculate_impulse_system
            impulse_df = calculate_impulse_system(df, ema_period=ema_periods[0] if ema_periods else 13)
        
        # Detect if data contains intraday (minute) timepoints
        # First check if timeframe is explicitly intraday
        is_intraday = timeframe in ['1d', 'yesterday'] 
        
        # If timeframe parameter isn't available, fall back to data frequency detection
        if not is_intraday and len(df) > 1:
            # Check if time difference between points is less than a day
            time_diff = (df['Date'].iloc[1] - df['Date'].iloc[0]).total_seconds()
            is_intraday = time_diff < 24*60*60
            
            # Additional check: if data has more than 30 points in a single day, it's likely intraday
            if len(df) > 30:
                first_day = df['Date'].iloc[0].date()
                last_day = df['Date'].iloc[-1].date()
                if first_day == last_day:
                    is_intraday = True
        
        # Create figure with dark theme
        fig = go.Figure()
        
        # Add different chart types based on selection
        if chart_type == 'candlestick':
            # Standard candlestick (with or without Impulse System)
            if use_impulse_system and impulse_df is not None:
                # Use impulse system coloring (groupby date and create separate traces)
                from impulse_functions import get_impulse_colors
                
                # Create a separate trace for each impulse color
                for color in ['green', 'red', 'blue']:
                    # Filter data for this color
                    color_data = impulse_df[impulse_df['impulse_color'] == color]
                    
                    # Skip if no data for this color
                    if len(color_data) == 0:
                        continue
                    
                    # Get appropriate colors for this impulse color
                    colors = get_impulse_colors(color)
                    
                    # Add trace for this color group
                    fig.add_trace(
                        go.Candlestick(
                            x=color_data['Date'],
                            open=color_data['Open'],
                            high=color_data['High'],
                            low=color_data['Low'],
                            close=color_data['Close'],
                            name=f"{symbol} ({color})",
                            increasing_line_color=colors['increasing_line_color'],
                            decreasing_line_color=colors['decreasing_line_color'],
                            increasing_fillcolor=colors['increasing_fillcolor'],
                            decreasing_fillcolor=colors['decreasing_fillcolor'],
                            line=dict(width=1),
                            opacity=0.9
                        )
                    )
            else:
                # Standard candlestick without impulse system
                fig.add_trace(
                    go.Candlestick(
                        x=df['Date'],
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name=symbol,
                        increasing_line_color='#00ff88',  # Green for up candles
                        decreasing_line_color='#ff4444',  # Red for down candles
                        increasing_fillcolor='rgba(0, 255, 136, 0.4)',
                        decreasing_fillcolor='rgba(255, 68, 68, 0.4)',
                        line=dict(width=1),
                        opacity=0.9
                    )
                )
        
        elif chart_type == 'japanese':
            # Japanese style candlesticks
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=symbol,
                    increasing_line_color='#00d4aa',  # Teal for up candles
                    decreasing_line_color='#ff6b6b',  # Coral red for down candles
                    increasing_fillcolor='rgba(0, 212, 170, 0.5)',
                    decreasing_fillcolor='rgba(255, 107, 107, 0.5)',
                    line=dict(width=1.5)
                )
            )
        
        elif chart_type == 'mountain':
            # Enhanced mountain chart with custom coloring
            
            # Calculate first price for scaling reference
            first_price = df['Close'].iloc[0] if len(df) > 0 else 0
            
            # Set colors for mountain chart
            line_color = '#00d4aa'  # Teal line
            fill_color = 'rgba(0, 212, 170, 0.2)'  # Semi-transparent teal
            
            # Add the main price trace with fill to zero (standard area chart)
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Close'],
                    mode='lines',
                    name=f'{symbol} Close',
                    line=dict(color=line_color, width=2),
                    fill='tozeroy',  # Standard fill to zero/bottom of chart
                    fillcolor=fill_color,
                    hovertemplate='%{x}<br>Price: $%{y:.2f}<br>Change: %{customdata:.2f}%<extra></extra>',
                    customdata=[(price/first_price - 1) * 100 for price in df['Close']]  # Show % change from first value
                )
            )
        
        # Add EMA indicators if enabled (remove 'not is_intraday' condition)
        if 'show' in show_ema:
            colors = ['#3366cc', '#ff9900', '#9900ff', '#ff6b6b', '#4ecdc4', '#45b7d1']
            
            # First, add the Value Zone fill if we have exactly 2 EMAs
            if len(ema_periods) >= 2:
                ema1_col = f'EMA_{ema_periods[0]}'
                ema2_col = f'EMA_{ema_periods[1]}'
                
                if ema1_col in df.columns and ema2_col in df.columns:
                    # Add the first EMA line (will be used as the base for the fill)
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df[ema1_col],
                            mode='lines',
                            name=f'EMA {ema_periods[0]}',
                            line=dict(color=colors[0], width=2),
                            showlegend=True
                        )
                    )
                    
                    # Add the second EMA line with fill to the first EMA (creates Value Zone)
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df[ema2_col],
                            mode='lines',
                            name=f'EMA {ema_periods[1]}',
                            line=dict(color=colors[1], width=2),
                            fill='tonexty',  # Fill to the previous trace (first EMA)
                            fillcolor='rgba(102, 178, 255, 0.15)',  # Light blue with 15% opacity
                            showlegend=True
                        )
                    )
                    
                    # Add remaining EMAs (if any) without fill
                    for i in range(2, len(ema_periods)):
                        period = ema_periods[i]
                        ema_col = f'EMA_{period}'
                        if ema_col in df.columns:
                            color = colors[i % len(colors)]
                            fig.add_trace(
                                go.Scatter(
                                    x=df['Date'],
                                    y=df[ema_col],
                                    mode='lines',
                                    name=f'EMA {period}',
                                    line=dict(color=color, width=2)
                                )
                            )
                else:
                    # Fallback: plot EMAs normally if columns don't exist
                    for i, period in enumerate(ema_periods):
                        ema_col = f'EMA_{period}'
                        if ema_col in df.columns:
                            color = colors[i % len(colors)]
                            fig.add_trace(
                                go.Scatter(
                                    x=df['Date'],
                                    y=df[ema_col],
                                    mode='lines',
                                    name=f'EMA {period}',
                                    line=dict(color=color, width=2)
                                )
                            )
            else:
                # If less than 2 EMAs, plot them normally
                for i, period in enumerate(ema_periods):
                    ema_col = f'EMA_{period}'
                    if ema_col in df.columns:
                        color = colors[i % len(colors)]
                        fig.add_trace(
                            go.Scatter(
                                x=df['Date'],
                                y=df[ema_col],
                                mode='lines',
                                name=f'EMA {period}',
                                line=dict(color=color, width=2)
                            )
                        )
        
        # Add ATR bands if selected
        if atr_bands and 'ATR' in df.columns:
            for band_str in atr_bands:
                try:
                    band_multiplier = float(band_str)
                    upper_band = df['Close'] + (df['ATR'] * band_multiplier)
                    lower_band = df['Close'] - (df['ATR'] * band_multiplier)
                    
                    # Upper band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=upper_band,
                            mode='lines',
                            name=f'+{band_multiplier} ATR',
                            line=dict(color='rgba(255, 255, 255, 0.5)', width=1, dash='dot')
                        )
                    )
                    
                    # Lower band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=lower_band,
                            mode='lines',
                            name=f'-{band_multiplier} ATR',
                            line=dict(color='rgba(255, 255, 255, 0.5)', width=1, dash='dot')
                        )
                    )
                except Exception as e:
                    pass

        # Previous code for adding a horizontal close line was here
        # This has been replaced with a better implementation later in the function
        # that uses monthly data to get the official previous close price

        # Calculate dynamic title with price and percentage changes
        title_text = symbol
        title_color = '#00d4aa'  # Default color
        
        if len(df) > 0:
            current_price = df['Close'].iloc[-1]
            
            # For percentage calculation, use the first price of the dataset as reference
            if len(df) > 1:
                if is_intraday:
                    # For 1D view, compare with opening price (approximates previous close)
                    reference_price = df['Open'].iloc[0]
                else:
                    # For other timeframes, compare with first price in the dataset
                    reference_price = df['Close'].iloc[0]
                
                price_change = current_price - reference_price
                percent_change = (price_change / reference_price) * 100
                
                # Determine arrow and color based on percentage change
                if percent_change > 0:
                    arrow = "↗"
                    title_color = '#00ff88'  # Green for positive percentage
                elif percent_change < 0:
                    arrow = "↘"
                    title_color = '#ff4444'  # Red for negative percentage
                else:
                    arrow = "→"
                    title_color = '#ffaa00'  # Yellow/orange for neutral
                
                # Get current time in HH:MM:SS format
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # Format title: SYMBOL - PRICE$ (arrow change, %change)
                main_title = f"{symbol} - ${current_price:.2f} ({arrow} ${abs(price_change):.2f}, {percent_change:+.2f}%)"
                # Store the current time and price info for status indicator
                symbol_info = {
                    'symbol': symbol,
                    'price': current_price,
                    'change': price_change,
                    'percent': percent_change,
                    'time': current_time,
                    'color': title_color
                }
            else:
                # Single data point case
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                main_title = f"{symbol} - ${current_price:.2f}"
                # Store minimal info for status indicator
                symbol_info = {
                    'symbol': symbol,
                    'price': current_price,
                    'time': current_time,
                    'color': title_color
                }

        # Update layout for dark theme with bold title
        layout_settings = {
            'title': {
                'text': main_title,
                'font': {
                    'color': title_color,
                    'size': 24,
                    'family': 'Inter, sans-serif',
                    'weight': 'bold'
                },
                'y': 0.95,
                'x': 0.05,
                'xanchor': 'left',
                'yanchor': 'top'
            },
            'height': 430, # Adjusted to match the 55vh in the layout
            'showlegend': True,
            'xaxis_rangeslider_visible': False,
            'template': 'plotly_dark',
            'paper_bgcolor': '#000000',
            'plot_bgcolor': '#000000',
            'font': dict(color='#ffffff'),
            'margin': dict(l=40, r=40, t=70, b=20) # Increased top margin for subtitle
        }
        
        # For all chart types, calculate the appropriate y-axis range
        if len(df) > 0:
            # Get the min and max values from the data for consistent y-axis across chart types
            if 'Low' in df.columns and 'High' in df.columns:
                # For candlestick data, use full price range (High/Low)
                y_min = df['Low'].min()
                y_max = df['High'].max()
            else:
                # For line data only, use Close prices
                y_min = df['Close'].min()
                y_max = df['Close'].max()
            
            # Add a buffer (1%) for better visualization
            y_range_buffer = (y_max - y_min) * 0.05
            y_min = y_min - y_range_buffer
            y_max = y_max + y_range_buffer
            
            # Set y-axis range explicitly
            layout_settings['yaxis'] = dict(
                range=[y_min, y_max],
                autorange=False,
                fixedrange=False  # Allow zooming on y-axis
            )
            
        fig.update_layout(**layout_settings)
        
        # Update axes colors and explicitly exclude weekends
        fig.update_xaxes(
            gridcolor='#444', 
            zerolinecolor='#444',
            rangebreaks=[
                # Don't show weekends (Saturday=6, Sunday=0)
                dict(bounds=["sat", "mon"])
            ]
        )
        
        # Configure y-axis appearance
        yaxis_config = {
            'gridcolor': '#444', 
            'zerolinecolor': '#444'
        }
        
        # Don't override our explicit y-axis settings from layout_settings
        # Just apply styling configs here
        fig.update_yaxes(**yaxis_config)
        
        # Check Value Zone status for EMAs
        is_in_value_zone = False
        if 'show' in show_ema and not is_intraday and len(ema_periods) >= 2:
            is_in_value_zone = check_value_zone_status(df, ema_periods)
        
        # Return the figure, value zone status, and symbol info for status indicator
        return fig, is_in_value_zone, symbol_info if 'symbol_info' in locals() else None

    except Exception as e:
        pass
        # Return a simple error message chart
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading chart: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#000000',
            plot_bgcolor='#000000'
        )
        return fig, False, None

def update_consolidated_chart(data, symbol, chart_type, adx_components, volume_comparison=None):
    """Update the consolidated chart below main chart"""
    if not data:
        return go.Figure()
    
    # Ensure we have a valid volume comparison value
    volume_comparison = volume_comparison or 'none'
    
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    
    fig = go.Figure()
    
    if chart_type == 'volume':
        # Get min and max dates for the main data
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        
        # If comparison is selected, fetch and prepare comparison data
        comparison_data = None
        if volume_comparison != 'none':
            comparison_data = get_comparison_volume(volume_comparison, None, min_date, max_date)
        
        if comparison_data is not None:
            # Calculate average volumes for comparison
            avg_volume_main = df['Volume'].mean()
            avg_volume_comp = comparison_data['Volume'].mean()
            
            # Determine which is more liquid (higher volume)
            main_is_higher = avg_volume_main > avg_volume_comp
            
            # Set colors based on liquidity
            main_color = 'rgba(0, 212, 170, 0.6)' if main_is_higher else 'rgba(255, 68, 68, 0.6)'
            comp_color = 'rgba(255, 68, 68, 0.6)' if main_is_higher else 'rgba(0, 212, 170, 0.6)'
            
            # Scale volumes for better comparison (normalize to percentage of their average)
            df['Volume_Scaled'] = df['Volume'] / avg_volume_main
            comparison_data['Volume_Scaled'] = comparison_data['Volume'] / avg_volume_comp
            
            # Add main volume bars
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume_Scaled'],
                    name=f'{symbol} Volume',
                    marker_color=main_color,
                    opacity=0.9
                )
            )
            
            # Add comparison volume bars
            fig.add_trace(
                go.Bar(
                    x=comparison_data['Date'],
                    y=comparison_data['Volume_Scaled'],
                    name=f'{volume_comparison} Volume',
                    marker_color=comp_color,
                    opacity=0.7
                )
            )
            
            # Update y-axis title to reflect scaling
            title = f'{symbol} vs {volume_comparison} Volume (Normalized)'
            yaxis_title = 'Normalized Volume'
        else:
            # Regular single-stock volume chart
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume'],
                    name='Volume',
                    marker_color='rgba(0, 212, 170, 0.6)'
                )
            )
            title = f'{symbol} Trading Volume'
            yaxis_title = 'Volume'
        
    elif chart_type == 'macd':
        # MACD chart with histogram
        if 'MACD_hist' in df.columns:
            colors = ['#00ff88' if (val is not None and val >= 0) else '#ff4444' for val in df['MACD_hist']]
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['MACD_hist'],
                    name='MACD Histogram',
                    marker_color=colors,
                    opacity=0.7
                )
            )
            
        if 'MACD' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['MACD'],
                    mode='lines',
                    name='MACD',
                    line=dict(color='#3366cc', width=2)
                )
            )
            
        if 'MACD_signal' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['MACD_signal'],
                    mode='lines',
                    name='MACD Signal',
                    line=dict(color='#ff4444', width=2)
                )
            )
        title = f'{symbol} MACD'
        yaxis_title = 'MACD'
        
    elif chart_type == 'force':
        # Force Index as histogram
        if 'Force_Index' in df.columns:
            colors = ['#00ff88' if (val is not None and val >= 0) else '#ff4444' for val in df['Force_Index']]
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Force_Index'],
                    name='Force Index',
                    marker_color=colors,
                    opacity=0.8
                )
            )
        title = f'{symbol} Force Index'
        yaxis_title = 'Force Index'
        
    elif chart_type == 'ad':
        # A/D Line
        if 'AD_Line' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['AD_Line'],
                    mode='lines',
                    name='A/D Line',
                    line=dict(color='#ff9900', width=2)
                )
            )
        title = f'{symbol} Accumulation/Distribution Line'
        yaxis_title = 'A/D Line'
    
    elif chart_type == 'adx':
        # ADX, DI+, and DI-
        adx_components = adx_components or ['adx', 'di_plus', 'di_minus']  # Default to show all
        
        # ADX Line (purple)
        if 'ADX' in df.columns and ('adx' in adx_components or not adx_components):
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['ADX'],
                    mode='lines',
                    name='ADX',
                    line=dict(color='#9c27b0', width=2)  # Purple color
                )
            )
        
        # DI+ (green)
        if 'DI_plus' in df.columns and ('di_plus' in adx_components or not adx_components):
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['DI_plus'],
                    mode='lines',
                    name='DI+',
                    line=dict(color='#00ff88', width=2)  # Green color
                )
            )
        
        # DI- (red)
        if 'DI_minus' in df.columns and ('di_minus' in adx_components or not adx_components):
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['DI_minus'],
                    mode='lines',
                    name='DI-',
                    line=dict(color='#ff4444', width=2)  # Red color
                )
            )
        
        # Add reference line at ADX=25 (strong trend threshold)
        fig.add_hline(
            y=25,
            line_dash="dot",
            line_color="rgba(255, 255, 255, 0.5)",
            row=2, col=1,
            annotation_text="Strong Trend (25)",
            annotation_position="top right",
            annotation_font_size=10
        )
        
        title = f'{symbol} ADX/DMI'
        yaxis_title = 'Value'
    
    else:
        title = f'{symbol} Indicator'
        yaxis_title = 'Value'
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title=yaxis_title,
        height=330,  # Increased by 50% to match the 45vh in the layout
        showlegend=True,
        template='plotly_dark',
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        font=dict(color='#ffffff'),
        title_font=dict(color='#00d4aa'),
        margin=dict(l=40, r=40, t=40, b=20) # Compact margins
    )
    
    # Update axes colors and explicitly exclude weekends
    fig.update_xaxes(
        gridcolor='#444', 
        zerolinecolor='#444',
        rangebreaks=[
            # Don't show weekends (Saturday=6, Sunday=0)
            dict(bounds=["sat", "mon"])
        ]
    )
    fig.update_yaxes(gridcolor='#444', zerolinecolor='#444')
    
    return fig

def update_combined_chart(data, symbol, chart_type, show_ema, ema_periods, atr_bands, lower_chart_type, adx_components, volume_comparison=None, relayout_data=None, timeframe=None, use_impulse_system=False, bollinger_bands=None, autoenvelope=None):
    """Update a combined chart with main price chart on top and indicator chart below"""
    try:
        if not data:
            return go.Figure(), {'display': 'none'}, 'd-block'
        
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        symbol = symbol or 'SPY'
        chart_type = chart_type or 'candlestick'
        show_ema = show_ema or []
        ema_periods = ema_periods or [13, 26]
        atr_bands = atr_bands or []
        lower_chart_type = lower_chart_type or 'volume'
        bollinger_bands = bollinger_bands or {'show': False, 'period': 26, 'stddev': 2}
        autoenvelope = autoenvelope or {'show': False, 'period': 26, 'percent': 6}
        
        # Handle empty data (e.g., when market is closed for 1D view)
        if df.empty:
            fig = go.Figure()
            
            # Add message for empty chart
            if lower_chart_type == 'volume' and len([col for col in df.columns if col.startswith('1d') or col == 'Date']) == 0:
                message = "US Market is currently closed.<br>1D view will show real-time data when market opens (9:30 AM - 4:00 PM ET)."
            else:
                message = f"No data available for {symbol}"
            
            fig.add_annotation(
                text=message,
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color="#00d4aa"),
                bgcolor="rgba(0, 0, 0, 0.8)",
                bordercolor="#444",
                borderwidth=1
            )
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='#000000',
                plot_bgcolor='#000000',
                height=800,
                margin=dict(l=40, r=40, t=60, b=40),
                title=f'{symbol} - Market Closed',
                title_font=dict(color='#ffaa00', size=18)  # Orange for market closed
            )
            
            return fig, {'display': 'none'}, 'd-block'
        
        # Check if we are using 1D timeframe (based on data frequency)
        # Determine if this is intraday data using both timeframe parameter and data frequency
        is_intraday_timeframe = timeframe in ['1d', 'yesterday']
        
        # Also check data frequency as a backup method
        is_intraday_data = False
        if len(df) > 2:
            time_diff = (df['Date'].iloc[1] - df['Date'].iloc[0]).total_seconds()
            is_intraday_data = time_diff < 3600  # Less than 1 hour between points
            
        # Use either method to determine if it's intraday
        is_intraday = is_intraday_timeframe or is_intraday_data
        
        # Create subplots with shared x-axis
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],  # 70% for main chart, 30% for lower chart
            subplot_titles=(None, None),  # Remove titles for cleaner look
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # === MAIN CHART (Row 1) ===
        if chart_type in ['candlestick', 'japanese']:
            # Candlestick chart
            if use_impulse_system and chart_type == 'candlestick':
                # Use Impulse System for coloring (imported at function level to avoid circular imports)
                from impulse_functions import calculate_impulse_system, get_impulse_colors
                
                # Add Impulse System coloring to the dataframe
                impulse_df = calculate_impulse_system(df, ema_period=ema_periods[0] if ema_periods else 13)
                
                # Create a separate trace for each impulse color
                for color in ['green', 'red', 'blue']:
                    # Filter data for this color
                    color_data = impulse_df[impulse_df['impulse_color'] == color]
                    
                    # Skip if no data for this color
                    if len(color_data) == 0:
                        continue
                        
                    # Get appropriate colors for this impulse color
                    colors = get_impulse_colors(color)
                    
                    # Add trace for this color group
                    fig.add_trace(
                        go.Candlestick(
                            x=color_data['Date'],
                            open=color_data['Open'],
                            high=color_data['High'],
                            low=color_data['Low'],
                            close=color_data['Close'],
                            name=f"{symbol} ({color})",
                            increasing_line_color=colors['increasing_line_color'],
                            decreasing_line_color=colors['decreasing_line_color'],
                            increasing_fillcolor=colors['increasing_fillcolor'],
                            decreasing_fillcolor=colors['decreasing_fillcolor'],
                            line=dict(width=1),
                            opacity=0.9
                        ),
                        row=1, col=1
                    )
            else:
                # Standard candlestick without impulse system
                fig.add_trace(
                    go.Candlestick(
                        x=df['Date'],
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name=symbol,
                        increasing_line_color='#00ff88',
                        decreasing_line_color='#ff4444',
                        increasing_fillcolor='#00ff88',
                        decreasing_fillcolor='#ff4444'
                    ),
                    row=1, col=1
                )
        elif chart_type == 'mountain':
            # Mountain (area) chart
            if len(df) >= 2:
                price_start = df['Close'].iloc[0]
                price_end = df['Close'].iloc[-1]
                is_uptrend = price_end >= price_start
                
                line_color = '#00d4aa'  # Teal line
                fill_color = 'rgba(0, 212, 170, 0.2)'  # Semi-transparent teal
            else:
                line_color = '#00d4aa'
                fill_color = 'rgba(0, 212, 170, 0.3)'
            
            first_price = df['Close'].iloc[0]
            
            # For subplots, we need to specify the fill properly
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Close'],
                    mode='lines',
                    name=f'{symbol} Close',
                    line=dict(color=line_color, width=2),
                    fill='tonexty',  # Fill to next y (which will be the baseline we add)
                    fillcolor=fill_color,
                    hovertemplate='%{x}<br>Price: $%{y:.2f}<br>Change: %{customdata:.2f}%<extra></extra>',
                    customdata=[(price/first_price - 1) * 100 for price in df['Close']]  # Show % change from first value
                ),
                row=1, col=1
            )
            
            # Add a baseline trace for proper fill (invisible)
            y_min_baseline = df['Close'].min() * 0.95  # Set baseline slightly below minimum
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=[y_min_baseline] * len(df),
                    mode='lines',
                    line=dict(color='rgba(0,0,0,0)', width=0),  # Invisible line
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=1
            )
        
        # Add EMA indicators if enabled (remove 'not is_intraday' condition)
        if 'show' in show_ema:
            colors = ['#3366cc', '#ff9900', '#9900ff', '#ff6b6b', '#4ecdc4', '#45b7d1']
            
            # First, add the Value Zone fill if we have exactly 2 EMAs
            if len(ema_periods) >= 2:
                ema1_col = f'EMA_{ema_periods[0]}'
                ema2_col = f'EMA_{ema_periods[1]}'
                
                if ema1_col in df.columns and ema2_col in df.columns:
                    # Add the first EMA line (will be used as the base for the fill)
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df[ema1_col],
                            mode='lines',
                            name=f'EMA {ema_periods[0]}',
                            line=dict(color=colors[0], width=1.5),
                            opacity=0.8,
                            showlegend=True
                        ),
                        row=1, col=1
                    )
                    
                    # Add the second EMA line with fill to the first EMA (creates Value Zone)
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df[ema2_col],
                            mode='lines',
                            name=f'EMA {ema_periods[1]}',
                            line=dict(color=colors[1], width=1.5),
                            fill='tonexty',  # Fill to the previous trace (first EMA)
                            fillcolor='rgba(102, 178, 255, 0.15)',  # Light blue with 15% opacity
                            opacity=0.8,
                            showlegend=True
                        ),
                        row=1, col=1
                    )
                    
                    # Add remaining EMAs (if any) without fill
                    for i in range(2, len(ema_periods)):
                        period = ema_periods[i]
                        ema_col = f'EMA_{period}'
                        if ema_col in df.columns:
                            color = colors[i % len(colors)]
                            fig.add_trace(
                                go.Scatter(
                                    x=df['Date'],
                                    y=df[ema_col],
                                    mode='lines',
                                    name=f'EMA {period}',
                                    line=dict(color=color, width=1.5),
                                    opacity=0.8
                                ),
                                row=1, col=1
                            )
                else:
                    # Fallback: plot EMAs normally if columns don't exist
                    for i, period in enumerate(ema_periods):
                        ema_col = f'EMA_{period}'
                        if ema_col in df.columns:
                            color = colors[i % len(colors)]
                            fig.add_trace(
                                go.Scatter(
                                    x=df['Date'],
                                    y=df[ema_col],
                                    mode='lines',
                                    name=f'EMA {period}',
                                    line=dict(color=color, width=1.5),
                                    opacity=0.8
                                ),
                                row=1, col=1
                            )
            else:
                # If less than 2 EMAs, plot them normally
                for i, period in enumerate(ema_periods):
                    ema_col = f'EMA_{period}'
                    if ema_col in df.columns:
                        color = colors[i % len(colors)]
                        fig.add_trace(
                            go.Scatter(
                                x=df['Date'],
                                y=df[ema_col],
                                mode='lines',
                                name=f'EMA {period}',
                                line=dict(color=color, width=1.5),
                                opacity=0.8
                            ),
                            row=1, col=1
                        )
        
        # Add ATR bands if enabled
        if atr_bands and 'ATR' in df.columns:
            for band_str in atr_bands:
                try:
                    band_multiplier = float(band_str)
                    upper_band = df['Close'] + (df['ATR'] * band_multiplier)
                    lower_band = df['Close'] - (df['ATR'] * band_multiplier)
                    
                    # Upper band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=upper_band,
                            mode='lines',
                            name=f'+{band_multiplier} ATR',
                            line=dict(color='rgba(255, 255, 255, 0.5)', width=1, dash='dot')
                        ),
                        row=1, col=1
                    )
                    
                    # Lower band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=lower_band,
                            mode='lines',
                            name=f'-{band_multiplier} ATR',
                            line=dict(color='rgba(255, 255, 255, 0.5)', width=1, dash='dot')
                        ),
                        row=1, col=1
                    )
                except ValueError:
                    continue
        
        # Add Bollinger Bands if enabled
        if bollinger_bands and bollinger_bands.get('show'):
            try:
                period = bollinger_bands.get('period', 26)
                stddev = bollinger_bands.get('stddev', 2)
                # Calculate Bollinger Bands - requires at least 'period' number of data points
                if len(df) > period:
                    # Calculate the middle band (Simple Moving Average)
                    df['BB_middle'] = df['Close'].rolling(window=period).mean()
                    # Calculate standard deviation
                    rolling_std = df['Close'].rolling(window=period).std()
                    # Calculate upper and lower bands
                    df['BB_upper'] = df['BB_middle'] + (rolling_std * stddev)
                    df['BB_lower'] = df['BB_middle'] - (rolling_std * stddev)
                    # Upper band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df['BB_upper'],
                            mode='lines',
                            name=f'BB +{stddev}\u03c3',
                            line=dict(color='rgba(173, 20, 255, 0.5)', width=1, dash='dot'),  # Purple
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    # Middle band (SMA)
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df['BB_middle'],
                            mode='lines',
                            name=f'BB SMA({period})',
                            line=dict(color='rgba(173, 20, 255, 0.5)', width=1),  # Purple
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    # Lower band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df['BB_lower'],
                            mode='lines',
                            name=f'BB -{stddev}\u03c3',
                            line=dict(color='rgba(173, 20, 255, 0.5)', width=1, dash='dot'),  # Purple
                            showlegend=False
                        ),
                        row=1, col=1
                    )
            except Exception as e:
                print(f"Error calculating Bollinger Bands: {e}")
        
        # Add Autoenvelope if enabled
        if autoenvelope and autoenvelope.get('show'):
            try:
                period = autoenvelope.get('period', 26)
                percent = autoenvelope.get('percent', 6)
                # Calculate Autoenvelope - requires at least 'period' number of data points
                if len(df) > period:
                    # Calculate the middle line (Simple Moving Average)
                    df['AE_middle'] = df['Close'].rolling(window=period).mean()
                    # Calculate upper and lower bands (percentage based)
                    multiplier = percent / 100
                    df['AE_upper'] = df['AE_middle'] * (1 + multiplier)
                    df['AE_lower'] = df['AE_middle'] * (1 - multiplier)
                    # Upper band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df['AE_upper'],
                            mode='lines',
                            name=f'Env +{percent}%',
                            line=dict(color='rgba(0, 176, 246, 0.5)', width=1, dash='dot'),  # Blue
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    # Middle band (SMA)
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df['AE_middle'],
                            mode='lines',
                            name=f'Env SMA({period})',
                            line=dict(color='rgba(0, 176, 246, 0.5)', width=1),  # Blue
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    # Lower band
                    fig.add_trace(
                        go.Scatter(
                            x=df['Date'],
                            y=df['AE_lower'],
                            mode='lines',
                            name=f'Env -{percent}%',
                            line=dict(color='rgba(0, 176, 246, 0.5)', width=1, dash='dot'),  # Blue
                            showlegend=False
                        ),
                        row=1, col=1
                    )
            except Exception as e:
                print(f"Error calculating Autoenvelope: {e}")
        
        # Add previous day's close line for intraday charts (Today or Previous Market Period)
        if is_intraday and len(df) > 0:
            # Get the official previous close from a 1-month timeframe (like shown in 1M+ views)
            try:
                # Get 1-month daily data to ensure we get the official previous close price
                monthly_data = yf.download(symbol, period="1mo", interval="1d", progress=False)
                
                if not monthly_data.empty:
                    # Get yesterday's close or the last available close price
                    # This ensures consistency with what's shown in 1M+ views
                    if len(monthly_data) >= 2:
                        prev_close = float(monthly_data['Close'].iloc[-2])  # Convert to float to ensure it's a scalar
                        
                        print(f"Adding previous close line for {symbol}: ${prev_close:.2f}")
                        
                        # Add horizontal line for the official previous close
                        fig.add_trace(
                            go.Scatter(
                                x=[df['Date'].min(), df['Date'].max()],
                                y=[prev_close, prev_close],
                                mode='lines',
                                line=dict(color='rgba(255, 255, 255, 0.8)', width=1.5, dash='dash'),
                                name=f'Prev Close: ${prev_close:.2f}',
                                hoverinfo='y',
                                showlegend=False
                            ), 
                            row=1, col=1
                        )
                        
                        # Add annotation for the previous close value
                        fig.add_annotation(
                            x=df['Date'].min(),
                            y=prev_close,
                            text=f"Prev Close: ${prev_close:.2f}",
                            showarrow=False,
                            xanchor='left',
                            yanchor='bottom',
                            xshift=10,
                            bgcolor='rgba(0,0,0,0.6)',
                            bordercolor='rgba(0,0,0,0)',  # Transparent border
                            borderwidth=0,               # No border
                            borderpad=4,
                            font=dict(color='white', size=10)
                        )
                    else:
                        # If we only have one day of data, use that close as reference
                        prev_close = float(monthly_data['Close'].iloc[-1])  # Convert to float to ensure it's a scalar
                        
                        # Add horizontal line for the official previous close
                        fig.add_trace(
                            go.Scatter(
                                x=[df['Date'].min(), df['Date'].max()],
                                y=[prev_close, prev_close],
                                mode='lines',
                                line=dict(color='rgba(255, 255, 255, 0.8)', width=1.5, dash='dash'),
                                name=f'Last Close: ${prev_close:.2f}',
                                hoverinfo='y',
                                showlegend=False
                            ), 
                            row=1, col=1
                        )
                        
                        # Add annotation for the last close value
                        fig.add_annotation(
                            x=df['Date'].min(),
                            y=prev_close,
                            text=f"Last Close: ${prev_close:.2f}",
                            showarrow=False,
                            xanchor='left',
                            yanchor='bottom',
                            xshift=10,
                            bgcolor='rgba(0,0,0,0.6)',
                            bordercolor='rgba(0,0,0,0)',  # Transparent border
                            borderwidth=0,               # No border
                            borderpad=4,
                            font=dict(color='white', size=10)
                        )
                else:
                    # Fallback to use the first open price if we can't get monthly data
                    fallback_close = float(df['Open'].iloc[0])  # Convert to float to ensure it's a scalar
                    
                    # Add horizontal line with fallback price
                    fig.add_trace(
                        go.Scatter(
                            x=[df['Date'].min(), df['Date'].max()],
                            y=[fallback_close, fallback_close],
                            mode='lines',
                            line=dict(color='rgba(255, 255, 255, 0.5)', width=1, dash='dash'),
                            name=f'Approx. Prev: ${fallback_close:.2f}',
                            hoverinfo='y',
                            showlegend=False
                        ), 
                        row=1, col=1
                    )
                    
                    # Add annotation for the approximate previous close
                    fig.add_annotation(
                        x=df['Date'].min(),
                        y=fallback_close,
                        text=f"Approx. Prev: ${fallback_close:.2f}",
                        showarrow=False,
                        xanchor='left',
                        yanchor='bottom',
                        xshift=10,
                        bgcolor='rgba(0,0,0,0.6)',
                        bordercolor='rgba(0,0,0,0)',  # Transparent border
                        borderwidth=0,               # No border
                        borderpad=4,
                        font=dict(color='white', size=10)
                    )
            except Exception as e:
                print(f"Error fetching previous close for {symbol}: {e}")
                # Try a more direct approach as fallback
                try:
                    # Try to get yesterday's close using direct Yahoo Finance API call
                    ticker = yf.Ticker(symbol)
                    prev_close = ticker.info.get('previousClose')
                    
                    if prev_close and isinstance(prev_close, (int, float)):
                        prev_close = float(prev_close)  # Ensure it's a float scalar
                        print(f"Using ticker.info for previous close: ${prev_close:.2f}")
                        fig.add_trace(
                            go.Scatter(
                                x=[df['Date'].min(), df['Date'].max()],
                                y=[prev_close, prev_close],
                                mode='lines',
                                line=dict(color='rgba(255, 255, 255, 0.8)', width=1.5, dash='dash'),
                                name=f'Prev Close: ${prev_close:.2f}',
                                hoverinfo='y',
                                showlegend=False
                            ), 
                            row=1, col=1
                        )
                        
                        # Add annotation for the previous close value
                        fig.add_annotation(
                            x=df['Date'].min(),
                            y=prev_close,
                            text=f"Prev Close: ${prev_close:.2f}",
                            showarrow=False,
                            xanchor='left',
                            yanchor='bottom',
                            xshift=10,
                            bgcolor='rgba(0,0,0,0.6)',
                            bordercolor='rgba(0,0,0,0)',  # Transparent border
                            borderwidth=0,               # No border
                            borderpad=4,
                            font=dict(color='white', size=10)
                        )
                except Exception as fallback_error:
                    print(f"Fallback for previous close also failed: {fallback_error}")
                    # Continue without adding the line

        # Calculate dynamic title with price and percentage changes
        title_text = symbol
        title_color = '#00d4aa'  # Default color
        
        if len(df) > 0:
            current_price = df['Close'].iloc[-1]
            
            # For percentage calculation, use the first price of the dataset as reference
            if len(df) > 1:
                if is_intraday:
                    # For 1D view, compare with opening price (approximates previous close)
                    reference_price = df['Open'].iloc[0]
                else:
                    # For other timeframes, compare with first price in the dataset
                    reference_price = df['Close'].iloc[0]
                
                price_change = current_price - reference_price
                percent_change = (price_change / reference_price) * 100
                
                # Determine arrow and color based on percentage change
                if percent_change > 0:
                    arrow = "↗"
                    title_color = '#00ff88'  # Green for positive percentage
                elif percent_change < 0:
                    arrow = "↘"
                    title_color = '#ff4444'  # Red for negative percentage
                else:
                    arrow = "→"
                    title_color = '#ffaa00'  # Yellow/orange for neutral
                
                # Get current time in HH:MM:SS format
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # Format main title
                main_title = f"{symbol} - ${current_price:.2f} ({arrow} ${abs(price_change):.2f}, {percent_change:+.2f}%)"
            else:
                # Single data point case with current time
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                main_title = f"{symbol} - ${current_price:.2f}"

        # Update layout for dark theme
        layout_settings = {
            'title': title_text,
            'height': 430, # Adjusted to match the 55vh in the layout
            'showlegend': True,
            'xaxis_rangeslider_visible': False,
            'template': 'plotly_dark',
            'paper_bgcolor': '#000000',
            'plot_bgcolor': '#000000',
            'font': dict(color='#ffffff'),
            'title_font': dict(color=title_color, size=20),
            'margin': dict(l=40, r=40, t=50, b=20) # Compact margins
        }
        
        # For all chart types, calculate the appropriate y-axis range
        if len(df) > 0:
            # Get the min and max values from the data for consistent y-axis across chart types
            if 'Low' in df.columns and 'High' in df.columns:
                # For candlestick data, use full price range (High/Low)
                y_min = df['Low'].min()
                y_max = df['High'].max()
            else:
                # For line data only, use Close prices
                y_min = df['Close'].min()
                y_max = df['Close'].max()
            
            # Add a buffer (1%) for better visualization
            y_range_buffer = (y_max - y_min) * 0.05
            y_min = y_min - y_range_buffer
            y_max = y_max + y_range_buffer
            
            # Set y-axis range explicitly
            layout_settings['yaxis'] = dict(
                range=[y_min, y_max],
                autorange=False,
                fixedrange=False  # Allow zooming on y-axis
            )
            
        fig.update_layout(**layout_settings)
        
        # Update axes colors and explicitly exclude weekends
        fig.update_xaxes(
            gridcolor='#444', 
            zerolinecolor='#444',
            rangebreaks=[
                # Don't show weekends (Saturday=6, Sunday=0)
                dict(bounds=["sat", "mon"])
            ]
        )
        
        # Configure y-axis appearance
        yaxis_config = {
            'gridcolor': '#444', 
            'zerolinecolor': '#444'
        }
        
        # Don't override our explicit y-axis settings from layout_settings
        # Just apply styling configs here
        fig.update_yaxes(**yaxis_config)
        
        # Generate a stable uirevision that doesn't change with EMA parameters
        # This ensures rangeslider position persists across EMA changes
        stable_uirevision = f"{symbol}_{chart_type}_{lower_chart_type}"
        
        # Update layout with dynamic title and colors
        fig.update_layout(
            height=800,  # Set explicit height for combined chart
            showlegend=True,
            template='plotly_dark',
            paper_bgcolor='#000000',
            plot_bgcolor='#000000',
            font=dict(color='#ffffff'),
            title=dict(
                text=main_title,  # Dynamic title with price and changes
                font=dict(
                    color=title_color, 
                    size=24,
                    family='Inter, sans-serif',
                    weight='bold'
                ),
                y=0.95,
                x=0.05,
                xanchor='left',
                yanchor='top'
            ),
            margin=dict(l=40, r=40, t=70, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            # Configure rangeslider to appear below the lower chart
            xaxis=dict(
                domain=[0, 1],
                anchor='y',
                rangeslider=dict(visible=False)  # Disable rangeslider on main chart
            ),
            xaxis2=dict(
                domain=[0, 1],
                anchor='y2',
                rangeslider=dict(
                    visible=True,
                    thickness=0.05,  # Make it thinner
                    bgcolor='#2d3035',
                    bordercolor='#444',
                    borderwidth=1
                ),
                # Preserve rangeslider position across updates with stable uirevision
                uirevision=stable_uirevision
            ),
            # Preserve zoom and pan state across updates with stable uirevision
            uirevision=stable_uirevision
        )
        
        # Calculate consistent y-axis range for main chart
        if len(df) > 0:
            # Get the min and max values from the data for consistent y-axis across chart types
            if 'Low' in df.columns and 'High' in df.columns:
                # For candlestick data, use full price range (High/Low)
                y_min = df['Low'].min()
                y_max = df['High'].max()
            else:
                # For line data only, use Close prices
                y_min = df['Close'].min()
                y_max = df['Close'].max()
            
            # Add a buffer (3%) for better visualization
            y_range_buffer = (y_max - y_min) * 0.03
            y_min = y_min - y_range_buffer
            y_max = y_max + y_range_buffer
            
            # Set y-axis range explicitly for main chart
            fig.update_yaxes(
                range=[y_min, y_max],
                autorange=False,
                fixedrange=False,
                row=1, col=1
            )
        
        # Update x-axes (shared x-axis for synchronized zooming)
        fig.update_xaxes(
            gridcolor='#444', 
            zerolinecolor='#444',
            rangebreaks=[
                dict(bounds=["sat", "mon"])  # Exclude weekends
            ],
            # Enable synchronized zooming and panning
            matches='x',  # All x-axes will match the first x-axis
            # Preserve zoom state across updates with stable uirevision
            uirevision=stable_uirevision
        )
        
        # Preserve zoom/pan state if relayout_data contains range information
        if relayout_data and 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            try:
                # Apply the preserved x-axis range
                x_range = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
                fig.update_xaxes(range=x_range)
            except Exception as e:
                pass
        elif relayout_data and 'xaxis2.range[0]' in relayout_data and 'xaxis2.range[1]' in relayout_data:
            try:
                # Apply the preserved x-axis range from the lower chart
                x_range = [relayout_data['xaxis2.range[0]'], relayout_data['xaxis2.range[1]']]
                fig.update_xaxes(range=x_range)
            except Exception as e:
                pass
        
        # Update y-axes styling
        fig.update_yaxes(gridcolor='#444', zerolinecolor='#444')
        
        # Update subplot titles
        fig.update_annotations(font_color='#00d4aa')
        
        # Add lower chart in row 2 based on selected indicator type
        if lower_chart_type == 'volume':
            # Volume chart (default)
            colors = []
            for i in range(len(df)):
                if i > 0 and df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                    colors.append('#00ff88')  # Green volume for price up
                else:
                    colors.append('#ff4444')  # Red volume for price down
            
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume'],
                    name='Volume',
                    marker=dict(color=colors),
                    opacity=0.8,
                    hovertemplate='%{x}<br>Volume: %{y:,.0f}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Add comparison volume if selected
            if volume_comparison and volume_comparison != 'none':
                # Get comparison volume data
                comparison_data = get_comparison_volume(volume_comparison, None, df['Date'].min(), df['Date'].max())
                
                if comparison_data is not None and not comparison_data.empty:
                    # Merge the data on Date
                    merged_data = pd.merge(
                        df[['Date', 'Volume']], 
                        comparison_data, 
                        on='Date', 
                        how='inner',
                        suffixes=('', '_comp')
                    )
                    
                    if not merged_data.empty:
                        # Calculate average volumes for normalization
                        avg_volume_main = merged_data['Volume'].mean()
                        avg_volume_comp = merged_data['Volume_comp'].mean()
                        
                        # Normalize volumes to make them comparable
                        if avg_volume_main > 0 and avg_volume_comp > 0:
                            # Normalize both volumes to show relative changes
                            merged_data['Volume_Norm'] = merged_data['Volume'] / avg_volume_main
                            merged_data['Volume_Comp_Norm'] = merged_data['Volume_comp'] / avg_volume_comp
                            
                            # Display the comparison volume
                            fig.add_trace(
                                go.Bar(
                                    x=merged_data['Date'],
                                    y=merged_data['Volume_Comp_Norm'],
                                    name=f'{volume_comparison} Vol',
                                    marker=dict(color='#ff4444'),  # Red for comparison
                                    opacity=0.7,
                                    hovertemplate='%{x}<br>' + f'{volume_comparison} Vol: ' + '%{y:.2f}x<extra></extra>'
                                ),
                                row=2, col=1
                            )
                            
                            # Update the primary volume data to use the normalized values
                            # and update its appearance to be green for contrast
                            for trace in fig.data:
                                if trace.name == 'Volume':
                                    trace.y = merged_data['Volume_Norm']
                                    trace.marker.color = '#00ff88'  # Green for primary
                                    trace.hovertemplate = '%{x}<br>' + f'{symbol} Vol: ' + '%{y:.2f}x<extra></extra>'
                            
                            # Update the y-axis title
                            fig.update_yaxes(
                                title_text=f"Relative Volume ({symbol} vs {volume_comparison})",
                                row=2, col=1
                            )
        
        elif lower_chart_type == 'macd':
            # MACD indicator chart
            if 'MACD' in df.columns and 'MACD_signal' in df.columns and 'MACD_hist' in df.columns:
                # MACD line
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['MACD'],
                        name='MACD',
                        line=dict(color='#00ff88', width=1.5)
                    ),
                    row=2, col=1
                )
                
                # Signal line
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['MACD_signal'],
                        name='Signal',
                        line=dict(color='#ff4444', width=1.5)
                    ),
                    row=2, col=1
                )
                
                # MACD histogram as bars
                colors = []
                for val in df['MACD_hist']:  # Changed from MACD_histogram to MACD_hist
                    if val >= 0:
                        colors.append('#00ff88')  # Green for positive
                    else:
                        colors.append('#ff4444')  # Red for negative
                
                fig.add_trace(
                    go.Bar(
                        x=df['Date'],
                        y=df['MACD_hist'],  # Changed from MACD_histogram to MACD_hist
                        name='Histogram',
                        marker=dict(color=colors),
                        opacity=0.7
                    ),
                    row=2, col=1
                )
                
                # Set y-axis title for MACD
                fig.update_yaxes(title_text="MACD", row=2, col=1)
            
        elif lower_chart_type == 'force':
            # Force Index chart
            if 'Force_Index' in df.columns:
                colors = []
                for val in df['Force_Index']:
                    if val >= 0:
                        colors.append('#00ff88')  # Green for positive force
                    else:
                        colors.append('#ff4444')  # Red for negative force
                
                fig.add_trace(
                    go.Bar(
                        x=df['Date'],
                        y=df['Force_Index'],
                        name='Force Index',
                        marker=dict(color=colors),
                        opacity=0.7
                    ),
                    row=2, col=1
                )
                
                # Set y-axis title for Force Index
                fig.update_yaxes(title_text="Force Index", row=2, col=1)
                
        elif lower_chart_type == 'ad':
            # A/D Line chart
            if 'AD' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['AD'],
                        name='A/D Line',
                        line=dict(color='#00d4aa', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(0, 212, 170, 0.2)'
                    ),
                    row=2, col=1
                )
                
                # Set y-axis title for A/D Line
                fig.update_yaxes(title_text="A/D Line", row=2, col=1)
                
        elif lower_chart_type == 'adx':
            # ADX/DMI chart
            adx_components = adx_components or ['adx', 'di_plus', 'di_minus']
            
            # ADX line (strength of trend)
            if 'ADX' in df.columns and 'adx' in adx_components:
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['ADX'],
                        name='ADX',
                        line=dict(color='#9900ff', width=2)  # Changed to purple
                    ),
                    row=2, col=1
                )
            
            # +DI line (bullish trend strength)
            if 'DI_plus' in df.columns and 'di_plus' in adx_components:
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['DI_plus'],
                        name='+DI',
                        line=dict(color='#00ff88', width=1.5)
                    ),
                    row=2, col=1
                )
            
            # -DI line (bearish trend strength)
            if 'DI_minus' in df.columns and 'di_minus' in adx_components:
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['DI_minus'],
                        name='-DI',
                        line=dict(color='#ff4444', width=1.5)
                    ),
                    row=2, col=1
                )
            
            # Add reference line at ADX=25 (strong trend threshold)
            fig.add_hline(
                y=25,
                line_dash="dot",
                line_color="rgba(255, 255, 255, 0.5)",
                row=2, col=1,
                annotation_text="Strong Trend (25)",
                annotation_position="top right",
                annotation_font_size=10
            )
            
            # Set y-axis title for ADX/DMI
            fig.update_yaxes(title_text="ADX/DMI", row=2, col=1)
            
        elif lower_chart_type == 'stochastic':
            # Slow Stochastic chart with %K and %D
            if 'Stoch_K' in df.columns and 'Stoch_D' in df.columns:
                # %K line (green)
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['Stoch_K'],
                        name='%K',
                        line=dict(color='#00ff88', width=2)  # Green
                    ),
                    row=2, col=1
                )
                
                # %D line (red)
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['Stoch_D'],
                        name='%D',
                        line=dict(color='#ff4444', width=2)  # Red
                    ),
                    row=2, col=1
                )
                
                # Add overbought line at 80%
                fig.add_hline(
                    y=80,
                    line_dash="dot",
                    line_color="rgba(255, 68, 68, 0.7)",
                    row=2, col=1,
                    annotation_text="Overbought (80)",
                    annotation_position="top right",
                    annotation_font_size=10,
                    annotation_font_color="rgba(255, 68, 68, 0.8)"
                )
                
                # Add oversold line at 20%
                fig.add_hline(
                    y=20,
                    line_dash="dot",
                    line_color="rgba(0, 255, 136, 0.7)",
                    row=2, col=1,
                    annotation_text="Oversold (20)",
                    annotation_position="bottom right",
                    annotation_font_size=10,
                    annotation_font_color="rgba(0, 255, 136, 0.8)"
                )
                
                # Set y-axis range from 0 to 100 and title
                fig.update_yaxes(
                    title_text="Stochastic (%)",
                    range=[0, 100],
                    row=2, col=1
                )
                
        elif lower_chart_type == 'rsi':
            # RSI chart with overbought/oversold areas
            if 'RSI' in df.columns:
                # Create a helper function to find fill areas
                def find_fill_areas(values, dates, threshold, below=True):
                    """Find areas where RSI is below/above threshold and create fill polygons"""
                    fill_areas = []
                    
                    for i in range(len(values)):
                        if pd.isna(values.iloc[i]):
                            continue
                        
                        if below and values.iloc[i] < threshold:
                            # Start of oversold area (below threshold)
                            area_start = i
                            # Find the end of this oversold period
                            area_end = i
                            for j in range(i + 1, len(values)):
                                if pd.isna(values.iloc[j]) or values.iloc[j] >= threshold:
                                    area_end = j - 1
                                    break
                                area_end = j
                            
                            if area_end > area_start:  # Only create area if it spans multiple points
                                # Create fill area coordinates
                                x_coords = list(dates.iloc[area_start:area_end+1])
                                y_coords = list(values.iloc[area_start:area_end+1])
                                
                                # Close the polygon by adding baseline points
                                x_coords.extend([dates.iloc[area_end], dates.iloc[area_start]])
                                y_coords.extend([threshold, threshold])
                                
                                fill_areas.append((x_coords, y_coords))
                        
                        elif not below and values.iloc[i] > threshold:
                            # Start of overbought area (above threshold)
                            area_start = i
                            # Find the end of this overbought period
                            area_end = i
                            for j in range(i + 1, len(values)):
                                if pd.isna(values.iloc[j]) or values.iloc[j] <= threshold:
                                    area_end = j - 1
                                    break
                                area_end = j
                            
                            if area_end > area_start:  # Only create area if it spans multiple points
                                # Create fill area coordinates
                                x_coords = list(dates.iloc[area_start:area_end+1])
                                y_coords = list(values.iloc[area_start:area_end+1])
                                
                                # Close the polygon by adding baseline points
                                x_coords.extend([dates.iloc[area_end], dates.iloc[area_start]])
                                y_coords.extend([threshold, threshold])
                                
                                fill_areas.append((x_coords, y_coords))
                    
                    return fill_areas
                
                # Find oversold fill areas (below 30) - Green
                oversold_areas = find_fill_areas(df['RSI'], df['Date'], 30, below=True)
                
                for x_coords, y_coords in oversold_areas:
                    fig.add_trace(
                        go.Scatter(
                            x=x_coords,
                            y=y_coords,
                            fill='toself',
                            fillcolor='rgba(0, 255, 136, 0.3)',  # Green with transparency
                            line=dict(color='rgba(0,0,0,0)', width=0),  # Invisible line
                            showlegend=False,
                            hoverinfo='skip',
                            name='Oversold Area'
                        ),
                        row=2, col=1
                    )
                
                # Find overbought fill areas (above 70) - Red
                overbought_areas = find_fill_areas(df['RSI'], df['Date'], 70, below=False)
                
                for x_coords, y_coords in overbought_areas:
                    fig.add_trace(
                        go.Scatter(
                            x=x_coords,
                            y=y_coords,
                            fill='toself',
                            fillcolor='rgba(255, 68, 68, 0.3)',  # Red with transparency
                            line=dict(color='rgba(0,0,0,0)', width=0),  # Invisible line
                            showlegend=False,
                            hoverinfo='skip',
                            name='Overbought Area'
                        ),
                        row=2, col=1
                    )
                
                # Add main RSI line (white)
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['RSI'],
                        name='RSI',
                        line=dict(color='#ffffff', width=2)  # White
                    ),
                    row=2, col=1
                )
                
                # Add overbought line at 70
                fig.add_hline(
                    y=70,
                    line_dash="dot",
                    line_color="rgba(255, 68, 68, 0.7)",
                    row=2, col=1,
                    annotation_text="Overbought (70)",
                    annotation_position="top right",
                    annotation_font_size=10,
                    annotation_font_color="rgba(255, 68, 68, 0.8)"
                )
                
                # Add oversold line at 30
                fig.add_hline(
                    y=30,
                    line_dash="dot",
                    line_color="rgba(0, 255, 136, 0.7)",
                    row=2, col=1,
                    annotation_text="Oversold (30)",
                    annotation_position="bottom right",
                    annotation_font_size=10,
                    annotation_font_color="rgba(0, 255, 136, 0.8)"
                )
                
                # Set y-axis range from 0 to 100 and title
                fig.update_yaxes(
                    title_text="RSI",
                    range=[0, 100],
                    row=2, col=1
                )
        
        elif lower_chart_type == 'obv':
            # On Balance Volume chart
            if 'OBV' in df.columns:
                # Add OBV line with area fill
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df['OBV'],
                        name='OBV',
                        line=dict(color='#00d4aa', width=2),  # Teal color
                        fill='tozeroy',  # Fill to zero baseline
                        fillcolor='rgba(0, 212, 170, 0.2)',  # Semi-transparent teal
                        hovertemplate='%{x}<br>OBV: %{y:,.0f}<extra></extra>'
                    ),
                    row=2, col=1
                )
                
                # Set y-axis title for OBV
                fig.update_yaxes(title_text="OBV", row=2, col=1)
        
        # Check Value Zone status and add annotation if applicable
        is_in_value_zone = False
        if 'show' in show_ema and not is_intraday and len(ema_periods) >= 2:
            is_in_value_zone = check_value_zone_status(df, ema_periods)
            
            if is_in_value_zone:
                # Add a subtle annotation below the chart indicating the stock is in the Value Zone
                fig.add_annotation(
                    text="✓ This stock is in the Value Zone",
                    xref="paper", yref="paper",
                    x=0.02, y=0.02,  # Bottom left corner
                    xanchor='left', yanchor='bottom',
                    showarrow=False,
                    font=dict(size=12, color="#00d4aa", family="Arial"),
                    bgcolor="rgba(0, 212, 170, 0.1)",
                    bordercolor="#00d4aa",
                    borderwidth=1,
                    borderpad=4
                )
        
        return fig, {'backgroundColor': '#000000', 'height': '90vh'}, 'd-none'
        
    except Exception as e:
        print(f"Error updating combined chart: {e}")
        return go.Figure(), {'display': 'none'}, 'd-block'

def update_symbol_status(symbol):
    """Update symbol status display based on current symbol"""
    if not symbol or symbol == 'SPY':
        return "SPY - S&P 500 ETF", {'color': '#00d4aa', 'fontSize': '14px'}
    else:
        return f"{symbol}", {'color': '#fff', 'fontSize': '14px'}

def update_indicator_options(timeframe):
    """Update indicator options based on timeframe"""
    # Always show EMA controls for all timeframes
    ema_style = {'display': 'block'}
    
    # Lower chart options - remove Force Index for intraday
    is_intraday = timeframe in ['1d', 'yesterday']
    if is_intraday:
        lower_options = [
            {'label': 'Volume', 'value': 'volume'},
            {'label': 'MACD', 'value': 'macd'},
            {'label': 'A/D Line', 'value': 'ad'},
            {'label': 'ADX/DMI', 'value': 'adx'},
            {'label': 'Slow Stochastic', 'value': 'stochastic'},
            {'label': 'RSI', 'value': 'rsi'},
            {'label': 'OBV', 'value': 'obv'}
        ]
    else:
        lower_options = [
            {'label': 'Volume', 'value': 'volume'},
            {'label': 'MACD', 'value': 'macd'},
            {'label': 'Force Index', 'value': 'force'},
            {'label': 'A/D Line', 'value': 'ad'},
            {'label': 'ADX/DMI', 'value': 'adx'},
            {'label': 'Slow Stochastic', 'value': 'stochastic'},
            {'label': 'RSI', 'value': 'rsi'},
            {'label': 'OBV', 'value': 'obv'}
        ]
    return ema_style, ema_style, lower_options

def check_value_zone_status(df, ema_periods):
    """Check if the current stock price is in the Value Zone (between two EMAs)"""
    try:
        if len(df) == 0 or len(ema_periods) < 2:
            return False
        
        # Get the last (most recent) price
        current_price = df['Close'].iloc[-1]
        
        # Get the two EMA values (we'll use the first two EMA periods)
        ema1_col = f'EMA_{ema_periods[0]}'
        ema2_col = f'EMA_{ema_periods[1]}'
        
        if ema1_col not in df.columns or ema2_col not in df.columns:
            return False
        
        # Get the last EMA values
        ema1_value = df[ema1_col].iloc[-1]
        ema2_value = df[ema2_col].iloc[-1]
        
        # Check if price is between the two EMAs
        ema_min = min(ema1_value, ema2_value)
        ema_max = max(ema1_value, ema2_value)
        
        is_in_zone = ema_min <= current_price <= ema_max
        
        return is_in_zone
        
    except Exception as e:
        pass
        return False

def update_stock_status_indicator(symbol_info):
    """Generate status indicator with last updated information"""
    if not symbol_info:
        return html.Div("No data available", style={'color': '#aaa', 'fontSize': '12px'})
    
    # Get the basic information
    symbol = symbol_info.get('symbol', '')
    time = symbol_info.get('time', '')
    color = symbol_info.get('color', '#00d4aa')
    
    # Create the status content
    content = []
    
    # Add symbol and price with appropriate styling
    if 'price' in symbol_info:
        price = symbol_info.get('price', 0)
        content.append(
            html.Div([
                html.Span(f"{symbol} ", style={'fontWeight': 'bold', 'color': color}),
                html.Span(f"${price:.2f}", style={'color': '#ffffff'})
            ], style={'fontSize': '14px'})
        )
    
    # Add change information if available
    if 'change' in symbol_info and 'percent' in symbol_info:
        change = symbol_info.get('change', 0)
        percent = symbol_info.get('percent', 0)
        
        # Determine arrow based on change
        arrow = "↗" if change > 0 else "↘" if change < 0 else "→"
        
        content.append(
            html.Div([
                html.Span(f"{arrow} ${abs(change):.2f} ({percent:+.2f}%)", 
                          style={'color': color, 'fontWeight': 'bold'})
            ], style={'fontSize': '13px'})
        )
    
    # Add last updated time
    content.append(
        html.Div(f"Last updated {time}", 
                 style={'color': '#aaa', 'fontSize': '11px', 'marginTop': '2px', 'textAlign': 'left'})
    )
    
    return html.Div(content, style={'textAlign': 'left', 'padding': '5px', 'borderRadius': '4px'})