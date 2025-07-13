"""
Stock Scanner Functions for Technical Analysis Dashboard
Based on Dr. Alexander Elder's Trading Methods

This module provides comprehensive stock scanning functiona            # Calculate ATR (13-period for consistency)
            tr1 = high_prices - low_prices
            tr2 = abs(high_prices - close_prices.shift(1))
            tr3 = abs(low_prices - close_prices.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=13).mean()ith
technical indicator filters and market universe management.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import random

# Import technical analysis functions from existing functions.py
from .analysis_functions import calculate_indicators

class StockScanner:
    def __init__(self, cache_file='scanner_cache.json'):
        self.cache_file = cache_file
        self.update_threshold_hours = 4  # Update every 4 hours during market hours
        self.universe = self._get_stock_universe()
        self.max_workers = 8  # Reasonable thread pool size
        
    def _get_stock_universe(self):
        """Get comprehensive stock universe for scanning"""
        return {
            'sp500': [
                # Large Cap S&P 500 stocks - Top 100 by market cap
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'UNH',
                'LLY', 'JNJ', 'V', 'XOM', 'JPM', 'WMT', 'PG', 'MA', 'ORCL', 'HD',
                'CVX', 'ABBV', 'BAC', 'ASML', 'CRM', 'KO', 'AVGO', 'PEP', 'TMO', 'COST',
                'MRK', 'NFLX', 'ACN', 'ADBE', 'LIN', 'ABT', 'CSCO', 'DHR', 'VZ', 'NKE',
                'TXN', 'DIS', 'WFC', 'NEE', 'COP', 'RTX', 'PM', 'SPGI', 'UNP', 'T',
                'BMY', 'SCHW', 'HON', 'LOW', 'AXP', 'QCOM', 'IBM', 'UPS', 'ELV', 'BLK',
                'GS', 'PLD', 'MDT', 'AMD', 'CAT', 'SBUX', 'INTU', 'GILD', 'DE', 'TJX',
                'AMT', 'GE', 'BKNG', 'ADP', 'MDLZ', 'CVS', 'CI', 'MMC', 'SYK', 'VRTX',
                'MO', 'ZTS', 'CB', 'SO', 'DUK', 'PGR', 'CL', 'TMUS', 'ITW', 'EOG',
                'BSX', 'FDX', 'EMR', 'AON', 'CSX', 'NSC', 'REGN', 'APD', 'PNC', 'GM'
            ],
            'nasdaq100': [
                # NASDAQ 100 tech/growth focused
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE',
                'CRM', 'ORCL', 'CSCO', 'INTC', 'QCOM', 'AMD', 'INTU', 'MU', 'AMAT', 'LRCX',
                'KLAC', 'MRVL', 'SNPS', 'CDNS', 'FTNT', 'TEAM', 'WDAY', 'DDOG', 'CRWD', 'ZM',
                'DOCU', 'OKTA', 'SPLK', 'MDB', 'NET', 'DXCM', 'ILMN', 'BIIB', 'GILB', 'MRNA'
            ],
            'dow30': [
                # Dow Jones 30 Industrial Average
                'AAPL', 'MSFT', 'UNH', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'HD', 'CVX',
                'MRK', 'AXP', 'BA', 'IBM', 'CAT', 'GS', 'MCD', 'DIS', 'MMM', 'TRV',
                'NKE', 'KO', 'HON', 'CRM', 'AMGN', 'VZ', 'WBA', 'CSCO', 'DOW', 'INTC'
            ],
            'etfs': [
                # Popular ETFs for market exposure
                'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'BND', 'VYM', 'VTEB',
                'XLE', 'XLF', 'XLK', 'XLV', 'XLI', 'XLC', 'XLRE', 'XLP', 'XLU', 'XLB', 'XLY',
                'GLD', 'SLV', 'USO', 'TLT', 'HYG', 'LQD', 'EEM', 'FXI', 'EWJ', 'EFA'
            ],
            'growth': [
                # High-growth technology and innovative companies
                'TSLA', 'NVDA', 'AMD', 'NFLX', 'CRM', 'ADBE', 'PYPL', 'SQ', 'SHOP', 'ROKU',
                'ZM', 'DOCU', 'OKTA', 'CRWD', 'DDOG', 'SNOW', 'NET', 'PLTR', 'COIN', 'RBLX',
                'U', 'TWLO', 'FSLY', 'ESTC', 'DKNG', 'PENN', 'BYND', 'TDOC', 'PTON', 'MRNA',
                'BNTX', 'ZEN', 'BILL', 'SMAR', 'FROG', 'AI', 'SMCI', 'AVAV', 'SEDG', 'PLUG'
            ],
            'dividend': [
                # Dividend-focused stable companies
                'JNJ', 'PG', 'KO', 'PEP', 'WMT', 'MCD', 'VZ', 'T', 'XOM', 'CVX',
                'PM', 'MO', 'SO', 'DUK', 'NEE', 'D', 'AEP', 'EXC', 'SRE', 'PEG',
                'O', 'STOR', 'WPC', 'NNN', 'ADC', 'STAG', 'EPR', 'GOOD', 'SRC', 'VICI'
            ],
            'spanish': [
                # Spanish stocks (IBEX 35, main .MC tickers) - Updated comprehensive list
                'SAN.MC', 'BBVA.MC', 'ITX.MC', 'IBE.MC', 'REP.MC', 'TEF.MC', 'AMS.MC', 'AENA.MC',
                'ANA.MC', 'CABK.MC', 'CLNX.MC', 'COL.MC', 'ENG.MC', 'FER.MC', 'GRF.MC', 'IAG.MC',
                'MAP.MC', 'MEL.MC', 'MRL.MC', 'NTGY.MC', 'PHM.MC', 'RED.MC', 'SGRE.MC', 'SLR.MC',
                'SAB.MC', 'ACS.MC', 'ALM.MC', 'BKT.MC', 'CIE.MC', 'ELE.MC', 'LOG.MC', 'VIS.MC',
                # Additional IBEX 35 stocks
                'ACX.MC', 'ACR.MC', 'ACS.MC', 'AENA.MC', 'AMS.MC', 'ANA.MC', 'BBVA.MC', 'BKT.MC',
                'CABK.MC', 'CIE.MC', 'CLNX.MC', 'COL.MC', 'ELE.MC', 'ENG.MC', 'FER.MC', 'GRF.MC',
                'IAG.MC', 'IBE.MC', 'ITX.MC', 'LOG.MC', 'MAP.MC', 'MEL.MC', 'MRL.MC', 'NTGY.MC',
                'PHM.MC', 'RED.MC', 'REP.MC', 'SAB.MC', 'SAN.MC', 'SGRE.MC', 'SLR.MC', 'TEF.MC',
                'VIS.MC', 'ZAL.MC'
            ],
            'spanish_indices': [
                # Spanish indices and ETFs (as available on Yahoo Finance)
                '^IBEX', 'EWP', 'ES35.MI', 'IBEX.MC', 'BME.MC', 'XES.MC'
            ]
        }
    
    def _load_cache(self):
        """Load existing scanner data from cache file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Convert to DataFrame with proper date handling
                df = pd.DataFrame(cache_data['data'])
                df['last_updated'] = pd.to_datetime(df['last_updated'])
                return df, cache_data.get('last_full_update', None)
            except Exception as e:
                print(f"Error loading cache: {e}")
                return pd.DataFrame(), None
        return pd.DataFrame(), None
    
    def _save_cache(self, df):
        """Save scanner data to cache file"""
        try:
            # Convert DataFrame to serializable format
            cache_data = {
                'data': df.to_dict('records'),
                'last_full_update': datetime.now().isoformat(),
                'total_symbols': len(df),
                'universe_info': {k: len(v) for k, v in self.universe.items()}
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            print(f"Cache saved with {len(df)} symbols")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _needs_update(self):
        """Check if cache needs updating based on time threshold"""
        if not os.path.exists(self.cache_file):
            return True
            
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            last_updated_str = cache_data.get('last_full_update', '2000-01-01')
            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            hours_since_update = (datetime.now() - last_updated).total_seconds() / 3600
            
            return hours_since_update > self.update_threshold_hours
        except Exception as e:
            print(f"Error checking cache age: {e}")
            return True
    
    def _calculate_indicators_for_symbol(self, symbol, period='6mo'):
        """Calculate all technical indicators for a single symbol"""
        try:
            # Create a fresh ticker object for thread safety
            ticker = yf.Ticker(symbol)
            
            # Special handling for Spanish stocks - they may have different data availability
            if symbol.endswith('.MC'):
                # Spanish stocks might need longer period for sufficient data
                data = ticker.history(period='1y')  # Use 1 year for Spanish stocks
            else:
                data = ticker.history(period=period)
            
            # Check if data is valid
            if data is None or len(data) == 0 or len(data) < 30:  # Reduced minimum for Spanish stocks
                return None
            
            # Handle MultiIndex columns (when downloading single symbol, yfinance sometimes returns MultiIndex)
            if isinstance(data.columns, pd.MultiIndex):
                # Flatten MultiIndex columns by taking the first level (the price type)
                data.columns = data.columns.droplevel(1)
            
            # Calculate basic indicators using existing functions
            # Note: We'll use simplified calculations here for speed
            close_prices = data['Close'].dropna()
            volume = data['Volume'].dropna()
            high_prices = data['High'].dropna()
            low_prices = data['Low'].dropna()
            
            if len(close_prices) < 20:  # Reduced minimum for Spanish stocks
                return None
            
            # Calculate EMAs
            ema_13 = pd.Series(close_prices.ewm(span=13, adjust=False).mean(), index=close_prices.index)
            ema_26 = pd.Series(close_prices.ewm(span=26, adjust=False).mean(), index=close_prices.index)
            
            # Calculate RSI (13-period)
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=13).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=13).mean()
            rs = gain / loss
            rsi = pd.Series(100 - (100 / (1 + rs)), index=close_prices.index)
            
            # Calculate MACD
            ema_12 = close_prices.ewm(span=12, adjust=False).mean()
            macd_line = pd.Series(ema_12 - ema_26, index=close_prices.index)
            signal_line = pd.Series(macd_line.ewm(span=9, adjust=False).mean(), index=close_prices.index)
            histogram = pd.Series(macd_line - signal_line, index=close_prices.index)
            
            # Calculate ATR (13-period for consistency)
            tr1 = high_prices - low_prices
            tr2 = abs(high_prices - close_prices.shift(1))
            tr3 = abs(low_prices - close_prices.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = pd.Series(true_range.rolling(window=13).mean(), index=close_prices.index)
            
            # Get latest values with explicit scalar conversion
            latest = data.iloc[-1]
            latest_close = float(latest['Close'])
            latest_volume = int(float(latest['Volume'])) if not pd.isna(latest['Volume']) else 0
            latest_ema_13 = float(ema_13.iloc[-1]) if not ema_13.empty and not pd.isna(ema_13.iloc[-1]) else np.nan
            latest_ema_26 = float(ema_26.iloc[-1]) if not ema_26.empty and not pd.isna(ema_26.iloc[-1]) else np.nan
            latest_rsi = float(rsi.iloc[-1]) if not rsi.empty and not pd.isna(rsi.iloc[-1]) else np.nan
            latest_macd = float(macd_line.iloc[-1]) if not macd_line.empty and not pd.isna(macd_line.iloc[-1]) else np.nan
            latest_signal = float(signal_line.iloc[-1]) if not signal_line.empty and not pd.isna(signal_line.iloc[-1]) else np.nan
            latest_atr = float(atr.iloc[-1]) if not atr.empty and not pd.isna(atr.iloc[-1]) else np.nan
            latest_histogram = float(histogram.iloc[-1]) if not histogram.empty and not pd.isna(histogram.iloc[-1]) else np.nan
            
            # Calculate price change
            if len(close_prices) >= 2:
                price_change_pct = float(((latest_close - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100)
            else:
                price_change_pct = 0.0
            
            # Calculate average volume (20-day)
            if len(volume) >= 20:
                avg_volume_20 = volume.rolling(window=20).mean()
                if isinstance(avg_volume_20, pd.Series) and not avg_volume_20.empty:
                    avg_volume_20_value = float(avg_volume_20.iloc[-1]) if not pd.isna(avg_volume_20.iloc[-1]) else float(latest_volume)
                else:
                    avg_volume_20_value = float(latest_volume)
            else:
                avg_volume_20_value = float(latest_volume)
            volume_vs_avg = (float(latest_volume) / avg_volume_20_value) if avg_volume_20_value > 0 else 1.0
            
            # Detect divergences using MACD histogram for more accurate detection
            divergences = self._detect_divergences(close_prices, rsi, histogram)
            
            # Detect RSI extremes
            rsi_extreme = self._detect_rsi_extremes(rsi)
            
            # Build scanner result
            scanner_data = {
                'symbol': symbol,
                'price': round(latest_close, 2),
                'volume': latest_volume,
                'volume_vs_avg': round(volume_vs_avg, 2),
                'ema_13': round(latest_ema_13, 2) if not pd.isna(latest_ema_13) else None,
                'ema_26': round(latest_ema_26, 2) if not pd.isna(latest_ema_26) else None,
                'in_value_zone': self._check_value_zone(latest_close, latest_ema_13, latest_ema_26),
                'above_ema_13': latest_close > latest_ema_13 if not pd.isna(latest_ema_13) else False,
                'above_ema_26': latest_close > latest_ema_26 if not pd.isna(latest_ema_26) else False,
                'ema_trend': 'bullish' if (not pd.isna(latest_ema_13) and not pd.isna(latest_ema_26) and latest_ema_13 > latest_ema_26) else 'bearish',
                'rsi': round(latest_rsi, 2) if not pd.isna(latest_rsi) else None,
                'rsi_extreme': rsi_extreme,
                'macd_signal': self._get_macd_signal(latest_macd, latest_signal),
                'macd_divergence': divergences['macd_divergence'],
                'rsi_divergence': divergences['rsi_divergence'],
                'atr_pct': round((latest_atr / latest_close) * 100, 2) if not pd.isna(latest_atr) else None,
                'price_change_pct': round(price_change_pct, 2),
                'last_updated': datetime.now().isoformat()
            }
            
            return scanner_data
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            return None
    
    def _check_value_zone(self, price, ema_13, ema_26):
        """Check if price is in Value Zone between EMAs"""
        if pd.isna(ema_13) or pd.isna(ema_26) or pd.isna(price):
            return False
        
        upper_ema = max(ema_13, ema_26)
        lower_ema = min(ema_13, ema_26)
        return lower_ema <= price <= upper_ema
    
    def _get_macd_signal(self, macd_line, signal_line):
        """Get simplified MACD signal"""
        if pd.isna(macd_line) or pd.isna(signal_line):
            return 'neutral'
        
        if macd_line > signal_line:
            return 'bullish'
        else:
            return 'bearish'
    
    def _detect_divergences(self, close_prices, rsi, macd_line, lookback=50):
        """
        Enhanced divergence detection based on research criteria
        
        Research shows most tradable divergences occur when distance between 
        two peaks/bottoms of MACD-H is between 20-40 bars, closer to 20 being better.
        """
        if len(close_prices) < lookback:
            return {'macd_divergence': 'none', 'rsi_divergence': 'none'}
        
        # Get recent data for analysis
        recent_close = close_prices.tail(lookback)
        recent_rsi = rsi.tail(lookback) if rsi is not None and len(rsi) >= lookback else None
        recent_macd = macd_line.tail(lookback) if macd_line is not None and len(macd_line) >= lookback else None
        
        divergences = {'macd_divergence': 'none', 'rsi_divergence': 'none'}
        
        # Enhanced MACD Divergence Detection
        if recent_macd is not None and not recent_macd.isna().all():
            macd_div = self._detect_macd_divergence_enhanced(recent_close, recent_macd)
            divergences['macd_divergence'] = macd_div
        
        # RSI Divergence Detection (enhanced to match MACD approach)
        if recent_rsi is not None and not recent_rsi.isna().all():
            rsi_div = self._detect_rsi_divergence_enhanced(recent_close, recent_rsi)
            divergences['rsi_divergence'] = rsi_div
        
        return divergences
    
    def _detect_macd_divergence_enhanced(self, close_prices, macd_histogram):
        """
        Enhanced MACD divergence detection based on research criteria
        
        Research shows most tradable divergences occur when distance between 
        two peaks/bottoms of MACD-H is between 20-40 bars, closer to 20 being better.
        
        Looks for:
        1. Two peaks or two bottoms in MACD-H (histogram)
        2. Distance between peaks/bottoms: 20-40 bars (optimal 20-30)
        3. Price making higher highs while MACD-H makes lower highs (bearish divergence)
        4. Price making lower lows while MACD-H makes higher lows (bullish divergence)
        """
        try:
            # Use MACD histogram (MACD-H) for divergence detection as per research
            # Find peaks and troughs in MACD histogram
            macd_peaks = self._find_peaks(macd_histogram, prominence=0.0001)  # Lower prominence for histogram
            macd_troughs = self._find_troughs(macd_histogram, prominence=0.0001)
            
            # Find peaks and troughs in price
            price_peaks = self._find_peaks(close_prices, prominence=0.01)
            price_troughs = self._find_troughs(close_prices, prominence=0.01)
            
            # Check for bearish divergence (price higher highs, MACD-H lower highs)
            if len(macd_peaks) >= 2 and len(price_peaks) >= 2:
                # Get the two most recent peaks
                recent_macd_peaks = sorted(macd_peaks)[-2:]
                recent_price_peaks = sorted(price_peaks)[-2:]
                
                # Check distance between MACD peaks (should be 20-40 bars, optimal 20-30)
                macd_peak_distance = abs(recent_macd_peaks[1] - recent_macd_peaks[0])
                
                # Additional validation: ensure peaks are recent enough (within last 50 bars)
                max_recent_peak = max(recent_macd_peaks)
                if max_recent_peak >= len(macd_histogram) - 10:  # Peak should be within last 10 bars
                    if 20 <= macd_peak_distance <= 40:  # Optimal range per research
                        # Check if price made higher high while MACD-H made lower high
                        price_higher = close_prices.iloc[recent_price_peaks[1]] > close_prices.iloc[recent_price_peaks[0]]
                        macd_lower = macd_histogram.iloc[recent_macd_peaks[1]] < macd_histogram.iloc[recent_macd_peaks[0]]
                        
                        # Additional validation: ensure the divergence is significant
                        price_change_pct = abs(close_prices.iloc[recent_price_peaks[1]] - close_prices.iloc[recent_price_peaks[0]]) / close_prices.iloc[recent_price_peaks[0]] * 100
                        macd_change_pct = abs(macd_histogram.iloc[recent_macd_peaks[1]] - macd_histogram.iloc[recent_macd_peaks[0]]) / abs(macd_histogram.iloc[recent_macd_peaks[0]]) * 100 if macd_histogram.iloc[recent_macd_peaks[0]] != 0 else 0
                        
                        if price_higher and macd_lower and price_change_pct > 1.0 and macd_change_pct > 5.0:
                            return 'bearish'
            
            # Check for bullish divergence (price lower lows, MACD-H higher lows)
            if len(macd_troughs) >= 2 and len(price_troughs) >= 2:
                # Get the two most recent troughs
                recent_macd_troughs = sorted(macd_troughs)[-2:]
                recent_price_troughs = sorted(price_troughs)[-2:]
                
                # Check distance between MACD troughs (should be 20-40 bars, optimal 20-30)
                macd_trough_distance = abs(recent_macd_troughs[1] - recent_macd_troughs[0])
                
                # Additional validation: ensure troughs are recent enough (within last 50 bars)
                max_recent_trough = max(recent_macd_troughs)
                if max_recent_trough >= len(macd_histogram) - 10:  # Trough should be within last 10 bars
                    if 20 <= macd_trough_distance <= 40:  # Optimal range per research
                        # Check if price made lower low while MACD-H made higher low
                        price_lower = close_prices.iloc[recent_price_troughs[1]] < close_prices.iloc[recent_price_troughs[0]]
                        macd_higher = macd_histogram.iloc[recent_macd_troughs[1]] > macd_histogram.iloc[recent_macd_troughs[0]]
                        
                        # Additional validation: ensure the divergence is significant
                        price_change_pct = abs(close_prices.iloc[recent_price_troughs[1]] - close_prices.iloc[recent_price_troughs[0]]) / close_prices.iloc[recent_price_troughs[0]] * 100
                        macd_change_pct = abs(macd_histogram.iloc[recent_macd_troughs[1]] - macd_histogram.iloc[recent_macd_troughs[0]]) / abs(macd_histogram.iloc[recent_macd_troughs[0]]) * 100 if macd_histogram.iloc[recent_macd_troughs[0]] != 0 else 0
                        
                        if price_lower and macd_higher and price_change_pct > 1.0 and macd_change_pct > 5.0:
                            return 'bullish'
            
            return 'none'
            
        except Exception as e:
            print(f"Error in enhanced MACD divergence detection: {e}")
            return 'none'
    
    def _detect_rsi_divergence_enhanced(self, close_prices, rsi):
        """
        Enhanced RSI divergence detection based on research criteria
        
        Research shows most tradable divergences occur when distance between 
        two peaks/bottoms of RSI is between 20-40 bars, closer to 20 being better.
        
        Looks for:
        1. Two peaks or two bottoms in RSI
        2. Distance between peaks/bottoms: 20-40 bars (optimal 20-30)
        3. Price making higher highs while RSI makes lower highs (bearish divergence)
        4. Price making lower lows while RSI makes higher lows (bullish divergence)
        """
        try:
            # Find peaks and troughs in RSI
            rsi_peaks = self._find_peaks(rsi, prominence=0.001)
            rsi_troughs = self._find_troughs(rsi, prominence=0.001)
            
            # Find peaks and troughs in price
            price_peaks = self._find_peaks(close_prices, prominence=0.01)
            price_troughs = self._find_troughs(close_prices, prominence=0.01)
            
            # Check for bearish divergence (price higher highs, RSI lower highs)
            if len(rsi_peaks) >= 2 and len(price_peaks) >= 2:
                # Get the two most recent peaks
                recent_rsi_peaks = sorted(rsi_peaks)[-2:]
                recent_price_peaks = sorted(price_peaks)[-2:]
                
                # Check distance between RSI peaks (should be 20-40 bars, optimal 20-30)
                rsi_peak_distance = abs(recent_rsi_peaks[1] - recent_rsi_peaks[0])
                
                # Additional validation: ensure peaks are recent enough (within last 50 bars)
                max_recent_rsi_peak = max(recent_rsi_peaks)
                if max_recent_rsi_peak >= len(rsi) - 10:  # Peak should be within last 10 bars
                    if 20 <= rsi_peak_distance <= 40:  # Optimal range per research
                        # Check if price made higher high while RSI made lower high
                        price_higher = close_prices.iloc[recent_price_peaks[1]] > close_prices.iloc[recent_price_peaks[0]]
                        rsi_lower = rsi.iloc[recent_rsi_peaks[1]] < rsi.iloc[recent_rsi_peaks[0]]
                        
                        # Additional validation: ensure the divergence is significant
                        price_change_pct = abs(close_prices.iloc[recent_price_peaks[1]] - close_prices.iloc[recent_price_peaks[0]]) / close_prices.iloc[recent_price_peaks[0]] * 100
                        rsi_change_pct = abs(rsi.iloc[recent_rsi_peaks[1]] - rsi.iloc[recent_rsi_peaks[0]]) / abs(rsi.iloc[recent_rsi_peaks[0]]) * 100 if rsi.iloc[recent_rsi_peaks[0]] != 0 else 0
                        
                        if price_higher and rsi_lower and price_change_pct > 1.0 and rsi_change_pct > 5.0:
                            return 'bearish'
            
            # Check for bullish divergence (price lower lows, RSI higher lows)
            if len(rsi_troughs) >= 2 and len(price_troughs) >= 2:
                # Get the two most recent troughs
                recent_rsi_troughs = sorted(rsi_troughs)[-2:]
                recent_price_troughs = sorted(price_troughs)[-2:]
                
                # Check distance between RSI troughs (should be 20-40 bars, optimal 20-30)
                rsi_trough_distance = abs(recent_rsi_troughs[1] - recent_rsi_troughs[0])
                
                # Additional validation: ensure troughs are recent enough (within last 50 bars)
                max_recent_rsi_trough = max(recent_rsi_troughs)
                if max_recent_rsi_trough >= len(rsi) - 10:  # Trough should be within last 10 bars
                    if 20 <= rsi_trough_distance <= 40:  # Optimal range per research
                        # Check if price made lower low while RSI made higher low
                        price_lower = close_prices.iloc[recent_price_troughs[1]] < close_prices.iloc[recent_price_troughs[0]]
                        rsi_higher = rsi.iloc[recent_rsi_troughs[1]] > rsi.iloc[recent_rsi_troughs[0]]
                        
                        # Additional validation: ensure the divergence is significant
                        price_change_pct = abs(close_prices.iloc[recent_price_troughs[1]] - close_prices.iloc[recent_price_troughs[0]]) / close_prices.iloc[recent_price_troughs[0]] * 100
                        rsi_change_pct = abs(rsi.iloc[recent_rsi_troughs[1]] - rsi.iloc[recent_rsi_troughs[0]]) / abs(rsi.iloc[recent_rsi_troughs[0]]) * 100 if rsi.iloc[recent_rsi_troughs[0]] != 0 else 0
                        
                        if price_lower and rsi_higher and price_change_pct > 1.0 and rsi_change_pct > 5.0:
                            return 'bullish'
            
            return 'none'
            
        except Exception as e:
            print(f"Error in enhanced RSI divergence detection: {e}")
            return 'none'
    
    def _find_peaks(self, series, prominence=0.001):
        """
        Find peaks in a time series with minimum prominence
        
        Args:
            series: pandas Series with numeric values
            prominence: minimum prominence for a peak to be considered
            
        Returns:
            List of indices where peaks occur
        """
        peaks = []
        if len(series) < 3:
            return peaks
        
        for i in range(1, len(series) - 1):
            # Check if current point is higher than neighbors
            if series.iloc[i] > series.iloc[i-1] and series.iloc[i] > series.iloc[i+1]:
                # Calculate prominence (minimum drop on either side)
                left_drop = series.iloc[i] - series.iloc[i-1]
                right_drop = series.iloc[i] - series.iloc[i+1]
                min_drop = min(left_drop, right_drop)
                
                if min_drop >= prominence:
                    peaks.append(i)
        
        return peaks
    
    def _find_troughs(self, series, prominence=0.001):
        """
        Find troughs (valleys) in a time series with minimum prominence
        
        Args:
            series: pandas Series with numeric values
            prominence: minimum prominence for a trough to be considered
            
        Returns:
            List of indices where troughs occur
        """
        troughs = []
        if len(series) < 3:
            return troughs
        
        for i in range(1, len(series) - 1):
            # Check if current point is lower than neighbors
            if series.iloc[i] < series.iloc[i-1] and series.iloc[i] < series.iloc[i+1]:
                # Calculate prominence (minimum rise on either side)
                left_rise = series.iloc[i-1] - series.iloc[i]
                right_rise = series.iloc[i+1] - series.iloc[i]
                min_rise = min(left_rise, right_rise)
                
                if min_rise >= prominence:
                    troughs.append(i)
        
        return troughs
    
    def _detect_rsi_extremes(self, rsi):
        """Detect RSI overbought and oversold conditions"""
        if rsi is None or len(rsi) == 0 or rsi.isna().all():
            return 'neutral'
        
        latest_rsi = rsi.iloc[-1]
        if pd.isna(latest_rsi):
            return 'neutral'
        
        if latest_rsi >= 70:
            return 'overbought'
        elif latest_rsi <= 30:
            return 'oversold'
        else:
            return 'neutral'
    
    def _get_universe_symbols(self, selected_universes):
        """Get all symbols from selected universes"""
        all_symbols = []
        for universe in selected_universes:
            if universe in self.universe:
                all_symbols.extend(self.universe[universe])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        return unique_symbols
    
    def filter_spanish_stocks(self, symbols):
        """Filter a list of symbols to only those ending in .MC (Spanish stocks)"""
        return [s for s in symbols if s.endswith('.MC')]
    
    def filter_spanish_indices(self, symbols):
        """Filter a list of symbols to only those that are Spanish indices/ETFs (customize as needed)"""
        spanish_indices = set([
            '^IBEX', 'EWP', 'ES35.MI', 'IBEX.MC', 'BME.MC', 'XES.MC'
        ])
        return [s for s in symbols if s in spanish_indices]

    def _validate_spanish_symbol(self, symbol):
        """Validate if a Spanish stock symbol is likely to have data"""
        if not symbol.endswith('.MC'):
            return False
        
        # Common Spanish stock patterns that are more likely to have data
        valid_prefixes = ['SAN', 'BBVA', 'ITX', 'IBE', 'REP', 'TEF', 'AMS', 'AENA', 
                         'ANA', 'CABK', 'CLNX', 'COL', 'ENG', 'FER', 'GRF', 'IAG',
                         'MAP', 'MEL', 'MRL', 'NTGY', 'PHM', 'RED', 'SGRE', 'SLR',
                         'SAB', 'ACS', 'ALM', 'BKT', 'CIE', 'ELE', 'LOG', 'VIS',
                         'ACX', 'ACR', 'ZAL']
        
        symbol_prefix = symbol.replace('.MC', '')
        return symbol_prefix in valid_prefixes

    def _get_spanish_market_info(self, symbol):
        """Get additional market information for Spanish stocks"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant Spanish market information
            market_info = {
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'country': info.get('country', 'Spain')
            }
            
            return market_info
        except Exception as e:
            print(f"Error getting market info for {symbol}: {e}")
            return None

    def scan_stocks(self, filters=None, universes=None, max_results=50, sort_by='volume', random_sample=False):
        """
        Perform stock scan with filters
        
        Args:
            filters: Dictionary of filter criteria
            universes: List of universes to scan ['sp500', 'nasdaq100', etc.]
            max_results: Maximum number of results to return
            sort_by: How to sort results ('volume', 'change', 'rsi', 'random')
            random_sample: If True or int, return random sample instead of filtered results
        """
        
        if universes is None:
            universes = ['sp500']
        
        # Get symbols to scan
        symbols_to_scan = self._get_universe_symbols(universes)
        
        if not symbols_to_scan:
            return pd.DataFrame()
        
        # Special handling for Spanish stocks
        spanish_stocks_present = any('spanish' in universe for universe in universes)
        if spanish_stocks_present:
            print("Spanish stocks detected - applying enhanced validation and data handling")
            # Filter out potentially problematic Spanish symbols
            symbols_to_scan = [s for s in symbols_to_scan if not s.endswith('.MC') or self._validate_spanish_symbol(s)]
        
        print(f"Starting scan of {len(symbols_to_scan)} symbols from {universes}")
        
        # If random sample requested, just return random symbols
        if random_sample and isinstance(random_sample, int):
            random_symbols = random.sample(symbols_to_scan, min(random_sample, len(symbols_to_scan)))
            symbols_to_scan = random_symbols
            print(f"Random sample mode: scanning {len(symbols_to_scan)} random symbols")
        elif random_sample and isinstance(random_sample, bool) and random_sample:
            # If random_sample is True, use max_results as the sample size
            random_symbols = random.sample(symbols_to_scan, min(max_results, len(symbols_to_scan)))
            symbols_to_scan = random_symbols
            print(f"Random sample mode: scanning {len(symbols_to_scan)} random symbols")
        
        # Multi-threaded scanning for performance
        results = []
        completed = 0
        spanish_results = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_symbol = {
                executor.submit(self._calculate_indicators_for_symbol, symbol): symbol 
                for symbol in symbols_to_scan
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1
                
                try:
                    result = future.result(timeout=45)  # Increased timeout for Spanish stocks
                    if result:
                        results.append(result)
                        if symbol.endswith('.MC'):
                            spanish_results += 1
                    
                    # Progress update every 10 symbols
                    if completed % 10 == 0:
                        print(f"Processed {completed}/{len(symbols_to_scan)} symbols...")
                        if spanish_stocks_present:
                            print(f"Spanish stocks found so far: {spanish_results}")
                        
                except Exception as e:
                    print(f"Error with {symbol}: {e}")
                    continue
        
        if not results:
            print("No valid results found")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Apply filters if provided and not in random mode
        if filters and not random_sample:
            df = self._apply_filters(df, filters)
        
        # Sort results
        df = self._sort_results(df, sort_by)
        
        # Limit results
        if max_results and len(df) > max_results:
            df = df.head(max_results)
        
        # Save to cache
        self._save_cache(df)
        
        print(f"Scan complete: {len(df)} results after filtering")
        if spanish_stocks_present:
            spanish_final = len(df[df['symbol'].str.endswith('.MC')])
            print(f"Spanish stocks in final results: {spanish_final}")
        
        return df
    
    def _apply_filters(self, df, filters):
        """Apply user-defined filters to scanner results"""
        if df.empty:
            return df
            
        filtered_df = df.copy()
        
        try:
            # Value Zone filter
            if filters.get('value_zone_only'):
                filtered_df = filtered_df[filtered_df['in_value_zone'] == True]
            
            # EMA trend filter
            if filters.get('ema_trend') and filters['ema_trend'] != 'any':
                filtered_df = filtered_df[filtered_df['ema_trend'] == filters['ema_trend']]
            
            # Price above EMA filters
            if filters.get('above_ema_13'):
                filtered_df = filtered_df[filtered_df['above_ema_13'] == True]
            if filters.get('above_ema_26'):
                filtered_df = filtered_df[filtered_df['above_ema_26'] == True]
            
            # RSI range filter - only apply to stocks with valid RSI values
            if filters.get('rsi_min') is not None:
                filtered_df = filtered_df[
                    (filtered_df['rsi'].notna()) & (filtered_df['rsi'] >= filters['rsi_min'])
                ]
            if filters.get('rsi_max') is not None:
                filtered_df = filtered_df[
                    (filtered_df['rsi'].notna()) & (filtered_df['rsi'] <= filters['rsi_max'])
                ]
            
            # RSI extreme filter (overbought/oversold)
            if filters.get('rsi_extreme') and filters['rsi_extreme'] != 'any':
                filtered_df = filtered_df[filtered_df['rsi_extreme'] == filters['rsi_extreme']]
            
            # Divergence filters
            if filters.get('macd_divergence') and filters['macd_divergence'] != 'any':
                filtered_df = filtered_df[filtered_df['macd_divergence'] == filters['macd_divergence']]
            
            if filters.get('rsi_divergence') and filters['rsi_divergence'] != 'any':
                filtered_df = filtered_df[filtered_df['rsi_divergence'] == filters['rsi_divergence']]
            
            # MACD signal filter
            if filters.get('macd_signal') and filters['macd_signal'] != 'any':
                filtered_df = filtered_df[filtered_df['macd_signal'] == filters['macd_signal']]
            
            # Volume filter
            if filters.get('min_volume'):
                filtered_df = filtered_df[filtered_df['volume'] >= filters['min_volume']]
            
            # Price range filter
            if filters.get('price_min') is not None:
                filtered_df = filtered_df[filtered_df['price'] >= filters['price_min']]
            if filters.get('price_max') is not None:
                filtered_df = filtered_df[filtered_df['price'] <= filters['price_max']]
            
            # Price change filter
            if filters.get('change_min') is not None:
                filtered_df = filtered_df[filtered_df['price_change_pct'] >= filters['change_min']]
            if filters.get('change_max') is not None:
                filtered_df = filtered_df[filtered_df['price_change_pct'] <= filters['change_max']]
                
        except Exception as e:
            print(f"Error applying filters: {e}")
            return df
        
        return filtered_df
    
    def _sort_results(self, df, sort_by):
        """Sort results based on specified criteria"""
        if df.empty:
            return df
            
        try:
            if sort_by == 'volume':
                return df.sort_values('volume', ascending=False)
            elif sort_by == 'change':
                return df.sort_values('price_change_pct', ascending=False)
            elif sort_by == 'rsi':
                # Sort by RSI, putting NaN values at the end
                return df.sort_values('rsi', ascending=True, na_position='last')
            elif sort_by == 'random':
                return df.sample(frac=1).reset_index(drop=True)
            else:
                return df.sort_values('volume', ascending=False)  # Default to volume
        except Exception as e:
            print(f"Error sorting results: {e}")
            return df

# Preset filter configurations for quick scans
PRESET_FILTERS = {
    'divergence_signs': {
        'name': 'Divergence Signs',
        'description': 'Stocks showing bullish or bearish divergence signals',
        'filters': {
            'macd_divergence': 'any',  # Will be set to 'bullish' or 'bearish' in UI
            'rsi_divergence': 'any',   # Will be set to 'bullish' or 'bearish' in UI
            'min_volume': 500000
        }
    },
    'rsi_extremes': {
        'name': 'RSI Extremes',
        'description': 'Stocks with RSI overbought (>70) or oversold (<30) conditions',
        'filters': {
            'rsi_extreme': 'any',  # Will be set to 'overbought' or 'oversold' in UI
            'min_volume': 500000
        }
    },
    'bullish_momentum': {
        'name': 'Bullish Momentum',
        'description': 'EMA bullish alignment with MACD above signal',
        'filters': {
            'ema_trend': 'bullish',
            'macd_signal': 'bullish',
            'above_ema_13': True,
            'min_volume': 500000
        }
    },
    'high_volume': {
        'name': 'High Volume Breakouts',
        'description': 'Stocks with unusually high volume',
        'filters': {
            'min_volume': 5000000,
            'change_min': 2  # At least 2% change
        }
    },
    'strong_gainers': {
        'name': 'Strong Daily Gainers',
        'description': 'Stocks up more than 2% today',
        'filters': {
            'change_min': 2,
            'min_volume': 500000
        }
    },
    'spanish_value': {
        'name': 'Spanish Value Stocks',
        'description': 'Spanish stocks in value zone with good volume',
        'filters': {
            'value_zone_only': True,
            'min_volume': 100000  # Lower volume threshold for Spanish market
        }
    },
    'spanish_momentum': {
        'name': 'Spanish Momentum Stocks',
        'description': 'Spanish stocks with bullish momentum',
        'filters': {
            'ema_trend': 'bullish',
            'above_ema_13': True,
            'min_volume': 100000
        }
    },
    'spanish_oversold': {
        'name': 'Spanish Oversold Recovery',
        'description': 'Spanish stocks with RSI below 30',
        'filters': {
            'rsi_max': 30,
            'min_volume': 50000  # Very low threshold for Spanish market
        }
    }
}

def get_preset_filter(preset_name):
    """Get a preset filter configuration"""
    return PRESET_FILTERS.get(preset_name, {})

def get_available_presets():
    """Get list of available preset filters"""
    return list(PRESET_FILTERS.keys())
