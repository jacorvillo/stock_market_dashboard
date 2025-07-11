"""
backtesting_functions.py
Functions and classes to support the Backtesting tab/game feature.
"""

import pandas as pd
from datetime import datetime, timedelta
from analysis_functions import get_stock_data

# --- State Management ---
def initialize_backtesting_state():
    """
    Initialize or reset the backtesting state (cash, positions, history, etc.).
    Returns a dictionary representing the initial state.
    """
    return {
        'cash': 1000.0,
        'position': None,  # None or dict with keys: type, entry_price, quantity, stop_loss, entry_date
        'history': [],     # List of closed trades
        'current_date': None,  # The current date in the simulation
        'stock': None,     # The selected stock symbol
        'data': None       # Cached DataFrame of stock data for the session
    }

# --- Data Slicing ---
def get_data_up_to_date(stock_symbol, end_date):
    """
    Return historical stock data for the given symbol up to (and including) end_date.
    Uses get_stock_data from analysis_functions.
    """
    # Fetch 1y of data for flexibility, then slice
    data_tuple = get_stock_data(stock_symbol, period="1y")
    if isinstance(data_tuple, tuple):
        df = data_tuple[0]
    else:
        df = data_tuple
    if df is None or df.empty:
        return pd.DataFrame()
    df = df[df['Date'] <= pd.to_datetime(end_date)]
    return df.copy()

# --- Order Handling ---
def place_order(state, order_type, price, quantity, stop_loss=None):
    """
    Place a buy or sell order, update state accordingly.
    order_type: 'buy' or 'sell'
    price: execution price
    quantity: number of shares
    stop_loss: optional stop loss price
    Returns updated state.
    """
    if state['position'] is not None:
        raise ValueError("Position already open. Close it before placing a new order.")
    cost = price * quantity
    if order_type == 'buy':
        if cost > state['cash']:
            raise ValueError("Not enough cash to buy.")
        state['cash'] -= cost
    elif order_type == 'sell':
        # For short selling, allow negative cash (margin)
        state['cash'] += cost
    else:
        raise ValueError("Invalid order type.")
    state['position'] = {
        'type': order_type,
        'entry_price': price,
        'quantity': quantity,
        'stop_loss': stop_loss,
        'entry_date': state['current_date']
    }
    return state

# --- Position Management ---
def advance_day(state):
    """
    Advance the simulation by one day, updating state and checking for stop loss triggers.
    Returns updated state.
    """
    if state['data'] is None or state['current_date'] is None:
        raise ValueError("No data or current date set.")
    df = state['data']
    current_dt = pd.to_datetime(state['current_date'])
    # Find the next available date in the data
    future_dates = df[df['Date'] > current_dt]['Date']
    if future_dates.empty:
        raise ValueError("No more data to advance.")
    next_date = future_dates.iloc[0]
    state['current_date'] = next_date
    # Check stop loss if position is open
    if state['position'] is not None and state['position']['stop_loss'] is not None:
        row = df[df['Date'] == next_date]
        if not row.empty:
            low = row['Low'].values[0]
            high = row['High'].values[0]
            pos = state['position']
            if pos['type'] == 'buy' and low <= pos['stop_loss']:
                # Stop loss hit for long
                state = close_position(state, pos['stop_loss'])
            elif pos['type'] == 'sell' and high >= pos['stop_loss']:
                # Stop loss hit for short
                state = close_position(state, pos['stop_loss'])
    return state

def close_position(state, close_price):
    """
    Close the current open position at the given price, update cash and history.
    Returns updated state.
    """
    pos = state['position']
    if pos is None:
        raise ValueError("No open position to close.")
    pnl = calculate_pnl(pos['entry_price'], close_price, pos['quantity'], pos['type'])
    if pos['type'] == 'buy':
        state['cash'] += close_price * pos['quantity']
    elif pos['type'] == 'sell':
        state['cash'] -= close_price * pos['quantity']
    # Record trade history
    trade = pos.copy()
    trade['exit_price'] = close_price
    trade['exit_date'] = state['current_date']
    trade['pnl'] = pnl
    state['history'].append(trade)
    state['position'] = None
    return state

# --- Utility ---
def calculate_pnl(entry_price, exit_price, quantity, order_type):
    """
    Calculate profit and loss for a closed position.
    order_type: 'buy' or 'sell'
    """
    if order_type == 'buy':
        return (exit_price - entry_price) * quantity
    elif order_type == 'sell':
        return (entry_price - exit_price) * quantity
    else:
        raise ValueError("Invalid order type for P&L calculation.") 