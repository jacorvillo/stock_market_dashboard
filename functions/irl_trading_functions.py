import pandas as pd
import numpy as np
import yfinance as yf
import ta
import numbers

CSV_FILE = 'equity_data.csv'

FIELDS = [
    'equity',
    'open_positions',
    'amount_invested',
    # 'side',  # Remove from FIELDS, handle separately
    'stop_price',
    'value_at_entry',
    'stocks_in_positions',
    'stock_price_at_entry',
    'stock_price_at_close',
    'net_gain_loss_amount',
    'net_gain_loss_percent',
    'target_price',
    'stop_hit',  # Field to track if stop was hit
    'stop_hit_price',  # Field to store the price when stop was hit
]

def load_trading_df():
    return pd.read_csv(CSV_FILE)

def save_trading_df(df):
    df.to_csv(CSV_FILE, index=False)

def to_native(obj):
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_native(v) for v in obj]
    elif isinstance(obj, numbers.Integral):
        return int(obj)
    elif isinstance(obj, numbers.Real):
        return float(obj)
    else:
        return obj

def calculate_trade_apgar(stock_symbol, side='buy'):
    """
    Calculate Trade Apgar score based on Elder's methodology
    
    The Trade Apgar evaluates 5 components on a scale of 0-2:
    For BUY positions:
    1. Weekly Impulse: Red=0, Green=1, Blue=2
    2. Daily Impulse: Red=0, Green=1, Blue=2  
    3. Daily Price vs Value: Above=0, In Zone=1, Below=2
    4. False Breakout: None=0, Happened=1, On Verge=2
    5. Perfection: Neither=0, One=1, Both=2
    
    For SELL/SHORT positions:
    1. Weekly Impulse: Red=2, Green=0, Blue=1
    2. Daily Impulse: Red=2, Green=0, Blue=1
    3. Daily Price vs Value: Above=2, In Zone=1, Below=0
    4. False Breakout: None=0, Happened=1, On Verge=2
    5. Perfection: Neither=0, One=1, Both=2
    
    Args:
        stock_symbol: Stock symbol to analyze
        side: 'buy' for long positions, 'sell' for short positions
    
    Returns:
    - Dictionary with detailed scores and total
    - Total score must be 7+ with no zeros to pass
    """
    try:
        # Get weekly and daily data
        ticker = yf.Ticker(stock_symbol)
        weekly_data = ticker.history(period='6mo', interval='1wk')
        # Fetch 6 months of daily data for proper indicator warmup
        daily_data = ticker.history(period='6mo', interval='1d')
        
        if weekly_data.empty or daily_data.empty:
            return {
                'total_score': 0,
                'passed': False,
                'error': 'Unable to fetch data',
                'details': {
                    'weekly_impulse': {'score': 0, 'color': 'unknown', 'reason': 'No data'},
                    'daily_impulse': {'score': 0, 'color': 'unknown', 'reason': 'No data'},
                    'daily_price': {'score': 0, 'position': 'unknown', 'reason': 'No data'},
                    'false_breakout': {'score': 0, 'status': 'unknown', 'reason': 'No data'},
                    'perfection': {'score': 0, 'timeframes': 0, 'reason': 'No data'}
                }
            }
        
        # Calculate indicators for both timeframes
        weekly_data = calculate_indicators_for_apgar(weekly_data)
        daily_data = calculate_indicators_for_apgar(daily_data)
        
        # 1. Weekly Impulse Score
        weekly_impulse = calculate_impulse_score(weekly_data, side)
        
        # 2. Daily Impulse Score  
        daily_impulse = calculate_impulse_score(daily_data, side)
        
        # 3. Daily Price vs Value Score
        daily_price_score = calculate_price_vs_value_score(daily_data, side)
        
        # 4. False Breakout Score
        false_breakout_score = calculate_false_breakout_score(daily_data, side)
        
        # 5. Perfection Score (both timeframes looking perfect)
        perfection_score = calculate_perfection_score(weekly_data, daily_data, side)
        
        # Calculate total score
        total_score = (weekly_impulse['score'] + daily_impulse['score'] + 
                      daily_price_score['score'] + false_breakout_score['score'] + 
                      perfection_score['score'])
        
        # Check if any component scored zero
        has_zeros = (weekly_impulse['score'] == 0 or daily_impulse['score'] == 0 or
                    daily_price_score['score'] == 0 or false_breakout_score['score'] == 0 or
                    perfection_score['score'] == 0)
        
        # Pass criteria: total >= 7 and no zeros
        passed = total_score >= 7 and not has_zeros
        
        result = {
            'total_score': total_score,
            'passed': passed,
            'side': side,
            'details': {
                'weekly_impulse': weekly_impulse,
                'daily_impulse': daily_impulse,
                'daily_price': daily_price_score,
                'false_breakout': false_breakout_score,
                'perfection': perfection_score
            }
        }
        return to_native(result)
        
    except Exception as e:
        result = {
            'total_score': 0,
            'passed': False,
            'side': side,
            'error': str(e),
            'details': {
                'weekly_impulse': {'score': 0, 'color': 'unknown', 'reason': f'Error: {str(e)}'},
                'daily_impulse': {'score': 0, 'color': 'unknown', 'reason': f'Error: {str(e)}'},
                'daily_price': {'score': 0, 'position': 'unknown', 'reason': f'Error: {str(e)}'},
                'false_breakout': {'score': 0, 'status': 'unknown', 'reason': f'Error: {str(e)}'},
                'perfection': {'score': 0, 'timeframes': 0, 'reason': f'Error: {str(e)}'}
            }
        }
        return to_native(result)

