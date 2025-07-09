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

# Import functions from functions.py
from functions import (
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

# Import scanner functions
from scanner_functions import StockScanner, get_preset_filter, get_available_presets

# Enhanced CSS with Inter font and bold white card headers
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Font family for all elements */
* {
    font-family: 'Inter', sans-serif !important;
}

/* Background colors and text colors */
body, .card, .card-header, .card-body, .nav-tabs, .tab-content, .tab-pane {
    background-color: #000000 !important;
    color: #fff !important;
}

/* Card styling */
.card, .card-header {
    border-color: #444 !important;
}

.card-header {
    border-bottom: 1px solid #333 !important;
}

/* Card headers - Bold and white */
.card-header h1, .card-header h2, .card-header h3, 
.card-header h4, .card-header h5, .card-header h6 {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    margin: 0 !important;
}

/* All headers should be bold and white */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
}



/* Enhanced Form control styling */
.form-control, .form-select {
    background-color: #000000 !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

.form-control:focus, .form-select:focus {
    background-color: #000000 !important;
    border-color: #00d4aa !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.1) !important;
    color: #fff !important;
}

/* Ensure dbc.Select has consistent styling */
.form-select option {
    background-color: #000000 !important;
    color: #fff !important;
}

/* Navigation tabs */
.nav-tabs {
    background-color: #000000 !important;
    border-bottom: 1px solid #444 !important;
}

.nav-tabs .nav-link {
    background-color: #000000 !important;
    border: 1px solid #444 !important;
    color: #ccc !important;
    font-weight: 500 !important;
    border-radius: 8px 8px 0 0 !important;
}

.nav-tabs .nav-link:hover, .nav-tabs .nav-link.active {
    color: #00d4aa !important;
    border-color: #00d4aa !important;
}

.nav-tabs .nav-link.active {
    background-color: #000000 !important;
    border-color: #00d4aa #00d4aa #000000 !important;
}

/* Enhanced Form controls */
.form-check-input {
    background-color: #222 !important;
    border: 2px solid #666 !important;
    border-radius: 6px !important;
}

.form-check-input:checked {
    background-color: #00d4aa !important;
    border-color: #00d4aa !important;
}

.form-check-label {
    color: #fff !important;
    padding-left: 8px !important;
    font-weight: 500 !important;
}

/* Enhanced Button effects */
.btn {
    font-family: 'Inter', sans-serif !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
}

.btn-success {
    background: linear-gradient(45deg, #00d4aa, #00ff88) !important;
    border: none !important;
    color: #000 !important;
}

.btn-secondary {
    background-color: #333 !important;
    border-color: #444 !important;
    color: #fff !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #000000;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #444;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #00d4aa;
}

/* Enhanced Labels styling */
.form-label, label {
    color: #fff !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    margin-bottom: 8px !important;
}

/* Input styling enhancements */
input[type="number"], input[type="text"] {
    background-color: #000000 !important;
    border: 1px solid #333 !important;
    border-radius: 6px !important;
    color: #fff !important;
    font-weight: 500 !important;
}

input[type="number"]:focus, input[type="text"]:focus {
    border-color: #00d4aa !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.1) !important;
}

/* Card enhancements */
.card {
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}

.card-header {
    border-radius: 12px 12px 0 0 !important;
}

.card-body {
    border-radius: 0 0 12px 12px !important;
}

/* Alert styling for AMOLED */
.alert {
    border-radius: 8px !important;
    border: 1px solid #333 !important;
    background-color: #000000 !important;
}

.alert-warning {
    color: #ffcc00 !important;
    border-color: #ffcc00 !important;
}
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
                                label="🔍 Scanner",
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
                                                        dbc.Button("Value Zone", id="preset-value-zone", size="sm", color="info", outline=True, className="mb-2 w-100")
                                                    ], width=6),
                                                    dbc.Col([
                                                        dbc.Button("Oversold RSI", id="preset-oversold", size="sm", color="warning", outline=True, className="mb-2 w-100")
                                                    ], width=6)
                                                ]),
                                                dbc.Row([
                                                    dbc.Col([
                                                        dbc.Button("High Volume", id="preset-volume", size="sm", color="success", outline=True, className="mb-2 w-100")
                                                    ], width=6),
                                                    dbc.Col([
                                                        dbc.Button("Random 25", id="preset-random", size="sm", color="secondary", outline=True, className="mb-2 w-100")
                                                    ], width=6)
                                                ], className="mb-3"),
                                                
                                                html.Hr(style={'borderColor': '#333'}),
                                                
                                                # Expandable Filter Sections
                                                dbc.Accordion([
                                                    dbc.AccordionItem([
                                                        # Elder's Core Filters
                                                        dbc.Checklist(
                                                            id='elder-filters',
                                                            options=[
                                                                {'label': '📊 In Value Zone (13-26 EMA)', 'value': 'value_zone'},
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
                                                                {'label': 'Recovery (30-40)', 'value': 'recovery'},
                                                                {'label': 'Neutral (40-60)', 'value': 'neutral'},
                                                                {'label': 'Overbought Setup (60-70)', 'value': 'setup'},
                                                                {'label': 'Overbought (> 70)', 'value': 'overbought'}
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
                                                            options=[
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
                                                                {'label': '💰 Dividend Stocks', 'value': 'dividend'}
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
                                                                    options=[
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
                                                
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'})
                                    ])
                                ]
                            ),
                            # Stock Search Tab (Analysis)
                            dbc.Tab(
                                label="🛠️ Analysis",
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
                                                        {'label': '📅 Previous Market Period', 'value': 'yesterday'},
                                                        {'label': '📅 1 Month', 'value': '1mo'},
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
                                                )
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3"),
                                        
                                        # EMA and ATR Settings Card (Main Chart Settings)
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
                                                    style={'color': '#fff'}
                                                )
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3"),
                                        
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
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'})
                                    ])
                                ]
                            ),
                            # Insights Tab
                            dbc.Tab(
                                label="💡 Insights",
                                tab_id="insights-tab",
                                children=[
                                    html.Div(style={'padding': '15px 0'}, children=[
                                        dbc.Card([
                                            dbc.CardHeader(html.H4("💡 Insights", className="text-center", style={'color': '#00d4aa'})),
                                            dbc.CardBody([
                                                # Current Stock Display (read-only)
                                                dbc.Label("Analyzing Current Stock:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                                                html.Div(
                                                    id='insights-current-stock',
                                                    style={
                                                        'backgroundColor': '#000000',
                                                        'border': '2px solid #00d4aa',
                                                        'borderRadius': '8px',
                                                        'padding': '12px 16px',
                                                        'marginBottom': '20px',
                                                        'textAlign': 'center'
                                                    },
                                                    children=[
                                                        html.H5("SPY", style={'color': '#00d4aa', 'margin': '0', 'fontWeight': 'bold'})
                                                    ]
                                                ),
                                                
                                                # Trading Style Selection
                                                dbc.Label("Trading Style:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '15px'}),
                                                dbc.RadioItems(
                                                    id='insights-trading-style',
                                                    options=[
                                                        {
                                                            'label': html.Div([
                                                                html.Div([
                                                                    "⚡ Day Trading",
                                                                    html.Small(" (Intraday positions)", style={'color': '#ccc', 'display': 'block', 'fontStyle': 'italic'})
                                                                ], style={'marginLeft': '8px'})
                                                            ]), 
                                                            'value': 'day_trading'
                                                        },
                                                        {
                                                            'label': html.Div([
                                                                html.Div([
                                                                    "📊 Swing Trading",
                                                                    html.Small(" (2-10 day positions)", style={'color': '#ccc', 'display': 'block', 'fontStyle': 'italic'})
                                                                ], style={'marginLeft': '8px'})
                                                            ]), 
                                                            'value': 'swing_trading'
                                                        },
                                                        {
                                                            'label': html.Div([
                                                                html.Div([
                                                                    "🌱 Long-term Trading",
                                                                    html.Small(" (Weeks to months)", style={'color': '#ccc', 'display': 'block', 'fontStyle': 'italic'})
                                                                ], style={'marginLeft': '8px'})
                                                            ]), 
                                                            'value': 'longterm_trading'
                                                        }
                                                    ],
                                                    value='swing_trading',  # Default to swing trading
                                                    style={'color': '#fff'},
                                                    className="mb-4"
                                                ),
                                                
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
                            )
                        ],
                        style={'backgroundColor': '#000000'}
                    )
                ]),
                id="sidebar-collapse",
                is_open=True
            ),
            width=3,
            id="sidebar-col"
        ),
        
        # Charts column
        dbc.Col([
            # Error message component
            html.Div(
                id="chart-error-message", 
                className="alert alert-warning fade show d-none",
                children=[]
            ),
            # Market closed message - hidden by default
            html.Div(
                id="market-closed-message",
                className="d-none",
                style={
                    'height': '90vh', 
                    'display': 'flex', 
                    'alignItems': 'center', 
                    'justifyContent': 'center', 
                    'flexDirection': 'column',
                    'backgroundColor': '#000000',
                    'borderRadius': '8px',
                    'padding': '20px',
                    'border': '1px solid #333'
                },
                children=[
                    html.H2("US markets are closed right now", style={'color': '#ff4444', 'textAlign': 'center', 'marginBottom': '20px'}),
                    html.H5("Come back during market hours (9:30AM - 4:00PM ET)", 
                           style={'color': '#ccc', 'textAlign': 'center', 'fontWeight': 'normal'}),
                    html.Div(style={'marginTop': '30px', 'textAlign': 'center'}, children=[
                        dbc.Button(
                            "⏮️ View Previous Session",
                            id="view-yesterday-btn",
                            color="danger",
                            outline=True
                        )
                    ])
                ]
            ),
            # Main content area that switches between chart and scanner results
            html.Div(
                id="main-content-area",
                style={'height': '90vh', 'backgroundColor': '#000000', 'position': 'relative'},
                children=[
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
        ], width=9, id="chart-col")
    ]), # Added missing closing bracket for dbc.Row
    
    # Auto-refresh component - Optimized interval
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Update every 30 seconds - balanced for performance
        n_intervals=0
    ),
    
    # Store components for data and symbol
    dcc.Store(id='stock-data-store'),
    dcc.Store(id='current-symbol-store', data='SPY'),
    dcc.Store(id='ema-periods-store', data=[13, 26])
    
], fluid=True, style={'backgroundColor': '#000000', 'minHeight': '100vh'})

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

