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
    update_indicator_options
)

# Custom CSS for dark theme with full black background and Inter font
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif !important;
}

.dash-dropdown .Select-control {
    background-color: #000000 !important;
    border-color: #444 !important;
    color: #fff !important;
}

.dash-dropdown .Select-menu-outer {
    background-color: #000000 !important;
    border-color: #444 !important;
}

.dash-dropdown .Select-option {
    background-color: #000000 !important;
    color: #fff !important;
}

.dash-dropdown .Select-option:hover {
    background-color: #00d4aa !important;
    color: #000 !important;
}

.dash-dropdown .Select-value-label {
    color: #fff !important;
}

body {
    background-color: #000000 !important;
    color: #fff !important;
}

/* Additional customizations for consistency */
.card {
    background-color: #000000 !important;
    border-color: #444 !important;
}

.card-header {
    background-color: #000000 !important;
    border-bottom: 1px solid #333 !important;
}

.card-body {
    background-color: #000000 !important;
}

.btn {
    font-family: 'Inter', sans-serif !important;
}

/* Improve readability of text on black background */
h1, h2, h3, h4, h5, h6 {
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
}

.form-control, .form-select {
    background-color: #000000 !important;
    border-color: #444 !important;
    color: #fff !important;
}

/* Make scrollbars match theme */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #111;
}

::-webkit-scrollbar-thumb {
    background: #444;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #00d4aa;
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
    # Sidebar toggle button (fixed position)
    dbc.Button(
        "☰", 
        id="sidebar-toggle-button", 
        color="secondary", 
        className="mb-3",
        style={"position": "fixed", "top": "20px", "left": "20px", "zIndex": "1000", "fontSize": "20px", "fontWeight": "bold", "padding": "5px 12px"}
    ),
    
    # Main content row with sidebar and charts
    dbc.Row([
        # Sidebar column with collapse functionality
        dbc.Col(
            dbc.Collapse(
                html.Div(style={'height': '95vh', 'overflow-y': 'auto'}, children=[            dbc.Card([
                dbc.CardHeader(html.H4("🔍 Stock Search", className="text-center", style={'color': '#00d4aa'})),
                dbc.CardBody([
                    dbc.Label("Stock Symbol:", style={'color': '#fff', 'fontWeight': 'bold'}),
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
                                    'border': '1px solid #444'
                                },
                                className="text-uppercase"
                            )
                        ], width=9),
                        dbc.Col([
                            dbc.Button("🔍", id="search-button", color="success", n_clicks=0, className="w-100")
                        ], width=3)
                    ], className="mb-3"),
                    
                    dbc.Label("Time Frame:", style={'color': '#fff', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
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
                        value='1d',  # Default to 1D view
                        className="mb-3",
                        style={'backgroundColor': '#000000', 'color': '#fff'}
                    ),
                    
                    dbc.Label("Chart Type:", style={'color': '#fff', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
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
                    dbc.Label("EMA Periods:", style={'color': '#fff', 'fontWeight': 'bold'}),
                    html.Div(id='ema-periods-container', children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Fast EMA:", style={'color': '#fff', 'fontSize': '12px'}),
                                dbc.Input(id='ema-period-0', type='number', value=13, min=1, max=200, size='sm')
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Slow EMA:", style={'color': '#fff', 'fontSize': '12px'}),
                                dbc.Input(id='ema-period-1', type='number', value=26, min=1, max=200, size='sm')
                            ], width=6)
                        ], className="mb-2"),
                    ]),
                    dbc.Checklist(
                        id='show-ema',
                        options=[{'label': 'Show EMAs', 'value': 'show'}],
                        value=['show'],
                        style={'color': '#fff'},
                        className="mb-3"
                    ),
                    
                    html.Hr(style={'borderColor': '#444', 'margin': '10px 0px'}),
                    
                    # Moving ATR bands into the EMA settings card
                    dbc.Label("ATR Bands:", style={'color': '#fff', 'fontWeight': 'bold'}),
                    dbc.Checklist(
                        id='atr-bands',
                        options=[
                            {'label': '±1 ATR', 'value': '1'},
                            {'label': '±2 ATR', 'value': '2'},
                            {'label': '±3 ATR', 'value': '3'}
                        ],
                        value=[],
                        inline=True,
                        style={'color': '#fff'}
                    )
                ], style={'backgroundColor': '#000000'})
            ], style={'backgroundColor': '#000000', 'border': '1px solid #444'}, className="mb-3"),
            
            # Lower Chart Selection Card (moved up)
            dbc.Card([
                dbc.CardHeader(html.H5("📊 Lower Chart", style={'color': '#00d4aa'})),
                dbc.CardBody([
                    dbc.Label("Display:", style={'color': '#fff', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
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
                    
                    # Dynamic settings based on selected lower chart
                    html.Div(id='lower-chart-settings', children=[
                        # Settings will be dynamically generated based on selection
                    ])
                ], style={'backgroundColor': '#000000'})
            ], style={'backgroundColor': '#000000', 'border': '1px solid #444'})
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
    
    # Auto-refresh component - optimized for faster updates
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # Update every 10 seconds for faster ticker switching
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

# Callback to update symbol status message
@callback(
    Output('stock-symbol-status', 'children'),
    Output('stock-symbol-status', 'style'),
    [Input('current-symbol-store', 'data')]
)
def update_symbol_status_callback(symbol):
    """Call update_symbol_status function from functions module"""
    return update_symbol_status(symbol)

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

# Callback for loading indicator with timestamp
@callback(
    Output('loading-output', 'children'),
    [Input('current-symbol-store', 'data')],
    prevent_initial_call=True
)
def update_loading_feedback(symbol):
    """Provide feedback when loading new ticker data with timestamp"""
    if symbol:
        timestamp = datetime.now().strftime('%H:%M:%S')
        return html.Div([
            html.Span(f"✅ {symbol} ", style={'color': '#00d4ff', 'fontWeight': 'bold'}),
            html.Span(f"loaded at {timestamp}", style={'color': '#aaa', 'fontSize': '12px'})
        ])
    return ""

# Run the server
if __name__ == '__main__':
    print("Starting Stock Dashboard Server...")
    print("Open http://127.0.0.1:8050/ in your web browser to view the dashboard")
    app.run(debug=True, port=8050)

