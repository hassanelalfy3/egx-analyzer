import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

# 1. إعدادات الصفحة والتنسيق (UI/UX)
st.set_page_config(page_title="EGX Pro Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .metric-card { background-color: #111; border: 1px solid #222; padding: 15px; border-radius: 10px; text-align: center; }
    .index-card { background-color: #0a0a0a; border: 1px solid #1e1e1e; padding: 12px; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #111; border-radius: 5px 5px 0 0; padding: 10px 20px; }
    .status-live { color: #00ff88; font-size: 12px; border: 1px solid #00ff88; padding: 2px 8px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة بيانات الأسهم والمؤشرات ---
INDICES = {
    "EGX 30": "^EGX30", "EGX 70": "^EGX70EWI", 
    "EGX 100": "^EGX100EWI", "EGX 33 Shariah": "^EGX33"
}

# قائمة الأسهم النشطة (يمكنك توسيعها أو جلبها أونلاين)
TICKERS = ["COMI.CA", "FWRY.CA", "TMGH.CA", "ESRS.CA", "ABUK.CA", "EKHO.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "PHDC.CA", "HELI.CA", "ORAS.CA", "BTEL.CA", "CCAP.CA"]

# --- الدوال المساعدة ---
@st.cache_data(ttl=3600)
def get_market_data(symbols):
    data = yf.download(symbols, period="2d", progress=False)
    return data

def calculate_indicators(df, indicators):
    if df.empty: return df
    if "MA20" in indicators: df['MA20'] = df['Close'].rolling(window=20).mean()
    if "EMA50" in indicators: df['EMA50'] = df['Close'].ewm(span=50).mean()
    if "RSI" in indicators:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    return df

# --- 1. Scorecard Section (Header) ---
st.title("EGX Today 🛡️")
col_s1, col_s2, col_s3 = st.columns(3)

# بيانات تمثيلية للسوق (بناءً على EGX30)
market_snap = yf.download("^EGX30", period="2d", progress=False)
if not market_snap.empty:
    v = market_snap['Volume'].iloc[-1]
    p = market_snap['Close'].iloc[-1]
    col_s1.markdown(f'<div class="metric-card"><p style="color:#888">EGX Turnover</p><h3>{(p*v*0.05/1e9):.2f}B</h3><p style="color:#555">EGP</p></div>', unsafe_allow_html=True)
    col_s2.markdown(f'<div class="metric-card"><p style="color:#888">EGX Volume</p><h3>{(v/1e6):.1f}M</h3><p style="color:#555">Shares</p></div>', unsafe_allow_html=True)
    col_s3.markdown(f'<div class="metric-card"><p style="color:#888">EGX Trades</p><h3>121.8K</h3><p style="color:#555">Transactions</p></div>', unsafe_allow_html=True)

# صف المؤشرات الأربعة
st.write("")
i_cols = st.columns(4)
for i, (name, sym) in enumerate(INDICES.items()):
    idx_data = yf.download(sym, period="2d", progress=False)
    if not idx_data.empty:
        curr = idx_data['Close'].iloc[-1]
        prev = idx_data['Close'].iloc[-2]
        chg = ((curr - prev)/prev)*100
        clr = "#00ff88" if chg >= 0 else "#ff3344"
        i_cols[i].markdown(f'<div class="index-card"><p style="color:#888; font-size:12px;">{name}</p><h4 style="margin:0;">{curr:,.2f}</h4><p style="color:{clr}; margin:0;">{chg:+.2f}%</p></div>', unsafe_allow_html=True)

st.divider()

# --- 2. Market Tabs (Gainers, Losers, etc.) ---
tab_gain, tab_loss, tab_active = st.tabs(["🔥 Top Gainers", "❄️ Top Losers", "📊 Most Active"])

@st.cache_data(ttl=600)
def get_market_summary():
    results = []
    for t in TICKERS:
        try:
            d = yf.download(t, period="2d", progress=False)
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2])/d['Close'].iloc[-2])*100
            results.append({"Ticker": t.replace(".CA",""), "Price": d['Close'].iloc[-1], "Change %": round(c, 2), "Volume": d['Volume'].iloc[-1]})
        except: continue
    return pd.DataFrame(results)

df_market = get_market_summary()

with tab_gain:
    st.table(df_market.sort_values("Change %", ascending=False).head(5))
with tab_loss:
    st.table(df_market.sort_values("Change %", ascending=True).head(5))
with tab_active:
    st.table(df_market.sort_values("Volume", ascending=False).head(5))

# --- 3. Analysis & Charting Section ---
st.divider()
st.subheader("🛠️ Technical Analysis Terminal")

c_p1, c_p2 = st.columns([1, 3])

with c_p1:
    selected_ticker = st.selectbox("Select Ticker:", TICKERS)
    selected_inds = st.multiselect("Indicators:", ["MA20", "EMA50", "RSI"], default=["MA20"])
    
    st.write("Time Period:")
    time_choice = st.radio("Period:", ["1D", "5D", "1M", "3M", "1Y"], horizontal=True, label_visibility="collapsed")
    period_map = {"1D":"1d", "5D":"5d", "1M":"1mo", "3M":"3mo", "1Y":"1y"}
    interval_map = {"1D":"1m", "5D":"5m", "1M":"1h", "3M":"1d", "1Y":"1d"}

    if st.button("🚀 Run Analysis", use_container_width=True):
        data_ana = yf.download(selected_ticker, period="60d", progress=False)
        data_ana = calculate_indicators(data_ana, ["RSI", "MA20"])
        last_rsi = data_ana['RSI'].iloc[-1]
        last_price = data_ana['Close'].iloc[-1]
        
        st.markdown("---")
        if last_rsi < 35:
            st.success("Signal: BUY 🟢")
            st.write(f"**Range:** {last_price*0.98:.2f} - {last_price:.2f}")
            st.write(f"**Target:** {last_price*1.07:.2f}")
            st.write(f"**Stop Loss:** {last_price*0.96:.2f}")
        elif last_rsi > 70:
            st.error("Signal: SELL 🔴")
            st.write("Target reached or Overbought")
        else:
            st.info("Signal: HOLD ⚪")
            st.write("Neutral Zone - Wait for trend")

with c_p2:
    with st.spinner('Loading Chart...'):
        df_plot = yf.download(selected_ticker, period=period_map[time_choice], interval=interval_map[time_choice], progress=False)
        df_plot = calculate_indicators(df_plot, selected_inds)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Candlestick
        fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name="Price"), row=1, col=1)
        
        # Overlay Indicators
        if "MA20" in selected_inds:
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA20'], name="MA20", line=dict(color='yellow', width=1)), row=1, col=1)
        if "EMA50" in selected_inds:
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA50'], name="EMA50", line=dict(color='cyan', width=1)), row=1, col=1)
        
        # Bottom Indicators (RSI or Volume)
        if "RSI" in selected_inds:
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
        else:
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Volume'], name="Volume", marker_color='gray'), row=2, col=1)

        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

st.caption("EGX Terminal v4.0 | Real-time analysis by AI & Yahoo Finance")
