import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
import pandas_ta as ta  # Added for professional technical analysis

# 1. Page Config
st.set_page_config(page_title="EGX Pro Terminal 2026", layout="wide", initial_sidebar_state="expanded")

# 2. Modern Dark CSS
st.markdown("""
    <style>
    .main { background-color: #080808; }
    div[data-testid="stMetric"] { background-color: #111; border: 1px solid #222; padding: 15px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #888; font-weight: bold; }
    .status-box { padding: 20px; border-radius: 10px; border-left: 5px solid #00ff88; background: #111; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def clean_df(df):
    if df is None or df.empty: return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=600)
def get_stock_stats(ticker, target_gain=0, investment=1):
    try:
        data = yf.download(ticker, period="60d", progress=False)
        df = clean_df(data)
        if df.empty: return None
        
        close_now = float(df['Close'].iloc[-1])
        close_prev = float(df['Close'].iloc[-2])
        change = ((close_now - close_prev) / close_prev) * 100
        
        # Expert Technicals using pandas_ta
        atr = ta.atr(df['High'], df['Low'], df['Close'], length=14).iloc[-1]
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        # Goal-Based TP Calculation
        # If user wants $1000 gain on $5000 investment, they need a 20% move.
        required_move_pct = target_gain / investment if investment > 0 else 0
        goal_tp = close_now * (1 + required_move_pct)
        
        # Volatility-Adjusted SL (1.5x ATR below current)
        sl_level = close_now - (atr * 1.5)
        
        return {
            "Symbol": ticker.replace(".CA", ""),
            "Price": round(close_now, 2),
            "Change %": round(change, 2),
            "RSI": round(rsi, 1),
            "Buy Range": f"{round(close_now - (atr*0.3), 2)}-{round(close_now, 2)}",
            "Goal TP": round(goal_tp, 2),
            "Volatility SL": round(sl_level, 2),
            "Volume": int(df['Volume'].iloc[-1])
        }
    except: return None

# --- SIDEBAR: GOALS & INPUTS ---
st.sidebar.header("🎯 Trading Goals")
target_usd = st.sidebar.number_input("Target Profit (EGP)", value=5000)
capital_usd = st.sidebar.number_input("Investment Capital (EGP)", value=50000)
st.sidebar.divider()

TICKERS = ["COMI.CA", "FWRY.CA", "TMGH.CA", "ESRS.CA", "ABUK.CA", "EKHO.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "PHDC.CA", "HELI.CA"]

# --- HEADER ---
st.title("EGX Today 🛡️")
m1, m2, m3, m4, m5, m6 = st.columns(6)
indices = {"EGX 30": "^EGX30", "EGX 70": "^EGX70EWI", "EGX 100": "^EGX100EWI", "EGX 33": "^EGX33"}

cols = [m1, m2, m3, m4]
for i, (name, sym) in enumerate(indices.items()):
    try:
        d = clean_df(yf.download(sym, period="2d", progress=False))
        val = d['Close'].iloc[-1]
        chg = ((val - d['Close'].iloc[-2])/d['Close'].iloc[-2])*100
        cols[i].metric(name, f"{val:,.0f}", f"{chg:+.2f}%")
    except: continue

st.divider()

# --- TABS ---
tab_market, tab_terminal = st.tabs(["🌐 Market Overview", "📈 Trading Terminal"])

with tab_market:
    with st.spinner('Analysing Market...'):
        all_stats = [get_stock_stats(t, target_usd, capital_usd) for t in TICKERS]
        df_final = pd.DataFrame([s for s in all_stats if s is not None])

    if not df_final.empty:
        c_gain, c_loss = st.columns(2)
        with c_gain:
            st.subheader("🔥 Top Gainers")
            st.dataframe(df_final.sort_values("Change %", ascending=False).head(5), use_container_width=True, hide_index=True)
        with c_loss:
            st.subheader("❄️ Top Losers")
            st.dataframe(df_final.sort_values("Change %", ascending=True).head(5), use_container_width=True, hide_index=True)
        
        st.subheader("📊 All Market Signals (Goal-Adjusted)")
        st.dataframe(df_final.style.background_gradient(subset=['Change %', 'RSI'], cmap='RdYlGn'), use_container_width=True, hide_index=True)

with tab_terminal:
    c_side, c_chart = st.columns([1, 3])
    
    with c_side:
        asset = st.selectbox("Select Asset", TICKERS)
        tf = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "1d"], index=4)
        
        # Get Ticker Data for Insight
        ticker_obj = yf.Ticker(asset)
        stats = get_stock_stats(asset, target_usd, capital_usd)
        
        if stats:
            st.markdown(f"""
            <div class="status-box">
                <h4>Analysis for {asset}</h4>
                <p><b>Target TP:</b> {stats['Goal TP']} EGP</p>
                <p><b>Risk SL:</b> {stats['Volatility SL']} EGP</p>
                <p><b>RSI Status:</b> {stats['RSI']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("📰 Latest News")
        news = ticker_obj.news[:3]
        for n in news:
            st.caption(f"🔗 [{n['title']}]({n['link']})")

    with c_chart:
        period_map = {"1m":"1d", "5m":"1d", "15m":"5d", "1h":"1mo", "1d":"1y"}
        df_c = clean_df(yf.download(asset, period=period_map[tf], interval=tf, progress=False))
        
        if not df_c.empty:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
            
            # Candlestick
            fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="Price"), row=1, col=1)
            
            # Indicators
            ema20 = ta.ema(df_c['Close'], length=20)
            fig.add_trace(go.Scatter(x=df_c.index, y=ema20, name="EMA20", line=dict(color='#00ff88', width=1.5)), row=1, col=1)
            
            # Volume
            fig.add_trace(go.Bar(x=df_c.index, y=df_c['Volume'], name="Volume", marker_color='rgba(100,100,100,0.3)'), row=2, col=1)
            
            fig.update_layout(height=650, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

st.caption(f"EGX Terminal v8.0-Goal-Based | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
