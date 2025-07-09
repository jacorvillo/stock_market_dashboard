# 📈 Stock Market Dashboard

A free Python Dash web application for real-time stock market visualization with technical indicators.

## Features

- Real-time stock data from Yahoo Finance with multiple timeframes. Works with any US stock symbol (so long as it's available)
- Candlestick and Mountain (area) charts
- Sidebar with stock symbol search and timeframe selection
- (Ongoing): Technical indicators (e.g., RSI, %R, OBV)

> [!success] Current indicators available:
> - EMA (Exponential Moving Average)*: Two EMAs and the Value Zone between them
> - Volume: Volume bars with optional comparison to another market
> - MACD (Moving Average Convergence Divergence)*: MACD line, signal line, and histogram
> - Force Index*
> - DIR (Directional Movement Index)*: +DI, -DI, and ADX
> - A/D Line (Accumulation/Distribution Line)*
>
>
> *Timeframe can be changed for these indicators

> [!Summary] Indicators in development:
> - RSI (Relative Strength Index)
> - %R (Williams %R)
> - OBV (On-Balance Volume)

- (To do): Add signals (buy/sell) based on technical indicators

### Requirements
- Python 3.8+
- Internet connection for live data

### Installation and Usage
```bash
# Clone or download the project
cd stock_test

# Install dependencies  
pip install -r requirements.txt

# Run the app
python app.py
```
Open `http://localhost:8050` in your browser to view the dashboard.

### Notes
- This is for educational purposes only, not financial advice
- Data may have slight delays during high market volatility
- Some symbols may not be available or may require subscription data