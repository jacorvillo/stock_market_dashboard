import json
import os

WATCHLIST_FILE = 'watchlist.json'

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_watchlist(watchlist):
    try:
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(watchlist, f, indent=2)
    except Exception as e:
        print(f"Error saving watchlist: {e}")

def add_to_watchlist(symbol):
    watchlist = load_watchlist()
    symbol = symbol.strip().upper()
    if symbol and symbol not in watchlist:
        watchlist.append(symbol)
        save_watchlist(watchlist)
    return watchlist

def remove_from_watchlist(symbol):
    watchlist = load_watchlist()
    symbol = symbol.strip().upper()
    if symbol in watchlist:
        watchlist.remove(symbol)
        save_watchlist(watchlist)
    return watchlist 