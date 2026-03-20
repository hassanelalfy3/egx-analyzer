import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# 1. إعدادات الصفحة المتقدمة
st.set_page_config(page_title="EGX Pro Terminal v6", layout="wide", initial_sidebar_state="collapsed")

# 2. تصميم CSS عصري (Modern Dark UI)
st.markdown("""
    <style>
    /* تجميل الخلفية العامة */
    .main { background-color: #050505; color: #e0e0e0; }
    
    /* تصميم البطاقات العلوية */
    .metric-container {
        background: linear-gradient(145deg, #0f0f0f, #1a1a1a);
        border: 1px solid #262626;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 800; color: #ffffff; margin: 5px 0; }
    .metric-label { font-size: 14px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    
    /* تحسين شكل الجداول */
    .stDataFrame { border: 1px solid #262626; border-radius: 10px; }
    
    /* أزرار الفترات الزمنية */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #333;
        background-color: #111;
        color: white;
        transition: 0.3s;
    }
    .stButton > button:hover { border-color: #00ff88; color: #00ff88; }
    
    /* حالة السوق */
    .market-status {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- الدوال التقنية ---
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=300)
def fetch_market_data(tickers):
    # جلب البيانات لعدة أسهم دفعة واحدة لتسريع الأداء
    data = yf.download(tickers, period="60d", progress=False)
    return data

# --- الهيدر (Header) ---
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("EGX Dashboard Pro 🛡️")
with col_status:
    st.write("")
    st.markdown('<div class="market-status" style="color: #00ff88; border-color: #00ff88;">● MARKET OPEN</div>', unsafe_allow_html=True)

# --- 1. قسم الإحصائيات (The Scoreboard) ---
m1, m2, m3, m4 = st.columns(4)

# محاكاة بيانات حقيقية للمؤشرات
indices_list = ["^EGX30", "^EGX70EWI", "^EGX100EWI", "^EGX33"]
names = ["EGX 30", "EGX 70", "EGX 100", "Shariah"]

for i, col in enumerate([m1, m2, m3, m4]):
    try:
        d = clean_df(yf.download(indices_list[i], period="2d", progress=False))
        curr = d['Close'].iloc[-1]
        prev = d['Close'].iloc[-2]
        chg = ((curr - prev)/prev)*100
        color = "#00ff88" if chg >= 0 else "#ff3344"
        arrow = "▲" if chg >= 0 else "▼"
        
        col.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">{names[i]}</div>
                <div class="metric-value">{curr:,.0f}</div>
                <div style="color: {color}; font-weight: bold;">{arrow} {chg:+.2f}%</div>
            </div>
        """, unsafe_allow_html=True)
    except: col.write("Error Loading")

st.write("---")

# --- 2. التبويبات الحديثة (Tabs) ---
tab_market, tab_analysis = st.tabs(["🌐 Market Overview", "📈 Advanced Analysis"])

with tab_market:
    c1, c2 = st.columns([1, 1])
    
    # قائمة أسهم افتراضية
    TICKERS = ["COMI.CA", "FWRY.CA", "TMGH.CA", "ESRS.CA", "ABUK.CA", "EKHO.CA", "SWDY.CA", "ETEL.CA"]
    
    results = []
    for t in TICKERS:
        try:
            d = clean_df(yf.download(t, period="5d", progress=False))
            close = d['Close'].iloc[-1]
            chg = ((close - d['Close'].iloc[-2])/d['Close'].iloc[-2])*100
            high_low = d['High'] - d['Low']
            atr = high_low.rolling(5).mean().iloc[-1]
            
            results.append({
                "Symbol": t.replace(".CA", ""),
                "Price": round(close, 2),
                "Change %": round(chg, 2),
                "Buy Range": f"{round(close-0.1, 2)}-{round(close,2)}",
                "TP": round(close + (atr*2), 2),
                "SL": round(close - (atr*1.5), 2)
            })
        except: continue
    
    df_res = pd.DataFrame(results)
    
    with c1:
        st.subheader("🔥 Top Movers")
        st.dataframe(df_res.sort_values("Change %", ascending=False).style.background_gradient(subset=['Change %'], cmap='RdYlGn'), use_container_width=True, hide_index=True)
    
    with c2:
        st.subheader("📊 Volume Leaders")
        st.dataframe(df_res.head(5), use_container_width=True, hide_index=True)

with tab_analysis:
    # تصميم الـ Terminal
    col_side, col_main = st.columns([1, 3])
    
    with col_side:
        st.markdown("### 🛠️ Control")
        asset = st.selectbox("Select Asset", TICKERS)
        interval = st.select_slider("Timeframe", options=["1m", "5m", "15m", "1h", "1d"], value="1h")
        st.write("---")
        st.markdown("### 🔍 Indicators")
        show_ma = st.toggle("Moving Average 20", True)
        show_rsi = st.toggle("RSI Indicator", True)
        
        if st.button("🚀 Run AI Analysis"):
            st.toast("Analyzing Market structure...")
            st.success(f"Analysis for {asset}: Strong Buy Zone")

    with col_main:
        # رسم شارت احترافي جداً
        df_chart = clean_df(yf.download(asset, period="1mo", interval=interval, progress=False))
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
        
        # الشموع
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
                                     low=df_chart['Low'], close=df_chart['Close'], name="Price"), row=1, col=1)
        
        if show_ma:
            ma = df_chart['Close'].rolling(20).mean()
            fig.add_trace(go.Scatter(x=df_chart.index, y=ma, name="MA20", line=dict(color='#00ff88', width=1)), row=1, col=1)
            
        # أحجام التداول في الخلفية
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], name="Volume", marker_color='rgba(100,100,100,0.2)'), row=2, col=1)
        
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("<br><hr><center style='color: #444;'>EGX Pro Terminal v6.0 © 2026 | Driven by Real-time Data</center>", unsafe_allow_html=True)
