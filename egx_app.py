import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Ultimate Radar", layout="wide", page_icon="📈")

# --- قاعدة بيانات شاملة تشمل المؤشرات والأسهم ---
EGX_DB = {
    # المؤشرات الرئيسية
    "مؤشر EGX 30": "^EGX30",
    "مؤشر EGX 70 EWI": "^EGX70EWI",
    "مؤشر EGX 100 EWI": "^EGX100EWI",
    "مؤشر EGX 33 Shariah": "^EGX33",
    
    # أهم الأسهم
    "البنك التجاري الدولي": "COMI.CA",
    "فوري": "FWRY.CA",
    "مجموعة طلعت مصطفى": "TMGH.CA",
    "إي فاينانس": "EFIH.CA",
    "حديد عز": "ESRS.CA",
    "أبو قير للأسمدة": "ABUK.CA",
    "مصر للألومنيوم": "EALU.CA",
    "سيدي كرير للبتروكيماويات": "SKPC.CA",
    "النساجون الشرقيون": "ORWE.CA",
    "بالم هيلز": "PHDC.CA",
    "مدينة مصر للإسكان": "MASR.CA",
    "إعمار مصر": "EMFD.CA",
    "مصر الجديدة للإسكان": "HELI.CA",
    "السويدي إلكتريك": "SWDY.CA",
    "المصرية للاتصالات": "ETEL.CA",
    "أموك": "AMOC.CA",
    "القلعة": "CCAP.CA",
    "بلتون المالية": "BTEL.CA",
    "إي في جي هيرمس": "HRHO.CA",
    "كيما": "EGCH.CA",
    "موبكو": "MFPC.CA",
    "جهينة": "JUFO.CA",
    "دومتي": "DMTY.CA",
    "أوراسكوم للتنمية": "ORHD.CA",
    "أوراسكوم للإنشاء": "ORAS.CA",
    "جي بي أوتو": "GBCO.CA",
    "ابن سينا فارما": "ISPH.CA",
    "مصرف أبوظبي الإسلامي": "ADIB.CA",
    "كريدي أجريكول": "CIEB.CA",
    "فيصل الإسلامي": "FAIT.CA"
}

# تجهيز الخيارات للعرض في القائمة
display_options = {f"{name} ({ticker})": ticker for name, ticker in EGX_DB.items()}

# --- إدارة الحالة (Watchlist) ---
if 'my_watchlist' not in st.session_state:
    # جعل المؤشرات هي الافتراضية عند الفتح
    st.session_state.my_watchlist = ["^EGX30", "^EGX70EWI", "COMI.CA", "FWRY.CA"]

# --- القائمة الجانبية ---
st.sidebar.header("📁 إدارة المحفظة والمؤشرات")

# اختيار متعدد (Multiselect)
selected_items = st.sidebar.multiselect(
    "اختر المؤشرات والأسهم لمراقبتها:",
    options=list(display_options.keys()),
    default=[k for k, v in display_options.items() if v in st.session_state.my_watchlist]
)

if st.sidebar.button("💾 حفظ وتحديث الرادار"):
    st.session_state.my_watchlist = [display_options[x] for x in selected_items]
    st.rerun()

# --- الدوال الفنية ---
def get_indicators(df):
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # المتوسطات والبولينجر
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    std = df['Close'].rolling(window=20).std()
    df['Lower_Band'] = df['SMA20'] - (std * 2)
    return df

# --- الواجهة الرئيسية ---
st.title("🏹 رادار البورصة المصرية الذكي")

# 1. الماسح الضوئي (Scanner)
with st.expander("🔍 فحص وتحليل الحالة الحالية", expanded=True):
    if st.button("🚀 تشغيل الفحص"):
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
                    
                    status = "انتظار ⚪"
                    buy_range, tp, sl = "-", "-", "-"
                    
                    # ملاحظة: استراتيجية الشراء والبيع للمؤشرات تكون للمتابعة العامة
                    if rsi < 35:
                        status = "تشبع بيعي 🟢"
                        buy_range = f"{round(price * 0.99, 2)} - {price}"
                        tp = f"{round(price * 1.05, 2)}"
                        sl = round(min(price * 0.97, last['Lower_Band']), 2)
                    elif rsi > 70:
                        status = "تشبع شرائي 🔴"
                    
                    results.append({
                        "الاسم/الرمز": ticker,
                        "السعر/النقطة": price,
                        "RSI": rsi,
                        "الحالة": status,
                        "الدعم/نطاق الشراء": buy_range,
                        "المقاومة/الهدف": tp
                    })
            except: continue
            progress_bar.progress((i + 1) / len(st.session_state.my_watchlist))
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.info("اختر عناصر من القائمة الجانبية لبدء الفحص.")

# 2. الشارت التفصيلي
if st.session_state.my_watchlist:
    st.divider()
    selected_view = st.selectbox("عرض الرسم البياني التفصيلي:", st.session_state.my_watchlist)
    
    with st.spinner('جاري التحميل...'):
        df_plot = yf.download(selected_view, period="1y", interval="1d", progress=False)
        df_plot = get_indicators(df_plot)

    if df_plot is not None:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        # الشموع
        fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], 
                                     low=df_plot['Low'], close=df_plot['Close'], name="السعر"), row=1, col=1)
        # RSI
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
        
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
