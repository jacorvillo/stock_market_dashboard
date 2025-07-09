# 📈 Stock Market Dashboard

A free Python Dash toolbox for real-time stock market visualization with indicators. Based on the book The New Trading for a Living by Dr. Alexander Elder

## Features

- Real-time stock data from Yahoo Finance with multiple timeframes. Works with any US stock symbol (so long as it's available)
- Candlestick and Mountain (area) charts
- Sidebar with stock symbol search and timeframe selection
- (Ongoing): Technical indicators (e.g., RSI, %R, OBV)

> [!TIP] 
> Current indicators available:
> - EMA (Exponential Moving Average)*: Two EMAs and the Value Zone between them
> - Volume: Volume bars with optional comparison to another market
> - MACD (Moving Average Convergence Divergence)*: MACD line, signal line, and histogram
> - Force Index*
> - DIR (Directional Movement Index)*: +DI, -DI, and ADX
> - A/D Line (Accumulation/Distribution Line)*
> - Slow Stochastic*: %K and %D lines
> - RSI (Relative Strength Index)*
> - OBV (On-Balance Volume)*
>
> *Timeframe can be changed for these indicators


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

## Todo

- [ ] (Short term) Implement additional technical indicators

> [!IMPORTANT] 
> Indicators in development:
> - %R (Williams %R)
> - New High/New Low index
> - Consensus and commitment indicators
> - Others

- [x] Improve UI/UX design
- [ ] (Short/long term) Insights: signals (buy/sell) based on technical indicators, both in the chart and as alerts

- [ ] (Longer term) Add stock scanner functionality to filter stocks based on technical indicators and other criteria
- [ ] (Longer term) Add popular system trading strategies (Triple Screen Trading System, Impulse System, Channel trading)
- [ ] (Longer term) Add backtesting functionality to test strategies against historical data
- [ ] (Longer term) Expand to other markets (ETFs, Options, CFDs, futures, forex)