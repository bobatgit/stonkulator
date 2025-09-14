# -*- coding: utf-8 -*-
"""Stonkulator MVP 1 - GCP Cloud Run
Basic Data Pipeline: Dashboard showing live stock data for S&P 500 (^GSPC)

This is the refactored version of OLD_stonkulator.py designed to run as a
containerized GCP Cloud Run service.
"""

import pandas as pd
import yfinance as yf
import panel as pn
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

# Enable Panel extensions
pn.extension('plotly')

# Configure Panel for containerized deployment
pn.config.autoreload = False
pn.config.allow_websocket_origin = ["*"]


@pn.cache(ttl=300)  # Cache for 5 minutes
def fetch_stock_data(symbol="^GSPC", period="2y"):
    """Fetch stock data from yFinance with caching"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)

        if data.empty:
            raise ValueError(f"No data found for {symbol}")

        # Add calculated fields
        data['Returns'] = data['Close'].pct_change()
        data['EMA_9'] = data['Close'].ewm(span=9).mean()
        data['EMA_50'] = data['Close'].ewm(span=50).mean()
        data['EMA_200'] = data['Close'].ewm(span=200).mean()

        return data

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def create_stock_chart(data, symbol):
    """Create interactive stock price chart using Plotly"""
    if data is None or data.empty:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

    fig = go.Figure()

    # Main price line
    fig.add_trace(go.Scatter(
        x=data.index, y=data['Close'],
        mode='lines', name=f'{symbol} Close',
        line=dict(color='#00BFFF', width=2)
    ))

    # Exponential moving averages
    if 'EMA_9' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data['EMA_9'],
            mode='lines', name='EMA 9',
            line=dict(color='orange', width=1), opacity=0.7
        ))

    if 'EMA_50' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data['EMA_50'],
            mode='lines', name='EMA 50',
            line=dict(color='#4169E1', width=1), opacity=0.7
        ))

    if 'EMA_200' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data['EMA_200'],
            mode='lines', name='EMA 200',
            line=dict(color='#191970', width=1), opacity=0.7
        ))

    fig.update_layout(
        title=f"{symbol} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        height=500,
        showlegend=True,
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig


def create_stats_panel(data):
    """Create key statistics display for chart view"""
    if data is None or data.empty:
        return pn.pane.Markdown("**No data available**")

    # Calculate key metrics
    current_price = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
    daily_change = current_price - prev_close
    daily_change_pct = (daily_change / prev_close) * 100

    period_start = data['Close'].iloc[0]
    period_return = ((current_price - period_start) / period_start) * 100

    returns = data['Returns'].dropna()
    volatility = returns.std() * np.sqrt(252) * 100
    annualized_return = returns.mean() * 252 * 100

    avg_volume = data['Volume'].mean()
    latest_volume = data['Volume'].iloc[-1]

    stats_text = f"""## S&P 500 Statistics

**Current Price:**
${current_price:.2f}

**Daily Change:**
${daily_change:.2f} ({daily_change_pct:+.2f}%)

**Period Return:**
{period_return:+.2f}%

**Annualized Return:**
{annualized_return:+.2f}%

**Annualized Volatility:**
{volatility:.1f}%

**Volume:**
{latest_volume:,.0f}

**Avg Volume:**
{avg_volume:,.0f}

**Data Range:**
{data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}
"""

    return pn.pane.Markdown(stats_text)


def create_dashboard_app():
    """Create the Panel dashboard application"""
    # Fetch data for S&P 500
    data = fetch_stock_data("^GSPC", "2y")

    # Create components
    chart = pn.pane.Plotly(
        create_stock_chart(data, "^GSPC"),
        sizing_mode='stretch_width',
        height=500
    )
    stats = create_stats_panel(data)

    # Create layout using MaterialTemplate
    dashboard = pn.template.MaterialTemplate(
        title="Stonkulator MVP 1 - S&P 500 Dashboard",
        sidebar=[
            pn.pane.Markdown("## Stonkulator MVP 1"),
            pn.pane.Markdown("**Live S&P 500 Analysis**"),
            pn.Spacer(height=20),
            stats
        ],
        main=[chart],
        header_background='#2596be',
        theme=pn.template.DarkTheme
    )

    return dashboard


def serve_cloud_run():
    """Simple Cloud Run server setup for MVP 1"""
    print("🚀 Starting Stonkulator MVP 1 for Cloud Run...")

    # Test components first
    if not test_local():
        print("❌ Component tests failed!")
        exit(1)

    # Get port from environment (Cloud Run sets this)
    port = int(os.environ.get('PORT', 8080))

    # Create and serve dashboard
    dashboard = create_dashboard_app()

    print(f"🌐 Serving on port {port}")
    pn.serve(
        dashboard,
        port=port,
        host='0.0.0.0',
        show=False,
        autoreload=False,
        allow_websocket_origin=['*']
    )


def test_local():
    """Test function for local development"""
    print("🧪 Testing Stonkulator MVP 1 components...")

    # Test data fetch
    test_data = fetch_stock_data("^GSPC", "1y")
    if test_data is not None:
        print(f"✅ Data fetched: {len(test_data)} days")
        print(f"📊 Latest close: ${test_data['Close'].iloc[-1]:.2f}")
    else:
        print("❌ Data fetch failed")
        return False

    # Test chart creation
    test_chart = create_stock_chart(test_data, "^GSPC")
    if test_chart is not None:
        print("✅ Chart created")
    else:
        print("❌ Chart creation failed")
        return False

    print("🎉 MVP 1 Components Ready!")
    return True


def serve_locally(port=8080):
    """Serve dashboard locally for development/testing"""
    print("🚀 Starting Stonkulator MVP 1 locally...")

    if not test_local():
        print("❌ Component tests failed!")
        return

    dashboard = create_dashboard_app()
    print(f"🌐 Serving dashboard at: http://localhost:{port}")
    pn.serve(dashboard, port=port, show=True)


if __name__ == "__main__":
    # Check if running in Cloud Run
    if os.environ.get('PORT'):
        serve_cloud_run()
    else:
        serve_locally()