def calculate_indicators_for_apgar(df):
    """Calculate required indicators for Apgar scoring"""
    df = df.copy()
    
    # Calculate EMAs
    from ta.trend import EMAIndicator, MACD
    df['EMA_13'] = EMAIndicator(df['Close'], window=13).ema_indicator()
    df['EMA_26'] = EMAIndicator(df['Close'], window=26).ema_indicator()
    
    # Calculate MACD
    macd = MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_hist'] = macd.macd_diff()
    
    # Calculate EMA slope for impulse
    df['ema_slope'] = df['EMA_13'].diff()
    df['macd_hist_change'] = df['MACD_hist'].diff()
    
    return df

def calculate_impulse_score(df, side='buy'):
    """Calculate impulse score (0-2) based on EMA trend and MACD momentum"""
    from functions.impulse_functions import calculate_impulse_system
    if len(df) < 2:
        return {'score': 0, 'color': 'unknown', 'reason': 'Insufficient data'}
    # Use the centralized impulse system logic
    impulse_df = calculate_impulse_system(df, ema_period=13)
    color = impulse_df['impulse_color'].iloc[-1] if len(impulse_df) > 0 else 'unknown'
    # Scoring: depends on side
    if side == 'buy':
        if color == 'red':
            score = 0
        elif color == 'green':
            score = 1
        elif color == 'blue':
            score = 2
        else:
            score = 0
        # Blue after red gets bonus (bears losing power)
        if color == 'blue' and len(impulse_df) > 2:
            prev_color = impulse_df['impulse_color'].iloc[-2]
            prev_prev_color = impulse_df['impulse_color'].iloc[-3]
            if prev_prev_color == 'red':
                score = 2
    else:  # side == 'sell' or 'short'
        if color == 'red':
            score = 2
        elif color == 'green':
            score = 0
        elif color == 'blue':
            score = 1
        else:
            score = 0
        # Blue after green gets bonus (bulls losing power)
        if color == 'blue' and len(impulse_df) > 2:
            prev_color = impulse_df['impulse_color'].iloc[-2]
            prev_prev_color = impulse_df['impulse_color'].iloc[-3]
            if prev_prev_color == 'green':
                score = 1
    return {
        'score': score,
        'color': color,
        'reason': f'Impulse color: {color}'
    }

def calculate_price_vs_value_score(df, side='buy'):
    """Calculate price vs value score (0-2)"""
    if len(df) < 20:
        return {'score': 0, 'position': 'unknown', 'reason': 'Insufficient data'}
    
    latest_price = df['Close'].iloc[-1]
    
    # Calculate value zone using 20-period SMA as proxy for "value"
    sma_20 = df['Close'].rolling(20).mean().iloc[-1]
    
    # Define value zone as ±5% around SMA
    value_upper = sma_20 * 1.05
    value_lower = sma_20 * 0.95
    
    if side == 'buy':
        if latest_price > value_upper:
            position = 'above'
            score = 0
        elif value_lower <= latest_price <= value_upper:
            position = 'in_zone'
            score = 1
        else:
            position = 'below'
            score = 2
    else: # side == 'sell' or 'short'
        if latest_price > value_upper:
            position = 'above'
            score = 2
        elif value_lower <= latest_price <= value_upper:
            position = 'in_zone'
            score = 1
        else:
            position = 'below'
            score = 0
    
    return {
        'score': score,
        'position': position,
        'reason': f'Price ${latest_price:.2f} vs Value Zone ${value_lower:.2f}-${value_upper:.2f}'
    }

