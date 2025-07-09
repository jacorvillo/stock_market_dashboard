"""
Technical Analysis Insights Module
Generates dynamic trading insights based on multiple technical indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class TechnicalInsights:
    """Main class for generating technical analysis insights"""
    
    def __init__(self):
        self.indicators = {}
        self.signals = {}
        self.overall_sentiment = "NEUTRAL"
        self.confidence_score = 0.0
        
    def analyze_stock(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Main analysis function that processes all indicators and generates insights
        
        Args:
            df: DataFrame with OHLCV data and calculated indicators
            symbol: Stock symbol for context
            
        Returns:
            Dictionary containing all insights and recommendations
        """
        if df.empty or len(df) < 5:
            return self._get_fallback_insights(symbol)
            
        # Extract latest values for analysis
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Analyze each indicator
        insights = {
            'symbol': symbol,
            'timestamp': latest.name if hasattr(latest, 'name') else 'Latest',
            'price_analysis': self._analyze_price_action(df),
            'volume_analysis': self._analyze_volume(df),
            'trend_analysis': self._analyze_trend_indicators(df),
            'momentum_analysis': self._analyze_momentum_indicators(df),
            'volatility_analysis': self._analyze_volatility(df),
            'divergence_analysis': self._analyze_divergences(df),
            'overall_sentiment': self._calculate_overall_sentiment(df),
            'trading_recommendation': self._generate_trading_recommendation(df),
            'risk_assessment': self._assess_risk_levels(df),
            'key_levels': self._identify_key_levels(df)
        }
        
        return insights
    
    def _analyze_price_action(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze basic price action and trends"""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Price change analysis
        price_change = latest['Close'] - prev['Close']
        price_change_pct = (price_change / prev['Close']) * 100 if prev['Close'] > 0 else 0
        
        # Trend analysis with EMAs
        ema_trends = []
        for col in df.columns:
            if col.startswith('EMA_'):
                period = col.split('_')[1]
                if latest['Close'] > latest[col]:
                    ema_trends.append({'text': f"Above EMA{period}", 'color': '#28a745'})
                else:
                    ema_trends.append({'text': f"Below EMA{period}", 'color': '#dc3545'})
        
        # Candle pattern analysis
        candle_type = self._identify_candle_pattern(latest, prev)
        
        # Price direction
        if price_change > 0:
            price_direction = {'text': 'Bullish', 'color': '#28a745'}
        elif price_change < 0:
            price_direction = {'text': 'Bearish', 'color': '#dc3545'}
        else:
            price_direction = {'text': 'Neutral', 'color': '#ffc107'}
        
        analysis = {
            'current_price': latest['Close'],
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'price_direction': price_direction,
            'ema_status': ema_trends,
            'candle_pattern': candle_type,
            'summary': self._generate_price_summary(price_change_pct, ema_trends, candle_type)
        }
        
        return analysis
    
    def _analyze_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns and OBV"""
        latest = df.iloc[-1]
        
        # Volume analysis
        avg_volume = df['Volume'].tail(20).mean()
        volume_ratio = latest['Volume'] / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio > 1.5:
            volume_signal = {'text': 'High Volume - Strong conviction', 'color': '#28a745'}
        elif volume_ratio < 0.5:
            volume_signal = {'text': 'Low Volume - Weak conviction', 'color': '#dc3545'}
        else:
            volume_signal = {'text': 'Normal Volume', 'color': '#ffc107'}
        
        # OBV analysis
        obv_trend = {'text': '', 'color': '#ccc'}
        if 'OBV' in df.columns and len(df) > 5:
            obv_ma = df['OBV'].tail(5).mean()
            if latest['OBV'] > obv_ma:
                obv_trend = {'text': 'OBV Rising - Accumulation', 'color': '#28a745'}
            else:
                obv_trend = {'text': 'OBV Falling - Distribution', 'color': '#dc3545'}
        
        analysis = {
            'current_volume': latest['Volume'],
            'volume_ratio': volume_ratio,
            'volume_signal': volume_signal,
            'obv_trend': obv_trend,
            'summary': f"{volume_signal['text']}. {obv_trend['text']}"
        }
        
        return analysis
    
    def _analyze_trend_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze MACD, ADX, and DMI indicators"""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        analysis = {}
        
        # MACD Analysis
        if all(col in df.columns for col in ['MACD', 'MACD_signal', 'MACD_hist']):
            if latest['MACD'] > latest['MACD_signal']:
                if prev['MACD'] <= prev['MACD_signal']:
                    macd_signal = {'text': 'MACD Bullish Crossover', 'color': '#28a745'}
                else:
                    macd_signal = {'text': 'MACD Above Signal', 'color': '#28a745'}
                macd_trend = "Bullish"
            else:
                if prev['MACD'] >= prev['MACD_signal']:
                    macd_signal = {'text': 'MACD Bearish Crossover', 'color': '#dc3545'}
                else:
                    macd_signal = {'text': 'MACD Below Signal', 'color': '#dc3545'}
                macd_trend = "Bearish"
            
            analysis['macd'] = {
                'signal': macd_signal,
                'trend': macd_trend,
                'histogram': "Increasing" if latest['MACD_hist'] > prev['MACD_hist'] else "Decreasing"
            }
        
        # ADX/DMI Analysis
        if all(col in df.columns for col in ['ADX', 'DI_plus', 'DI_minus']):
            if latest['ADX'] > 25:
                adx_strength = {'text': 'Strong Trend', 'color': '#28a745'}
            elif latest['ADX'] > 20:
                adx_strength = {'text': 'Moderate Trend', 'color': '#ffc107'}
            else:
                adx_strength = {'text': 'Weak Trend', 'color': '#dc3545'}
            
            if latest['DI_plus'] > latest['DI_minus']:
                dmi_signal = {'text': 'Bullish DMI', 'color': '#28a745'}
            else:
                dmi_signal = {'text': 'Bearish DMI', 'color': '#dc3545'}
            
            analysis['adx_dmi'] = {
                'strength': adx_strength,
                'direction': dmi_signal,
                'adx_value': latest['ADX']
            }
        
        return analysis
    
    def _analyze_momentum_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze RSI, Stochastic, and Force Index"""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        analysis = {}
        
        # RSI Analysis
        if 'RSI' in df.columns:
            if latest['RSI'] > 70:
                rsi_signal = {'text': 'Overbought', 'color': '#dc3545'}
                rsi_zone = "Consider taking profits"
            elif latest['RSI'] < 30:
                rsi_signal = {'text': 'Oversold', 'color': '#28a745'}
                rsi_zone = "Potential buying opportunity"
            elif latest['RSI'] > 50:
                rsi_signal = {'text': 'Bullish Zone', 'color': '#28a745'}
                rsi_zone = "Momentum favors buyers"
            else:
                rsi_signal = {'text': 'Bearish Zone', 'color': '#dc3545'}
                rsi_zone = "Momentum favors sellers"
            
            analysis['rsi'] = {
                'value': latest['RSI'],
                'signal': rsi_signal,
                'interpretation': rsi_zone
            }
        
        # Stochastic Analysis
        if all(col in df.columns for col in ['Stoch_K', 'Stoch_D']):
            if latest['Stoch_K'] > 80:
                stoch_signal = {'text': 'Stoch Overbought', 'color': '#dc3545'}
                stoch_zone = "Potential reversal zone"
            elif latest['Stoch_K'] < 20:
                stoch_signal = {'text': 'Stoch Oversold', 'color': '#28a745'}
                stoch_zone = "Potential bounce zone"
            else:
                if latest['Stoch_K'] > latest['Stoch_D']:
                    stoch_signal = {'text': 'Stoch Bullish', 'color': '#28a745'}
                else:
                    stoch_signal = {'text': 'Stoch Bearish', 'color': '#dc3545'}
                stoch_zone = "Neutral zone"
            
            analysis['stochastic'] = {
                'k_value': latest['Stoch_K'],
                'd_value': latest['Stoch_D'],
                'signal': stoch_signal,
                'interpretation': stoch_zone
            }
        
        # Force Index Analysis
        if 'Force_Index' in df.columns:
            if latest['Force_Index'] > 0:
                if prev['Force_Index'] <= 0:
                    force_signal = {'text': 'Force Index Turned Positive', 'color': '#28a745'}
                else:
                    force_signal = {'text': 'Positive Force Index', 'color': '#28a745'}
                force_trend = "Bullish pressure"
            else:
                if prev['Force_Index'] >= 0:
                    force_signal = {'text': 'Force Index Turned Negative', 'color': '#dc3545'}
                else:
                    force_signal = {'text': 'Negative Force Index', 'color': '#dc3545'}
                force_trend = "Bearish pressure"
            
            analysis['force_index'] = {
                'value': latest['Force_Index'],
                'signal': force_signal,
                'trend': force_trend
            }
        
        return analysis
    
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze ATR and volatility patterns"""
        latest = df.iloc[-1]
        
        analysis = {}
        
        if 'ATR' in df.columns:
            # Calculate ATR as percentage of price
            atr_pct = (latest['ATR'] / latest['Close']) * 100 if latest['Close'] > 0 else 0
            
            if atr_pct > 3:
                volatility_level = {'text': 'High Volatility', 'color': '#dc3545'}
                volatility_msg = "Increased risk and opportunity"
            elif atr_pct > 1.5:
                volatility_level = {'text': 'Moderate Volatility', 'color': '#ffc107'}
                volatility_msg = "Normal market conditions"
            else:
                volatility_level = {'text': 'Low Volatility', 'color': '#28a745'}
                volatility_msg = "Stable price action"
            
            analysis['atr'] = {
                'value': latest['ATR'],
                'percentage': atr_pct,
                'level': volatility_level,
                'interpretation': volatility_msg
            }
        
        return analysis
    
    def _analyze_divergences(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect potential bullish/bearish divergences"""
        if len(df) < 10:
            return {'detected': False, 'summary': "Insufficient data for divergence analysis"}
        
        # Get recent data for analysis
        recent_data = df.tail(10)
        
        divergences = []
        
        # RSI Divergence
        if 'RSI' in df.columns:
            price_trend = recent_data['Close'].iloc[-1] > recent_data['Close'].iloc[0]
            rsi_trend = recent_data['RSI'].iloc[-1] > recent_data['RSI'].iloc[0]
            
            if price_trend and not rsi_trend:
                divergences.append({'text': 'RSI Bearish Divergence', 'color': '#dc3545'})
            elif not price_trend and rsi_trend:
                divergences.append({'text': 'RSI Bullish Divergence', 'color': '#28a745'})
        
        # MACD Divergence
        if 'MACD' in df.columns:
            price_trend = recent_data['Close'].iloc[-1] > recent_data['Close'].iloc[0]
            macd_trend = recent_data['MACD'].iloc[-1] > recent_data['MACD'].iloc[0]
            
            if price_trend and not macd_trend:
                divergences.append({'text': 'MACD Bearish Divergence', 'color': '#dc3545'})
            elif not price_trend and macd_trend:
                divergences.append({'text': 'MACD Bullish Divergence', 'color': '#28a745'})
        
        analysis = {
            'detected': len(divergences) > 0,
            'divergences': divergences,
            'summary': f"{len(divergences)} divergence(s) detected" if divergences else "No significant divergences detected"
        }
        
        return analysis
    
    def _calculate_overall_sentiment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall market sentiment based on all indicators"""
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        latest = df.iloc[-1]
        
        # Price vs EMAs
        for col in df.columns:
            if col.startswith('EMA_'):
                total_signals += 1
                if latest['Close'] > latest[col]:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
        
        # MACD
        if all(col in df.columns for col in ['MACD', 'MACD_signal']):
            total_signals += 1
            if latest['MACD'] > latest['MACD_signal']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # RSI
        if 'RSI' in df.columns:
            total_signals += 1
            if latest['RSI'] > 50:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # ADX/DMI
        if all(col in df.columns for col in ['DI_plus', 'DI_minus']):
            total_signals += 1
            if latest['DI_plus'] > latest['DI_minus']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Force Index
        if 'Force_Index' in df.columns:
            total_signals += 1
            if latest['Force_Index'] > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Calculate sentiment
        if total_signals > 0:
            bullish_pct = (bullish_signals / total_signals) * 100
            bearish_pct = (bearish_signals / total_signals) * 100
        else:
            bullish_pct = bearish_pct = 50
        
        if bullish_pct >= 70:
            sentiment = {'text': 'STRONGLY BULLISH', 'color': '#28a745', 'weight': 'bold'}
            confidence = "High"
        elif bullish_pct >= 60:
            sentiment = {'text': 'BULLISH', 'color': '#28a745', 'weight': 'normal'}
            confidence = "Moderate"
        elif bearish_pct >= 70:
            sentiment = {'text': 'STRONGLY BEARISH', 'color': '#dc3545', 'weight': 'bold'}
            confidence = "High"
        elif bearish_pct >= 60:
            sentiment = {'text': 'BEARISH', 'color': '#dc3545', 'weight': 'normal'}
            confidence = "Moderate"
        else:
            sentiment = {'text': 'NEUTRAL', 'color': '#ffc107', 'weight': 'normal'}
            confidence = "Low"
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'total_signals': total_signals,
            'bullish_percentage': bullish_pct,
            'bearish_percentage': bearish_pct
        }
    
    def _generate_trading_recommendation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate specific trading recommendations"""
        latest = df.iloc[-1]
        
        # Get overall sentiment
        sentiment_data = self._calculate_overall_sentiment(df)
        bullish_pct = sentiment_data['bullish_percentage']
        
        # Generate recommendation based on multiple factors
        if bullish_pct >= 75:
            recommendation = {'text': 'STRONG BUY', 'color': '#28a745', 'weight': 'bold'}
            action_color = "#28a745"
            risk_level = "Low-Medium"
        elif bullish_pct >= 65:
            recommendation = {'text': 'BUY', 'color': '#28a745', 'weight': 'normal'}
            action_color = "#28a745"
            risk_level = "Medium"
        elif bullish_pct >= 55:
            recommendation = {'text': 'WEAK BUY', 'color': '#28a745', 'weight': 'normal'}
            action_color = "#28a745"
            risk_level = "Medium"
        elif bullish_pct >= 45:
            recommendation = {'text': 'HOLD', 'color': '#ffc107', 'weight': 'normal'}
            action_color = "#ffc107"
            risk_level = "Medium"
        elif bullish_pct >= 35:
            recommendation = {'text': 'WEAK SELL', 'color': '#dc3545', 'weight': 'normal'}
            action_color = "#dc3545"
            risk_level = "Medium"
        elif bullish_pct >= 25:
            recommendation = {'text': 'SELL', 'color': '#dc3545', 'weight': 'normal'}
            action_color = "#dc3545"
            risk_level = "Medium-High"
        else:
            recommendation = {'text': 'STRONG SELL', 'color': '#dc3545', 'weight': 'bold'}
            action_color = "#dc3545"
            risk_level = "High"
        
        # Add specific action items
        action_items = []
        
        # Check for overbought/oversold conditions
        if 'RSI' in df.columns:
            if latest['RSI'] > 75:
                action_items.append({'text': 'Consider taking profits - RSI overbought', 'color': '#dc3545'})
            elif latest['RSI'] < 25:
                action_items.append({'text': 'Consider adding position - RSI oversold', 'color': '#28a745'})
        
        # Always suggest stop loss based on current closing price
        stop_loss_price = latest['Close'] * 0.95  # 5% below current close as default
        if 'ATR' in df.columns:
            # Use ATR for more dynamic stop loss, but ensure it's below current close
            atr_stop = latest['Close'] - (2 * latest['ATR'])
            if atr_stop < latest['Close']:  # Ensure stop is below current price
                stop_loss_price = atr_stop
        
        action_items.append({'text': f'Suggested stop loss: ${stop_loss_price:.2f}', 'color': '#dc3545'})
        
        return {
            'recommendation': recommendation,
            'risk_level': risk_level,
            'confidence': sentiment_data['confidence'],
            'action_items': action_items,
            'bullish_percentage': bullish_pct
        }
    
    def _assess_risk_levels(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess current risk levels and volatility"""
        latest = df.iloc[-1]
        
        risk_factors = []
        
        # Volatility risk
        if 'ATR' in df.columns:
            atr_pct = (latest['ATR'] / latest['Close']) * 100
            if atr_pct > 4:
                risk_factors.append({'text': 'High volatility risk', 'color': '#dc3545'})
            elif atr_pct > 2:
                risk_factors.append({'text': 'Moderate volatility', 'color': '#ffc107'})
        
        # Momentum divergence risk
        divergence_data = self._analyze_divergences(df)
        if divergence_data['detected']:
            risk_factors.append({'text': 'Divergence signals present', 'color': '#dc3545'})
        
        # Overbought/oversold risk
        if 'RSI' in df.columns:
            if latest['RSI'] > 80:
                risk_factors.append({'text': 'Extremely overbought', 'color': '#dc3545'})
            elif latest['RSI'] < 20:
                risk_factors.append({'text': 'Extremely oversold - potential reversal', 'color': '#28a745'})
        
        if len(risk_factors) >= 3:
            overall_risk = {'text': 'High', 'color': '#dc3545'}
        elif len(risk_factors) >= 2:
            overall_risk = {'text': 'Elevated', 'color': '#ffc107'}
        elif len(risk_factors) == 1:
            overall_risk = {'text': 'Moderate', 'color': '#28a745'}
        else:
            overall_risk = {'text': 'Low', 'color': '#28a745'}
        
        return {
            'overall_risk': overall_risk,
            'risk_factors': risk_factors,
            'risk_count': len(risk_factors)
        }
    
    def _identify_key_levels(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify key support and resistance levels"""
        if len(df) < 20:
            return {'support': None, 'resistance': None, 'summary': "Insufficient data"}
        
        recent_data = df.tail(20)
        latest = df.iloc[-1]
        
        # Simple support/resistance calculation
        recent_highs = recent_data['High'].max()
        recent_lows = recent_data['Low'].min()
        
        # ATR-based levels
        if 'ATR' in df.columns:
            atr = latest['ATR']
            resistance = latest['Close'] + (2 * atr)
            support = latest['Close'] - (2 * atr)
        else:
            resistance = recent_highs
            support = recent_lows
        
        return {
            'resistance': resistance,
            'support': support,
            'recent_high': recent_highs,
            'recent_low': recent_lows,
            'summary': f"Key resistance: ${resistance:.2f}, Key support: ${support:.2f}"
        }
    
    def _identify_candle_pattern(self, latest, prev) -> Dict[str, str]:
        """Identify basic candle patterns"""
        body_size = abs(latest['Close'] - latest['Open'])
        total_range = latest['High'] - latest['Low']
        
        if total_range == 0:
            return {'text': 'Doji - Indecision', 'color': '#ffc107'}
        
        body_ratio = body_size / total_range
        
        if body_ratio < 0.1:
            return {'text': 'Doji - Indecision', 'color': '#ffc107'}
        elif latest['Close'] > latest['Open']:
            if body_ratio > 0.7:
                return {'text': 'Strong Bullish Candle', 'color': '#28a745'}
            else:
                return {'text': 'Bullish Candle', 'color': '#28a745'}
        else:
            if body_ratio > 0.7:
                return {'text': 'Strong Bearish Candle', 'color': '#dc3545'}
            else:
                return {'text': 'Bearish Candle', 'color': '#dc3545'}
    
    def _generate_price_summary(self, price_change_pct, ema_trends, candle_type) -> str:
        """Generate a summary of price action"""
        summary_parts = []
        
        if abs(price_change_pct) > 2:
            if price_change_pct > 0:
                summary_parts.append(f"Strong upward move ({price_change_pct:.1f}%)")
            else:
                summary_parts.append(f"Strong downward move ({price_change_pct:.1f}%)")
        
        # Count EMA positions
        above_emas = len([trend for trend in ema_trends if trend['color'] == '#28a745'])
        total_emas = len(ema_trends)
        
        if total_emas > 0:
            if above_emas == total_emas:
                summary_parts.append("Above all EMAs")
            elif above_emas == 0:
                summary_parts.append("Below all EMAs")
            else:
                summary_parts.append(f"Mixed EMA signals ({above_emas}/{total_emas} bullish)")
        
        return ". ".join(summary_parts) if summary_parts else "Neutral price action"
    
    def _get_fallback_insights(self, symbol: str) -> Dict[str, Any]:
        """Return fallback insights when data is insufficient"""
        return {
            'symbol': symbol,
            'timestamp': 'Insufficient Data',
            'price_analysis': {'summary': 'Insufficient data for price analysis'},
            'volume_analysis': {'summary': 'Insufficient data for volume analysis'},
            'trend_analysis': {},
            'momentum_analysis': {},
            'volatility_analysis': {},
            'divergence_analysis': {'detected': False, 'summary': 'Insufficient data'},
            'overall_sentiment': {
                'sentiment': {'text': 'UNKNOWN', 'color': '#ffc107', 'weight': 'normal'},
                'confidence': 'Very Low'
            },
            'trading_recommendation': {
                'recommendation': {'text': 'WAIT', 'color': '#ffc107', 'weight': 'normal'},
                'risk_level': 'Unknown',
                'action_items': [{'text': 'Wait for sufficient market data', 'color': '#ffc107'}]
            },
            'risk_assessment': {'overall_risk': 'Unknown', 'risk_factors': []},
            'key_levels': {'summary': 'Insufficient data for level analysis'}
        }


def generate_insights_summary(insights: Dict[str, Any]) -> str:
    """Generate a concise HTML summary of all insights"""
    
    summary_html = f"""
    <div style="padding: 20px; background-color: #1a1a1a; border-radius: 10px; color: white;">
        <h3 style="color: #fff; margin-bottom: 20px;">📊 Technical Analysis Summary for {insights['symbol']}</h3>
        
        <div style="margin-bottom: 15px;">
            <strong>Overall Sentiment:</strong> {insights['overall_sentiment']['sentiment']} 
            <span style="color: #ccc;">({insights['overall_sentiment']['confidence']} confidence)</span>
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Trading Recommendation:</strong> {insights['trading_recommendation']['recommendation']}
            <span style="color: #ccc;"> (Risk: {insights['trading_recommendation']['risk_level']})</span>
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Price Action:</strong> {insights['price_analysis']['summary']}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Volume Analysis:</strong> {insights['volume_analysis']['summary']}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Risk Assessment:</strong> {insights['risk_assessment']['overall_risk']} risk level
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Key Levels:</strong> {insights['key_levels']['summary']}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Divergences:</strong> {insights['divergence_analysis']['summary']}
        </div>
    </div>
    """
    
    return summary_html