# Create hidden divs to store values when not visible in UI
# These will be shared across callbacks
app.layout.children.extend([
    dcc.Store(id='macd-fast-store', data=12),
    dcc.Store(id='macd-slow-store', data=26),
    dcc.Store(id='macd-signal-store', data=9),
    dcc.Store(id='force-smoothing-store', data=2),
    dcc.Store(id='adx-period-store', data=13),
    dcc.Store(id='adx-components-store', data=['adx', 'di_plus', 'di_minus']),
    dcc.Store(id='stochastic-period-store', data=5),
    dcc.Store(id='rsi-period-store', data=13)
])

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

# Callback to update RSI period store
@callback(
    Output('rsi-period-store', 'data'),
    Input('rsi-period', 'value'),
    prevent_initial_call=True
)
def update_rsi_store_callback(period):
    """Call update_rsi_store function from functions module"""
    return update_rsi_store(period)

# Callback to update data with custom indicator parameters
@callback(
    [Output('stock-data-store', 'data'),
     Output('chart-error-message', 'children'),
     Output('chart-error-message', 'className')],
    [Input('interval-component', 'n_intervals'),
     Input('current-symbol-store', 'data'),
     Input('timeframe-dropdown', 'value'),
     Input('ema-periods-store', 'data'),
     # Use store values instead of direct references to UI elements
     Input('macd-fast-store', 'data'),
     Input('macd-slow-store', 'data'),
     Input('macd-signal-store', 'data'),
     Input('force-smoothing-store', 'data'),
     Input('adx-period-store', 'data'),
     Input('stochastic-period-store', 'data'),
     Input('rsi-period-store', 'data')]
)
def update_data_callback(n, symbol, timeframe, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, adx_period, stoch_period, rsi_period):
    """Call update_data function from functions module"""
    return update_data(n, symbol, timeframe, ema_periods, macd_fast, macd_slow, macd_signal, force_smoothing, adx_period, stoch_period, rsi_period)

