import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Pro Radar", layout="wide")

def add_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['Upper_Band'] = df['SMA20'] + (df['Close'].rolling(window=20).std() * 2)
    df['Lower_Band'] = df['SMA20'] - (df['Close'].rolling(window=20).std() * 2)
    return df

def get_recommendation(df):
    if len(df) < 2: return {"action": "N/A", "tp1": "-", "tp2": "-", "sl": "-", "reason": "No data"}
    last = df.iloc[-1]
    price, rsi = float(last['Close']), float(last['RSI'])
    rec = {"action": "HOLD ⚪", "tp1": "-", "tp2": "-", "sl": "-", "reason": "Neutral zone."}
    if rsi <= 35 or price <= last['Lower_Band']:
        rec = {"action": "BUY 🟢", "sl": round(price * 0.97, 2), "tp1": round(last['SMA20'], 2), "tp2": round(last['Upper_Band'], 2), "reason": "Oversold/Support hit."}
    elif rsi >= 70 or price >= last['Upper_Band']:
        rec = {"action": "SELL 🔴", "tp1": "-", "tp2": "-", "sl": "-", "reason": "Overbought/Resistance hit."}
    return rec

# --- واجهة التطبيق ---
st.title("🏹 EGX Smart Radar Pro")

# --- قائمة التحكم الجانبية الجديدة ---
st.sidebar.header("⚙️ إعدادات التحليل")

egx_list = ["COMI.CA", "FWRY.CA", "TMGH.CA", "EKHO.CA", "ABUK.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "ORAS.CA", "PHDC.CA"]
selected_stock = st.sidebar.selectbox("اختر السهم:", egx_list)

# إعداد الفواصل الزمنية (Intervals)
interval_options = {
    "1 Minute": "1m",
    "5 Minutes": "5m",
    "30 Minutes": "30m",
    "1 Hour": "1h",
    "1 Day": "1d",
    "1 Week": "1wk"
}
selected_label = st.sidebar.selectbox("الفصل الزمني (Timeframe):", list(interval_options.keys()), index=4)
interval = interval_options[selected_label]

# تحديد الفترة الإجمالية تلقائياً بناءً على الفصل الزمني (قيود yfinance)
if interval in ['1m', '5m', '30m']:
    period = "7d"  # البيانات اللحظية محدودة بـ 7 أيام
elif interval == '1h':
    period = "1mo"
else:
    period = "1y"

# سحب البيانات
with st.spinner(f'جاري تحميل بيانات {selected_label}...'):
    df = yf.download(selected_stock, period=period, interval=interval, progress=False)

if not df.empty:
    df = add_indicators(df)
    rec = get_recommendation(df)
    
    # عرض المؤشرات السريعة
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("التوصية", rec["action"])
    c2.metric("هدف 1", rec["tp1"])
    c3.metric("هدف 2", rec["tp2"])
    c4.metric("وقف خسارة", rec["sl"])
    
    st.info(f"💡 **تحليل الفاصل الزمني ({selected_label}):** {rec['reason']}")

    # الشارت
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ لا توجد بيانات متاحة لهذا الفاصل الزمني حالياً (تأكد من وقت الجلسة).")
