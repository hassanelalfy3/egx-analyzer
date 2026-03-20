import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Live Scanner", layout="wide", page_icon="🌐")

# --- وظيفة جلب قائمة الأسهم أونلاين ---
@st.cache_data(ttl=86400) # يتم تحديث القائمة مرة كل 24 ساعة فقط لتسريع التطبيق
def fetch_egx_symbols():
    try:
        # محاولة جلب البيانات من Wikipedia (جدول شركات الـ EGX30 أو EGX100)
        url = "https://en.wikipedia.org/wiki/EGX_30_Index"
        tables = pd.read_html(url)
        df_wiki = tables[1] # الجدول الثاني عادة يحتوي على القائمة
        
        # تنظيف البيانات وتحويلها لقاموس (اسم الشركة: الرمز)
        # ملاحظة: سنقوم بإضافة .CA للرموز للتوافق مع Yahoo Finance
        symbols_dict = {}
        for _, row in df_wiki.iterrows():
            ticker = str(row['Ticker symbol']).strip()
            if ".CA" not in ticker: ticker += ".CA"
            name = str(row['Company']).strip()
            symbols_dict[f"{name} ({ticker})"] = ticker
            
        return symbols_dict
    except Exception as e:
        # قائمة احتياطية في حال فشل الاتصال بالإنترنت
        st.error(f"حدث خطأ في جلب القائمة أونلاين: {e}")
        return {"CIB (COMI.CA)": "COMI.CA", "Fawry (FWRY.CA)": "FWRY.CA", "TMG (TMGH.CA)": "TMGH.CA"}

# --- تحميل البيانات ---
st.sidebar.header("📡 جلب البيانات أونلاين")
with st.sidebar:
    with st.spinner("جاري تحديث قائمة الأسهم..."):
        ALL_STOCKS = fetch_egx_symbols()

# --- إدارة الحالة (Watchlist) ---
if 'my_watchlist' not in st.session_state:
    st.session_state.my_watchlist = ["COMI.CA", "FWRY.CA", "TMGH.CA"]

# --- القائمة الجانبية للتفاعل ---
selected_from_online = st.sidebar.multiselect(
    "اختر الأسهم من القائمة المحدثة:",
    options=list(ALL_STOCKS.keys()),
    default=[k for k, v in ALL_STOCKS.items() if v in st.session_state.my_watchlist]
)

if st.sidebar.button("💾 حفظ القائمة المختارة"):
    st.session_state.my_watchlist = [ALL_STOCKS[x] for x in selected_from_online]
    st.rerun()

# --- الدوال التقنية (كما هي) ---
def get_indicators(df):
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['Lower_Band'] = df['SMA20'] - (std * 2)
    return df

# --- الواجهة الرئيسية ---
st.title("🏹 رادار البورصة - التحديث التلقائي")

with st.expander("🔍 الماسح الضوئي (Scanner)", expanded=True):
    if st.button("🚀 ابدأ فحص الأسهم المختارة"):
        results = []
        progress_bar = st.progress(0)
        for i, ticker in enumerate(st.session_state.my_watchlist):
            try:
                data = yf.download(ticker, period="60d", interval="1d", progress=False)
                df = get_indicators(data)
                if df is not None:
                    last = df.iloc[-1]
                    price, rsi = round(float(last['Close']), 2), round(float(last['RSI']), 2)
                    status = "انتظار ⚪"
                    buy_range, tp, sl = "-", "-", "-"
                    if rsi < 35:
                        status = "شراء 🟢"
                        buy_range = f"{round(price * 0.99, 2)} - {price}"
                        tp = f"{round(price * 1.05, 2)} / {round(price * 1.10, 2)}"
                        sl = round(min(price * 0.97, last['Lower_Band']), 2)
                    elif rsi > 70: status = "بيع 🔴"
                    results.append({"السهم": ticker, "السعر": price, "الحالة": status, "نطاق الشراء": buy_range, "الأهداف": tp, "الوقف": sl})
            except: continue
            progress_bar.progress((i + 1) / len(st.session_state.my_watchlist))
        if results: st.table(pd.DataFrame(results))

# الشارت التفصيلي
if st.session_state.my_watchlist:
    st.divider()
    selected_stock = st.selectbox("عرض الشارت لـ:", st.session_state.my_watchlist)
    df_plot = yf.download(selected_stock, period="1y", interval="1d", progress=False)
    df_plot = get_indicators(df_plot)
    if df_plot is not None:
        fig = go.Figure(data=[go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'])])
        fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