# Callback for combined chart
@callback(
    [Output('combined-chart', 'figure'),
     Output('combined-chart', 'style'),
     Output('market-closed-message', 'className')],
    [Input('stock-data-store', 'data'),
     Input('current-symbol-store', 'data'),
     Input('chart-type-dropdown', 'value'),
     Input('show-ema', 'value'),
     Input('ema-periods-store', 'data'),
     Input('atr-bands', 'value'),
     Input('lower-chart-selection', 'value'),
     Input('adx-components-store', 'data'),
     Input('timeframe-dropdown', 'value')],
    [State('combined-chart', 'relayoutData')],
    prevent_initial_call=False
)
def update_combined_chart_callback(data, symbol, chart_type, show_ema, ema_periods, atr_bands, lower_chart_type, adx_components, timeframe, relayout_data):
    """Call update_combined_chart function from functions module"""
    # Try to get volume comparison value, but don't require it
    ctx = dash.callback_context
    volume_comparison = 'none'  # Default value
    
    # Create a basic empty figure for when we're not showing the chart
    empty_fig = go.Figure()
    
    # Check if we're in "Today" mode and data is empty (markets closed)
    if timeframe == '1d' and (not data or len(data) == 0):
        now_local = datetime.now()
        
        # Determine if the market should be open right now based on ET time
        # Convert local time to ET (assuming CEST, which is UTC+2, while ET in summer is UTC-4)
        et_time = now_local - timedelta(hours=6)  # Rough adjustment from CEST to ET
        is_weekend = et_time.weekday() >= 5  # Saturday=5, Sunday=6
        
        # Market hours: 9:30 AM - 4:00 PM ET, weekdays only
        is_market_hours = (
            not is_weekend and
            ((et_time.hour > 9 or (et_time.hour == 9 and et_time.minute >= 30)) and
             (et_time.hour < 16))
        )
        
        # Only show the "markets closed" message during times when markets would normally be open
        if is_market_hours:
            # Market should be open, but no data - likely a holiday or issue
            return empty_fig, {'display': 'none'}, 'd-block'
        else:
            # Outside normal market hours, show a message that reflects that
            return empty_fig, {'display': 'none'}, 'd-block'
    else:
        # Normal case - show the chart and hide the message
        # Pass relayout data to preserve zoom/pan state
        fig = update_combined_chart(data, symbol, chart_type, show_ema, ema_periods, 
                                   atr_bands, lower_chart_type, adx_components, 
                                   volume_comparison, relayout_data, timeframe)
        return fig, {'backgroundColor': '#000000', 'height': '90vh'}, 'd-none'

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
     State('combined-chart', 'relayoutData')],
    prevent_initial_call=True
)
def update_combined_chart_volume_comparison(volume_comparison, data, symbol, chart_type, show_ema, ema_periods, atr_bands, lower_chart_type, adx_components, timeframe, relayout_data):
    """Update combined chart when volume comparison changes"""
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
            fig = update_combined_chart(data, symbol, chart_type, show_ema, ema_periods, atr_bands, lower_chart_type, adx_components, volume_comparison, relayout_data, timeframe)
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
    Output('timeframe-dropdown', 'value', allow_duplicate=True),
    [Input('view-yesterday-btn', 'n_clicks')],
    prevent_initial_call=True
)
def view_yesterday_callback(n_clicks):
    """Switch to yesterday's data when the button is clicked"""
    if n_clicks:
        return 'yesterday'
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

