import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# 1. إعدادات الصفحة والتنسيق
st.set_page_config(page_title="EGX Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .metric-card { background-color: #111; border: 1px solid #222; padding: 15px; border-radius: 10px; text-align: center; }
    .index-card { background-color: #0a0a0a; border: 1px solid #1e1e1e; padding: 12px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة البيانات ---
INDICES = {"EGX 30": "^EGX30", "EGX 70": "^EGX70EWI", "EGX 100": "^EGX100EWI", "EGX 33": "^EGX33"}
TICKERS = ["COMI.CA", "FWRY.CA", "TMGH.CA", "ESRS.CA", "ABUK.CA", "EKHO.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "PHDC.CA"]

# --- الدوال المساعدة ---
def clean_df(df):
    """تنظيف الجداول من العناوين المتعددة لتجنب ValueError"""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def calculate_indicators(df, indicators):
    df = clean_df(df)
    if df.empty: return df
    if "MA20" in indicators: df['MA20'] = df['Close'].rolling(window=20).mean()
    if "EMA50" in indicators: df['EMA50'] = df['Close'].ewm(span=50).mean()
    if "RSI" in indicators:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    return df

# --- 1. Scorecard Section ---
st.title("EGX Today 🛡️")
c1, c2, c3 = st.columns(3)

try:
    m_snap = yf.download("^EGX30", period="2d", progress=False)
    m_snap = clean_df(m_snap)
    v = float(m_snap['Volume'].iloc[-1])
    p = float(m_snap['Close'].iloc[-1])
    c1.markdown(f'<div class="metric-card"><p>Turnover</p><h3>{(p*v*0.05/1e9):.2f}B</h3><p>EGP</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><p>Volume</p><h3>{(v/1e6):.1f}M</h3><p>Shares</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><p>Trades</p><h3>121.8K</h3><p>Trans.</p></div>', unsafe_allow_html=True)
except: st.write("Market Stats Unavailable")

# صف المؤشرات
i_cols = st.columns(4)
for i, (name, sym) in enumerate(INDICES.items()):
    try:
        idx_d = clean_df(yf.download(sym, period="2d", progress=False))
        curr, prev = idx_d['Close'].iloc[-1], idx_d['Close'].iloc[-2]
        chg = ((curr - prev)/prev)*100
        clr = "#00ff88" if chg >= 0 else "#ff3344"
        i_cols[i].markdown(f'<div class="index-card"><p>{name}</p><h4>{curr:,.0f}</h4><p style="color:{clr}">{chg:+.2f}%</p></div>', unsafe_allow_html=True)
    except: continue

st.divider()

# --- 2. Market Tabs (المكان الذي حدث فيه الخطأ) ---
tab_gain, tab_loss, tab_active = st.tabs(["🔥 Top Gainers", "❄️ Top Losers", "📊 Most Active"])

@st.cache_data(ttl=600)
def get_market_summary():
    results = []
    for t in TICKERS:
        try:
            d = clean_df(yf.download(t, period="2d", progress=False))
            close_now = float(d['Close'].iloc[-1])
            close_prev = float(d['Close'].iloc[-2])
            change = ((close_now - close_prev) / close_prev) * 100
            results.append({
                "Ticker": t.replace(".CA", ""),
                "Price": round(close_now, 2),
                "Change %": round(float(change), 2),
                "Volume": int(d['Volume'].iloc[-1])
            })
        except: continue
    return pd.DataFrame(results)

df_market = get_market_summary()

if not df_market.empty:
    with tab_gain:
        st.dataframe(df_market.sort_values(by="Change %", ascending=False).head(5), use_container_width=True, hide_index=True)
    with tab_loss:
        st.dataframe(df_market.sort_values(by="Change %", ascending=True).head(5), use_container_width=True, hide_index=True)
    with tab_active:
        st.dataframe(df_market.sort_values(by="Volume", ascending=False).head(5), use_container_width=True, hide_index=True)

# --- 3. Charting & Analysis ---
st.divider()
cp1, cp2 = st.columns([1, 3])

with cp1:
    sel_t = st.selectbox("Select Asset:", TICKERS)
    sel_inds = st.multiselect("Indicators:", ["MA20", "EMA50", "RSI"], default=["MA20"])
    time_p = st.radio("Period:", ["1D", "5D", "1M", "1Y"], horizontal=True)
    p_map = {"1D":"1d", "5D":"5d", "1M":"1mo", "1Y":"1y"}
    i_map = {"1D":"1m", "5D":"5m", "1M":"1h", "1Y":"1d"}

    if st.button("🚀 Run Analysis", use_container_width=True):
        d_ana = calculate_indicators(yf.download(sel_t, period="60d", progress=False), ["RSI"])
        rsi_val = d_ana['RSI'].iloc[-1]
        p_val = d_ana['Close'].iloc[-1]
        if rsi_val < 35: st.success(f"BUY 🟢\nTarget: {p_val*1.07:.2f}")
        elif rsi_val > 70: st.error(f"SELL 🔴\nOverbought")
        else: st.info("HOLD ⚪\nNeutral RSI")

with cp2:
    df_p = calculate_indicators(yf.download(sel_t, period=p_map[time_p], interval=i_map[time_p], progress=False), sel_inds)
    if not df_p.empty:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_p.index, open=df_p['Open'], high=df_p['High'], low=df_p['Low'], close=df_p['Close'], name="Price"), row=1, col=1)
        if "MA20" in sel_inds: fig.add_trace(go.Scatter(x=df_p.index, y=df_p['MA20'], name="MA20", line=dict(color='yellow')), row=1, col=1)
        if "RSI" in sel_inds: fig.add_trace(go.Scatter(x=df_p.index, y=df_p['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
        else: fig.add_trace(go.Bar(x=df_p.index, y=df_p['Volume'], name="Volume"), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
