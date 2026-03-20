import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# 1. إعدادات الصفحة بتصميم عصري
st.set_page_config(page_title="EGX Pro Terminal", layout="wide", initial_sidebar_state="expanded")

# تطبيق CSS مخصص لتحسين مظهر الجداول والخطوط
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stTable { border-radius: 10px; overflow: hidden; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة البيانات ---
EGX_DB = {
    "EGX 30": "^EGX30", "EGX 70 EWI": "^EGX70EWI", "EGX 100 EWI": "^EGX100EWI", "EGX 33 Shariah": "^EGX33",
    "CIB": "COMI.CA", "Fawry": "FWRY.CA", "TMG Holding": "TMGH.CA", "Ezz Steel": "ESRS.CA",
    "Abu Qir": "ABUK.CA", "Sidi Kerir": "SKPC.CA", "Palm Hills": "PHDC.CA", "Heliopolis": "HELI.CA"
}

# --- إدارة الحالة ---
if 'my_watchlist' not in st.session_state:
    st.session_state.my_watchlist = ["^EGX30", "^EGX70EWI", "COMI.CA", "TMGH.CA"]

# --- الدوال التقنية المحسنة ---
def get_indicators(df):
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # EMA for smoother trends
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Volume MA
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
    return df

# --- Sidebar (Control Panel) ---
with st.sidebar:
    st.title("🛡️ EGX Terminal")
    st.markdown("---")
    selected_items = st.multiselect(
        "إضافة/حذف من المراقبة:",
        options=list(EGX_DB.keys()),
        default=[k for k, v in EGX_DB.items() if v in st.session_state.my_watchlist]
    )
    if st.button("تحديث لوحة البيانات", use_container_width=True):
        st.session_state.my_watchlist = [EGX_DB[x] for x in selected_items]
        st.rerun()
    st.info(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")

# --- الرئيسية ---
st.title("📈 EGX Market Intelligence")

# 1. قسم كروت السوق (Market Metrics)
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
indices = ["^EGX30", "^EGX70EWI", "COMI.CA", "^EGX100EWI"]
cols = [m_col1, m_col2, m_col3, m_col4]

for idx, ticker in enumerate(indices):
    try:
        d = yf.download(ticker, period="2d", progress=False)
        last_p = d['Close'].iloc[-1]
        prev_p = d['Close'].iloc[-2]
        change = ((last_p - prev_p) / prev_p) * 100
        cols[idx].metric(ticker.replace("^", ""), f"{last_p:,.2f}", f"{change:+.2f}%")
    except: continue

st.markdown("---")

# 2. تنظيم المحتوى باستخدام Tabs
tab1, tab2 = st.tabs(["🔍 الرادار الشامل", "📊 التحليل العميق"])

with tab1:
    st.subheader("Market Scanner (Daily Signals)")
    results = []
    for ticker in st.session_state.my_watchlist:
        try:
            data = yf.download(ticker, period="60d", progress=False)
            df = get_indicators(data)
            if df is not None:
                last = df.iloc[-1]
                price = last['Close']
                rsi = last['RSI']
                
                # منطق الحالة الاحترافي
                status = "Wait ⚪"
                color = "white"
                if rsi < 35: status, color = "Strong Buy 🟢", "#00ff00"
                elif rsi > 70: status, color = "Overbought 🔴", "#ff4b4b"
                elif last['EMA20'] > last['EMA50']: status, color = "Bullish 🚀", "#00d4ff"
                
                results.append({
                    "Ticker": ticker.replace(".CA", "").replace("^", ""),
                    "Price": f"{price:,.2f}",
                    "RSI": f"{rsi:.1f}",
                    "Trend": status,
                    "Target": f"{price*1.05:,.2f}",
                    "Stop": f"{price*0.97:,.2f}"
                })
        except: continue
    
    if results:
        df_res = pd.DataFrame(results)
        st.dataframe(df_res, use_container_width=True, hide_index=True)

with tab2:
    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        detail_stock = st.selectbox("اختر السهم للتحليل:", st.session_state.my_watchlist)
        period = st.selectbox("الفترة:", ["1mo", "3mo", "6mo", "1y", "2y"])
    
    with st.spinner('Building Chart...'):
        df_plot = yf.download(detail_stock, period=period, progress=False)
        df_plot = get_indicators(df_plot)
        
        if df_plot is not None:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Candlestick
            fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], 
                                         low=df_plot['Low'], close=df_plot['Close'], name="Price"), row=1, col=1)
            # EMA Lines
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA20'], name="EMA20", line=dict(color='#00d4ff', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA50'], name="EMA50", line=dict(color='#ffaa00', width=1)), row=1, col=1)
            
            # Volume Bars
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Volume'], name="Volume", marker_color='rgba(100,100,100,0.3)'), row=2, col=1)
            
            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False,
                             margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("EGX Terminal v3.0 | Real-time Data by Yahoo Finance")