# Callback to update the current stock display in Insights tab
@callback(
    Output('insights-current-stock', 'children'),
    [Input('current-symbol-store', 'data')]
)
def update_insights_current_stock(current_symbol):
    """Update the current stock display in the Insights tab"""
    symbol = current_symbol or 'SPY'
    return html.H5(symbol, style={'color': '#00d4aa', 'margin': '0', 'fontWeight': 'bold'})

# Callback to handle insights analysis
@callback(
    [Output('insights-status', 'children'),
     Output('insights-results', 'children')],
    [Input('run-insights-button', 'n_clicks')],
    [State('current-symbol-store', 'data'),
     State('insights-trading-style', 'value')],
    prevent_initial_call=True
)
def run_insights_analysis(n_clicks, current_symbol, trading_style):
    """Handle the insights analysis when the button is clicked"""
    if not n_clicks:
        raise PreventUpdate
    
    # Use current symbol or fallback to SPY
    symbol = current_symbol or 'SPY'
    
    # Validate trading style
    if not trading_style:
        return [
            dbc.Alert("Please select a trading style", color="warning", className="mt-2"),
            []
        ]
    
    # Show loading state
    loading_status = html.Div([
        dbc.Spinner(size="sm", color="success"),
        html.Span(" Analyzing " + symbol + " for " + trading_style.replace('_', ' ').title() + "...", 
                 style={'marginLeft': '10px', 'color': '#00d4aa'})
    ])
    
    # For now, return a placeholder result
    # This is where the actual AI analysis would be implemented
    
    # Get trading style display name and emoji
    style_info = {
        'day_trading': {'name': 'Day Trading', 'emoji': '⚡', 'color': '#ff6b6b'},
        'swing_trading': {'name': 'Swing Trading', 'emoji': '📊', 'color': '#4ecdc4'},
        'longterm_trading': {'name': 'Long-term Trading', 'emoji': '🌱', 'color': '#45b7d1'}
    }
    
    current_style = style_info.get(trading_style, style_info['swing_trading'])
    
    # Create placeholder results
    results = dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.Span(current_style['emoji'], style={'marginRight': '10px', 'fontSize': '24px'}),
                f"{current_style['name']} Analysis for {symbol}"
            ], style={'color': '#00d4aa', 'marginBottom': '0'})
        ]),
        dbc.CardBody([
            html.Div([
                html.H6("Insights is under development! It will include:", style={'color': '#fff', 'marginBottom': '15px'}),
                html.Ul([
                    html.Li(f"📊 Technical indicators optimized for {current_style['name'].lower()}", style={'color': '#ccc', 'marginBottom': '5px'}),
                    html.Li("🎯 Entry and exit signals", style={'color': '#ccc', 'marginBottom': '5px'}),
                    html.Li("⚠️ Risk assessment and position sizing", style={'color': '#ccc', 'marginBottom': '5px'}),
                    html.Li("📈 Market sentiment analysis", style={'color': '#ccc', 'marginBottom': '5px'}),
                    html.Li("🔮 Price targets and stop-loss recommendations", style={'color': '#ccc', 'marginBottom': '5px'})
                ], style={'listStyleType': 'none', 'paddingLeft': '0'})
            ])
        ])
    ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mt-3")
    
    return [[], results]