def calculate_false_breakout_score(df, side='buy'):
    """Calculate false breakout score (0-2)"""
    if len(df) < 20:
        return {'score': 0, 'status': 'unknown', 'reason': 'Insufficient data'}
    
    # Look for recent breakouts and their outcomes
    recent_high = df['High'].tail(10).max()
    recent_low = df['Low'].tail(10).min()
    current_price = df['Close'].iloc[-1]
    
    # Check if we're near recent highs/lows (potential breakout)
    near_high = current_price >= recent_high * 0.98
    near_low = current_price <= recent_low * 1.02
    
    if side == 'buy':
        if near_high or near_low:
            status = 'on_verge'
            score = 2
        else:
            # Check for recent failed breakouts
            high_breakout_failed = (df['High'].tail(5) > recent_high * 1.01).any() and current_price < recent_high
            low_breakout_failed = (df['Low'].tail(5) < recent_low * 0.99).any() and current_price > recent_low
            
            if high_breakout_failed or low_breakout_failed:
                status = 'happened'
                score = 1
            else:
                status = 'none'
                score = 0
    else: # side == 'sell' or 'short'
        if near_high or near_low:
            status = 'on_verge'
            score = 2
        else:
            # Check for recent failed breakouts
            high_breakout_failed = (df['High'].tail(5) < recent_high * 0.99).any() and current_price > recent_high
            low_breakout_failed = (df['Low'].tail(5) > recent_low * 1.01).any() and current_price < recent_low
            
            if high_breakout_failed or low_breakout_failed:
                status = 'happened'
                score = 1
            else:
                status = 'none'
                score = 0
    
    return {
        'score': score,
        'status': status,
        'reason': f'Current price ${current_price:.2f}, recent range ${recent_low:.2f}-${recent_high:.2f}'
    }

def calculate_perfection_score(weekly_df, daily_df, side='buy'):
    """Calculate perfection score (0-2) - both timeframes looking perfect"""
    weekly_perfect = is_timeframe_perfect(weekly_df, side)
    daily_perfect = is_timeframe_perfect(daily_df, side)
    
    perfect_count = sum([weekly_perfect, daily_perfect])
    
    if perfect_count == 0:
        score = 0
    elif perfect_count == 1:
        score = 1
    else:
        score = 2
    
    return {
        'score': score,
        'timeframes': perfect_count,
        'reason': f'Weekly: {"Perfect" if weekly_perfect else "Not perfect"}, Daily: {"Perfect" if daily_perfect else "Not perfect"}'
    }

def is_timeframe_perfect(df, side='buy'):
    """Check if a timeframe looks perfect for trading"""
    if len(df) < 5:
        return False
    
    latest = df.iloc[-1]
    if side == 'buy':
        # Perfect conditions: strong uptrend with momentum (no volume requirement)
        price_rising = latest['Close'] > df['Close'].iloc[-2]
        ema_rising = latest['EMA_13'] > df['EMA_13'].iloc[-2]
        macd_positive = latest['MACD_hist'] > 0
        return price_rising and ema_rising and macd_positive
    else: # side == 'sell' or 'short'
        # Perfect short: strong downtrend with momentum (no volume requirement)
        price_falling = latest['Close'] < df['Close'].iloc[-2]
        ema_falling = latest['EMA_13'] < df['EMA_13'].iloc[-2]
        macd_negative = latest['MACD_hist'] < 0
        return price_falling and ema_falling and macd_negative

# Open a new position (buy or sell) - now with optional Apgar validation
def open_position(df, stock, amount, price_at_entry, stop_price, target_price, side, require_apgar=False):
    # Calculate Trade Apgar score for informational purposes
    apgar_result = calculate_trade_apgar(stock, side)
    
    # Only enforce Apgar validation if explicitly required
    if require_apgar and not apgar_result['passed']:
        raise ValueError(f"Trade Apgar score {apgar_result['total_score']}/10 - Must be 7+ with no zeros. Details: {apgar_result['details']}")
    
    last_equity = df['equity'].iloc[-1]
    new_row = {f: np.nan for f in FIELDS}
    if side == 'buy':
        new_equity = last_equity - amount
    else:  # sell/short
        new_equity = last_equity + amount
    new_row['equity'] = float(new_equity)
    new_row['open_positions'] = 1.0
    new_row['amount_invested'] = amount
    new_row['stop_price'] = stop_price
    new_row['value_at_entry'] = amount
    new_row['stocks_in_positions'] = stock
    new_row['stock_price_at_entry'] = price_at_entry
    new_row['stock_price_at_close'] = np.nan
    new_row['net_gain_loss_amount'] = np.nan
    new_row['net_gain_loss_percent'] = np.nan
    new_row['target_price'] = target_price
    new_row['stop_hit'] = False
    new_row['stop_hit_price'] = np.nan
    # Create DataFrame row and set 'side' as string after
    new_row_df = pd.DataFrame([new_row])
    new_row_df['side'] = str(side)
    df = pd.concat([df, new_row_df], ignore_index=True)
    save_trading_df(df)
    return df

