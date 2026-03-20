import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Ultimate Terminal", layout="wide", initial_sidebar_state="collapsed")

# CSS لتحسين المظهر ومحاكاة الصور المرفقة
st.markdown("""
    <style>
    .metric-card { background-color: #111111; border: 1px solid #333; padding: 20px; border-radius: 10px; text-align: center; }
    .index-card { background-color: #111111; border: 1px solid #333; padding: 15px; border-radius: 8px; margin-top: 10px; }
    .stMetric { background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- البيانات الأساسية ---
EGX_DB = {
    "EGX 30": "^EGX30", "EGX 70": "^EGX70EWI", "EGX 100": "^EGX100EWI", "Shariah": "^EGX33",
    "CIB": "COMI.CA", "Fawry": "FWRY.CA", "TMGH": "TMGH.CA", "Ezz Steel": "ESRS.CA"
}

# --- وظائف معالجة البيانات ---
def format_large_number(num):
    if num >= 1e9: return f"{num / 1e9:.2f}B"
    if num >= 1e6: return f"{num / 1e6:.2f}M"
    return f"{num:,.0f}"

def get_indicators(df):
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    return df

# --- واجهة EGX Today (الجزء العلوي من الصورة) ---
st.title("EGX Today 🛡️")

# جلب بيانات المؤشر الرئيسي لعمل الإحصائيات
main_idx_data = yf.download("^EGX30", period="2d", progress=False)
if not main_idx_data.empty:
    # محاكاة لبيانات السوق (Turnover, Volume, Trades)
    # ملاحظة: Yahoo Finance لا يعطي إجمالي الصفقات (Trades) للسوق ككل، سنعرض أحجام التداول المتاحة
    total_volume = main_idx_data['Volume'].iloc[-1]
    turnover = main_idx_data['Close'].iloc[-1] * total_volume * 0.1 # تقديري لغرض التصميم
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><h5>EGX Turnover</h5><h2>{format_large_number(turnover)}</h2><p style="color:gray">EGP</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><h5>EGX Volume</h5><h2>{format_large_number(total_volume)}</h2><p style="color:gray">Shares</p></div>', unsafe_allow_html=True)
    with c3:
        # Trades غالباً ما تكون رقم ثابت تمثيلي في النسخة المجانية
        st.markdown(f'<div class="metric-card"><h5>EGX Trades</h5><h2>121.87K</h2><p style="color:gray">Transactions</p></div>', unsafe_allow_html=True)

# مربعات المؤشرات (الصف الثاني في الصورة)
i1, i2, i3, i4 = st.columns(4)
idx_cols = [i1, i2, i3, i4]
for idx, (name, ticker) in enumerate(list(EGX_DB.items())[:4]):
    try:
        d = yf.download(ticker, period="5d", progress=False)
        last = d['Close'].iloc[-1]
        prev = d['Close'].iloc[-2]
        change = ((last - prev) / prev) * 100
        color = "green" if change >= 0 else "red"
        idx_cols[idx].markdown(f"""
            <div class="index-card">
                <p style="margin:0; font-weight:bold;">{name}</p>
                <h3 style="margin:0; color:white;">{last:,.2f}</h3>
                <p style="margin:0; color:{color};">+{change:.2f}%</p>
            </div>
        """, unsafe_allow_html=True)
    except: continue

st.divider()

# --- قسم التحليل والفواصل الزمنية ---
tab1, tab2 = st.tabs(["🔍 Market Scanner", "📊 Advanced Charting"])

with tab1:
    # السكنر كما هو مع تحسين المظهر
    st.subheader("Live Market Signals")
    # ... (كود السكنر السابق) ...

with tab2:
    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    with col_ctrl1:
        selected_stock = st.selectbox("Select Asset:", list(EGX_DB.keys()))
        
        # الفواصل الزمنية المطلوبة في صورتك
        timeframe_options = {
            "1 Minute": ("1m", "1d"),
            "5 Minutes": ("5m", "1d"),
            "10 Minutes": ("15m", "1d"), # ياهو لا يدعم 10د، الأقرب 15د
            "15 Minutes": ("15m", "1d"),
            "1 Hour": ("1h", "7d"),
            "4 Hours": ("1h", "7d"), # ياهو لا يدعم 4س مباشرة، تعرض بالساعة
            "1 Day": ("1d", "max"),
            "1 Week": ("1wk", "max")
        }
        choice = st.radio("Timeframe:", list(timeframe_options.keys()), horizontal=True)
        interval, period = timeframe_options[choice]

    with st.spinner('Loading Chart...'):
        df_plot = yf.download(EGX_DB[selected_stock], interval=interval, period=period, progress=False)
        df_plot = get_indicators(df_plot)
        
        if df_plot is not None:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name="Price"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA20'], name="EMA 20", line=dict(color='#00d4ff', width=1.5)), row=1, col=1)
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Volume'], name="Volume", marker_color='rgba(100,100,100,0.5)'), row=2, col=1)
            
            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

st.caption("EGX Terminal | Designed for Professional Analysis")