# ========== STOCK SCANNER TAB CALLBACKS ==========

# Callback for preset scan buttons
@callback(
    [Output('elder-filters', 'value'),
     Output('rsi-preset', 'value'),
     Output('volume-preset', 'value'),
     Output('universe-selection', 'value'),
     Output('result-limit', 'value')],
    [Input('preset-value-zone', 'n_clicks'),
     Input('preset-oversold', 'n_clicks'),
     Input('preset-volume', 'n_clicks'),
     Input('preset-random', 'n_clicks')],
    prevent_initial_call=True
)
def handle_preset_buttons(value_zone_clicks, oversold_clicks, volume_clicks, random_clicks):
    """Handle quick preset scan button clicks"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'preset-value-zone':
        return ['value_zone'], 'any', 500000, ['sp500'], 25
    elif button_id == 'preset-oversold':
        return [], 'recovery', 1000000, ['sp500'], 25
    elif button_id == 'preset-volume':
        return [], 'any', 5000000, ['sp500', 'nasdaq100'], 25
    elif button_id == 'preset-random':
        return [], 'any', 0, ['sp500'], 25
    
    raise PreventUpdate

# Main scanner callback
@callback(
    [Output('scan-status', 'children'),
     Output('scanner-results-area', 'children'),
     Output('scanner-results-area', 'className'),
     Output('combined-chart', 'style', allow_duplicate=True)],
    [Input('start-scan-button', 'n_clicks')],
    [State('elder-filters', 'value'),
     State('rsi-preset', 'value'),
     State('volume-preset', 'value'),
     State('price-preset', 'value'),
     State('change-preset', 'value'),
     State('universe-selection', 'value'),
     State('result-limit', 'value'),
     State('sort-by', 'value')],
    prevent_initial_call=True,
    running=[(Output("start-scan-button", "disabled"), True, False)]
)
def run_stock_scan(n_clicks, elder_filters, rsi_preset, volume_preset, price_preset, 
                  change_preset, universe_selection, result_limit, sort_by):
    """Handle the stock scan when the button is clicked"""
    if not n_clicks:
        raise PreventUpdate
    
    try:
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
        
        # Determine if this is a random scan (for preset-random button)
        ctx = dash.callback_context
        random_sample = False
        if ctx.triggered:
            # Check if this was triggered by preset-random indirectly
            if not elder_filters and rsi_preset == 'any' and volume_preset == 0:
                random_sample = 25
        
        # Run the scan
        results_df = scanner.scan_stocks(
            filters=filters if not random_sample else None,
            universes=universe_selection or ['sp500'],
            max_results=result_limit or 25,
            sort_by=sort_by or 'volume',
            random_sample=random_sample
        )
        
        if results_df.empty:
            return (
                dbc.Alert("❌ No stocks found matching your criteria. Try adjusting your filters.", color="warning"),
                [],
                'd-none',  # Hide scanner results area
                {
                    'backgroundColor': '#000000', 
                    'height': '90vh',
                    'position': 'absolute',
                    'top': '0',
                    'left': '0',
                    'width': '100%',
                    'zIndex': 1,
                    'display': 'block'
                }  # Show normal chart
            )
        
        # Create results table
        table_data = results_df.copy()
        
        # Format data for display
        for col in ['price', 'ema_13', 'ema_26']:
            if col in table_data.columns:
                table_data[col] = table_data[col].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        
        if 'volume' in table_data.columns:
            table_data['volume'] = table_data['volume'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
        
        if 'price_change_pct' in table_data.columns:
            table_data['price_change_pct'] = table_data['price_change_pct'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")
        
        if 'rsi' in table_data.columns:
            table_data['rsi'] = table_data['rsi'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
        
        # Create data table
        table = dash_table.DataTable(
            id='scan-results-table',
            data=table_data.to_dict('records'),
            columns=[
                {'name': 'Symbol', 'id': 'symbol', 'type': 'text'},
                {'name': 'Price', 'id': 'price', 'type': 'text'},
                {'name': 'Change %', 'id': 'price_change_pct', 'type': 'text'},
                {'name': 'Volume', 'id': 'volume', 'type': 'text'},
                {'name': 'RSI', 'id': 'rsi', 'type': 'text'},
                {'name': 'EMA 13', 'id': 'ema_13', 'type': 'text'},
                {'name': 'EMA 26', 'id': 'ema_26', 'type': 'text'},
                {'name': 'EMA Trend', 'id': 'ema_trend', 'type': 'text'},
                {'name': 'In Value Zone', 'id': 'in_value_zone', 'type': 'text'},
                {'name': 'MACD Signal', 'id': 'macd_signal', 'type': 'text'}
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
            style_data_conditional=[
                # Green for positive changes
                {
                    'if': {
                        'filter_query': '{price_change_pct} contains "+"',
                        'column_id': 'price_change_pct'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                # Red for negative changes
                {
                    'if': {
                        'filter_query': '{price_change_pct} contains "-"',
                        'column_id': 'price_change_pct'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # Highlight bullish trend
                {
                    'if': {
                        'filter_query': '{ema_trend} = bullish',
                        'column_id': 'ema_trend'
                    },
                    'backgroundColor': '#1a4d3a',
                    'color': '#00ff88'
                },
                # Highlight bearish trend
                {
                    'if': {
                        'filter_query': '{ema_trend} = bearish',
                        'column_id': 'ema_trend'
                    },
                    'backgroundColor': '#4d1a1a',
                    'color': '#ff6b6b'
                },
                # Highlight value zone stocks
                {
                    'if': {
                        'filter_query': '{in_value_zone} = True',
                        'column_id': 'in_value_zone'
                    },
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4aa'
                },
                # Make symbol column clickable and prominent
                {
                    'if': {'column_id': 'symbol'},
                    'backgroundColor': '#1a3d4d',
                    'color': '#00d4aa',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'textDecoration': 'underline'
                }
            ],
            sort_action="native",
            page_size=20,
            page_action="native"
        )
        
        # Create summary info
        scan_type = "Random Sample" if random_sample else "Filtered Scan"
        universes_str = ", ".join(universe_selection or ['sp500']).upper()
        
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
                " in the table to load its 6-month chart for detailed analysis.",
            ], style={'marginBottom': '0', 'fontSize': '12px', 'fontStyle': 'italic'})
        ], color="info", className="mb-2")
        
        return success_msg, [instructions, table], 'd-block', {
            'backgroundColor': '#000000', 
            'height': '90vh',
            'position': 'absolute',
            'top': '0',
            'left': '0',
            'width': '100%',
            'zIndex': 1,
            'display': 'none'
        }
        
    except Exception as e:
        error_msg = dbc.Alert([
            html.H6("❌ Scan Failed", style={'marginBottom': '10px'}),
            html.P(f"Error: {str(e)}", style={'marginBottom': '0', 'fontSize': '14px'})
        ], color="danger")
        return error_msg, [], 'd-none', {
            'backgroundColor': '#000000', 
            'height': '90vh',
            'position': 'absolute',
            'top': '0',
            'left': '0',
            'width': '100%',
            'zIndex': 1,
            'display': 'block'
        }

# Callback to load clicked symbol into main chart and switch back to chart view
# Callback to load clicked symbol into main chart and switch back to chart view
@callback(
    [Output('stock-symbol-input', 'value', allow_duplicate=True),
     Output('current-symbol-store', 'data', allow_duplicate=True),
     Output('timeframe-dropdown', 'value', allow_duplicate=True),
     Output('scanner-results-area', 'className', allow_duplicate=True),
     Output('combined-chart', 'style', allow_duplicate=True),
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
            # Clear any formatting from the symbol (remove $ signs, etc.)
            clean_symbol = symbol.replace('$', '').strip()
            return (
                clean_symbol,                                        # Update symbol input
                clean_symbol,                                        # Update symbol store
                '6mo',                                               # Set timeframe to 6 months
                'd-none',                                            # Hide scanner results
                {
                    'backgroundColor': '#000000', 
                    'height': '90vh',
                    'position': 'absolute',
                    'top': '0',
                    'left': '0',
                    'width': '100%',
                    'zIndex': 1,
                    'display': 'block'
                },   # Show chart
                'stock-search-tab'                                   # Switch to stock search tab
            )
    raise PreventUpdate

# Callback to switch back to chart view when changing tabs
@callback(
    [Output('scanner-results-area', 'className', allow_duplicate=True),
     Output('combined-chart', 'style', allow_duplicate=True)],
    [Input('sidebar-tabs', 'active_tab')],
    prevent_initial_call=True
)
def switch_view_on_tab_change(active_tab):
    """Switch back to chart view when changing away from scanner tab"""
    if active_tab != 'scanner-tab':
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
    raise PreventUpdate

# Run the server
if __name__ == '__main__':
    print("Starting Stock Dashboard Server...")
    print("Open http://127.0.0.1:8050/ in your web browser to view the dashboard")
    app.run(debug=True, port=8050)