# Update stop price for an open position
def update_stop_price(df, stock, new_stop_price):
    # Find the last open position for this stock
    open_mask = (df['stocks_in_positions'] == stock) & (df['open_positions'] == 1.0)
    if not open_mask.any():
        raise ValueError(f"No open position found for stock {stock}")
    idx = df[open_mask].index[-1]
    df.at[idx, 'stop_price'] = new_stop_price
    save_trading_df(df)
    return df

# Check if stop was hit during position lifetime
def check_stop_hit(df, stock):
    """Check if the stop price was hit during the position's lifetime"""
    # Find the last open position for this stock
    open_mask = (df['stocks_in_positions'] == stock) & (df['open_positions'] == 1.0)
    if not open_mask.any():
        raise ValueError(f"No open position found for stock {stock}")
    idx = df[open_mask].index[-1]
    
    # Get position details
    stop_price = df.at[idx, 'stop_price']
    entry_price = df.at[idx, 'stock_price_at_entry']
    amount_invested = df.at[idx, 'amount_invested']
    
    # Determine if this is a long or short position
    is_long = amount_invested > 0
    
    try:
        # Get historical data from entry to now
        ticker = yf.Ticker(stock)
        # Get data from 30 days ago to now to cover the position period
        hist_data = ticker.history(period='30d')
        
        if hist_data.empty:
            return False, 0.0
        
        # Check if stop was hit
        if is_long:
            # For long positions, check if price went below stop
            stop_hit = (hist_data['Low'] <= stop_price).any()
            if stop_hit:
                # Find the first time the stop was hit
                stop_hit_idx = (hist_data['Low'] <= stop_price).idxmax()
                stop_hit_price = hist_data.loc[stop_hit_idx, 'Low']
                return True, stop_hit_price
        else:
            # For short positions, check if price went above stop
            stop_hit = (hist_data['High'] >= stop_price).any()
            if stop_hit:
                # Find the first time the stop was hit
                stop_hit_idx = (hist_data['High'] >= stop_price).idxmax()
                stop_hit_price = hist_data.loc[stop_hit_idx, 'High']
                return True, stop_hit_price
        
        return False, 0.0
        
    except Exception as e:
        print(f"Error checking stop hit for {stock}: {e}")
        return False, 0.0

# Close an open position
def close_position(df, stock, price_at_close):
    # Find the last open position for this stock
    open_mask = (df['stocks_in_positions'] == stock) & (df['open_positions'] == 1.0)
    if not open_mask.any():
        raise ValueError(f"No open position found for stock {stock}")
    idx = df[open_mask].index[-1]
    amount_invested = df.at[idx, 'amount_invested']
    price_at_entry = df.at[idx, 'stock_price_at_entry']
    side = df.at[idx, 'side'] if 'side' in df.columns else 'buy'
    shares = amount_invested / price_at_entry if price_at_entry != 0 else 0
    # Check if stop was hit during the position
    stop_hit, stop_hit_price = check_stop_hit(df, stock)
    # Use stop price if it was hit, otherwise use closing price
    if stop_hit:
        actual_close_price = stop_hit_price
        df.at[idx, 'stop_hit'] = True
        df.at[idx, 'stop_hit_price'] = stop_hit_price
    else:
        actual_close_price = price_at_close
        df.at[idx, 'stop_hit'] = False
        df.at[idx, 'stop_hit_price'] = np.nan
    # Calculate value at close and gain/loss
    if side == 'buy':
        value_at_close = shares * actual_close_price
        gain_loss = amount_invested * (actual_close_price / price_at_entry - 1)
    else:  # sell/short
        value_at_close = shares * actual_close_price
        gain_loss = amount_invested * (1 - actual_close_price / price_at_entry)
    gain_loss_percent = (gain_loss / amount_invested) * 100 if amount_invested != 0 else 0
    # Update the closed position fields
    df.at[idx, 'stock_price_at_close'] = actual_close_price
    df.at[idx, 'net_gain_loss_amount'] = gain_loss
    df.at[idx, 'net_gain_loss_percent'] = gain_loss_percent
    df.at[idx, 'open_positions'] = 0.0
    # Update equity
    last_equity = df['equity'].iloc[-1]
    # Only add/subtract the gain/loss, not the full value_at_close
    new_equity = last_equity + gain_loss
    new_row = {f: np.nan for f in FIELDS}
    new_row_df = pd.DataFrame([new_row])
    new_row_df['side'] = str(side)
    new_row_df['equity'] = float(new_equity)
    df = pd.concat([df, new_row_df], ignore_index=True)
    save_trading_df(df)
    return df 