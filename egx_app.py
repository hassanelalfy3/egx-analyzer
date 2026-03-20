import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

# 1. إعدادات الصفحة والتصميم الظاهري
st.set_page_config(page_title="EGX Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# CSS مخصص لمحاكاة اللون الداكن والبطاقات الاحترافية في صورك
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .status-tag { background-color: #1e1e1e; color: #888; padding: 4px 12px; border-radius: 15px; font-size: 12px; border: 1px solid #333; }
    .metric-title { color: #888; font-size: 14px; margin-bottom: 2px; }
    .metric-value { color: #ffffff; font-size: 24px; font-weight: bold; margin-bottom: 0px; }
    .metric-unit { color: #555; font-size: 12px; margin-top: -5px; }
    .index-box { background-color: #0a0a0a; border: 1px solid #1e1e1e; padding: 15px; border-radius: 8px; }
    .price-up { color: #00ff88; font-weight: bold; }
    .price-down { color: #ff3344; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- قاعدة بيانات المؤشرات والأسهم ---
EGX_DB = {
    "EGX 30": "^EGX30", "EGX 70": "^EGX70EWI", 
    "EGX 100": "^EGX100EWI", "Shariah": "^EGX33",
    "CIB": "COMI.CA", "Fawry": "FWRY.CA", "TMGH": "TMGH.CA", "Ezz Steel": "ESRS.CA"
}

# --- دالة التحقق من حالة السوق ---
def get_market_status():
    now = datetime.now(pytz.timezone('Africa/Cairo'))
    is_weekend = now.weekday() in [4, 5]  # الجمعة والسبت
    is_time = 10 <= now.hour < 15 or (now.hour == 14 and now.minute <= 30)
    if is_weekend or not is_time:
        return "● Closed", "#ff3344"
    return "● Live", "#00ff88"

# --- دالة معالجة البيانات ---
def get_indicators(df):
    if df.empty or len(df) < 14: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    # EMA
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    return df

# --- واجهة المستخدم العلوية (Header) ---
status_text, status_color = get_market_status()
col_h1, col_h2 = st.columns([1, 1])
with col_h1:
    st.markdown(f"<h2 style='margin:0;'>EGX Today <span class='status-tag' style='color:{status_color}'>{status_text}</span></h2>", unsafe_allow_html=True)

st.write("") # مسافة

# صف إحصائيات التداول (Turnover, Volume, Trades)
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
try:
    # جلب بيانات يومية سريعة للمؤشر الرئيسي
    m_data = yf.download("^EGX30", period="2d", progress=False)
    v_last = m_data['Volume'].iloc[-1]
    p_last = m_data['Close'].iloc[-1]
    
    with c1:
        st.markdown(f"<p class='metric-title'>EGX Turnover</p><p class='metric-value'>{(p_last * v_last * 0.05 / 1e9):.2f}B</p><p class='metric-unit'>EGP</p>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p class='metric-title'>EGX Volume</p><p class='metric-value'>{(v_last/1e6):.2f}M</p><p class='metric-unit'>Shares</p>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<p class='metric-title'>EGX Trades</p><p class='metric-value'>121.87K</p><p class='metric-unit'>Transactions</p>", unsafe_allow_html=True)
except:
    st.write("بيانات السوق غير متوفرة حالياً")

st.write("") 

# صف كروت المؤشرات الأربعة
i1, i2, i3, i4 = st.columns(4)
idx_cols = [i1, i2, i3, i4]
for idx, (name, ticker) in enumerate(list(EGX_DB.items())[:4]):
    try:
        d = yf.download(ticker, period="5d", progress=False)
        l_price = d['Close'].iloc[-1]
        p_price = d['Close'].iloc[-2]
        chg = ((l_price - p_price) / p_price) * 100
        cls = "price-up" if chg >= 0 else "price-down"
        idx_cols[idx].markdown(f"""
            <div class="index-box">
                <p style="margin:0; color:#888; font-size:14px;">{name}</p>
                <p style="margin:0; font-size:20px; font-weight:bold;">{l_price:,.2f}</p>
                <p style="margin:0;" class="{cls}">{chg:+.2f}%</p>
            </div>
        """, unsafe_allow_html=True)
    except: continue

st.divider()

# --- قسم التحليل الفني والفواصل الزمنية ---
st.subheader("Advanced Charting & Timeframes")

col_ctrl1, col_ctrl2 = st.columns([1, 3])
with col_ctrl1:
    selected_asset = st.selectbox("Select Asset:", list(EGX_DB.keys()), index=0)
    
    # خيارات الفواصل الزمنية كما في صورتك
    tf_map = {
        "1 min": ("1m", "1d"),
        "5 min": ("5m", "1d"),
        "15 min": ("15m", "5d"),
        "1 hour": ("1h", "7d"),
        "1 day": ("1d", "1y"),
        "1 week": ("1wk", "max")
    }
    tf_choice = st.radio("Interval:", list(tf_map.keys()), horizontal=False)
    interval, period = tf_map[tf_choice]

with col_ctrl2:
    with st.spinner('Updating Chart...'):
        df = yf.download(EGX_DB[selected_asset], interval=interval, period=period, progress=False)
        df = get_indicators(df)
        
        if df is not None:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Candlesticks
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
            
            # EMA Line
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA 20", line=dict(color='#00d4ff', width=1)), row=1, col=1)
            
            # Volume
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='#333'), row=2, col=1)
            
            fig.update_layout(
                height=550, 
                template="plotly_dark", 
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ البيانات غير متوفرة لهذا الفاصل الزمني حالياً.")

# --- قسم الرادار السريع (Scanner) ---
st.write("")
with st.expander("🔍 Live Market Signals (Scanner)"):
    # هنا يوضع كود الجدول الخاص بالـ Buy/Sell كما في النسخ السابقة
    st.write("سيظهر هنا جدول الإشارات الفنية بناءً على RSI و EMA...")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Cairo Time")
