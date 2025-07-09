import dash
from dash import dcc, html, Input, Output, callback, State
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
                        active_tab="stock-search-tab",
                        children=[
                            # Stock Search Tab
                            dbc.Tab(
                                label="Stock Search",
                                tab_id="stock-search-tab",
                                children=[
                                    html.Div(style={'padding': '15px 0'}, children=[
                                        # Stock Search Card
                                        dbc.Card([
                                            dbc.CardHeader(html.H4("🔍 Stock Search", className="text-center", style={'color': '#00d4aa'})),
                                            dbc.CardBody([
                                                # Stock Symbol Input Section
                                                dbc.Label("Stock Symbol:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '10px'}),
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
                                                
                                                # Stock status indicator with enhanced styling
                                                html.Div(
                                                    id="stock-status-indicator",
                                                    className="mb-4",
                                                    style={
                                                        'textAlign': 'center',
                                                        'padding': '8px 12px',
                                                        'backgroundColor': '#000000',
                                                        'borderRadius': '6px',
                                                        'border': '1px solid #333'
                                                    }
                                                ),
                                                
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
                                                
                                                # EMA Toggle with enhanced styling
                                                html.Div([
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
                                                    )
                                                ], style={
                                                    'backgroundColor': '#000000',
                                                    'borderRadius': '8px',
                                                    'padding': '12px 16px',
                                                    'border': '1px solid #333'
                                                }),
                                                
                                                html.Hr(style={'borderColor': '#333', 'margin': '20px 0'}),
                                                
                                                # ATR Bands Section
                                                dbc.Label("ATR Volatility Bands:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '12px'}),
                                                html.Div([
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
                                                ], style={
                                                    'backgroundColor': '#000000',
                                                    'borderRadius': '8px',
                                                    'padding': '12px 16px',
                                                    'border': '1px solid #333'
                                                })
                                            ], style={'backgroundColor': '#000000'})
                                        ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3"),
                                        
                                        # Lower Chart Selection Card
                                        dbc.Card([
                                            dbc.CardHeader(html.H5("📊 Lower Chart", style={'color': '#00d4aa'})),
                                            dbc.CardBody([
                                                # Lower Chart Selection
                                                dbc.Label("Display:", style={'color': '#fff', 'fontWeight': 'bold', 'marginBottom': '12px'}),
                                                html.Div([
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
                                                    )
                                                ], style={
                                                    'backgroundColor': '#000000',
                                                    'borderRadius': '8px',
                                                    'padding': '12px 16px',
                                                    'border': '1px solid #333'
                                                }),
                                                
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
                                label="Insights",
                                tab_id="insights-tab",
                                children=[
                                    html.Div(style={'padding': '15px 0'}, children=[
                                        dbc.Card([
                                            dbc.CardHeader(html.H4("💡 Trading Insights", className="text-center", style={'color': '#00d4aa'})),
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
            # Combined chart with main price chart on top and indicator chart below
            dcc.Graph(id='combined-chart', style={'backgroundColor': '#000000', 'height': '90vh'})
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

# Run the server
if __name__ == '__main__':
    print("Starting Stock Dashboard Server...")
    print("Open http://127.0.0.1:8050/ in your web browser to view the dashboard")
    app.run(debug=True, port=8050)

