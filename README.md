# 📈 Stock Market Dashboard

A free, local Python Dash toolbox for real-time stock market visualization with indicators. Based on indicators and tips from the book [_The New Trading for a Living_](https://www.goodreads.com/book/show/22337485) by Dr. Alexander Elder

Current look:

![Stock Dashboard Screenshot](https://github.com/jacorvillo/stock_market_dashboard/blob/main/image.png)

## Features

This dashboard provides real-time US stock data from Yahoo Finance with multiple timeframes. Works with any stock symbol (so long as it's available)

As of now, the dashboard includes:

- **Scanner**: Find US stocks and ETFs based on technical indicators and other criteria
- **Analysis** (Ongoing): View real-time stock data at multiple timeframes with technical indicators. Includes Impulse System visualization

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
> - Bollinger Bands*
> - Autoenvelope*
>
> *Timeframe can be changed for these indicators

> [!IMPORTANT] 
> Indicators that I plan to add:
> - New High/New Low index
> - Stocks above 50-day EMA
> - Consensus and commitment indicators (Short interest, Days to cover)
> - Open Interest for options

- **Insights** (Ongoing): Get buy/sell signals based on different technical indicators

## Requirements
- Python 3.8+
- Internet connection for live data

## Installation and Usage
```bash
# Clone or download the project
cd stock_test

# Install dependencies  
pip install -r requirements.txt

# Run the app
python app.py
```
Open `http://localhost:8050` in your browser to view the dashboard.

## Notes
- This is for educational purposes only, it is NOT financial advice and I am not responsible for any financial losses you take!
- Data may have slight delays during high market volatility. I'm doing what I can to improve performance, but since it is heavily dependent on the Yahoo Finance API, there may be limitations

## Todo

- [ ] (Short term) Implement additional technical indicators
- [ ] (Short/long term) Insights: signals (buy/sell) based on technical indicators, both in the chart and as alerts
- [ ] (Longer term) Add popular system trading strategies (Triple Screen Trading System, ~~Impulse System, Channel trading~~)
- [ ] (Longer term) Analysis: Add backtesting functionality to test strategies against historical data

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
