import pandas as pd
import numpy as np
import yfinance as yf

CSV_FILE = 'equity_data.csv'

FIELDS = [
    'equity',
    'open_positions',
    'amount_invested',
    'side',  # New field to store buy/sell
    'stop_price',
    'value_at_entry',
    'stocks_in_positions',
    'stock_price_at_entry',
    'stock_price_at_close',
    'net_gain_loss_amount',
    'net_gain_loss_percent',
    'target_price',
    'stop_hit',  # New field to track if stop was hit
    'stop_hit_price',  # New field to store the price when stop was hit
]

def load_trading_df():
    return pd.read_csv(CSV_FILE)

def save_trading_df(df):
    df.to_csv(CSV_FILE, index=False)

# Open a new position (buy or sell)
def open_position(df, stock, amount, price_at_entry, stop_price, target_price, side):
    last_equity = df['equity'].iloc[-1]
    new_row = {f: np.nan for f in FIELDS}
    if side == 'buy':
        new_equity = last_equity - amount
    else:  # sell/short
        new_equity = last_equity + amount
    new_row['equity'] = new_equity
    new_row['open_positions'] = 1.0
    new_row['amount_invested'] = amount
    new_row['side'] = side
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
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
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
        gain_loss = value_at_close - amount_invested
    else:  # sell/short
        value_at_close = shares * (2 * price_at_entry - actual_close_price)
        gain_loss = amount_invested - value_at_close
    gain_loss_percent = (gain_loss / amount_invested) * 100 if amount_invested != 0 else 0
    # Update the closed position fields
    df.at[idx, 'stock_price_at_close'] = actual_close_price
    df.at[idx, 'net_gain_loss_amount'] = gain_loss
    df.at[idx, 'net_gain_loss_percent'] = gain_loss_percent
    df.at[idx, 'open_positions'] = 0.0
    # Update equity
    last_equity = df['equity'].iloc[-1]
    if side == 'buy':
        new_equity = last_equity + value_at_close
    else:
        new_equity = last_equity - value_at_close
    new_row = {f: np.nan for f in FIELDS}
    new_row['equity'] = new_equity
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_trading_df(df)
    return df 