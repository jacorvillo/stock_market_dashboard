import pandas as pd
import numpy as np

CSV_FILE = 'equity_data.csv'

FIELDS = [
    'equity',
    'open_positions',
    'amount_invested',
    'stop_price',
    'value_at_entry',
    'stocks_in_positions',
    'stock_price_at_entry',
    'stock_price_at_close',
    'net_gain_loss_amount',
    'net_gain_loss_percent',
    'target_price',
]

def load_trading_df():
    return pd.read_csv(CSV_FILE)

def save_trading_df(df):
    df.to_csv(CSV_FILE, index=False)

# Open a new position (buy or sell)
def open_position(df, stock, amount, price_at_entry, stop_price, target_price):
    last_equity = df['equity'].iloc[-1]
    new_equity = last_equity - amount
    new_row = {f: np.nan for f in FIELDS}
    new_row['equity'] = new_equity
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
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_trading_df(df)
    return df

# Close an open position
def close_position(df, stock, price_at_close):
    # Find the last open position for this stock
    open_mask = (df['stocks_in_positions'] == stock) & (df['open_positions'] == 1.0)
    if not open_mask.any():
        raise ValueError(f"No open position found for stock {stock}")
    idx = df[open_mask].index[-1]
    amount_invested = df.at[idx, 'amount_invested']
    price_at_entry = df.at[idx, 'stock_price_at_entry']
    shares = amount_invested / price_at_entry if price_at_entry != 0 else 0
    value_at_close = shares * price_at_close
    gain_loss = value_at_close - amount_invested
    gain_loss_percent = (gain_loss / amount_invested) * 100 if amount_invested != 0 else 0
    # Update the closed position fields
    df.at[idx, 'stock_price_at_close'] = price_at_close
    df.at[idx, 'net_gain_loss_amount'] = gain_loss
    df.at[idx, 'net_gain_loss_percent'] = gain_loss_percent
    df.at[idx, 'open_positions'] = 0.0
    # Update equity
    last_equity = df['equity'].iloc[-1]
    new_equity = last_equity + value_at_close
    new_row = {f: np.nan for f in FIELDS}
    new_row['equity'] = new_equity
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_trading_df(df)
    return df 