import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- SET PAGE CONFIG ---
st.set_page_config(page_title="EGX Stock Analysis", layout="wide")

# --- CUSTOM FUNCTIONS ---
def clean_df(df):
    """Cleans yfinance multi-index columns if they exist"""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=600)
def get_stock_stats(ticker, target_gain=0, investment=1):
    """Fetches stock data and returns a cleaned dictionary of stats"""
    try:
        # Download 60 days to ensure enough data for 14-day indicators
        data = yf.download(ticker, period="60d", progress=False)
        df = clean_df(data)
        
        # VALIDATION: Ensure we have enough data to calculate RSI/ATR
        if df.empty or len(df) < 15:
            return None
        
        # FIX: Explicitly cast to float to prevent "identically-labeled Series" error
        close_now = float(df['Close'].iloc[-1])
        close_prev = float(df['Close'].iloc[-2])
        volume_now = int(df['Volume'].iloc[-1])
        
        # Technical Indicators
        change = ((close_now - close_prev) / close_prev) * 100
        rsi_series = ta.rsi(df['Close'], length=14)
        atr_series = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        if rsi_series is None or rsi_series.empty:
            return None
            
        rsi = float(rsi_series.iloc[-1])
        atr = float(atr_series.iloc[-1])
        
        # Calculations
        required_move_pct = target_gain / investment if investment > 0 else 0
        goal_tp = close_now * (1 + required_move_pct)
        sl_level = close_now - (atr * 1.5)
        
        return {
            "Symbol": ticker.replace(".CA", ""),
            "Price": round(close_now, 2),
            "Change %": round(change, 2),
            "RSI": round(rsi, 1),
            "Buy Range": f"{round(close_now - (atr*0.3), 2)} - {round(close_now, 2)}",
            "Goal TP": round(goal_tp, 2),
            "Volatility SL": round(sl_level, 2),
            "Volume": volume_now
        }
    except Exception:
        return None

# --- UI LAYOUT ---
st.title("🇪🇬 EGX Market Dashboard")

# Sidebar - User Inputs
st.sidebar.header("Investment Settings")
target_gain = st.sidebar.number_input("Target Profit (EGP)", value=500)
investment_amt = st.sidebar.number_input("Investment Amount (EGP)", value=5000)

# Stock List (Egyptian Exchange Tickers)
egx_tickers = ["ABUK.CA", "EAST.CA", "FWRY.CA", "HRHO.CA", "COMI.CA", "TMGH.CA", "EKHO.CA"]

# --- PROCESSING ---
with st.spinner("Fetching market data..."):
    market_data = []
    for t in egx_tickers:
        stats = get_stock_stats(t, target_gain, investment_amt)
        if stats:
            market_data.append(stats)

if market_data:
    df_market = pd.DataFrame(market_data)
    
    # --- TOP GAINERS TABLE ---
    st.subheader("🚀 Top 5 Gainers (Today)")
    # We use .reset_index(drop=True) to ensure clean sorting labels
    top_gainers = df_market.sort_values("Change %", ascending=False).head(5).reset_index(drop=True)
    
    # Gradient styling requires 'matplotlib' in requirements.txt
    st.table(top_gainers.style.background_gradient(subset=['Change %'], cmap='RdYlGn'))

    # --- ALL STOCKS DATA ---
    st.subheader("📊 Market Overview")
    st.dataframe(df_market, use_container_width=True)
    
else:
    st.error("Could not fetch data. Check your internet connection or Yahoo Finance rate limits.")

# --- FOOTER ---
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
