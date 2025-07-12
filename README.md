# 📈 Stock Market Dashboard

A free, local Python Dash toolbox for real-time stock market visualization with indicators. Based on indicators and tips from the book [_The New Trading for a Living_](https://www.goodreads.com/book/show/22337485) by Dr. Alexander Elder

Current look:

![Stock Dashboard Screenshot](https://github.com/jacorvillo/stock_market_dashboard/blob/main/image.png)

## 🚀 Features

This dashboard provides real-time US stock data from Yahoo Finance with multiple timeframes. Works with any stock symbol (so long as it's available)

### 📊 Available Indicators

> [!TIP] 
> Current indicators available:
> - **EMA (Exponential Moving Average)**: Two EMAs and the Value Zone between them
> - **Volume**: Volume bars with optional comparison to another market
> - **MACD (Moving Average Convergence Divergence)**: MACD line, signal line, and histogram
> - **Force Index**: Volume-weighted momentum indicator
> - **ADX (Directional Movement Index)**: +DI, -DI, and ADX for trend strength
> - **A/D Line (Accumulation/Distribution Line)**: Volume flow indicator
> - **Slow Stochastic**: %K and %D lines with overbought/oversold levels
> - **RSI (Relative Strength Index)**: Momentum oscillator
> - **OBV (On-Balance Volume)**: Volume flow indicator
> - **Bollinger Bands**: Volatility bands
> - **Autoenvelope**: Percentage-based envelope
> - **ATR Bands**: Average True Range volatility bands
> - **Impulse System visualization**
>
> *All indicators support multiple timeframes and customizable parameters*

## 🎯 Tab Overview

### 🔍 Scanner
**Find stocks based on technical criteria and market conditions**, with presets and many universes to pick from!

### 🛠️ Analysis Tab
**Comprehensive real-life technical analysis with customizable indicators**, at multiple timeframe supports 

### 💡 Insights Tab
**Trading recommendations based on indicators** (no, no AI, I swear), fit for day or swing trading

### 💸 IRL Trading Simulator
**Practice real-life trading with virtual money and position management!** For when the real time comes. Start with 1000$ and work your way to the top, with target price, dynamic stop-loss and equity curve.



## 📋 Requirements
- Python 3.8+
- Internet connection for live data

## 🚀 Installation and Usage
```bash
# Clone or download the project
cd stock_test

# Install dependencies  
pip install -r requirements.txt

# Run the app
python app.py
```
Open `http://localhost:8050` in your browser to view the dashboard.

## ⚠️ Important Notes
- **Educational Purpose Only**: This is for educational purposes only, it is NOT financial advice and I am not responsible for any financial losses you take!
- **Data Delays**: Data may have slight delays during high market volatility. Performance depends on Yahoo Finance API limitations
- **Market Hours**: Some features work best during market hours (9:30 AM - 4:00 PM ET)
- **Symbol Support**: Not all symbols available on Yahoo Finance may work perfectly

## 🔮 Future Roadmap

### Short Term
- General market indicators (New High/New Low index, Stocks above 50-day EMA)
- Enhanced insights with more trading strategies
- IRL Trading functionality for real-time strategy testing

### Long Term
- Consensus and commitment indicators (Short interest, Days to cover)
- Options analysis with Open Interest data
- Advanced risk management tools

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
