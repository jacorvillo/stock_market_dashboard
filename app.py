import dash
from dash import dcc, html, Input, Output, callback, State, dash_table
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime as dt
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
import yfinance as yf
import ta
import json
import xarray as xr
import os
from dash.dependencies import ALL
from dash.dash_table import Format, FormatTemplate
import threading
import time

# Import functions from functions module
from functions.analysis_functions import (
    get_stock_data, 
    calculate_indicators,
    update_lower_chart_settings,
    update_symbol,
    format_symbol_input,
    update_macd_stores,
    update_force_store,
    update_adx_stores,
    update_stochastic_store,
    update_rsi_store,
    update_data,
    update_combined_chart,
    update_symbol_status,
    update_indicator_options,
    update_stock_status_indicator
)

from functions.impulse_functions import calculate_impulse_system, get_impulse_colors
from functions.scanner_functions import StockScanner, get_preset_filter, get_available_presets
from functions.insights_functions import TechnicalInsights, generate_insights_summary
from functions.irl_trading_functions import open_position, close_position, load_trading_df, save_trading_df, update_stop_price, calculate_trade_apgar
from functions.watchlist_functions import load_watchlist, add_to_watchlist, remove_from_watchlist

# Enhanced CSS with Inter font and bold white card headers
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }
#update-insights-stock-button:hover { background-color: transparent !important; border-color: #00d4aa !important; color: #00d4aa !important; }
body, .card, .card-header, .card-body, .nav-tabs, .tab-content, .tab-pane { background-color: #000000 !important; color: #fff !important; }
.card, .card-header { border-color: #000 !important; }
.card-header { border-bottom: 1px solid #333 !important; }
.card-header h1, .card-header h2, .card-header h3, .card-header h4, .card-header h5, .card-header h6 { color: #ffffff !important; font-weight: 700 !important; font-family: 'Inter', sans-serif !important; margin: 0 !important; }
h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; }
.form-control, .form-select { background-color: #000000 !important; border: 1px solid #333 !important; border-radius: 8px !important; color: #fff !important; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important; }
.form-control:focus, .form-select:focus { background-color: #000000 !important; border-color: #00d4aa !important; box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.1) !important; color: #fff !important; }
.form-select option { background-color: #000000 !important; color: #fff !important; }
.nav-tabs { background-color: #000000 !important; border-bottom: 1px solid #444 !important; }
.nav-tabs .nav-link { background-color: #000000 !important; border: 1px solid #444 !important; color: #ccc !important; font-weight: 500 !important; border-radius: 8px 8px 0 0 !important; }
.nav-tabs .nav-link:hover, .nav-tabs .nav-link.active { color: #00d4aa !important; border-color: #00d4aa !important; }
.nav-tabs .nav-link.active { background-color: #000000 !important; border-color: #00d4aa #00d4aa #000000 !important; }
.form-check-input { background-color: #222 !important; border: 2px solid #666 !important; border-radius: 6px !important; }
.form-check-input:checked { background-color: #00d4aa !important; border-color: #00d4aa !important; }
.form-check-label { color: #fff !important; padding-left: 8px !important; font-weight: 500 !important; }
.btn { font-family: 'Inter', sans-serif !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.3s ease !important; }
.btn:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important; }
.btn-success { background: linear-gradient(45deg, #00d4aa, #00ff88) !important; border: none !important; color: #000 !important; }
.btn-secondary { background-color: #333 !important; border-color: #444 !important; color: #fff !important; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #000000; border-radius: 4px; }
::-webkit-scrollbar-thumb { background: #444; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #00d4aa; }
.form-label, label { color: #fff !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; margin-bottom: 8px !important; }
input[type="number"], input[type="text"] { background-color: #000000 !important; border: 1px solid #333 !important; border-radius: 6px !important; color: #fff !important; font-weight: 500 !important; }
input[type="number"]:focus, input[type="text"]:focus { border-color: #00d4aa !important; box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.1) !important; }
.card { border-radius: 12px !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important; }
.card-header { border-radius: 12px 12px 0 0 !important; }
.card-body { border-radius: 0 0 12px 12px !important; }
.alert { border-radius: 8px !important; border: 1px solid #333 !important; background-color: #000000 !important; }
.alert-warning { color: #ffcc00 !important; border-color: #ffcc00 !important; }
"""

# Initialize the Dash app with Dark Bootstrap theme and Font Awesome for icons
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, 'https://use.fontawesome.com/releases/v5.15.4/css/all.css'], suppress_callback_exceptions=True)
app.title = "Stock Dashboard"

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        ''' + custom_css + '''
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# All functions moved to functions.py module

# App layout with advanced customization
app.layout = dbc.Container([
    # Sidebar toggle button (fixed position at bottom left)
    dbc.Button(
        "☰", 
        id="sidebar-toggle-button", 
        color="secondary", 
        className="mb-3",
        style={"position": "fixed", "bottom": "20px", "left": "20px", "zIndex": "1000", "fontSize": "20px", "fontWeight": "bold", "padding": "5px 12px"}
    ),
    
    # Main content row with sidebar and charts
    dbc.Row([
        # Sidebar column with collapse functionality
        dbc.Col(
            dbc.Collapse(
                html.Div(style={'height': '95vh', 'overflow-y': 'auto'}, children=[
                    # Tabs for sidebar content
                    dbc.Tabs(
                        id="sidebar-tabs",
                        active_tab="scanner-tab",
                        children=[
                            # Stock Scanner Tab
                            dbc.Tab(
                                label="🔍",
                                tab_id="scanner-tab",
                                children=[
                                    html.Div(style={'padding': '15px 0'}, children=[
                                        dbc.Card([
                                            dbc.CardHeader(html.H4("🔍 Scanner", className="text-center", style={'color': '#00d4aa'})),
                                            dbc.CardBody([
                                                # Quick Preset Scans
                                                dbc.Label("🚀 Quick Scans:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Button("Divergence Signs", id="preset-divergence", size="sm", color="info", outline=True, className="mb-2 w-100")
                                                    ], width=6),
                                                    dbc.Col([
                                                        dbc.Button("RSI Extremes", id="preset-rsi-extremes", size="sm", color="warning", outline=True, className="mb-2 w-100")
                                                    ], width=6)
                                                ]),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Button("High Volume", id="preset-volume", size="sm", color="success", outline=True, className="mb-2 w-100")
                                                    ], width=6),
                                                    dbc.Col([
                                                        dbc.Button("Trade Apgar > 7", id="preset-apgar", size="sm", color="success", outline=True, className="mb-2 w-100")
                                                    ], width=6)
                                                ], className="mb-3"),
                                                # Remove All Filters Button
                                                dbc.Button(
                                                    "🗑️ Remove All Filters",
                                                    id="remove-all-filters",
                                                    size="sm",
                                                    color="danger",
                                                    outline=True,
                                                    className="w-100 mb-3"
                                                ),
                                                
                                                html.Hr(style={'borderColor': '#333'}),
                                                
                                                # Expandable Filter Sections
                                                dbc.Accordion([
                                                    dbc.AccordionItem([
                                                        # Elder's Core Filters
                                                        dbc.Checklist(
                                                            id='elder-filters',
                                                            options=[
                                                                {'label': '📊 MACD Bullish Divergence', 'value': 'macd_bullish_divergence'},
                                                                {'label': '📊 MACD Bearish Divergence', 'value': 'macd_bearish_divergence'},
                                                                {'label': '📊 RSI Bullish Divergence', 'value': 'rsi_bullish_divergence'},
                                                                {'label': '📊 RSI Bearish Divergence', 'value': 'rsi_bearish_divergence'},
                                                                {'label': '📈 Bullish EMA Alignment', 'value': 'ema_bullish'},
                                                                {'label': '💪 Bullish MACD Signal', 'value': 'macd_bullish'},
                                                                {'label': '📊 Above 13 EMA', 'value': 'above_ema_13'}
                                                            ],
                                                            value=[],
                                                            style={'color': '#fff'}
                                                        )
                                                    ], title="🎯 Elder's Methods", item_id="elder-section"),
                                                    
                                                    dbc.AccordionItem([
                                                        # RSI Range Preset
                                                        dbc.Label("RSI Range:", style={'color': '#fff', 'marginBottom': '10px'}),
                                                        dbc.Select(
                                                            id='rsi-preset',
                                                            options=[
                                                                {'label': 'Any RSI', 'value': 'any'},
                                                                {'label': 'Oversold (< 30)', 'value': 'oversold'},
                                                                {'label': 'Overbought (> 70)', 'value': 'overbought'},
                                                                {'label': 'Recovery (30-40)', 'value': 'recovery'},
                                                                {'label': 'Neutral (40-60)', 'value': 'neutral'},
                                                                {'label': 'Overbought Setup (60-70)', 'value': 'setup'}
                                                            ],
                                                            value='any',
                                                            className="mb-3"
                                                        )
                                                    ], title="📊 Momentum Filters", item_id="momentum-section"),
                                                    
                                                    dbc.AccordionItem([
                                                        # Volume Presets
                                                        dbc.Label("Minimum Volume:", style={'color': '#fff', 'marginBottom': '10px'}),
                                                        dbc.Select(
                                                            id='volume-preset',
                                                            options=[  # type: ignore
                                                                {'label': 'Any Volume', 'value': 0},
                                                                {'label': 'Light Trading (> 100K)', 'value': 100000},
                                                                {'label': 'Moderate Trading (> 500K)', 'value': 500000},
                                                                {'label': 'Active Trading (> 1M)', 'value': 1000000},
                                                                {'label': 'High Volume (> 5M)', 'value': 5000000}
                                                            ],
                                                            value=500000,
                                                            className="mb-3"
                                                        )
                                                    ], title="📊 Volume & Activity", item_id="volume-section"),
                                                    
                                                    dbc.AccordionItem([
                                                        # Price Range Presets
                                                        dbc.Label("Price Range:", style={'color': '#fff', 'marginBottom': '10px'}),
                                                        dbc.Select(
                                                            id='price-preset',
                                                            options=[
                                                                {'label': 'Any Price', 'value': 'any'},
                                                                {'label': 'Penny Stocks (< $5)', 'value': 'penny'},
                                                                {'label': 'Low Price ($5-$20)', 'value': 'low'},
                                                                {'label': 'Medium Price ($20-$100)', 'value': 'medium'},
                                                                {'label': 'High Price ($100-$500)', 'value': 'high'},
                                                                {'label': 'Premium Stocks (> $500)', 'value': 'premium'}
                                                            ],
                                                            value='any',
                                                            className="mb-3"
                                                        ),
                                                        
                                                        # Daily Change Filter
                                                        dbc.Label("Daily Price Change:", style={'color': '#fff', 'marginBottom': '10px'}),
                                                        dbc.Select(
                                                            id='change-preset',
                                                            options=[
                                                                {'label': 'Any Change', 'value': 'any'},
                                                                {'label': 'Strong Gainers (> +5%)', 'value': 'strong_up'},
                                                                {'label': 'Moderate Gainers (+2% to +5%)', 'value': 'moderate_up'},
                                                                {'label': 'Small Moves (-2% to +2%)', 'value': 'stable'},
                                                                {'label': 'Moderate Decliners (-5% to -2%)', 'value': 'moderate_down'},
                                                                {'label': 'Strong Decliners (< -5%)', 'value': 'strong_down'}
                                                            ],
                                                            value='any'
                                                        )
                                                    ], title="💰 Price & Change Filters", item_id="price-section"),
                                                    
                                                    dbc.AccordionItem([
                                                        # Stock Universe Selection
                                                        dbc.Label("Stock Universe:", style={'color': '#fff', 'marginBottom': '10px'}),
                                                        dbc.Checklist(
                                                            id='universe-selection',
                                                            options=[
                                                                {'label': '📈 S&P 500', 'value': 'sp500'},
                                                                {'label': '🚀 NASDAQ 100', 'value': 'nasdaq100'},
                                                                {'label': '🏛️ Dow Jones 30', 'value': 'dow30'},
                                                                {'label': '📊 Popular ETFs', 'value': 'etfs'},
                                                                {'label': '🌱 Growth Stocks', 'value': 'growth'},
                                                                {'label': '💰 Dividend Stocks', 'value': 'dividend'},
                                                                {'label': '🇪🇸 Spanish Stocks', 'value': 'spanish'},
                                                                {'label': '🇪🇸 Spanish Indices', 'value': 'spanish_indices'}
                                                            ],
                                                            value=['sp500'],
                                                            style={'color': '#fff'},
                                                            className="mb-3"
                                                        ),
                                                        
                                                        # Result Options
                                                        dbc.Label("Scan Options:", style={'color': '#fff', 'marginBottom': '10px'}),
                                                        dbc.Row([
                                                            dbc.Col([
                                                                dbc.Label("Max Results:", style={'color': '#ccc', 'fontSize': '12px'}),
                                                                dbc.Select(
                                                                    id='result-limit',
                                                                    options=[  # type: ignore
                                                                        {'label': 'Top 10', 'value': 10},
                                                                        {'label': 'Top 25', 'value': 25},
                                                                        {'label': 'Top 50', 'value': 50},
                                                                        {'label': 'Top 100', 'value': 100}
                                                                    ],
                                                                    value=25,
                                                                    size='sm'
                                                                )
                                                            ], width=6),
                                                            dbc.Col([
                                                                dbc.Label("Sort By:", style={'color': '#ccc', 'fontSize': '12px'}),
                                                                dbc.Select(
                                                                    id='sort-by',
                                                                    options=[
                                                                        {'label': 'Volume', 'value': 'volume'},
                                                                        {'label': 'Price Change %', 'value': 'change'},
                                                                        {'label': 'RSI', 'value': 'rsi'},
                                                                        {'label': 'Random', 'value': 'random'}
                                                                    ],
                                                                    value='volume',
                                                                    size='sm'
                                                                )
                                                            ], width=6)
                                                        ])
                                                    ], title="🎯 Universe & Results", item_id="universe-section")
                                                ], start_collapsed=True, className="mb-3"),
                                                
                                                # Scan Button
                                                dbc.Button(
                                                    [
                                                        html.Span("🔍", style={'marginRight': '8px', 'fontSize': '18px'}),
                                                        html.Span("Start Scan", style={'color': '#000', 'fontWeight': 'bold'})
                                                    ],
                                                    id="start-scan-button",
                                                    color="success",
                                                    size="lg",
                                                    className="w-100 mb-3",
                                                    style={
                                                        'background': 'linear-gradient(45deg, #00d4aa, #00ff88)',
                                                        'border': 'none',
                                                        'fontWeight': 'bold'
                                                    },
                                                    n_clicks=0
                                                ),
                                                
                                                # Scan Status
                                                html.Div(id="scan-status", className="text-center mb-3"),
                                                
                                                # Watchlist Section
                                                html.Hr(style={'borderColor': '#333'}),
                                                dbc.Card([
                                                    dbc.CardHeader(html.H5("👀 Watchlist", className="text-center", style={'color': '#00d4aa'})),
                                                    dbc.CardBody([
                                                        # Add Stock to Watchlist
                                                        dbc.Row([
                                                            dbc.Col([
                                                                dbc.Input(
                                                                    id='watchlist-symbol-input',
                                                                    placeholder="Enter stock symbol (e.g., AAPL)",
                                                                    type="text",
                                                                    style={
                                                                        'backgroundColor': '#000000', 
                                                                        'color': '#fff',
                                                                        'border': '2px solid #444',
                                                                        'borderRadius': '8px',
                                                                        'padding': '8px 12px',
                                                                        'fontSize': '14px',
                                                                        'fontWeight': '500',
                                                                        'height': '40px'  # Set fixed height
                                                                    },
                                                                    className="text-uppercase"
                                                                )
                                                            ], width=8),
                                                            dbc.Col([
                                                                dbc.Button(
                                                                    "Add",
                                                                    id="add-to-watchlist-btn",
                                                                    color="success",
                                                                    size="sm",
                                                                    className="w-100",
                                                                    style={
                                                                        'background': 'linear-gradient(45deg, #00d4aa, #00ff88)',
                                                                        'border': 'none',
                                                                        'fontWeight': 'bold',
                                                                        'height': '40px',  # Match input height
                                                                        'padding': '0',    # Remove extra padding
                                                                        'borderRadius': '8px'
                                                                    }
                                                                )
                                                            ], width=4)
                                                        ], className="mb-3", align="center"),  # Add align="center"
                                                        
                                                        # Watchlist Status
                                                        html.Div(id="watchlist-status", className="text-center mb-3"),
                                                        
                                                        # Open Positions Info
                                                        html.Div([
                                                            html.Small([
                                                                html.Span("📈", style={'color': '#00ff88', 'marginRight': '5px'}),
                                                                "Open positions are automatically included and cannot be removed"
                                                            ], style={'color': '#ccc', 'fontStyle': 'italic', 'fontSize': '11px'})
                                                        ], className="mb-2"),
                                                        
                                                        # Watchlist Table
                                                        html.Div(id="watchlist-table-container", children=[
                                                            dbc.Label("Your Watchlist:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                            html.Div(id="watchlist-table", children="No stocks in watchlist")
                                                        ]),
                                                        
                                                        # Load Watchlist Button
                                                        dbc.Button(
                                                            [
                                                                html.Span("📊", style={'marginRight': '8px', 'fontSize': '16px'}),
                                                                html.Span("Load Watchlist", style={'color': '#000', 'fontWeight': 'bold'})
                                                            ],
                                                            id="load-watchlist-button",
                                                            color="info",
                                                            size="md",
                                                            className="w-100 mt-3",
                                                            style={
                                                                'background': 'linear-gradient(45deg, #007bff, #0056b3)',
                                                                'border': 'none',
                                                                'fontWeight': 'bold'
                                                            },
                                                            n_clicks=0
                                                        )
                                                    ], style={'backgroundColor': '#000000'})
                                                ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3"),
                                                
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'})
                                    ])
                                ]
                            ),
                            # Stock Search Tab (Analysis)
                            dbc.Tab(
                                label="🛠️",
                                tab_id="stock-search-tab",
                                children=[
                                    html.Div(style={'padding': '15px 0'}, children=[
                                        # Stock Search Card
                                        dbc.Card([
                                            dbc.CardHeader(html.H4("🛠️ Analysis", className="text-center", style={'color': '#00d4aa'})),
                                            dbc.CardBody([
                                                # Stock Symbol Input Section
                                                dbc.Label("Stock Symbol:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                
                                                # Stock status indicator between label and search bar - minimal space
                                                html.Div(
                                                    id="stock-status-indicator",
                                                    className="mb-2",
                                                    style={
                                                        'textAlign': 'center',
                                                        'fontSize': '12px',
                                                        'color': '#ccc'
                                                    }
                                                ),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Input(
                                                            id='stock-symbol-input',
                                                            placeholder="Enter any US stock symbol (e.g., AAPL, TSLA, SPY)",
                                                            value="SPY",
                                                            type="text",
                                                            style={
                                                                'backgroundColor': '#000000', 
                                                                'color': '#fff',
                                                                'border': '2px solid #444',
                                                                'borderRadius': '8px',
                                                                'padding': '12px 16px',
                                                                'fontSize': '16px',
                                                                'fontWeight': '500'
                                                            },
                                                            className="text-uppercase"
                                                        )
                                                    ], width=8),
                                                    dbc.Col([
                                                        dbc.Button(
                                                            [
                                                                html.Span("🔍", style={'marginRight': '5px', 'fontSize': '16px'}),
                                                                html.Span("Search", style={'fontWeight': 'bold'})
                                                            ],
                                                            id="search-button", 
                                                            color="success", 
                                                            n_clicks=0, 
                                                            className="w-100",
                                                            style={
                                                                'background': 'linear-gradient(45deg, #00d4aa, #00ff88)',
                                                                'border': 'none',
                                                                'borderRadius': '8px',
                                                                'padding': '12px 8px',
                                                                'fontWeight': 'bold',
                                                                'boxShadow': '0 4px 15px rgba(0, 212, 170, 0.2)'
                                                            }
                                                        )
                                                    ], width=4)
                                                ], className="mb-3"),
                                                
                                                html.Hr(style={'borderColor': '#333', 'margin': '20px 0'}),
                                                
                                                # Time Frame Section
                                                dbc.Label("Time Frame:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                dbc.Select(
                                                    id='timeframe-dropdown',
                                                    options=[
                                                        {'label': '📅 Today', 'value': '1d'},
                                                        {'label': '📅 6 Months', 'value': '6mo'},
                                                        {'label': '📅 Year to Date', 'value': 'ytd'},
                                                        {'label': '📅 1 Year', 'value': '1y'},
                                                        {'label': '📅 5 Years', 'value': '5y'},
                                                        {'label': '📅 Max', 'value': 'max'}
                                                    ],
                                                    value='1d',
                                                    className="mb-3",
                                                    style={'backgroundColor': '#000000', 'color': '#fff'}
                                                ),
                                                
                                                # Add frequency dropdown below timeframe dropdown
                                                dbc.Label("Frequency:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Select(
                                                            id='frequency-dropdown',
                                                            options=[
                                                                {'label': '1m', 'value': '1m'},
                                                                {'label': '2m', 'value': '2m'},
                                                                {'label': '5m', 'value': '5m'},
                                                                {'label': '8m', 'value': '8m'},  # Elder's tactical timeframe
                                                                {'label': '15m', 'value': '15m'},
                                                                {'label': '25m', 'value': '25m'},  # Custom 25m interval
                                                                {'label': '30m', 'value': '30m'},
                                                                {'label': '39m', 'value': '39m'},  # Elder's strategic timeframe
                                                            ],
                                                            value='1m',
                                                            className="mb-3",
                                                            style={'backgroundColor': '#000000', 'color': '#fff'}
                                                        )
                                                    ], width=8)
                                                ], className="mb-3"),
                                                
                                                # Chart Type Section
                                                dbc.Label("Chart Type:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                dbc.Select(
                                                    id='chart-type-dropdown',
                                                    options=[
                                                        {'label': '🕯️ Candlesticks', 'value': 'candlestick'},
                                                        {'label': '🏔️ Mountain Chart', 'value': 'mountain'}
                                                    ],
                                                    value='candlestick',
                                                    className="mb-3",
                                                    style={'backgroundColor': '#000000', 'color': '#fff'}
                                                ),
                                                
                                                # Impulse System Toggle
                                                html.Div([
                                                    dbc.Checklist(
                                                        options=[
                                                            {"label": "Use Impulse System", "value": 1}
                                                        ],
                                                        value=[],
                                                        id="impulse-system-toggle",
                                                        switch=True,
                                                        className="mb-2"
                                                    ),
                                                    dbc.FormText([
                                                        "Colors candles based on EMA trend & MACD momentum: ",
                                                        html.Span("■", style={'color': '#00ff88', 'fontWeight': 'bold'}), " Bullish, ", 
                                                        html.Span("■", style={'color': '#ff4444', 'fontWeight': 'bold'}), " Bearish, ", 
                                                        html.Span("■", style={'color': '#00d4ff', 'fontWeight': 'bold'}), " Neutral"
                                                    ],
                                                    style={'fontSize': '11px', 'color': '#aaa'})
                                                ], className="mb-3")
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3"),
                                        
                                        # EMA and ATR Settings Card (Main Chart Settings)
                                        # Lower Chart Selection Card
                                        dbc.Card([
                                            dbc.CardHeader(html.H5("📊 Lower Chart", style={'color': '#00d4aa'})),
                                            dbc.CardBody([
                                                # Lower Chart Selection
                                                dbc.Label("Display:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '12px'}),
                                                dbc.Select(
                                                    id='lower-chart-selection',
                                                    options=[
                                                        {'label': '📊 Volume', 'value': 'volume'},
                                                        {'label': '📈 MACD', 'value': 'macd'},
                                                        {'label': '💪 Force Index', 'value': 'force'},
                                                        {'label': '📉 A/D Line', 'value': 'ad'},
                                                        {'label': '📊 ADX/DI', 'value': 'adx'},
                                                        {'label': '🌊 Slow Stochastic', 'value': 'stochastic'},
                                                        {'label': '📊 RSI', 'value': 'rsi'},
                                                        {'label': '📈 OBV', 'value': 'obv'}
                                                    ],
                                                    value='volume',
                                                    style={'backgroundColor': '#000000', 'color': '#fff'},
                                                    className="mb-3"
                                                ),
                                                
                                                # Dynamic settings section with enhanced container
                                                html.Div([
                                                    html.Div(id='lower-chart-settings', children=[
                                                        # Settings will be dynamically generated based on selection
                                                    ])
                                                ], style={
                                                    'marginTop': '15px'
                                                })
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}),

                                        dbc.Card([
                                            dbc.CardHeader(html.H5("📈 Main Chart Settings", style={'color': '#00d4aa'})),
                                            dbc.CardBody([
                                                # EMA Section
                                                dbc.Label("EMA Periods:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '12px'}),
                                                html.Div(id='ema-periods-container', children=[
                                                    dbc.Row([
                                                        dbc.Col([
                                                            dbc.Label("Fast EMA:", style={'color': '#ccc', 'fontSize': '12px', 'marginBottom': '5px'}),
                                                            dbc.Input(
                                                                id='ema-period-0', 
                                                                type='number', 
                                                                value=13, 
                                                                min=1, 
                                                                max=200, 
                                                                size='sm',
                                                                style={
                                                                    'backgroundColor': '#000000',
                                                                    'border': '1px solid #333',
                                                                    'color': '#fff',
                                                                    'borderRadius': '6px'
                                                                }
                                                            )
                                                        ], width=6),
                                                        dbc.Col([
                                                            dbc.Label("Slow EMA:", style={'color': '#ccc', 'fontSize': '12px', 'marginBottom': '5px'}),
                                                            dbc.Input(
                                                                id='ema-period-1', 
                                                                type='number', 
                                                                value=26, 
                                                                min=1, 
                                                                max=200, 
                                                                size='sm',
                                                                style={
                                                                    'backgroundColor': '#000000',
                                                                    'border': '1px solid #333',
                                                                    'color': '#fff',
                                                                    'borderRadius': '6px'
                                                                }
                                                            )
                                                        ], width=6)
                                                    ], className="mb-3"),
                                                ]),
                                                
                                                # EMA Toggle
                                                dbc.Checklist(
                                                    id='show-ema',
                                                    options=[{
                                                        'label': html.Div([
                                                            html.Span("📊 Show EMAs", style={'color': '#fff', 'fontWeight': '500'})
                                                        ]), 
                                                        'value': 'show'
                                                    }],
                                                    value=['show'],
                                                    style={'color': '#fff'},
                                                    className="mb-3"
                                                ),
                                                
                                                html.Hr(style={'borderColor': '#333', 'margin': '20px 0'}),
                                                
                                                dbc.Label("Price Channels:", style={'color': '#00d4aa', 'fontWeight': 'bold', 'fontSize': '16px', 'marginBottom': '15px'}),
                                                
                                                # ATR Bands Section
                                                dbc.Label("ATR Volatility Bands:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '12px'}),
                                                dbc.Checklist(
                                                    id='atr-bands',
                                                    options=[
                                                        {
                                                            'label': html.Div([
                                                                html.Span("±1 ATR", style={'color': '#fff', 'fontWeight': '500'})
                                                            ]),
                                                            'value': '1'
                                                        },
                                                        {
                                                            'label': html.Div([
                                                                html.Span("±2 ATR", style={'color': '#fff', 'fontWeight': '500'})
                                                            ]),
                                                            'value': '2'
                                                        },
                                                        {
                                                            'label': html.Div([
                                                                html.Span("±3 ATR", style={'color': '#fff', 'fontWeight': '500'})
                                                            ]),
                                                            'value': '3'
                                                        }
                                                    ],
                                                    value=[],
                                                    inline=False,  # Stack vertically for better mobile experience
                                                    style={'color': '#fff'},
                                                    className="mb-3"
                                                ),
                                                
                                                # Bollinger Bands Section
                                                dbc.Label("Bollinger Bands:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '12px'}),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Checklist(
                                                            id='bollinger-bands',
                                                            options=[
                                                                {
                                                                    'label': html.Div([
                                                                        html.Span("Show Bollinger Bands", style={'color': '#fff', 'fontWeight': '500'})
                                                                    ]),
                                                                    'value': 'show'
                                                                }
                                                            ],
                                                            value=[],
                                                            style={'color': '#fff'},
                                                            className="mb-2"
                                                        )
                                                    ], width=12),
                                                    dbc.Col([
                                                        dbc.Label("Period:", style={'color': '#ccc', 'fontSize': '12px'}),
                                                        dbc.Input(id='bollinger-period', type='number', value=26, min=5, max=50, size='sm',
                                                                  style={'backgroundColor': '#000000', 'color': '#fff', 'border': '1px solid #333'})
                                                    ], width=6),
                                                    dbc.Col([
                                                        dbc.Label("StdDev:", style={'color': '#ccc', 'fontSize': '12px'}),
                                                        dbc.Input(id='bollinger-stddev', type='number', value=2, min=1, max=4, step=0.5, size='sm',
                                                                  style={'backgroundColor': '#000000', 'color': '#fff', 'border': '1px solid #333'})
                                                    ], width=6)
                                                ], className="mb-3"),
                                                
                                                # Autoenvelope Section
                                                dbc.Label("Autoenvelope:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '12px'}),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Checklist(
                                                            id='autoenvelope',
                                                            options=[
                                                                {
                                                                    'label': html.Div([
                                                                        html.Span("Show Autoenvelope", style={'color': '#fff', 'fontWeight': '500'})
                                                                    ]),
                                                                    'value': 'show'
                                                                }
                                                            ],
                                                            value=[],
                                                            style={'color': '#fff'},
                                                            className="mb-2"
                                                        )
                                                    ], width=12),
                                                    dbc.Col([
                                                        dbc.Label("Period:", style={'color': '#ccc', 'fontSize': '12px'}),
                                                        dbc.Input(id='autoenvelope-period', type='number', value=26, min=5, max=50, size='sm',
                                                                  style={'backgroundColor': '#000000', 'color': '#fff', 'border': '1px solid #333'})
                                                    ], width=6),
                                                    dbc.Col([
                                                        dbc.Label("Percent:", style={'color': '#ccc', 'fontSize': '12px'}),
                                                        dbc.Input(id='autoenvelope-percent', type='number', value=6, min=1, max=10, step=0.5, size='sm',
                                                                  style={'backgroundColor': '#000000', 'color': '#fff', 'border': '1px solid #333'})
                                                    ], width=6)
                                                ])
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3")
                                    ])
                                ]
                            ),
                            # Insights Tab
                            dbc.Tab(
                                label="💡",
                                tab_id="insights-tab",
                                children=[
                                    html.Div(style={'padding': '15px 0'}, children=[
                                        dbc.Card([
                                            dbc.CardHeader(html.H4("💡 Insights", className="text-center", style={'color': '#00d4aa'})),                            dbc.CardBody([
                                # Warning message with documentation link
                                html.Div([
                                    html.Span("⚠️", style={'color': '#ffc107', 'fontSize': '18px', 'marginRight': '8px'}),
                                    html.Span("Handle with care! Read the ", style={'color': '#fff', 'fontWeight': '500'}),
                                    html.A(
                                        "documentation",
                                        href="https://github.com/jacorvillo/stock_market_dashboard",
                                        target="_blank",
                                        style={
                                            'color': '#00d4aa',
                                            'textDecoration': 'underline',
                                            'fontWeight': 'bold'
                                        }
                                    ),
                                    html.Span(" first", style={'color': '#fff', 'fontWeight': '500'})
                                ], style={
                                    'backgroundColor': '#1a1a1a',
                                    'border': '1px solid #ffc107',
                                    'borderRadius': '8px',
                                    'padding': '12px 16px',
                                    'marginBottom': '20px',
                                    'textAlign': 'center'
                                }),
                                
                                # Trading Style Selection
                                dbc.Label("Trading Style:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '15px'}),
                                                dbc.RadioItems(
                                                    id='insights-trading-style',
                                                    options=[
                                                        {
                                                            'label': html.Div([
                                                                html.Div([
                                                                    "⚡ Short Term",
                                                                    html.Small(" (Today's data only)", style={'color': '#ccc', 'display': 'block', 'fontStyle': 'italic'})
                                                                ], style={'marginLeft': '8px'})
                                                            ]), 
                                                            'value': 'short_term'
                                                        },
                                                        {
                                                            'label': html.Div([
                                                                html.Div([
                                                                    "📊 Swing Trading",
                                                                    html.Small(" (2-10 day positions)", style={'color': '#ccc', 'display': 'block', 'fontStyle': 'italic'})
                                                                ], style={'marginLeft': '8px'})
                                                            ]), 
                                                            'value': 'swing_trading'
                                                        }
                                                    ],
                                                    value='swing_trading',  # Default to swing trading
                                                    style={'color': '#fff'},
                                                    className="mb-4"
                                                ),
                                                
                                                # Stock Symbol Input (moved below trading style)
                                                dbc.Label("Stock Symbol to Analyze:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Input(
                                                            id='insights-stock-input',
                                                            placeholder="Enter any US stock symbol (e.g., AAPL, TSLA, SPY)",
                                                            value="SPY",
                                                            type="text",
                                                            style={
                                                                'backgroundColor': '#000000', 
                                                                'color': '#fff',
                                                                'border': '3px solid #00d4aa',
                                                                'borderRadius': '8px',
                                                                'padding': '12px 16px',
                                                                'fontSize': '16px',
                                                                'fontWeight': '500',
                                                                'textAlign': 'center'
                                                            },
                                                            className="text-uppercase"
                                                        )
                                                    ], width=12)
                                                ], className="mb-3"),
                                                
                                                # Run Insights Button
                                                html.Div([
                                                    dbc.Button(
                                                        [
                                                            html.Span("🧠", style={'marginRight': '8px', 'fontSize': '18px'}),
                                                            # Text in black
                                                            html.Span("Run Insights!", style={'color': '#000', 'fontWeight': 'bold'})
                                                        ],
                                                        id="run-insights-button",
                                                        color="success",
                                                        size="lg",
                                                        className="w-100",
                                                        style={
                                                            'background': 'linear-gradient(45deg, #00d4aa, #00ff88)',
                                                            'border': 'none',
                                                            'fontWeight': 'bold',
                                                            'fontSize': '16px',
                                                            'padding': '12px 20px',
                                                            'boxShadow': '0 4px 15px rgba(0, 212, 170, 0.3)'
                                                        },
                                                        n_clicks=0
                                                    )
                                                ], className="mb-3"),
                                                
                                                # Loading/Status indicator
                                                html.Div(
                                                    id="insights-status",
                                                    style={'textAlign': 'center', 'marginTop': '10px'},
                                                    children=[]
                                                ),
                                                
                                                # Insights Results Area (initially hidden)
                                                html.Div(
                                                    id="insights-results",
                                                    style={'marginTop': '20px'},
                                                    children=[]
                                                )
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'})
                                    ])
                                ]
                            ),
                            # IRL Trade Tab
                            dbc.Tab(
                                label="💸",
                                tab_id="irl-trade-tab",
                                children=[
                                    html.Div(style={'padding': '15px 0'}, children=[
                                        dbc.Card([
                                            dbc.CardHeader(
                                                html.H4("💸 IRL Trade Simulator", className="text-center", style={'color': '#00d4aa'})
                                            ),
                                            dbc.CardBody([
                                                # Equity display with hide/show button
                                                html.Div(
                                                    id="irl-equity-display",
                                                    style={'fontSize': '22px', 'fontWeight': 'bold', 'marginBottom': '20px'}
                                                ),

                                                # Stock search and Trade Apgar section
                                                dbc.Label("Stock Symbol:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Input(id='irl-stock-symbol-input', placeholder="Enter stock symbol", type="text", className="mb-2 text-uppercase")
                                                    ], width=8),
                                                    dbc.Col([
                                                        dbc.Button("🔍 Check Apgar", id="irl-check-apgar-btn", color="info", size="sm", className="w-100")
                                                    ], width=4)
                                                ], className="mb-3"),
                                                
                                                # Trade Apgar Results (initially hidden)
                                                html.Div(
                                                    id="irl-apgar-results",
                                                    className="d-none",
                                                    children=[]
                                                ),

                                                # Open position form
                                                dbc.Label("Open Position:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                dbc.RadioItems(
                                                    id='irl-buy-sell-radio',
                                                    options=[
                                                        {'label': 'Buy', 'value': 'buy'},
                                                        {'label': 'Sell', 'value': 'sell'}
                                                    ],
                                                    value='buy',
                                                    inline=True,
                                                    className="mb-2"
                                                ),
                                                dbc.Input(id='irl-amount-input', placeholder="Amount to invest", type="number", className="mb-2"),
                                                
                                                # 2% Rule Warning (initially hidden)
                                                html.Div(
                                                    id="irl-2percent-warning",
                                                    className="d-none",
                                                    children=[
                                                        html.Small([
                                                            html.Span("⚠️", style={'color': '#ffc107', 'marginRight': '5px'}),
                                                            "This trade breaks the 2% Rule (risk management guideline)",
                                                        ], style={
                                                            'color': '#ffc107',
                                                            'fontSize': '11px',
                                                            'fontStyle': 'italic',
                                                            'backgroundColor': '#1a1a1a',
                                                            'padding': '5px 8px',
                                                            'borderRadius': '4px',
                                                            'border': '1px solid #ffc107'
                                                        })
                                                    ],
                                                    style={'marginBottom': '8px'}
                                                ),
                                                
                                                dbc.Input(id='irl-stop-input', placeholder="Stop price", type="number", className="mb-2"),
                                                dbc.Input(id='irl-target-input', placeholder="Target price", type="number", className="mb-2"),
                                                dbc.Button("Open Position", id="irl-open-position-btn", color="success", className="mb-3 w-100"),
                                                html.Div(id="irl-open-position-status", className="mb-3"),

                                                html.Hr(style={'borderColor': '#333', 'margin': '20px 0'}),

                                                # Close position section
                                                dbc.Label("Close Position:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                html.Div(id="irl-open-positions-list"),
                                            ])
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'})
                                    ])
                                ]
                            )
                        ],
                        style={'backgroundColor': '#000000'}
                    )
                ]),
                id="sidebar-collapse",
                is_open=True
            ),
            width=2,
            id="sidebar-col",
            style={"paddingLeft": "0", "paddingRight": "0", "marginLeft": "0", "marginRight": "0"}
        ),
        
        # Charts column
        dbc.Col([
            # Main content area that switches between chart and scanner results
            html.Div(
                id="main-content-area",
                style={'height': '90vh', 'backgroundColor': '#000000', 'position': 'relative'},
                children=[
                    # Intraday warning message component (positioned absolutely at bottom)
                    html.Div(
                        id="intraday-warning-message",
                        className="alert alert-warning fade show d-none",
                        style={
                            'position': 'absolute',
                            'bottom': '10px',
                            'left': '10px',
                            'right': '10px',
                            'zIndex': 1001,
                            'margin': '0'
                        },
                        children=[]
                    ),
                    # Error message component (positioned absolutely)
                    html.Div(
                        id="chart-error-message", 
                        className="alert alert-warning fade show d-none",
                        style={
                            'position': 'absolute',
                            'top': '10px',
                            'left': '10px',
                            'right': '10px',
                            'zIndex': 1001,
                            'margin': '0'
                        },
                        children=[]
                    ),
                    # Market closed message - hidden by default (positioned absolutely)
                    html.Div(
                        id="market-closed-message",
                        className="d-none",
                        style={
                            'position': 'absolute',
                            'top': '0',
                            'left': '0',
                            'width': '100%',
                            'height': '100%', 
                            'display': 'flex', 
                            'alignItems': 'center', 
                            'justifyContent': 'center', 
                            'flexDirection': 'column',
                            'backgroundColor': '#000000',
                            'borderRadius': '8px',
                            'padding': '20px',
                            'border': '1px solid #333',
                            'zIndex': 1002
                        },
                        children=[]  # Will be set dynamically in callback
                    ),
                    # Scanner Results Area (hidden by default, positioned absolutely)
                    html.Div(
                        id="scanner-results-area",
                        className="d-none",
                        style={
                            'position': 'absolute',
                            'top': '0',
                            'left': '0',
                            'width': '100%',
                            'height': '100%', 
                            'overflow': 'auto', 
                            'backgroundColor': '#000000',
                            'zIndex': 1000,
                            'padding': '20px'
                        },
                        children=[]
                    ),
                    # Combined chart with main price chart on top and indicator chart below
                    dcc.Graph(
                        id='combined-chart', 
                        style={
                            'backgroundColor': '#000000', 
                            'height': '90vh',
                            'position': 'absolute',
                            'top': '0',
                            'left': '0',
                            'width': '100%',
                            'zIndex': 1
                        }
                    )
                ]
            )
        ], width=10, id="chart-col", style={"paddingLeft": "0", "paddingRight": "0", "marginLeft": "0", "marginRight": "0"})
    ], style={"marginLeft": "0", "marginRight": "0", "paddingLeft": "0", "paddingRight": "0"}), # End of dbc.Row
    
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Update every 30 seconds - balanced for performance
        n_intervals=0
    ),
    dcc.Store(id='stock-data-store'),
    dcc.Store(id='current-symbol-store', data='SPY'),
    dcc.Store(id='ema-periods-store', data=[13, 26]),
    dcc.Store(id='irl-equity-store'),
    # Watchlist stores
    dcc.Store(id='watchlist-store', data=[]),
    # Hidden stores for indicator parameters
    dcc.Store(id='macd-fast-store', data=12),
    dcc.Store(id='macd-slow-store', data=26),
    dcc.Store(id='macd-signal-store', data=9),
    dcc.Store(id='force-smoothing-store', data=2),
    dcc.Store(id='adx-period-store', data=13),
    dcc.Store(id='adx-components-store', data=['adx', 'di_plus', 'di_minus']),
    dcc.Store(id='stochastic-period-store', data=5),
    dcc.Store(id='rsi-period-store', data=13),
    # New stores for Bollinger Bands and Autoenvelope
    dcc.Store(id='bollinger-bands-store', data={'show': False, 'period': 26, 'stddev': 2}),
    dcc.Store(id='autoenvelope-store', data={'show': False, 'period': 26, 'percent': 6}),
    # Store to track Trade Apgar preset
    dcc.Store(id='apgar-preset-store', data=False),
    # Store to track active preset button
    dcc.Store(id='active-preset-store', data=None),
    # Add a dcc.Store for scan progress
    dcc.Store(id='scan-progress-store', data={'percent': 0})
], fluid=True)  # Make container full width

# --- Scanner Progress Global State ---
scan_progress = {'percent': 0}
scan_progress_lock = threading.Lock()

def set_scan_progress(percent):
    with scan_progress_lock:
        scan_progress['percent'] = percent

def get_scan_progress():
    with scan_progress_lock:
        return scan_progress.get('percent', 0)

# Callback to update dynamic lower chart settings based on selection
@callback(
    Output('lower-chart-settings', 'children'),
    [Input('lower-chart-selection', 'value')]
)
def update_lower_chart_settings_callback(chart_type):
    """Call update_lower_chart_settings function from functions module"""
    return update_lower_chart_settings(chart_type)

# Callback to update symbol store
@callback(
    Output('current-symbol-store', 'data'),
    [Input('search-button', 'n_clicks'),
     Input('stock-symbol-input', 'n_submit')],
    [State('stock-symbol-input', 'value')]
)
def update_symbol_callback(n_clicks, n_submit, symbol):
    """Call update_symbol function from functions module"""
    return update_symbol(n_clicks or n_submit, symbol)

# Callback to handle direct changes to the input value and auto-uppercase
@callback(
    Output('stock-symbol-input', 'value', allow_duplicate=True),
    [Input('stock-symbol-input', 'value')],
    prevent_initial_call=True
)
def format_symbol_input_callback(value):
    """Call format_symbol_input function from functions module"""
    return format_symbol_input(value)

# Callback to manage EMA periods for two fixed EMAs
@callback(
    [Output('ema-periods-container', 'children'),
     Output('ema-periods-store', 'data')],
    [Input('ema-period-0', 'value'),
     Input('ema-period-1', 'value')],
    [State('ema-periods-store', 'data')]
)
def update_ema_periods_callback(ema0, ema1, current_emas):
    """Update EMA periods for the two fixed EMAs"""
    # Use default values if inputs are None or invalid
    fast_ema = ema0 if ema0 and ema0 > 0 else 13
    slow_ema = ema1 if ema1 and ema1 > 0 else 26
    
    # Create the fixed layout with two EMAs
    new_layout = [
        dbc.Row([
            dbc.Col([
                dbc.Label("Fast EMA:", style={'color': '#fff', 'fontSize': '12px'}),
                dbc.Input(id='ema-period-0', type='number', value=fast_ema, min=1, max=200, size='sm')
            ], width=6),
            dbc.Col([
                dbc.Label("Slow EMA:", style={'color': '#fff', 'fontSize': '12px'}),
                dbc.Input(id='ema-period-1', type='number', value=slow_ema, min=1, max=200, size='sm')
            ], width=6)
        ], className="mb-2"),
    ]
    
    return new_layout, [fast_ema, slow_ema]

# Callback to update store values when UI elements are present
@callback(
    [Output('macd-fast-store', 'data'),
     Output('macd-slow-store', 'data'),
     Output('macd-signal-store', 'data')],
    [Input('macd-fast', 'value'),
     Input('macd-slow', 'value'),
     Input('macd-signal', 'value')],
    prevent_initial_call=True
)
def update_macd_stores_callback(fast, slow, signal):
    """Call update_macd_stores function from functions module"""
    return update_macd_stores(fast, slow, signal)

# Callback to update force index store
@callback(
    Output('force-smoothing-store', 'data'),
    Input('force-smoothing', 'value'),
    prevent_initial_call=True
)
def update_force_store_callback(smoothing):
    """Call update_force_store function from functions module"""
    return update_force_store(smoothing)

# Callback to update ADX parameters store
@callback(
    [Output('adx-period-store', 'data'),
     Output('adx-components-store', 'data')],
    [Input('adx-period', 'value'),
     Input('adx-components', 'value')],
    prevent_initial_call=True
)
def update_adx_stores_callback(period, components):
    """Call update_adx_stores function from functions module"""
    return update_adx_stores(period, components)

# Callback to update stochastic period store
@callback(
    Output('stochastic-period-store', 'data'),
    Input('stochastic-period', 'value'),
    prevent_initial_call=True
)
def update_stochastic_store_callback(period):
    """Call update_stochastic_store function from functions module"""
    return update_stochastic_store(period)

# Callback to update Bollinger Bands store
@callback(
    Output('bollinger-bands-store', 'data'),
    [Input('bollinger-bands', 'value'),
     Input('bollinger-period', 'value'),
     Input('bollinger-stddev', 'value')],
    prevent_initial_call=True
)
def update_bollinger_store_callback(show, period, stddev):
    """Update Bollinger Bands settings"""
    return {
        'show': 'show' in show if show else False,
        'period': period,
        'stddev': stddev
    }

# Callback to update Autoenvelope store
@callback(
    Output('autoenvelope-store', 'data'),
    [Input('autoenvelope', 'value'),
     Input('autoenvelope-period', 'value'),
     Input('autoenvelope-percent', 'value')],
    prevent_initial_call=True
)
def update_autoenvelope_store_callback(show, period, percent):
    """Update Autoenvelope settings"""
    return {
        'show': 'show' in show if show else False,
        'period': period,
        'percent': percent
    }

# Callback to update RSI period store
@callback(
    Output('rsi-period-store', 'data'),
    Input('rsi-period', 'value'),
    prevent_initial_call=True
)
def update_rsi_store_callback(period):
    """Call update_rsi_store function from functions module"""
    return update_rsi_store(period)

# Add a callback to update frequency options based on timeframe
@callback(
    [Output('frequency-dropdown', 'options'), Output('frequency-dropdown', 'value')],
    [Input('timeframe-dropdown', 'value')]
)
def update_frequency_options(timeframe):
    """Update frequency options based on timeframe with proper Yahoo Finance intervals"""
    if timeframe in ['1d', 'yesterday']:
        # Intraday frequencies - only available for 1d and yesterday
        options = [
            {'label': '1m', 'value': '1m'},
            {'label': '2m', 'value': '2m'},
            {'label': '5m', 'value': '5m'},
            {'label': '8m', 'value': '8m'},  # Elder's tactical timeframe
            {'label': '15m', 'value': '15m'},
            {'label': '25m', 'value': '25m'},  # Custom 25m interval
            {'label': '30m', 'value': '30m'},
            {'label': '39m', 'value': '39m'},  # Elder's strategic timeframe
        ]
        value = '1m'  # Default to 1m for intraday
    elif timeframe == '6mo':
        # For 6 months, keep daily as default
        options = [
            {'label': '1d', 'value': '1d'},
            {'label': '1wk', 'value': '1wk'}
        ]
        value = '1d'  # Default to daily for 6 months
    elif timeframe in ['ytd', '1y', '5y', 'max']:
        # For YTD, 1Y, 5Y and max, default to weekly
        options = [
            {'label': '1d', 'value': '1d'},
            {'label': '1wk', 'value': '1wk'}
        ]
        value = '1wk'  # Default to weekly for longer timeframes
    else:
        # Default fallback
        options = [{'label': '1d', 'value': '1d'}]
        value = '1d'
    return options, value

# Callback to update data with custom indicator parameters
@callback(
    [Output('stock-data-store', 'data'),
     Output('chart-error-message', 'children'),
     Output('chart-error-message', 'className')],
    [Input('interval-component', 'n_intervals'),
     Input('current-symbol-store', 'data'),
     Input('timeframe-dropdown', 'value'),
     Input('frequency-dropdown', 'value'),
     Input('ema-periods-store', 'data'),
     Input('macd-fast-store', 'data'),
     Input('macd-slow-store', 'data'),
     Input('macd-signal-store', 'data'),
     Input('force-smoothing-store', 'data'),
     Input('adx-period-store', 'data'),
     Input('stochastic-period-store', 'data'),
     Input('rsi-period-store', 'data')]
)
def update_data_callback(n, symbol, timeframe, frequency, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, adx_period, stoch_period, rsi_period):
    """Call update_data function from functions module"""
    return update_data(n, symbol, timeframe, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, adx_period, stoch_period, rsi_period, frequency)

# Callback for combined chart
@callback(
    [Output('combined-chart', 'figure'),
     Output('combined-chart', 'style'),
     Output('market-closed-message', 'className'),
     Output('market-closed-message', 'children'),
     Output('intraday-warning-message', 'children'),
     Output('intraday-warning-message', 'className')],
    [Input('stock-data-store', 'data'),
     Input('current-symbol-store', 'data'),
     Input('chart-type-dropdown', 'value'),
     Input('show-ema', 'value'),
     Input('ema-periods-store', 'data'),
     Input('atr-bands', 'value'),
     Input('lower-chart-selection', 'value'),
     Input('adx-components-store', 'data'),
     Input('timeframe-dropdown', 'value'),
     Input('frequency-dropdown', 'value'),
     Input('impulse-system-toggle', 'value'),
     Input('bollinger-bands-store', 'data'),
     Input('autoenvelope-store', 'data'),
     Input('sidebar-tabs', 'active_tab')],
    [State('combined-chart', 'relayoutData')],
    prevent_initial_call=False
)
def update_combined_chart_callback(data, symbol, chart_type, show_ema, ema_periods, atr_bands, lower_chart_type, adx_components, timeframe, frequency, impulse_system_toggle, bollinger_bands, autoenvelope, active_tab, relayout_data):
    """Call update_combined_chart function from functions module"""
    ctx = dash.callback_context
    volume_comparison = 'none'  # Default value
    use_impulse_system = bool(impulse_system_toggle and 1 in impulse_system_toggle)
    unreliable_warning = None
    unreliable_class = 'alert alert-warning fade show d-none'

    # Check for unreliable indicators in intraday views
    is_intraday = timeframe in ['1d', 'yesterday']
    if data and is_intraday:
        import pandas as pd
        df = pd.DataFrame(data)
        unreliable_present = False
        if 'unreliable_indicators' in df.columns:
            unreliable_present = bool(df['unreliable_indicators'].any())
        if unreliable_present and active_tab != 'scanner-tab':
            unreliable_warning = (
                html.Div([
                    html.Span("⚠️", style={'color': '#ffc107', 'fontSize': '18px', 'marginRight': '8px'}),
                    html.Span("Indicator lines (EMA, MACD, RSI, Stochastic, ADX) may be unreliable for the first bars of the session due to limited lookback data.", style={'color': '#fff', 'fontWeight': '500'}),
                    html.Br(),
                    html.Span("This is normal for intraday charts. The lines become reliable as more data accumulates.", style={'color': '#aaa', 'fontSize': '12px'})
                ]),
            )
            unreliable_class = 'alert alert-warning fade show'
        elif active_tab == 'scanner-tab':
            unreliable_warning = None
            unreliable_class = 'alert alert-warning fade show d-none'

    # Always show the Today view, even if empty
    if timeframe == '1d' and (not data or len(data) == 0):
        empty_fig = go.Figure()
        # Dynamic closed market message with symbol
        closed_msg_children = [
            html.H2(f"The market for {symbol or 'this stock'} is currently closed or not available.", style={'color': '#ff4444', 'textAlign': 'center', 'marginBottom': '20px'}),
            html.H5("Try again during market hours, or view 5-year weekly data.", 
                   style={'color': '#ccc', 'textAlign': 'center', 'fontWeight': 'normal'}),
            html.Div(style={'marginTop': '30px', 'textAlign': 'center'}, children=[
                dbc.Button(
                    "📅 View 5Y/1WK",
                    id="view-5y-btn",
                    color="info",
                    outline=True
                )
            ])
        ]
        return empty_fig, {'backgroundColor': '#000000', 'height': '90vh'}, 'd-block', closed_msg_children, unreliable_warning, unreliable_class
    else:
        fig, style, market_closed = update_combined_chart(
            data, symbol, chart_type, show_ema, ema_periods, atr_bands, 
            lower_chart_type, adx_components, volume_comparison, relayout_data, 
            timeframe, frequency, use_impulse_system, bollinger_bands, autoenvelope
        )
        # When not closed, hide the message
        return fig, style, market_closed, [], unreliable_warning, unreliable_class

# Callback to hide EMA options for 1D timeframe
@callback(
    [Output('ema-periods-container', 'style'),
     Output('show-ema', 'style'),
     Output('lower-chart-selection', 'options')],
    [Input('timeframe-dropdown', 'value')]
)
def update_indicator_options_callback(timeframe):
    """Call update_indicator_options function from functions module"""
    return update_indicator_options(timeframe)

# Callback for volume comparison in combined chart (only when volume chart is active)
@callback(
    [Output('combined-chart', 'figure', allow_duplicate=True),
     Output('combined-chart', 'style', allow_duplicate=True),
     Output('market-closed-message', 'className', allow_duplicate=True)],
    [Input('volume-comparison-select', 'value')],
    [State('stock-data-store', 'data'),
     State('current-symbol-store', 'data'),
     State('chart-type-dropdown', 'value'),
     State('show-ema', 'value'),
     State('ema-periods-store', 'data'),
     State('atr-bands', 'value'),
     State('lower-chart-selection', 'value'),
     State('adx-components-store', 'data'),
     State('timeframe-dropdown', 'value'),
     State('impulse-system-toggle', 'value'),
     State('bollinger-bands-store', 'data'),
     State('autoenvelope-store', 'data'),
     State('combined-chart', 'relayoutData')],
    prevent_initial_call=True
)
def update_combined_chart_volume_comparison(volume_comparison, data, symbol, chart_type, show_ema, ema_periods, atr_bands, lower_chart_type, adx_components, timeframe, impulse_system_toggle, bollinger_bands, autoenvelope, relayout_data):
    """Update combined chart when volume comparison changes"""
    # Check if impulse system is enabled
    use_impulse_system = bool(impulse_system_toggle and 1 in impulse_system_toggle)
    # Only trigger when volume chart is selected
    if lower_chart_type == 'volume':
        volume_comparison = volume_comparison or 'none'
        
        # Check if we're in "Today" mode and data is empty (markets closed)
        if timeframe == '1d' and (not data or len(data) == 0):
            # Show the market closed message and hide the chart
            empty_fig = go.Figure()
            
            # We always show the market closed message when in Today mode with no data
            return empty_fig, {'display': 'none'}, 'd-block'
        else:
            # Normal case - show the chart and hide the message
            fig, style, market_closed = update_combined_chart(data, symbol, chart_type, show_ema, ema_periods, atr_bands, lower_chart_type, adx_components, volume_comparison, relayout_data, timeframe, None, use_impulse_system, bollinger_bands, autoenvelope)
            return fig, {'backgroundColor': '#000000', 'height': '90vh'}, 'd-none'
    else:
        # Return no update if not volume chart
        raise PreventUpdate

# Callback to toggle sidebar and adjust column widths
@callback(
    [Output("sidebar-collapse", "is_open"),
     Output("sidebar-col", "width"),
     Output("chart-col", "width")],
    [Input("sidebar-toggle-button", "n_clicks")],
    [State("sidebar-collapse", "is_open")]
)
def toggle_sidebar_and_resize(n_clicks, is_open):
    """Toggle sidebar visibility and adjust column widths"""
    if n_clicks:
        # If open, close it and increase chart width
        if is_open:
            return False, 0, 12
        # If closed, open it and reduce chart width
        else:
            return True, 3, 9
    
    # Default to open sidebar
    return True, 3, 9

# Callback for "View Previous Session" button in the market closed message
@callback(
    [Output('timeframe-dropdown', 'value', allow_duplicate=True),
     Output('frequency-dropdown', 'value', allow_duplicate=True)],
    [Input('view-5y-btn', 'n_clicks')],
    prevent_initial_call=True
)
def view_5y_callback(n_clicks):
    """Switch to 5-year weekly data when the button is clicked"""
    if n_clicks:
        return '5y', '1wk'
    raise PreventUpdate

# Callback for loading indicator with timestamp - simplified
@callback(
    Output('loading-output', 'children'),
    [Input('current-symbol-store', 'data')],
    prevent_initial_call=True
)
def update_loading_feedback(symbol):
    """Provide simple feedback when loading new ticker data"""
    if symbol:
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"✅ {symbol} loaded at {timestamp}"
    return ""

# Simplified stock status indicator callback
@callback(
    Output('stock-status-indicator', 'children'),
    [Input('current-symbol-store', 'data')]
)
def update_status_indicator_callback(symbol):
    """Update the stock status indicator with current symbol"""
    fallback_info = {
        'symbol': symbol or 'SPY',
        'time': datetime.now().strftime('%H:%M:%S'),
        'color': '#00d4aa'
    }
    return update_stock_status_indicator(fallback_info)

# ========== INSIGHTS TAB CALLBACKS ==========

# Callback to handle insights analysis
@callback(
    [Output('insights-status', 'children'),
     Output('insights-results', 'children')],
    [Input('run-insights-button', 'n_clicks'),
     Input('insights-stock-input', 'n_submit')],
    [State('insights-stock-input', 'value'),
     State('insights-trading-style', 'value')],
    prevent_initial_call=True
)
def run_insights_analysis(run_clicks, n_submit, insights_symbol, trading_style):
    """Handle the insights analysis when the button is clicked or Enter is pressed"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    # Use insights symbol or fallback to SPY
    symbol = (insights_symbol or 'SPY').strip().upper()
    
    # Validate trading style for analysis
    if not trading_style:
        return [
            dbc.Alert("Please select a trading style", color="warning", className="mt-2"),
            []
        ]
    
    try:
        # Show loading state first
        loading_status = html.Div([
            dbc.Spinner(size="sm", color="success"),
            html.Span(f" Analyzing {symbol} for {trading_style.replace('_', ' ').title()}...", 
                     style={'marginLeft': '10px', 'color': '#00d4aa'})
        ])
        
        # Determine timeframe based on trading style
        if trading_style == 'short_term':
            timeframe = '1d'  # Today's data only
        else:
            timeframe = '6mo'  # Good balance of data and relevance for swing trading
        
        # Fetch stock data with indicators
        stock_data_result = get_stock_data(symbol, timeframe)
        
        # Handle the tuple return from get_stock_data
        if isinstance(stock_data_result, tuple):
            stock_data = stock_data_result[0]  # Extract the DataFrame from the tuple
        else:
            stock_data = stock_data_result
        
        # Handle market closed scenario for Short Term analysis
        if trading_style == 'short_term' and (stock_data is None or stock_data.empty):
            market_closed_status = html.Div([
                html.Span("⚠️", style={'color': '#ffc107', 'marginRight': '10px', 'fontSize': '16px'}),
                html.Span(f"Market is currently closed for {symbol}", style={'color': '#ffc107'}),
                html.Br(),
                html.Small("Short Term analysis requires today's market data. Try again during market hours (9:30AM - 4:00PM ET).", 
                          style={'color': '#ccc', 'fontStyle': 'italic'})
            ])
            return [market_closed_status, [], dash.no_update]
        
        # Handle general data fetch errors
        if stock_data is None or stock_data.empty:
            return [
                dbc.Alert(f"Unable to fetch data for {symbol}. Please try again.", color="danger", className="mt-2"),
                []
            ]
        
        # Calculate all indicators
        df_with_indicators = calculate_indicators(
            stock_data, 
            ema_periods=[13, 26, 50],  # Standard EMA periods for analysis
            macd_fast=12, 
            macd_slow=26, 
            macd_signal=9,
            force_smoothing=2,
            adx_period=14,
            stoch_period=14,
            rsi_period=14
        )
        
        # Initialize insights analyzer
        insights_analyzer = TechnicalInsights()
        
        # Generate comprehensive insights
        insights_data = insights_analyzer.analyze_stock(df_with_indicators, symbol)
        
        # Generate formatted summary
        insights_summary = generate_insights_summary(insights_data)
        
        # Create detailed results cards
        results = create_insights_results_layout(insights_data, trading_style)
        
        # Return success status and results
        success_status = html.Div([
            html.Span("✅", style={'color': '#28a745', 'marginRight': '10px', 'fontSize': '16px'}),
            html.Span(f"Analysis completed for {symbol}", style={'color': '#28a745'})
        ])
        
        return [success_status, results]
        
    except Exception as e:
        # Handle any errors gracefully
        error_status = html.Div([
            html.Span("⚠️", style={'color': '#dc3545', 'marginRight': '10px', 'fontSize': '16px'}),
            html.Span(f"Error analyzing {symbol}: {str(e)}", style={'color': '#dc3545'})
        ])
        
        return [error_status, []]


def create_insights_results_layout(insights_data, trading_style):
    """Create the detailed insights results layout"""
    
    # Get trading style info
    style_info = {
        'short_term': {'name': 'Short Term', 'emoji': '⚡', 'color': '#ff6b6b'},
        'swing_trading': {'name': 'Swing Trading', 'emoji': '📊', 'color': '#4ecdc4'}
    }
    current_style = style_info.get(trading_style, style_info['swing_trading'])
    
    # Main summary card
    summary_card = dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.Span(current_style['emoji'], style={'marginRight': '10px', 'fontSize': '24px'}),
                f"{current_style['name']} Analysis for {insights_data['symbol']}"
            ], style={'color': '#00d4aa', 'marginBottom': '0'})
        ]),
        dbc.CardBody([
            # Overall sentiment and recommendation
            html.Div([
                html.H6("📊 Overall Market Assessment", style={'color': '#fff', 'marginBottom': '15px'}),
                html.Div([
                    html.Strong("Sentiment: "), 
                    html.Span(
                        insights_data['overall_sentiment']['sentiment']['text'], 
                        style={
                            'marginLeft': '10px',
                            'color': insights_data['overall_sentiment']['sentiment']['color'],
                            'fontWeight': insights_data['overall_sentiment']['sentiment'].get('weight', 'normal')
                        }
                    ),
                    html.Br(),
                    html.Strong("Recommendation: "), 
                    html.Span(
                        insights_data['trading_recommendation']['recommendation']['text'], 
                        style={
                            'marginLeft': '10px',
                            'color': insights_data['trading_recommendation']['recommendation']['color'],
                            'fontWeight': insights_data['trading_recommendation']['recommendation'].get('weight', 'normal')
                        }
                    ),
                    html.Br(),
                    html.Strong("Risk Level: "), 
                    html.Span(insights_data['trading_recommendation']['risk_level'], style={'marginLeft': '10px', 'color': '#ffc107'})
                ], style={'color': '#ccc', 'marginBottom': '20px'})
            ]),
            
            # Key insights row
            dbc.Row([
                dbc.Col([
                    html.H6("🎯 Price Action", style={'color': '#00d4aa'}),
                    html.P(insights_data['price_analysis']['summary'], style={'color': '#ccc'})
                ], width=6),
                dbc.Col([
                    html.H6("📈 Volume Analysis", style={'color': '#00d4aa'}),
                    html.P(insights_data['volume_analysis']['summary'], style={'color': '#ccc'})
                ], width=6)
            ]),
            
            # Action items
            html.Div([
                html.H6("💡 Action Items", style={'color': '#fff', 'marginBottom': '10px'}),
                html.Ul([
                    html.Li([
                        html.Span(item['text'], style={'color': item['color']})
                    ], style={'marginBottom': '5px'}) 
                    for item in insights_data['trading_recommendation'].get('action_items', [])
                ], style={'listStyleType': 'none', 'paddingLeft': '0'}) if insights_data['trading_recommendation'].get('action_items') else html.P("No specific action items at this time.", style={'color': '#ccc'})
            ])
        ])
    ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3")
    
    # Detailed indicators cards
    indicators_row = dbc.Row([
        # Trend indicators
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H6("📊 Trend Indicators", style={'color': '#00d4aa', 'marginBottom': '0'})),
                dbc.CardBody([
                    create_indicator_display("MACD", insights_data['trend_analysis'].get('macd', {})),
                    create_indicator_display("ADX/DMI", insights_data['trend_analysis'].get('adx_dmi', {}))
                ])
            ], style={'backgroundColor': '#1a1a1a', 'border': '1px solid #333'})
        ], width=6),
        
        # Momentum indicators  
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H6("⚡ Momentum Indicators", style={'color': '#00d4aa', 'marginBottom': '0'})),
                dbc.CardBody([
                    create_indicator_display("RSI", insights_data['momentum_analysis'].get('rsi', {})),
                    create_indicator_display("Stochastic", insights_data['momentum_analysis'].get('stochastic', {})),
                    create_indicator_display("Force Index", insights_data['momentum_analysis'].get('force_index', {}))
                ])
            ], style={'backgroundColor': '#1a1a1a', 'border': '1px solid #333'})
        ], width=6)
    ], className="mb-3")
    
    # Risk and levels card
    risk_levels_card = dbc.Card([
        dbc.CardHeader(html.H6("⚠️ Risk Assessment & Key Levels", style={'color': '#00d4aa', 'marginBottom': '0'})),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Strong("Risk Level: ", style={'color': '#fff'}),
                    html.Span(
                        insights_data['risk_assessment']['overall_risk']['text'],
                        style={'color': insights_data['risk_assessment']['overall_risk']['color']}
                    ),
                    html.Br(),
                    html.Strong("Risk Factors: ", style={'color': '#fff'}),
                    html.Ul([
                        html.Li([
                            html.Span(factor['text'], style={'color': factor['color']})
                        ]) 
                        for factor in insights_data['risk_assessment'].get('risk_factors', [])
                    ], style={'marginTop': '5px'}) if insights_data['risk_assessment'].get('risk_factors') else html.Span("No major risk factors detected", style={'color': '#28a745'})
                ], width=6),
                dbc.Col([
                    html.Strong("Key Levels: ", style={'color': '#fff'}),
                    html.P(insights_data['key_levels']['summary'], style={'color': '#ccc', 'marginTop': '5px'}),
                    html.Strong("Divergences: ", style={'color': '#fff'}),
                    html.P(insights_data['divergence_analysis']['summary'], style={'color': '#ccc', 'marginTop': '5px'})
                ], width=6)
            ])
        ])
    ], style={'backgroundColor': '#1a1a1a', 'border': '1px solid #333'}, className="mb-3")
    
    return [summary_card, indicators_row, risk_levels_card]


def create_indicator_display(name, data):
    """Create a formatted display for an individual indicator"""
    if not data:
        return html.Div([
            html.Strong(f"{name}: ", style={'color': '#fff'}),
            html.Span("No data available", style={'color': '#666'})
        ], style={'marginBottom': '10px'})
    
    # Handle signal display (could be dict or string)
    signal_element = ""
    if isinstance(data.get('signal'), dict):
        signal_element = html.Span(
            data['signal']['text'],
            style={'color': data['signal']['color']}
        )
    else:
        signal_element = html.Span(data.get('signal', 'N/A'))
    
    return html.Div([
        html.Strong(f"{name}: ", style={'color': '#fff'}),
        signal_element,
        html.Br() if data.get('interpretation') else "",
        html.Small(data.get('interpretation', ''), style={'color': '#aaa'}) if data.get('interpretation') else ""
    ], style={'marginBottom': '15px'})

# ========== STOCK SCANNER TAB CALLBACKS ==========

# Callback for preset scan buttons
@callback(
    [Output('elder-filters', 'value'),
     Output('rsi-preset', 'value'),
     Output('volume-preset', 'value'),
     Output('universe-selection', 'value'),
     Output('result-limit', 'value'),
     Output('apgar-preset-store', 'data'),
     Output('active-preset-store', 'data')],
    [Input('preset-divergence', 'n_clicks'),
     Input('preset-rsi-extremes', 'n_clicks'),
     Input('preset-volume', 'n_clicks'),
     Input('preset-apgar', 'n_clicks'),
     Input('remove-all-filters', 'n_clicks')],
    prevent_initial_call=True
)
def handle_preset_buttons(divergence_clicks, rsi_extremes_clicks, volume_clicks, apgar_clicks, remove_clicks):
    """Handle quick preset scan button clicks and remove all filters"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'preset-divergence':
        # For divergence, we'll set up filters that can be refined in the UI
        return [], 'any', 500000, ['sp500'], 25, False, 'divergence'
    elif button_id == 'preset-rsi-extremes':
        # For RSI extremes, we'll set up filters that can be refined in the UI
        return [], 'any', 500000, ['sp500'], 25, False, 'rsi_extremes'
    elif button_id == 'preset-volume':
        return [], 'any', 5000000, ['sp500', 'nasdaq100'], 25, False, 'volume'
    elif button_id == 'preset-apgar':
        # Set both buy and sell Apgar score filters to 7
        return [], 'any', 500000, ['sp500'], 25, True, 'apgar'
    elif button_id == 'remove-all-filters':
        # Reset all filters to default values with minimal volume filter
        return [], 'any', 0, ['sp500'], 25, False, None
    
    raise PreventUpdate

# Main scanner callback
@callback(
    [Output('scan-status', 'children'),
     Output('scanner-results-area', 'children'),
     Output('scanner-results-area', 'className'),
     Output('scan-progress-store', 'data')],
    [Input('start-scan-button', 'n_clicks')],
    [State('elder-filters', 'value'),
     State('rsi-preset', 'value'),
     State('volume-preset', 'value'),
     State('price-preset', 'value'),
     State('change-preset', 'value'),
     State('universe-selection', 'value'),
     State('result-limit', 'value'),
     State('sort-by', 'value'),
     State('apgar-preset-store', 'data')],
    prevent_initial_call=True,
    running=[(Output("start-scan-button", "disabled"), True, False),
             (Output('scan-status', 'children'), dbc.Spinner(size="sm", color="success", fullscreen=False, children=html.Span(" Scanning...", style={'marginLeft': '10px', 'color': '#00d4aa'})), "")]
)
def run_stock_scan(n_clicks, elder_filters, rsi_preset, volume_preset, price_preset, 
                  change_preset, universe_selection, result_limit, sort_by, apgar_preset):
    if not n_clicks:
        raise PreventUpdate
    # Always define progress_data and reset progress at the start
    set_scan_progress(0)
    progress_data = {'percent': 0}
    try:
        # Reset progress
        set_scan_progress(0)
        progress_data = {'percent': 0}
        # Show loading message
        loading_status = dbc.Alert([
            html.Div([
                dbc.Spinner(size="sm", color="success"),
                html.Span(f"Scanning {universe_selection or ['sp500']} universe... This may take 2-3 minutes.", 
                         style={'marginLeft': '10px', 'color': '#00d4aa'})
            ])
        ], color="info", className="mb-3")
        
        # Build filters from UI state
        filters = {}
        
        # Elder's filters
        if elder_filters:
            if 'value_zone' in elder_filters:
                filters['value_zone_only'] = True
            if 'ema_bullish' in elder_filters:
                filters['ema_trend'] = 'bullish'
            if 'macd_bullish' in elder_filters:
                filters['macd_signal'] = 'bullish'
            if 'above_ema_13' in elder_filters:
                filters['above_ema_13'] = True
        
        # RSI filters
        if rsi_preset and rsi_preset != 'any':
            rsi_ranges = {
                'oversold': {'min': 0, 'max': 30},
                'recovery': {'min': 30, 'max': 40},
                'neutral': {'min': 40, 'max': 60},
                'setup': {'min': 60, 'max': 70},
                'overbought': {'min': 70, 'max': 100}
            }
            if rsi_preset in rsi_ranges:
                filters['rsi_min'] = rsi_ranges[rsi_preset]['min']
                filters['rsi_max'] = rsi_ranges[rsi_preset]['max']
        
        # RSI extreme filters (overbought/oversold)
        if rsi_preset == 'overbought':
            filters['rsi_extreme'] = 'overbought'
        elif rsi_preset == 'oversold':
            filters['rsi_extreme'] = 'oversold'
        
        # Divergence filters
        if elder_filters:
            if 'macd_bullish_divergence' in elder_filters:
                filters['macd_divergence'] = 'bullish'
            elif 'macd_bearish_divergence' in elder_filters:
                filters['macd_divergence'] = 'bearish'
            
            if 'rsi_bullish_divergence' in elder_filters:
                filters['rsi_divergence'] = 'bullish'
            elif 'rsi_bearish_divergence' in elder_filters:
                filters['rsi_divergence'] = 'bearish'
        
        # Volume filter
        if volume_preset:
            filters['min_volume'] = volume_preset
        
        # Price range filters
        if price_preset and price_preset != 'any':
            price_ranges = {
                'penny': {'min': 0, 'max': 5},
                'low': {'min': 5, 'max': 20},
                'medium': {'min': 20, 'max': 100},
                'high': {'min': 100, 'max': 500},
                'premium': {'min': 500, 'max': None}
            }
            if price_preset in price_ranges:
                filters['price_min'] = price_ranges[price_preset]['min']
                filters['price_max'] = price_ranges[price_preset]['max']
        
        # Price change filters
        if change_preset and change_preset != 'any':
            change_ranges = {
                'strong_up': {'min': 5, 'max': None},
                'moderate_up': {'min': 2, 'max': 5},
                'stable': {'min': -2, 'max': 2},
                'moderate_down': {'min': -5, 'max': -2},
                'strong_down': {'min': None, 'max': -5}
            }
            if change_preset in change_ranges:
                filters['change_min'] = change_ranges[change_preset]['min']
                filters['change_max'] = change_ranges[change_preset]['max']
        
        # Initialize scanner and run scan
        scanner = StockScanner()
        
        # Add Trade Apgar filter if requested (score >= 7 for both buy and sell)
        if apgar_preset:
            filters['min_apgar_score'] = 7
            filters['min_apgar_sell_score'] = 7
        
        # Debug: Print the filters being applied
        print(f"Scanner filters: {filters}")
        print(f"Universe: {universe_selection or ['sp500']}")
        print(f"Max results: {result_limit or 25}")
        
        # Progress callback for scan_stocks
        def dash_progress_callback(completed, total):
            percent = int((completed / total) * 100)
            set_scan_progress(percent)
        # Run the scan (blocking, but updates progress)
        results_df = scanner.scan_stocks(
            filters=filters,
            universes=universe_selection or ['sp500'],
            max_results=result_limit or 25,
            sort_by=sort_by or 'volume',
            random_sample=False,
            progress_callback=dash_progress_callback
        )
        # After scan, set to 100%
        set_scan_progress(100)
        progress_data = {'percent': 100}
        
        if results_df.empty:
            return (
                dbc.Alert("❌ No stocks found matching your criteria. Try adjusting your filters.", color="warning"),
                [],
                'd-none',
                progress_data
            )
        
        # Create results table
        table_data = results_df.copy()
        
        # Format divergence and RSI extreme columns for display
        if 'macd_divergence' in table_data.columns:
            table_data['macd_divergence'] = table_data['macd_divergence'].apply(lambda x: x.title() if pd.notna(x) and x != 'none' else 'None')
        if 'rsi_divergence' in table_data.columns:
            table_data['rsi_divergence'] = table_data['rsi_divergence'].apply(lambda x: x.title() if pd.notna(x) and x != 'none' else 'None')
        if 'rsi_extreme' in table_data.columns:
            table_data['rsi_extreme'] = table_data['rsi_extreme'].apply(lambda x: x.title() if pd.notna(x) and x != 'neutral' else 'Neutral')
        # Capitalize and color MACD Signal and EMA Trend
        if 'macd_signal' in table_data.columns:
            table_data['macd_signal'] = table_data['macd_signal'].apply(lambda x: x.title() if pd.notna(x) else None)
        if 'ema_trend' in table_data.columns:
            table_data['ema_trend'] = table_data['ema_trend'].apply(lambda x: x.title() if pd.notna(x) else None)

        # Create data table
        table = dash_table.DataTable(
            id='scan-results-table',
            data=table_data.to_dict('records'),
            columns=[
                {'name': 'Symbol', 'id': 'symbol', 'type': 'text'},
                {'name': 'Price', 'id': 'price', 'type': 'numeric'},
                {'name': 'Change %', 'id': 'price_change_pct', 'type': 'numeric'},
                {'name': 'RSI', 'id': 'rsi', 'type': 'numeric'},
                {'name': 'RSI Status', 'id': 'rsi_extreme', 'type': 'text'},
                {'name': 'EMA Trend', 'id': 'ema_trend', 'type': 'text'},
                {'name': 'MACD Signal', 'id': 'macd_signal', 'type': 'text'},
                {'name': 'MACD Divergence', 'id': 'macd_divergence', 'type': 'text'},
                {'name': 'RSI Divergence', 'id': 'rsi_divergence', 'type': 'text'},
                {'name': 'Impulse (Weekly)', 'id': 'impulse_weekly', 'type': 'text'},
                {'name': 'Impulse (Daily)', 'id': 'impulse_daily', 'type': 'text'},
                {'name': 'Trade Apgar (Buy)', 'id': 'trade_apgar', 'type': 'numeric'},
                {'name': 'Trade Apgar (Sell)', 'id': 'trade_apgar_sell', 'type': 'numeric'}
            ],
            style_table={
                'backgroundColor': '#000000',
                'overflowX': 'auto'
            },
            style_cell={
                'backgroundColor': '#000000',
                'color': '#fff',
                'border': '1px solid #444',
                'textAlign': 'left',
                'padding': '8px',
                'fontFamily': 'Inter, sans-serif',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#00d4aa',
                'color': '#000',
                'fontWeight': 'bold',
                'border': '1px solid #00d4aa'
            },
            style_data_conditional=[  # type: ignore
                # Price coloring based on change (add background)
                {
                    'if': {
                        'filter_query': '{price_change_pct} > 0',
                        'column_id': 'price'
                    },
                    'color': '#00ff88',
                    'backgroundColor': '#1a4d3a',
                },
                {
                    'if': {
                        'filter_query': '{price_change_pct} < 0',
                        'column_id': 'price'
                    },
                    'color': '#ff6b6b',
                    'backgroundColor': '#4d1a1a',
                },
                # Change % coloring (existing)
                {
                    'if': {
                        'filter_query': '{price_change_pct} > 0',
                        'column_id': 'price_change_pct'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                {
                    'if': {
                        'filter_query': '{price_change_pct} < 0',
                        'column_id': 'price_change_pct'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # RSI coloring (add background)
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Overbought',
                        'column_id': 'rsi'
                    },
                    'color': '#ff6b6b',
                    'backgroundColor': '#4d1a1a',
                },
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Oversold',
                        'column_id': 'rsi'
                    },
                    'color': '#00ff88',
                    'backgroundColor': '#1a4d3a',
                },
                # RSI Status coloring (add background)
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Overbought',
                        'column_id': 'rsi_extreme'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b',
                },
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Oversold',
                        'column_id': 'rsi_extreme'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                },
                # EMA Trend coloring
                {
                    'if': {
                        'filter_query': '{ema_trend} = Bullish',
                        'column_id': 'ema_trend'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                },
                {
                    'if': {
                        'filter_query': '{ema_trend} = Bearish',
                        'column_id': 'ema_trend'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b',
                },
                # MACD Signal coloring
                {
                    'if': {
                        'filter_query': '{macd_signal} = Bullish',
                        'column_id': 'macd_signal'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                },
                {
                    'if': {
                        'filter_query': '{macd_signal} = Bearish',
                        'column_id': 'macd_signal'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b',
                },
                # MACD/RSI Divergence coloring (existing)
                {
                    'if': {
                        'filter_query': '{macd_divergence} = Bullish',
                        'column_id': 'macd_divergence'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                {
                    'if': {
                        'filter_query': '{macd_divergence} = Bearish',
                        'column_id': 'macd_divergence'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                {
                    'if': {
                        'filter_query': '{rsi_divergence} = Bullish',
                        'column_id': 'rsi_divergence'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                {
                    'if': {
                        'filter_query': '{rsi_divergence} = Bearish',
                        'column_id': 'rsi_divergence'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # Make symbol column clickable and prominent
                {
                    'if': {'column_id': 'symbol'},
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4aa',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'textDecoration': 'underline'
                },
                # Trade Apgar (Buy) coloring (fix logic)
                {
                    'if': {
                        'filter_query': '{trade_apgar} >= 7 and {trade_apgar_has_zeros} = true',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar} >= 7 and {trade_apgar_has_zeros} = false',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                # Trade Apgar (Sell) coloring (fix logic)
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} >= 7 and {trade_apgar_sell_has_zeros} = true',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} >= 7 and {trade_apgar_sell_has_zeros} = false',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                # Medium/low Apgar coloring (existing)
                {
                    'if': {
                        'filter_query': '{trade_apgar} >= 5 and {trade_apgar} < 7',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar} < 5',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} >= 5 and {trade_apgar_sell} < 7',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} < 5',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # Impulse Weekly coloring
                {
                    'if': {'filter_query': '{impulse_weekly} = Buy', 'column_id': 'impulse_weekly'},
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_weekly} = Sell', 'column_id': 'impulse_weekly'},
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff4444',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_weekly} = Neutral', 'column_id': 'impulse_weekly'},
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4ff',
                    'fontWeight': 'bold'
                },
                # Impulse Daily coloring
                {
                    'if': {'filter_query': '{impulse_daily} = Buy', 'column_id': 'impulse_daily'},
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_daily} = Sell', 'column_id': 'impulse_daily'},
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff4444',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_daily} = Neutral', 'column_id': 'impulse_daily'},
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4ff',
                    'fontWeight': 'bold'
                },
            ],
            sort_action="native",
            page_size=20,
            page_action="native"
        )
        
        # Create summary info
        scan_type = "Trade Apgar ≥ 7" if apgar_preset else "Filtered Scan"
        universes_str = ", ".join(universe_selection or ['sp500']).upper();
        
        success_msg = dbc.Alert([
            html.H6([
                html.Span("✅ ", style={'fontSize': '18px'}),
                f"{scan_type} Complete!"
            ], style={'marginBottom': '10px', 'color': '#00d4aa'}),
            html.P([
                f"Found {len(results_df)} stocks from {universes_str} universe(s). ",
                f"Sorted by {sort_by}."
            ], style={'marginBottom': '0', 'fontSize': '14px'})
        ], color="success", className="mb-3")
        
        # Create click-to-load instructions
        instructions = dbc.Alert([
            html.P([
                "💡 Tip: Click on any ",
                html.Strong("Symbol", style={'color': '#00d4aa'}),
                " in the table to load its 5-year weekly chart for detailed analysis.",
            ], style={'marginBottom': '0', 'fontSize': '12px', 'fontStyle': 'italic'})
        ], color="info", className="mb-2")
        
        return success_msg, [instructions, table], 'd-block', progress_data
        
    except Exception as e:
        error_msg = dbc.Alert([
            html.H6("❌ Scan Failed", style={'marginBottom': '10px'}),
            html.P(f"Error: {str(e)}", style={'marginBottom': '0', 'fontSize': '14px'})
        ], color="danger")
        return error_msg, [], 'd-none', progress_data

# Callback to reset preset stores after scan
@callback(
    [Output('apgar-preset-store', 'data', allow_duplicate=True),
     Output('active-preset-store', 'data', allow_duplicate=True)],
    [Input('start-scan-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_preset_stores_after_scan(n_clicks):
    """Reset the preset stores after a scan is completed"""
    return False, None

# Callbacks to update button styles based on active preset
@callback(
    [Output('preset-divergence', 'color'),
     Output('preset-divergence', 'outline')],
    [Input('active-preset-store', 'data')],
    prevent_initial_call=True
)
def update_divergence_button_style(active_preset):
    """Update divergence button style based on active preset"""
    if active_preset == 'divergence':
        return 'info', False  # Filled button
    else:
        return 'info', True   # Outline button

@callback(
    [Output('preset-rsi-extremes', 'color'),
     Output('preset-rsi-extremes', 'outline')],
    [Input('active-preset-store', 'data')],
    prevent_initial_call=True
)
def update_rsi_extremes_button_style(active_preset):
    """Update RSI extremes button style based on active preset"""
    if active_preset == 'rsi_extremes':
        return 'warning', False  # Filled button
    else:
        return 'warning', True   # Outline button

@callback(
    [Output('preset-volume', 'color'),
     Output('preset-volume', 'outline')],
    [Input('active-preset-store', 'data')],
    prevent_initial_call=True
)
def update_volume_button_style(active_preset):
    """Update volume button style based on active preset"""
    if active_preset == 'volume':
        return 'success', False  # Filled button
    else:
        return 'success', True   # Outline button

@callback(
    [Output('preset-apgar', 'color'),
     Output('preset-apgar', 'outline')],
    [Input('active-preset-store', 'data')],
    prevent_initial_call=True
)
def update_apgar_button_style(active_preset):
    """Update apgar button style based on active preset"""
    if active_preset == 'apgar':
        return 'success', False  # Filled button
    else:
        return 'success', True   # Outline button

# Callback to load clicked symbol into main chart and switch back to chart view
# Callback to load clicked symbol into main chart and switch back to chart view
@callback(
    [Output('stock-symbol-input', 'value', allow_duplicate=True),
     Output('current-symbol-store', 'data', allow_duplicate=True),
     Output('timeframe-dropdown', 'value', allow_duplicate=True),
     Output('frequency-dropdown', 'value', allow_duplicate=True),
     Output('sidebar-tabs', 'active_tab', allow_duplicate=True)],
    [Input('scan-results-table', 'active_cell')],
    [State('scan-results-table', 'data')],
    prevent_initial_call=True
)
def load_symbol_from_scanner(active_cell, table_data):
    """Load clicked symbol from scanner results into main chart and switch to chart view"""
    if active_cell and table_data:
        row = active_cell['row']
        if row < len(table_data):
            symbol = table_data[row]['symbol']
            # Clean the symbol (remove any potential formatting)
            clean_symbol = symbol.strip()
            return (
                clean_symbol,                                        # Update symbol input
                clean_symbol,                                        # Update symbol store
                '5y',                                                # Set timeframe to 5 years
                '1wk',                                               # Set frequency to weekly
                'stock-search-tab'                                   # Switch to stock search tab
            )
    raise PreventUpdate

@callback(
    [Output('stock-symbol-input', 'value', allow_duplicate=True),
     Output('current-symbol-store', 'data', allow_duplicate=True),
     Output('timeframe-dropdown', 'value', allow_duplicate=True),
     Output('sidebar-tabs', 'active_tab', allow_duplicate=True)],
    [Input('watchlist-results-table', 'active_cell')],
    [State('watchlist-results-table', 'data')],
    prevent_initial_call=True
)
def load_symbol_from_watchlist(active_cell, table_data):
    """Load a symbol from watchlist results into the chart"""
    if not active_cell or not table_data:
        raise PreventUpdate
    
    row = active_cell['row']
    if row < len(table_data):
        symbol = table_data[row]['symbol']
        # Clean the symbol (remove any potential formatting)
        clean_symbol = symbol.strip()
        return (
            clean_symbol,                                        # Update symbol input
            clean_symbol,                                        # Update symbol store
            '6mo',                                               # Set timeframe to 6 months
            'stock-search-tab'                                   # Switch to stock search tab
        )
    raise PreventUpdate

# ========== WATCHLIST CALLBACKS ==========

def get_open_positions_from_csv():
    """Get list of open positions from equity_data.csv"""
    try:
        if not os.path.exists('equity_data.csv'):
            return []
        
        df = pd.read_csv('equity_data.csv')
        open_positions = []
        
        # Find rows with open positions (open_positions == 1.0)
        open_mask = (df['open_positions'] == 1.0)
        if open_mask.any():
            for idx in df[open_mask].index:
                stock = df.at[idx, 'stocks_in_positions']
                if pd.notna(stock) and stock.strip():
                    open_positions.append(stock.strip().upper())
        
        return open_positions
    except Exception as e:
        print(f"Error reading open positions from CSV: {e}")
        return []

@callback(
    [Output('watchlist-store', 'data', allow_duplicate=True),
     Output('watchlist-status', 'children'),
     Output('watchlist-symbol-input', 'value')],
    [Input('add-to-watchlist-btn', 'n_clicks')],
    [State('watchlist-symbol-input', 'value'),
     State('watchlist-store', 'data')],
    prevent_initial_call=True
)
def add_to_watchlist_callback(n_clicks, symbol, current_watchlist):
    """Add a stock symbol to the watchlist and persist to file"""
    if not n_clicks or not symbol:
        raise PreventUpdate
    clean_symbol = symbol.strip().upper()
    if not clean_symbol:
        return dash.no_update, "Please enter a valid symbol.", ""
    if clean_symbol in current_watchlist:
        return dash.no_update, f"❌ {clean_symbol} is already in your watchlist.", ""
    # Add to persistent watchlist
    new_watchlist = add_to_watchlist(clean_symbol)
    return new_watchlist, f"✅ {clean_symbol} added to watchlist!", ""

@callback(
    [Output('watchlist-table', 'children'),
     Output('watchlist-table-container', 'style')],
    [Input('watchlist-store', 'data')],
    prevent_initial_call=False
)
def update_watchlist_display(watchlist_data):
    """Update the watchlist display"""
    if not watchlist_data or len(watchlist_data) == 0:
        return "No stocks in watchlist", {'display': 'block'}
    
    # Create watchlist items with remove buttons
    watchlist_items = []
    for i, symbol in enumerate(watchlist_data):
        # Check if this is an open position from CSV
        open_positions = get_open_positions_from_csv()
        is_open_position = symbol in open_positions
        
        # Create different styling for open positions
        symbol_style = {
            'color': '#00ff88' if is_open_position else '#fff',
            'fontWeight': 'bold',
            'fontSize': '14px' if is_open_position else '12px'
        }
        
        # Add position indicator for open positions
        position_indicator = ""
        if is_open_position:
            position_indicator = html.Span(" 📈", style={'color': '#00ff88', 'fontSize': '12px'})
        
        item = dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(symbol, style=symbol_style),
                    position_indicator
                ])
            ], width=8),
            dbc.Col([
                dbc.Button(
                    "Remove",
                    id={'type': 'remove-watchlist-btn', 'index': i},
                    color="danger",
                    size="sm",
                    style={'fontSize': '10px'},
                    disabled=is_open_position  # Disable remove button for open positions
                )
            ], width=4)
        ], className="mb-2", style={'alignItems': 'center'})
        watchlist_items.append(item)
    
    return watchlist_items, {'display': 'block'}

@callback(
    Output('watchlist-store', 'data', allow_duplicate=True),
    [Input({'type': 'remove-watchlist-btn', 'index': ALL}, 'n_clicks')],
    [State('watchlist-store', 'data')],
    prevent_initial_call=True
)
def remove_from_watchlist_callback(remove_clicks, current_watchlist):
    if not any(remove_clicks):
        raise PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    import json
    button_data = json.loads(triggered_id)
    index = button_data['index']
    if current_watchlist and 0 <= index < len(current_watchlist):
        symbol_to_remove = current_watchlist[index]
        # Remove from persistent watchlist
        new_watchlist = remove_from_watchlist(symbol_to_remove)
        return new_watchlist
    return dash.no_update



# Preload open positions into watchlist on app startup
@callback(
    Output('watchlist-store', 'data', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    prevent_initial_call='initial_duplicate'
)
def preload_open_positions_on_startup(n_intervals):
    """Preload open positions and watchlist from file on app startup, ensuring open positions are always included"""
    # Only run once on startup (when n_intervals is 0)
    if n_intervals == 0:
        # Load open positions from CSV
        open_positions = get_open_positions_from_csv()
        # Load from persistent watchlist file
        watchlist = load_watchlist()
        # Merge, open positions first, then rest, no duplicates
        seen = set(open_positions)
        merged = open_positions + [s for s in watchlist if s not in seen]
        return merged
    raise PreventUpdate

@callback(
    [Output('scan-status', 'children', allow_duplicate=True),
     Output('scanner-results-area', 'children', allow_duplicate=True),
     Output('scanner-results-area', 'className', allow_duplicate=True)],
    [Input('load-watchlist-button', 'n_clicks')],
    [State('watchlist-store', 'data')],
    prevent_initial_call=True,
    running=[(Output("load-watchlist-button", "disabled"), True, False),
             (Output('scan-status', 'children'), dbc.Spinner(size="sm", color="info", fullscreen=False, children=html.Span(" Loading watchlist...", style={'marginLeft': '10px', 'color': '#00d4aa'})), "")]
)
def load_watchlist_scan(n_clicks, watchlist_data):
    """Load and scan all stocks in the watchlist"""
    if not n_clicks or not watchlist_data or len(watchlist_data) == 0:
        raise PreventUpdate
    
    try:
        # Initialize scanner
        scanner = StockScanner()
        
        # Get open positions for reference
        open_positions = get_open_positions_from_csv()
        
        # Instead of manual loop, use scan_stocks with force_refresh=True for watchlist
        results_df = scanner.scan_stocks(
            filters=None,
            universes=None,
            max_results=len(watchlist_data),
            sort_by='volume',
            random_sample=False,
            force_refresh=True,
            symbols=watchlist_data
        )
        # But we want only the symbols in watchlist_data, so filter after scan
        if not results_df.empty:
            results_df = results_df[results_df['symbol'].isin(watchlist_data)]
        
        if results_df.empty:
            # Check if we have any open positions that failed
            open_position_failures = [s for s in results_df['symbol'] if s in open_positions]
            if open_position_failures:
                return (
                    dbc.Alert([
                        html.H6("⚠️ Watchlist Scan Results", style={'marginBottom': '10px'}),
                        html.P(f"No data found for {len(open_position_failures)} symbols including open positions: {', '.join(open_position_failures)}", 
                               style={'marginBottom': '5px'}),
                        html.Small("This may be due to market hours or data availability issues.", 
                                 style={'color': '#ccc', 'fontStyle': 'italic'})
                    ], color="warning"),
                    [],
                    'd-none'
                )
            else:
                return (
                    dbc.Alert("❌ No data found for watchlist symbols. Check if symbols are valid.", color="warning"),
                    [],
                    'd-none'
                )
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results_df)
        
        if results_df.empty:
            return (
                dbc.Alert("❌ No data found for watchlist symbols. Check if symbols are valid.", color="warning"),
                [],
                'd-none'
            )
        
        # Create results table (same logic as regular scanner)
        table_data = results_df.copy()
        
        # Format numeric columns
        if 'rsi' in table_data.columns:
            table_data['rsi'] = table_data['rsi'].apply(lambda x: round(x, 1) if pd.notna(x) else None)
        if 'price_change_pct' in table_data.columns:
            table_data['price_change_pct'] = table_data['price_change_pct'].apply(lambda x: round(x, 2) if pd.notna(x) else None)
        if 'price' in table_data.columns:
            table_data['price'] = table_data['price'].apply(lambda x: round(x, 2) if pd.notna(x) else None)
        if 'volume' in table_data.columns:
            table_data['volume'] = table_data['volume'].apply(lambda x: int(x) if pd.notna(x) else None)
        if 'trade_apgar' in table_data.columns:
            table_data['trade_apgar'] = table_data['trade_apgar'].apply(lambda x: int(x) if pd.notna(x) else None)
        
        # Format divergence and RSI extreme columns
        if 'macd_divergence' in table_data.columns:
            table_data['macd_divergence'] = table_data['macd_divergence'].apply(lambda x: x.title() if pd.notna(x) and x != 'none' else 'None')
        if 'rsi_divergence' in table_data.columns:
            table_data['rsi_divergence'] = table_data['rsi_divergence'].apply(lambda x: x.title() if pd.notna(x) and x != 'none' else 'None')
        if 'rsi_extreme' in table_data.columns:
            table_data['rsi_extreme'] = table_data['rsi_extreme'].apply(lambda x: x.title() if pd.notna(x) and x != 'neutral' else 'Neutral')
        if 'macd_signal' in table_data.columns:
            table_data['macd_signal'] = table_data['macd_signal'].apply(lambda x: x.title() if pd.notna(x) else None)
        if 'ema_trend' in table_data.columns:
            table_data['ema_trend'] = table_data['ema_trend'].apply(lambda x: x.title() if pd.notna(x) else None)

        # Create data table with enhanced styling for open positions
        table = dash_table.DataTable(
            id='watchlist-results-table',
            data=table_data.to_dict('records'),
            columns=[
                {'name': 'Symbol', 'id': 'symbol', 'type': 'text'},
                {'name': 'Price', 'id': 'price', 'type': 'numeric'},
                {'name': 'Change %', 'id': 'price_change_pct', 'type': 'numeric'},
                {'name': 'RSI', 'id': 'rsi', 'type': 'numeric'},
                {'name': 'RSI Status', 'id': 'rsi_extreme', 'type': 'text'},
                {'name': 'EMA Trend', 'id': 'ema_trend', 'type': 'text'},
                {'name': 'MACD Signal', 'id': 'macd_signal', 'type': 'text'},
                {'name': 'MACD Divergence', 'id': 'macd_divergence', 'type': 'text'},
                {'name': 'RSI Divergence', 'id': 'rsi_divergence', 'type': 'text'},
                {'name': 'Impulse (Weekly)', 'id': 'impulse_weekly', 'type': 'text'},
                {'name': 'Impulse (Daily)', 'id': 'impulse_daily', 'type': 'text'},
                {'name': 'Trade Apgar (Buy)', 'id': 'trade_apgar', 'type': 'numeric'},
                {'name': 'Trade Apgar (Sell)', 'id': 'trade_apgar_sell', 'type': 'numeric'}
            ],
            style_table={
                'backgroundColor': '#000000',
                'overflowX': 'auto'
            },
            style_cell={
                'backgroundColor': '#000000',
                'color': '#fff',
                'border': '1px solid #444',
                'textAlign': 'left',
                'padding': '8px',
                'fontFamily': 'Inter, sans-serif',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#00d4aa',
                'color': '#000',
                'fontWeight': 'bold',
                'border': '1px solid #00d4aa'
            },
            style_data_conditional=[  # type: ignore
                # Price coloring based on change (add background)
                {
                    'if': {
                        'filter_query': '{price_change_pct} > 0',
                        'column_id': 'price'
                    },
                    'color': '#00ff88',
                    'backgroundColor': '#1a4d3a',
                },
                {
                    'if': {
                        'filter_query': '{price_change_pct} < 0',
                        'column_id': 'price'
                    },
                    'color': '#ff6b6b',
                    'backgroundColor': '#4d1a1a',
                },
                # Change % coloring (existing)
                {
                    'if': {
                        'filter_query': '{price_change_pct} > 0',
                        'column_id': 'price_change_pct'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                {
                    'if': {
                        'filter_query': '{price_change_pct} < 0',
                        'column_id': 'price_change_pct'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # RSI coloring (add background)
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Overbought',
                        'column_id': 'rsi'
                    },
                    'color': '#ff6b6b',
                    'backgroundColor': '#4d1a1a',
                },
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Oversold',
                        'column_id': 'rsi'
                    },
                    'color': '#00ff88',
                    'backgroundColor': '#1a4d3a',
                },
                # RSI Status coloring (add background)
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Overbought',
                        'column_id': 'rsi_extreme'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b',
                },
                {
                    'if': {
                        'filter_query': '{rsi_extreme} = Oversold',
                        'column_id': 'rsi_extreme'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                },
                # EMA Trend coloring
                {
                    'if': {
                        'filter_query': '{ema_trend} = Bullish',
                        'column_id': 'ema_trend'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                },
                {
                    'if': {
                        'filter_query': '{ema_trend} = Bearish',
                        'column_id': 'ema_trend'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b',
                },
                # MACD Signal coloring
                {
                    'if': {
                        'filter_query': '{macd_signal} = Bullish',
                        'column_id': 'macd_signal'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                },
                {
                    'if': {
                        'filter_query': '{macd_signal} = Bearish',
                        'column_id': 'macd_signal'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b',
                },
                # MACD/RSI Divergence coloring (existing)
                {
                    'if': {
                        'filter_query': '{macd_divergence} = Bullish',
                        'column_id': 'macd_divergence'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                {
                    'if': {
                        'filter_query': '{macd_divergence} = Bearish',
                        'column_id': 'macd_divergence'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                {
                    'if': {
                        'filter_query': '{rsi_divergence} = Bullish',
                        'column_id': 'rsi_divergence'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                {
                    'if': {
                        'filter_query': '{rsi_divergence} = Bearish',
                        'column_id': 'rsi_divergence'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # Make symbol column clickable and prominent
                {
                    'if': {'column_id': 'symbol'},
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4aa',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'textDecoration': 'underline'
                },
                # Trade Apgar (Buy) coloring (fix logic)
                {
                    'if': {
                        'filter_query': '{trade_apgar} >= 7 and {trade_apgar_has_zeros} = true',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar} >= 7 and {trade_apgar_has_zeros} = false',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                # Trade Apgar (Sell) coloring (fix logic)
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} >= 7 and {trade_apgar_sell_has_zeros} = true',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} >= 7 and {trade_apgar_sell_has_zeros} = false',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                # Medium/low Apgar coloring (existing)
                {
                    'if': {
                        'filter_query': '{trade_apgar} >= 5 and {trade_apgar} < 7',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar} < 5',
                        'column_id': 'trade_apgar'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} >= 5 and {trade_apgar_sell} < 7',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#4d3a1a',
                    'color': '#ffcc00'
                },
                {
                    'if': {
                        'filter_query': '{trade_apgar_sell} < 5',
                        'column_id': 'trade_apgar_sell'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # Impulse Weekly coloring
                {
                    'if': {'filter_query': '{impulse_weekly} = Buy', 'column_id': 'impulse_weekly'},
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_weekly} = Sell', 'column_id': 'impulse_weekly'},
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff4444',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_weekly} = Neutral', 'column_id': 'impulse_weekly'},
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4ff',
                    'fontWeight': 'bold'
                },
                # Impulse Daily coloring
                {
                    'if': {'filter_query': '{impulse_daily} = Buy', 'column_id': 'impulse_daily'},
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_daily} = Sell', 'column_id': 'impulse_daily'},
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff4444',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{impulse_daily} = Neutral', 'column_id': 'impulse_daily'},
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4ff',
                    'fontWeight': 'bold'
                },
            ],
            page_size=20,
            page_action="native",
            sort_action="native"
        )
        
        # Create success message with open position info
        open_positions_found = len(results_df)
        total_symbols = len(results_df)
        
        if open_positions_found > 0:
            success_msg = dbc.Alert([
                html.H6([
                    html.Span("✅ ", style={'fontSize': '18px'}),
                    f"Watchlist scan completed!"
                ], style={'marginBottom': '10px', 'color': '#00d4aa'}),
                html.P([
                    f"Found data for {total_symbols} symbols ",
                    html.Span(f"({open_positions_found} open positions)", style={'color': '#00ff88', 'fontWeight': 'bold'}),
                    f". {len(results_df) - open_positions_found} symbols had no data."
                ], style={'marginBottom': '0', 'fontSize': '14px'})
            ], color="success", className="mb-3")
        else:
            success_msg = dbc.Alert([
                html.H6([
                    html.Span("✅ ", style={'fontSize': '18px'}),
                    f"Watchlist scan completed!"
                ], style={'marginBottom': '10px', 'color': '#00d4aa'}),
                html.P([
                    f"Found data for {total_symbols} symbols. {len(results_df) - open_positions_found} symbols had no data."
                ], style={'marginBottom': '0', 'fontSize': '14px'})
            ], color="success", className="mb-3")
        
        return (
            success_msg,
            [table],
            'd-block'
        )
        
    except Exception as e:
        return (
            dbc.Alert(f"❌ Error loading watchlist: {str(e)}", color="danger"),
            [],
            'd-none'
        )

# Callback to switch between scanner results and chart view based on active tab
@callback(
    [Output('scanner-results-area', 'className', allow_duplicate=True),
     Output('combined-chart', 'style', allow_duplicate=True)],
    [Input('sidebar-tabs', 'active_tab')],
    prevent_initial_call=True
)
def switch_view_on_tab_change(active_tab):
    """Switch between scanner results and chart view based on active tab"""
    if active_tab == 'scanner-tab':
        # Show scanner results area and hide chart when on scanner tab
        return 'd-block', {
            'backgroundColor': '#000000', 
            'height': '90vh',
            'position': 'absolute',
            'top': '0',
            'left': '0',
            'width': '100%',
            'zIndex': 1,
            'display': 'none'
        }
    else:
        # Show chart and hide scanner results for all other tabs
        return 'd-none', {
            'backgroundColor': '#000000', 
            'height': '90vh',
            'position': 'absolute',
            'top': '0',
            'left': '0',
            'width': '100%',
            'zIndex': 1,
            'display': 'block'
        }

# === IRL TRADE CALLBACKS (CSV version) ===

CSV_FILE = 'equity_data.csv'

# Callback: Check 2% rule warning
@callback(
    Output('irl-2percent-warning', 'className'),
    [Input('irl-amount-input', 'value'),
     Input('irl-equity-store', 'data')],
    prevent_initial_call=True
)
def check_2percent_rule(amount, equity_data):
    """Check if the investment amount exceeds 2% of equity and show warning"""
    if not amount or not equity_data:
        return 'd-none'  # Hide warning if no data
    
    try:
        # Get current equity
        df = pd.DataFrame(equity_data)
        current_equity = float(df['equity'].iloc[-1])
        
        # Calculate 2% of equity
        two_percent_limit = current_equity * 0.02
        
        # Check if amount exceeds 2% limit
        if float(amount) > two_percent_limit:
            return 'd-block'  # Show warning
        else:
            return 'd-none'  # Hide warning
            
    except (ValueError, TypeError, IndexError):
        return 'd-none'  # Hide warning on any error

# Callback: Load equity on tab open or after trade
@callback(
    Output('irl-equity-store', 'data'),
    Input('sidebar-tabs', 'active_tab'),
    Input('irl-open-position-btn', 'n_clicks'),
    Input({'type': 'irl-close-btn', 'index': ALL}, 'n_clicks'),
    Input({'type': 'irl-change-stop-btn', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=False
)
def update_irl_equity_store(tab, open_n, close_n, change_n):
    ctx = dash.callback_context
    if tab == 'irl-trade-tab' or ctx.triggered:
        if not os.path.exists(CSV_FILE):
            import create_equity_file
        df = load_trading_df()
        return df.to_dict('records')
    raise PreventUpdate

# Callback: Display equity (color-coded, hideable)
@callback(
    Output('irl-equity-display', 'children'),
    Output('irl-equity-display', 'style'),
    Input('irl-equity-store', 'data'),
    prevent_initial_call=False
)
def display_irl_equity(data):
    if not data:
        return "No equity data.", {'display': 'block'}
    df = pd.DataFrame(data)
    eq = float(df['equity'].iloc[-1])
    prev_eq = float(df['equity'].iloc[-2]) if len(df) > 1 else eq
    color = '#00ff88' if eq >= prev_eq else '#ff4444'
    style = {'color': color, 'fontSize': '22px', 'fontWeight': 'bold', 'marginBottom': '20px'}
    return f"Current Equity: ${eq:,.2f}", style

# Callback: Open position
@callback(
    Output('irl-open-position-status', 'children'),
    Output('irl-equity-store', 'data', allow_duplicate=True),
    Input('irl-open-position-btn', 'n_clicks'),
    State('irl-equity-store', 'data'),
    State('irl-stock-symbol-input', 'value'),
    State('irl-buy-sell-radio', 'value'),
    State('irl-amount-input', 'value'),
    State('irl-stop-input', 'value'),
    State('irl-target-input', 'value'),
    State('irl-stock-symbol-input', 'value'),
    State('irl-amount-input', 'value'),
    State('irl-stop-input', 'value'),
    State('irl-target-input', 'value'),
    State('irl-stock-symbol-input', 'value'),
    prevent_initial_call=True
)
def open_irl_position(n, data, symbol, side, amount, stop, target, *_):
    if not n:
        raise PreventUpdate
    if not symbol or not amount or not stop or not target:
        return "Please fill all fields.", dash.no_update
    df = pd.DataFrame(data) if data else load_trading_df()
    amt = abs(float(amount))  # Always positive
    
    # Check 2% rule
    current_equity = float(df['equity'].iloc[-1])
    two_percent_limit = current_equity * 0.02
    breaks_2percent_rule = amt > two_percent_limit
    
    try:
        df2 = open_position(df, symbol.upper(), amt, price_at_entry=float(amount), stop_price=float(stop), target_price=float(target), side=side)
        
        # Create status message
        if breaks_2percent_rule:
            status_msg = f"Position opened! ⚠️ Note: This trade breaks the 2% Rule (${amt:,.2f} > ${two_percent_limit:,.2f})"
        else:
            status_msg = "Position opened!"
            
        return status_msg, df2.to_dict('records')
    except Exception as e:
        return f"Error: {e}", dash.no_update

# Callback: List open positions
@callback(
    Output('irl-open-positions-list', 'children'),
    Input('irl-equity-store', 'data'),
    prevent_initial_call=False
)
def list_irl_open_positions(data):
    if not data:
        return "No positions."
    df = pd.DataFrame(data)
    open_mask = (df['open_positions'] == 1.0)
    if not open_mask.any():
        return "No open positions."
    items = []
    for idx in df[open_mask].index:
        stock = df.at[idx, 'stocks_in_positions']
        amt = df.at[idx, 'amount_invested']
        stop = df.at[idx, 'stop_price']
        target = df.at[idx, 'target_price']
        side = df.at[idx, 'side'] if 'side' in df.columns else 'buy'
        # Color: green for buy, red for sell
        if str(side).lower() == 'buy':
            pos_color = '#00ff88'
        elif str(side).lower() == 'sell':
            pos_color = '#ff4444'
        else:
            pos_color = '#fff'
        items.append(
            dbc.Row([
                dbc.Col([
                    html.Div(f"{stock} | Amount: {amt} | Stop: {stop} | Target: {target}", style={'color': pos_color, 'fontWeight': 'bold'}),
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(
                                id={'type': 'irl-new-stop-input', 'index': idx},
                                placeholder="New stop price",
                                type="number",
                                size="sm",
                                className="mt-1"
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Button(
                                "Change Stop",
                                id={'type': 'irl-change-stop-btn', 'index': idx},
                                color="warning",
                                size="sm",
                                className="mt-1"
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Button(
                                "Close",
                                id={'type': 'irl-close-btn', 'index': idx},
                                color="danger",
                                size="sm",
                                className="mt-1"
                            )
                        ], width=3)
                    ])
                ])
            ], className="mb-3")
        )
    return items

# Callback: Close position
@callback(
    Output('irl-equity-store', 'data', allow_duplicate=True),
    Output('irl-open-position-status', 'children', allow_duplicate=True),
    Input({'type': 'irl-close-btn', 'index': ALL}, 'n_clicks'),
    State('irl-equity-store', 'data'),
    prevent_initial_call=True
)
def close_irl_position(close_n, data):
    import yfinance as yf
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    for i, n in enumerate(close_n):
        if n:
            idx = i
            break
    else:
        raise PreventUpdate
    df = pd.DataFrame(data) if data else load_trading_df()
    open_mask = (df['open_positions'] == 1.0)
    open_idxs = [i for i, v in enumerate(open_mask) if v]
    if idx >= len(open_idxs):
        return dash.no_update, "Invalid position."
    pos_idx = df[open_mask].index[idx]
    stock = df.at[pos_idx, 'stocks_in_positions']
    # Fetch current price using yfinance
    try:
        ticker = yf.Ticker(stock)
        price_series = ticker.history(period='1d')['Close']
        price = float(price_series.iloc[-1])
        df2 = close_position(df, stock, price)
        return df2.to_dict('records'), f"Closed {stock} at {price:.2f} (current price)"
    except Exception as e:
        return dash.no_update, f"Error: {e}"

# Callback: Change stop price
@callback(
    Output('irl-equity-store', 'data', allow_duplicate=True),
    Output('irl-open-position-status', 'children', allow_duplicate=True),
    Input({'type': 'irl-change-stop-btn', 'index': ALL}, 'n_clicks'),
    State('irl-equity-store', 'data'),
    State({'type': 'irl-new-stop-input', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def change_stop_price(change_n, data, new_stops):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    for i, n in enumerate(change_n):
        if n:
            idx = i
            break
    else:
        raise PreventUpdate
    
    df = pd.DataFrame(data) if data else load_trading_df()
    open_mask = (df['open_positions'] == 1.0)
    open_idxs = [i for i, v in enumerate(open_mask) if v]
    if idx >= len(open_idxs):
        return dash.no_update, "Invalid position."
    
    pos_idx = df[open_mask].index[idx]
    stock = df.at[pos_idx, 'stocks_in_positions']
    new_stop = new_stops[idx] if new_stops and idx < len(new_stops) else None
    
    if not new_stop:
        return dash.no_update, "Please enter a new stop price."
    
    try:
        df2 = update_stop_price(df, stock, float(new_stop))
        return df2.to_dict('records'), f"Stop price updated for {stock} to {new_stop}"
    except Exception as e:
        return dash.no_update, f"Error: {e}"

# Callback: Check Trade Apgar score
@callback(
    [Output('irl-apgar-results', 'children'),
     Output('irl-apgar-results', 'className')],
    [Input('irl-check-apgar-btn', 'n_clicks')],
    [State('irl-stock-symbol-input', 'value'),
     State('irl-buy-sell-radio', 'value')],
    prevent_initial_call=True,
    running=[(Output("irl-check-apgar-btn", "disabled"), True, False)]
)
def check_trade_apgar(n_clicks, symbol, side):
    """Check Trade Apgar score for the entered symbol"""
    if not n_clicks or not symbol:
        raise PreventUpdate
    
    try:
        # Calculate Trade Apgar score for the selected side
        side = side or 'buy'  # Default to buy if not specified
        apgar_result = calculate_trade_apgar(symbol.strip().upper(), side)
        
        if apgar_result.get('error'):
            return [
                dbc.Alert([
                    html.H6("❌ Trade Apgar Check Failed", style={'marginBottom': '10px'}),
                    html.P(apgar_result['error'], style={'marginBottom': '0', 'fontSize': '14px'})
                ], color="danger"),
                'd-block'
            ]
        
        # Create detailed results display
        details = apgar_result['details']
        total_score = apgar_result['total_score']
        passed = apgar_result['passed']
        side_used = apgar_result.get('side', side)
        
        # Color coding for pass/fail
        if passed:
            header_color = "success"
            header_icon = "✅"
            status_text = "PASSED - Good trading conditions!"
        else:
            header_color = "warning"
            header_icon = "⚠️"
            # Check if it's due to score or zeros
            has_zeros = any(d['score'] == 0 for d in [details['weekly_impulse'], details['daily_impulse'], details['daily_price'], details['false_breakout'], details['perfection']])
            if has_zeros:
                status_text = f"ADVISORY - Score {total_score}/10 but has zero components"
            else:
                status_text = f"ADVISORY - Score {total_score}/10 (need 7+)"
        
        # Create score breakdown
        score_items = [
            html.Div([
                html.Strong(f"1. Weekly Impulse: ", style={'color': '#fff'}),
                html.Span(f"{details['weekly_impulse']['score']}/2", 
                         style={'color': '#00d4aa', 'fontWeight': 'bold'}),
                html.Br(),
                html.Small(f"Color: {details['weekly_impulse']['color'].title()}", 
                          style={'color': '#ccc', 'fontStyle': 'italic'}),
                html.Br(),
                html.Small(details['weekly_impulse']['reason'], 
                          style={'color': '#aaa', 'fontSize': '10px'})
            ], className="mb-2"),
            
            html.Div([
                html.Strong(f"2. Daily Impulse: ", style={'color': '#fff'}),
                html.Span(f"{details['daily_impulse']['score']}/2", 
                         style={'color': '#00d4aa', 'fontWeight': 'bold'}),
                html.Br(),
                html.Small(f"Color: {details['daily_impulse']['color'].title()}", 
                          style={'color': '#ccc', 'fontStyle': 'italic'}),
                html.Br(),
                html.Small(details['daily_impulse']['reason'], 
                          style={'color': '#aaa', 'fontSize': '10px'})
            ], className="mb-2"),
            
            html.Div([
                html.Strong(f"3. Daily Price vs Value: ", style={'color': '#fff'}),
                html.Span(f"{details['daily_price']['score']}/2", 
                         style={'color': '#00d4aa', 'fontWeight': 'bold'}),
                html.Br(),
                html.Small(f"Position: {details['daily_price']['position'].replace('_', ' ').title()}", 
                          style={'color': '#ccc', 'fontStyle': 'italic'}),
                html.Br(),
                html.Small(details['daily_price']['reason'], 
                          style={'color': '#aaa', 'fontSize': '10px'})
            ], className="mb-2"),
            
            html.Div([
                html.Strong(f"4. False Breakout: ", style={'color': '#fff'}),
                html.Span(f"{details['false_breakout']['score']}/2", 
                         style={'color': '#00d4aa', 'fontWeight': 'bold'}),
                html.Br(),
                html.Small(f"Status: {details['false_breakout']['status'].replace('_', ' ').title()}", 
                          style={'color': '#ccc', 'fontStyle': 'italic'}),
                html.Br(),
                html.Small(details['false_breakout']['reason'], 
                          style={'color': '#aaa', 'fontSize': '10px'})
            ], className="mb-2"),
            
            html.Div([
                html.Strong(f"5. Perfection: ", style={'color': '#fff'}),
                html.Span(f"{details['perfection']['score']}/2", 
                         style={'color': '#00d4aa', 'fontWeight': 'bold'}),
                html.Br(),
                html.Small(f"Perfect timeframes: {details['perfection']['timeframes']}", 
                          style={'color': '#ccc', 'fontStyle': 'italic'}),
                html.Br(),
                html.Small(details['perfection']['reason'], 
                          style={'color': '#aaa', 'fontSize': '10px'})
            ], className="mb-2")
        ]
        
        # Create the results card
        results_card = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.Span(header_icon, style={'marginRight': '8px', 'fontSize': '18px'}),
                    f"Trade Apgar Score ({side_used.upper()}): {total_score}/10"
                ], style={'color': '#fff', 'marginBottom': '0'})
            ], style={'backgroundColor': f'#{header_color}', 'border': 'none'}),
            dbc.CardBody([
                html.Div([
                    html.H6(status_text, style={'color': '#fff', 'marginBottom': '15px'}),
                    html.P([
                        "The Trade Apgar evaluates 5 components on a scale of 0-2. ",
                        html.Strong("Elder's A-trade criteria: Total score ≥ 7 AND no zero components."),
                        html.Br(),
                        html.Small("Based on Elder's methodology from 'Trading for a Living'", 
                                 style={'color': '#ccc', 'fontStyle': 'italic'})
                    ], style={'color': '#ccc', 'marginBottom': '20px'}),
                    
                    # Score breakdown
                    html.Div(score_items),
                    
                    # Advisory message
                    html.Div([
                        html.Hr(style={'borderColor': '#333', 'margin': '20px 0'}),
                        html.Div([
                            html.Strong("⚠️ Advisory:" if not passed else "✅ A-Trade Criteria Met:", 
                                      style={'color': '#ffc107' if not passed else '#28a745'}),
                            html.P([
                                "This trade doesn't meet Elder's A-trade criteria. " if not passed else "This trade meets Elder's A-trade criteria. ",
                                html.Strong("You can still trade, but consider finding a better opportunity." if not passed else "Good conditions for trading!"),
                                html.Br() if not passed else "",
                                html.Small(f"Score {total_score}/10 - {'Has zero components' if any(d['score'] == 0 for d in [details['weekly_impulse'], details['daily_impulse'], details['daily_price'], details['false_breakout'], details['perfection']]) else 'Below 7'} or has zero components" if not passed else "", 
                                         style={'color': '#ccc', 'fontStyle': 'italic'}) if not passed else ""
                            ], style={'color': '#ccc', 'marginTop': '5px'})
                        ])
                    ])
                ])
            ])
        ], style={'backgroundColor': '#1a1a1a', 'border': '1px solid #444'})
        
        return [results_card], 'd-block'
        
    except Exception as e:
        return [
            dbc.Alert([
                html.H6("❌ Trade Apgar Check Failed", style={'marginBottom': '10px'}),
                html.P(f"Error: {str(e)}", style={'marginBottom': '0', 'fontSize': '14px'})
            ], color="danger"),
            'd-block'
        ]

# Run the server
if __name__ == '__main__':
    print("Starting Stock Dashboard Server...")
    print("Open http://127.0.0.1:8050/ in your web browser to view the dashboard")
    app.run(debug=True, port=8050)


