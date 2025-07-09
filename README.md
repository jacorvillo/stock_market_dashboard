# 📈 Stock Market Dashboard

A Python Dash web application for real-time stock market visualization with technical indicators.

## Features

- **Real-time stock data** from Yahoo Finance
- **Multiple timeframes**: 1D (intraday), 5D, 1M, 6M, YTD, 1Y, 5Y, Max  
- **Chart types**: Candlestick and Mountain (area) charts
- **Technical indicators**: EMA, MACD, Force Index, A/D Line, ADX, Volume analysis
- **Market session handling**: Shows live data during market hours, previous session data when closed
- **Dark theme** with professional styling

## Main Components

### Stock Search
- Enter any US stock symbol (AAPL, TSLA, GOOGL, etc.)
- Automatic fallback to SPY if symbol not found

### Chart Display
- **Main chart**: Price action with candlesticks or mountain view
- **Secondary chart**: Technical indicators (Volume, MACD, Force Index, A/D Line, ADX)
- **Previous close reference**: Dotted line on intraday charts showing previous day's close

### Technical Indicators
- **EMA (Exponential Moving Average)**: Customizable periods
- **MACD**: Moving Average Convergence Divergence with histogram
- **Force Index**: Volume-weighted price momentum
- **A/D Line**: Accumulation/Distribution indicator  
- **ADX**: Average Directional Index for trend strength
- **ATR Bands**: Volatility bands around price
- **Volume Comparison**: Compare with major ETFs (SPY, QQQ, etc.)

## Quick Start

### Requirements
- Python 3.8+
- Internet connection for live data

### Installation
```bash
# Clone or download the project
cd stock_test

# Install dependencies  
pip install -r requirements.txt

# Run the app
python app.py
```

### Usage
1. Open `http://localhost:8050` in your browser
2. Enter a stock symbol and click Search
3. Select timeframe and chart type
4. Configure technical indicators in the sidebar
5. Charts update automatically every 30 seconds

## How It Works

### Market Sessions
- **Market Hours**: Shows live intraday data with minute-by-minute updates
- **Market Closed**: Displays "Previous Market Period" data (most recent trading session)
- **Weekends**: Automatically shows Friday's data

### Data Flow
1. Fetches real-time data from Yahoo Finance
2. Calculates technical indicators using the `ta` library
3. Renders interactive charts with Plotly
4. Updates every 30 seconds during market hours

### Smart Features
- **Caching**: Recent data cached for 60 seconds for faster symbol switching
- **Error Handling**: Falls back to SPY data if requested symbol fails
- **Timezone Conversion**: Handles market time (ET) vs local time
- **Weekend Skipping**: Charts exclude weekends automatically

## Technical Stack

- **Frontend**: Dash + Plotly.js for interactive charts
- **Backend**: Python with pandas for data processing  
- **Data Source**: Yahoo Finance via `yfinance` library
- **Styling**: Bootstrap (Cyborg theme) for dark mode
- **Technical Analysis**: `ta` library for indicator calculations

## File Structure
```
stock_test/
├── app.py           # Main application with UI layout and callbacks
├── functions.py     # Data fetching and chart generation functions  
├── requirements.txt # Python package dependencies
└── README.md       # This file
```

## Troubleshooting

### Common Issues
- **No data showing**: Check internet connection or try a different stock symbol
- **Port already in use**: Change port in `app.py`: `app.run_server(port=8051)`
- **Package errors**: Run `pip install -r requirements.txt` again

### Notes
- This is for educational purposes only, not financial advice
- Data may have slight delays during high market volatility
- Some symbols may not be available or may require subscription data

---

*Built with Python, Dash, and Plotly for interactive financial data visualization.*
