import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Portfolio Radar", layout="wide", page_icon="🎯")

# --- إدارة القائمة (State Management) ---
DEFAULT_STOCKS = ["COMI.CA", "FWRY.CA", "TMGH.CA", "EKHO.CA", "ABUK.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "ORAS.CA", "PHDC.CA"]

if 'custom_list' not in st.session_state:
    st.session_state.custom_list = DEFAULT_STOCKS.copy()

# --- الدالة الفنية للمؤشرات ---
def get_indicators(df):
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # Moving Averages & Bollinger
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['Lower_Band'] = df['SMA20'] - (std * 2)
    return df

# --- واجهة التطبيق والقائمة الجانبية ---
st.sidebar.header("🛠 إدارة قائمة الأسهم")

# أ. إضافة سهم جديد
new_ticker = st.sidebar.text_input("إضافة سهم جديد (مثال: HELI.CA)").upper()
if st.sidebar.button("➕ إضافة للقائمة"):
    if new_ticker:
        ticker_to_add = new_ticker if ".CA" in new_ticker else f"{new_ticker}.CA"
        if ticker_to_add not in st.session_state.custom_list:
            st.session_state.custom_list.append(ticker_to_add)
            st.success(f"تمت إضافة {ticker_to_add}")
            st.rerun()

st.sidebar.divider()

# ب. حذف س stocks
st.sidebar.subheader("🗑 حذف من القائمة")
to_delete = st.sidebar.selectbox("اختر السهم المراد حذفه:", ["-- اختر سهم --"] + st.session_state.custom_list)
if st.sidebar.button("❌ حذف السهم المحدد"):
    if to_delete != "-- اختر سهم --":
        st.session_state.custom_list.remove(to_delete)
        st.sidebar.warning(f"تم حذف {to_delete}")
        st.rerun()

if st.sidebar.button("🔄 إعادة ضبط المصنع"):
    st.session_state.custom_list = DEFAULT_STOCKS.copy()
    st.rerun()

# --- الجزء الرئيسي من التطبيق ---
st.title("🏹 رادار البورصة الذكي")

# 1. الرادار (Scanner)
with st.expander("🔍 فحص الأسهم الحالية", expanded=True):
    if st.button("🚀 ابدأ المسح الشامل"):
        results = []
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(st.session_state.custom_list):
            try:
                data = yf.download(ticker, period="60d", interval="1d", progress=False)
                df = get_indicators(data)
                if df is not None:
                    last = df.iloc[-1]
                    price = round(float(last['Close']), 2)
                    rsi = round(float(last['RSI']), 2)
                    
                    status = "انتظار ⚪"
                    buy_range, tp, sl = "-", "-", "-"
                    
                    if rsi < 35:
                        status = "شراء 🟢"
                        buy_range = f"{round(price * 0.99, 2)} - {price}"
                        tp = f"{round(price * 1.05, 2)} / {round(price * 1.10, 2)}"
                        sl = round(min(price * 0.97, last['Lower_Band']), 2)
                    elif rsi > 70:
                        status = "بيع 🔴"
                    
                    results.append({
                        "السهم": ticker.replace(".CA", ""),
                        "السعر": price,
                        "الحالة": status,
                        "نطاق الشراء": buy_range,
                        "الأهداف (TP)": tp,
                        "وقف الخسارة (SL)": sl
                    })
            except: continue
            progress_bar.progress((i + 1) / len(st.session_state.custom_list))
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.write("لا توجد بيانات حالياً.")

# 2. الشارت التفصيلي
st.divider()
selected_stock = st.selectbox("اختر سهم لعرض الشارت:", st.session_state.custom_list)
with st.spinner('جاري التحميل...'):
    df_plot = yf.download(selected_stock, period="1y", interval="1d", progress=False)
    df_plot = get_indicators(df_plot)

if df_plot is not None:
    fig = go.Figure(data=[go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'])])
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
