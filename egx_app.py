import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Live Radar Pro", layout="wide", page_icon="📈")

# --- وظيفة جلب قائمة الأسهم أونلاين بتجاوز الحظر ---
@st.cache_data(ttl=86400)
def fetch_egx_symbols():
    try:
        url = "https://en.wikipedia.org/wiki/EGX_30_Index"
        # انتحال شخصية متصفح حقيقي لتجنب 403 Forbidden
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        # قراءة الجداول باستخدام محرك lxml
        tables = pd.read_html(response.text, flavor='lxml')
        df_wiki = tables[1] 
        
        symbols_dict = {}
        for _, row in df_wiki.iterrows():
            ticker = str(row['Ticker symbol']).strip()
            if ".CA" not in ticker: ticker += ".CA"
            name = str(row['Company']).strip()
            symbols_dict[f"{name} ({ticker})"] = ticker
            
        return symbols_dict
    except Exception as e:
        # قائمة للطوارئ في حال فشل الموقع تماماً
        return {
            "CIB (COMI.CA)": "COMI.CA",
            "Fawry (FWRY.CA)": "FWRY.CA",
            "TMG Group (TMGH.CA)": "TMGH.CA",
            "Heliopolis (HELI.CA)": "HELI.CA"
        }

# --- الدوال الفنية للتحليل ---
def get_indicators(df):
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # Moving Averages
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # Bollinger Bands for Support/Resistance
    std = df['Close'].rolling(window=20).std()
    df['Lower_Band'] = df['SMA20'] - (std * 2)
    return df

# --- القائمة الجانبية وإدارة البيانات ---
st.sidebar.header("📡 مركز التحكم")
ALL_STOCKS = fetch_egx_symbols()

if 'my_watchlist' not in st.session_state:
    st.session_state.my_watchlist = list(ALL_STOCKS.values())[:5] # أول 5 أسهم كبداية

# الاختيار المتعدد من القائمة المجلوبة أونلاين
selected_names = st.sidebar.multiselect(
    "اختر الأسهم للمراقبة:",
    options=list(ALL_STOCKS.keys()),
    default=[k for k, v in ALL_STOCKS.items() if v in st.session_state.my_watchlist]
)

if st.sidebar.button("💾 حفظ وتحديث الرادار"):
    st.session_state.my_watchlist = [ALL_STOCKS[x] for x in selected_names]
    st.rerun()

# --- الواجهة الرئيسية ---
st.title("🏹 رادار البورصة المصرية - Smart Scanner")

# 1. قسم الماسح الضوئي (Scanner)
with st.expander("🔍 فحص وتحليل الإشارات الحالية", expanded=True):
    if st.button("🚀 تشغيل فحص السوق الآن"):
        results = []
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(st.session_state.my_watchlist):
            try:
                data = yf.download(ticker, period="60d", interval="1d", progress=False)
                df = get_indicators(data)
                if df is not None:
                    last = df.iloc[-1]
                    price = round(float(last['Close']), 2)
                    rsi = round(float(last['RSI']), 2)
                    
                    # منطق الإشارة
                    status = "انتظار ⚪"
                    buy_range, tp, sl = "-", "-", "-"
                    
                    if rsi < 35:
                        status = "شراء (تجميع) 🟢"
                        buy_range = f"{round(price * 0.99, 2)} - {price}"
                        tp = f"{round(price * 1.05, 2)} / {round(price * 1.10, 2)}"
                        sl = round(min(price * 0.97, last['Lower_Band']), 2)
                    elif rsi > 70:
                        status = "بيع (تخفيف) 🔴"
                    
                    results.append({
                        "السهم": ticker.replace(".CA", ""),
                        "السعر": price,
                        "RSI": rsi,
                        "الحالة": status,
                        "نطاق الشراء": buy_range,
                        "الأهداف": tp,
                        "الوقف": sl
                    })
            except: continue
            progress_bar.progress((i + 1) / len(st.session_state.my_watchlist))
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.warning("الرجاء اختيار أسهم من القائمة الجانبية.")

# 2. الشارت التفصيلي (للسهم المحدد)
if st.session_state.my_watchlist:
    st.divider()
    selected_stock = st.selectbox("عرض الرسم البياني المفصل:", st.session_state.my_watchlist)
    
    with st.spinner('جاري جلب بيانات الشارت...'):
        df_plot = yf.download(selected_stock, period="1y", interval="1d", progress=False)
        df_plot = get_indicators(df_plot)

    if df_plot is not None:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        # الشموع
        fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], 
                                     low=df_plot['Low'], close=df_plot['Close'], name="Price"), row=1, col=1)
        # المتوسطات
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['SMA20'], name="SMA20", line=dict(color='yellow')), row=1, col=1)
        # RSI
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
        
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

st.caption("ملاحظة: البيانات يتم جلبها تلقائياً من Yahoo Finance وموسوعة الـ EGX30.")
