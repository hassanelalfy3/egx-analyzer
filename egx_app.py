# working version
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS متقدم لتصميم Dark Modern
st.markdown("""
    <style>
    .main { background-color: #080808; }
    div[data-testid="stMetric"] { background-color: #111; border: 1px solid #222; padding: 15px; border-radius: 10px; }
    .metric-card { background: linear-gradient(145deg, #111, #1a1a1a); border: 1px solid #333; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] { color: #888; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stDataFrame { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- الدوال التقنية (مع معالجة الأخطاء) ---
def clean_df(df):
    if df is None or df.empty: return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=600)
def get_stock_stats(ticker):
    try:
        data = yf.download(ticker, period="60d", progress=False)
        df = clean_df(data)
        if df.empty: return None
        
        close_now = float(df['Close'].iloc[-1])
        close_prev = float(df['Close'].iloc[-2])
        change = ((close_now - close_prev) / close_prev) * 100
        
        # حساب ATR مبسط للأهداف
        high_low = df['High'] - df['Low']
        atr = high_low.rolling(14).mean().iloc[-1]
        
        return {
            "Symbol": ticker.replace(".CA", ""),
            "Price": round(close_now, 2),
            "Change %": round(change, 2),
            "Buy Range": f"{round(close_now - (atr*0.3), 2)}-{round(close_now, 2)}",
            "TP": round(close_now + (atr * 2), 2),
            "SL": round(close_now - (atr * 1.5), 2),
            "Volume": int(df['Volume'].iloc[-1])
        }
    except: return None

# --- الهيدر وإحصائيات السوق ---
st.title("EGX Today 🛡️")

m1, m2, m3, m4, m5, m6 = st.columns(6)
indices = {"EGX 30": "^EGX30", "EGX 70": "^EGX70EWI", "EGX 100": "^EGX100EWI", "EGX 33": "^EGX33"}

# عرض المؤشرات في الأعلى
cols = [m1, m2, m3, m4]
for i, (name, sym) in enumerate(indices.items()):
    try:
        d = clean_df(yf.download(sym, period="2d", progress=False))
        val = d['Close'].iloc[-1]
        chg = ((val - d['Close'].iloc[-2])/d['Close'].iloc[-2])*100
        cols[i].metric(name, f"{val:,.0f}", f"{chg:+.2f}%")
    except: continue

# إحصائيات السيولة (تقديرية بناءً على المؤشر)
try:
    idx_main = clean_df(yf.download("^EGX30", period="2d", progress=False))
    p, v = idx_main['Close'].iloc[-1], idx_main['Volume'].iloc[-1]
    m5.metric("Turnover", f"{(p*v*0.05/1e9):.1f}B", "EGP")
    m6.metric("Trades", "121K", "Trans.")
except: pass

st.divider()

# --- التبويبات والمحتوى ---
tab_market, tab_terminal = st.tabs(["🌐 Market Overview", "📈 Trading Terminal"])

with tab_market:
    TICKERS = ["COMI.CA", "FWRY.CA", "TMGH.CA", "ESRS.CA", "ABUK.CA", "EKHO.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "PHDC.CA", "HELI.CA"]
    
    with st.spinner('جاري تحليل الأسهم...'):
        all_stats = [get_stock_stats(t) for t in TICKERS]
        df_final = pd.DataFrame([s for s in all_stats if s is not None])

    if not df_final.empty:
        c_gain, c_loss = st.columns(2)
        with c_gain:
            st.subheader("🔥 Top Gainers")
            st.dataframe(df_final.sort_values("Change %", ascending=False).head(5), use_container_width=True, hide_index=True)
        with c_loss:
            st.subheader("❄️ Top Losers")
            st.dataframe(df_final.sort_values("Change %", ascending=True).head(5), use_container_width=True, hide_index=True)
        
        st.subheader("📊 All Market Signals")
        st.dataframe(df_final.style.background_gradient(subset=['Change %'], cmap='RdYlGn'), use_container_width=True, hide_index=True)

with tab_terminal:
    c_side, c_chart = st.columns([1, 3])
    
    with c_side:
        asset = st.selectbox("Select Asset", TICKERS)
        tf = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "1d"], index=3)
        inds = st.multiselect("Indicators", ["EMA20", "RSI", "Bollinger"], default=["EMA20"])
        
        if st.button("🚀 Run Analysis", use_container_width=True):
            # دالة التحليل البسيطة
            d_ana = clean_df(yf.download(asset, period="60d", progress=False))
            close = d_ana['Close'].iloc[-1]
            st.info(f"Analysis for {asset}\nPrice: {close:.2f}\nAction: Monitoring...")

    with c_chart:
        # رسم الشارت الاحترافي
        period_map = {"1m":"1d", "5m":"1d", "15m":"5d", "1h":"1mo", "1d":"1y"}
        df_c = clean_df(yf.download(asset, period=period_map[tf], interval=tf, progress=False))
        
        if not df_c.empty:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
            fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="Price"), row=1, col=1)
            
            if "EMA20" in inds:
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['Close'].ewm(span=20).mean(), name="EMA20", line=dict(color='#00ff88', width=1)), row=1, col=1)
            
            fig.add_trace(go.Bar(x=df_c.index, y=df_c['Volume'], name="Volume", marker_color='rgba(100,100,100,0.3)'), row=2, col=1)
            
            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

st.caption(f"Terminal v7.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
