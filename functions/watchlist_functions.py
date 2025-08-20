import json
import os

WATCHLIST_FILE = 'watchlist.json'

def load_watchlist():
    """Load watchlist from file. Returns dict with symbols as keys and intent ('buy'/'sell') as values."""
    if not os.path.exists(WATCHLIST_FILE):
        return {}
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            data = json.load(f)
        # Handle backwards compatibility with old list format
        if isinstance(data, list):
            # Convert old list format to new dict format (default to 'buy')
            return {symbol: 'buy' for symbol in data}
        return data
    except Exception:
        return {}

def save_watchlist(watchlist):
    """Save watchlist to file. Expects dict format."""
    try:
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(watchlist, f, indent=2)
    except Exception as e:
        print(f"Error saving watchlist: {e}")

def add_to_watchlist(symbol, intent='buy'):
    """Add symbol to watchlist with buy/sell intent."""
    watchlist = load_watchlist()
    symbol = symbol.strip().upper()
    intent = intent.lower() if intent in ['buy', 'sell'] else 'buy'
    
    if symbol:
        watchlist[symbol] = intent
        save_watchlist(watchlist)
    return watchlist

def remove_from_watchlist(symbol):
    """Remove symbol from watchlist."""
    watchlist = load_watchlist()
    symbol = symbol.strip().upper()
    if symbol in watchlist:
        del watchlist[symbol]
        save_watchlist(watchlist)
    return watchlist

def get_watchlist_symbols():
    """Get list of symbols from watchlist (for backwards compatibility)."""
    watchlist = load_watchlist()
    return list(watchlist.keys())

def get_watchlist_intent(symbol):
    """Get the intent (buy/sell) for a specific symbol."""
    watchlist = load_watchlist()
    symbol = symbol.strip().upper()
    return watchlist.get(symbol, None) 