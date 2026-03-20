import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Page Configuration
st.set_page_config(
    page_title="EGX Smart Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Technical Functions ---
def add_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['StdDev'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA20'] + (df['StdDev'] * 2)
    df['Lower_Band'] = df['SMA20'] - (df['StdDev'] * 2)
    return df

def get_recommendation(df):
    last = df.iloc[-1]
    price = float(last['Close'])
    rsi = float(last['RSI'])
    rec = {"action": "HOLD ⚪", "tp1": "-", "tp2": "-", "sl": "-", "reason": "Price is in a neutral zone."}
    if rsi <= 35 or price <= last['Lower_Band']:
        rec = {"action": "BUY 🟢", "sl": round(price * 0.95, 2), "tp1": round(last['SMA20'], 2), "tp2": round(last['Upper_Band'], 2), "reason": "Oversold or touching support."}
    elif rsi >= 70 or price >= last['Upper_Band']:
        rec = {"action": "SELL 🔴", "tp1": "-", "tp2": "-", "sl": "-", "reason": "Overbought or touching resistance."}
    return rec

# --- App Interface ---
st.title("🏹 EGX Smart Radar")
egx_list = ["COMI.CA", "FWRY.CA", "TMGH.CA", "EKHO.CA", "ABUK.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "ORAS.CA", "PHDC.CA"]
selected_stock = st.sidebar.selectbox("Select Stock:", egx_list)

with st.spinner('Fetching data...'):
    df = yf.download(selected_stock, period="1y", interval="1d", progress=False)

if not df.empty:
    df = add_indicators(df)
    rec = get_recommendation(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Action", rec["action"])
    c2.metric("Target 1", rec["tp1"])
    c3.metric("Target 2", rec["tp2"])
    c4.metric("Stop Loss", rec["sl"])
    st.info(f"💡 {rec['reason']}")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
