import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة لتناسب الموبايل
st.set_page_config(
    page_title="EGX Pro Radar",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# قائمة الأسهم المختارة (يمكنك إضافة المزيد)
EGX_LIST = ["COMI.CA", "FWRY.CA", "TMGH.CA", "EKHO.CA", "ABUK.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "ORAS.CA", "PHDC.CA"]

# --- الدوال الفنية ---
def get_indicators(df):
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # حساب RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # المتوسطات المتحركة
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # بولينجر باندز للدعم والمقاومة
    std = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA20'] + (std * 2)
    df['Lower_Band'] = df['SMA20'] - (std * 2)
    
    return df

# --- وظيفة الرادار الشامل (Scanner) ---
def run_market_scanner():
    results = []
    for ticker in EGX_LIST:
        data = yf.download(ticker, period="60d", interval="1d", progress=False)
        df = get_indicators(data)
        
        if df is not None:
            last = df.iloc[-1]
            prev = df.iloc[-2]
            price = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 2)
            
            # منطق الإشارة وإدارة المخاطر
            status = "انتظار ⚪"
            buy_range = "-"
            tp = "-"
            sl = "-"
            
            # إشارة شراء (RSI منخفض أو تقاطع ذهبي)
            if rsi < 35 or (prev['SMA20'] < prev['SMA50'] and last['SMA20'] > last['SMA50']):
                status = "شراء 🟢"
                buy_range = f"{round(price * 0.99, 2)} - {price}"
                tp = f"{round(price * 1.05, 2)} / {round(price * 1.10, 2)}"
                sl = round(min(price * 0.97, last['Lower_Band']), 2)
            
            # إشارة بيع (RSI مرتفع أو كسر متوسطات)
            elif rsi > 70 or (prev['SMA20'] > prev['SMA50'] and last['SMA20'] < last['SMA50']):
                status = "بيع 🔴"
                tp = "جني أرباح الآن"
            
            results.append({
                "السهم": ticker.replace(".CA", ""),
                "السعر": price,
                "RSI": rsi,
                "الحالة": status,
                "نطاق الشراء": buy_range,
                "الأهداف (TP)": tp,
                "وقف الخسارة (SL)": sl
            })
    return pd.DataFrame(results)

# --- واجهة المستخدم ---
st.title("🏹 رادار البورصة المصرية الذكي")

# 1. الرادار (Scanner)
with st.expander("🔍 الماسح الضوئي للسوق (Scanner)", expanded=True):
    if st.button("تحديث فحص الأسهم"):
        scanner_df = run_market_scanner()
        
        def color_status(val):
            color = 'white'
            if 'شراء' in val: color = '#90ee90'
            elif 'بيع' in val: color = '#ffcccb'
            return f'background-color: {color}; color: black'

        st.table(scanner_df.style.applymap(color_status, subset=['الحالة']))
    else:
        st.info("اضغط على الزر أعلاه لفحص حالة الـ 10 أسهم الكبرى فوراً.")

st.divider()

# 2. التحكم الجانبي للتحليل المفصل
st.sidebar.header("⚙️ إعدادات التحليل التفصيلي")
selected_stock = st.sidebar.selectbox("اختر السهم:", EGX_LIST)

interval_map = {
    "1 Minute": "1m", "5 Minutes": "5m", "30 Minutes": "30m", 
    "1 Hour": "1h", "1 Day": "1d", "1 Week": "1wk"
}
selected_label = st.sidebar.selectbox("الفصل الزمني:", list(interval_map.keys()), index=4)
interval = interval_map[selected_label]

# ضبط الفترة بناءً على الفاصل
period = "7d" if "Minute" in selected_label else "1y"

# 3. عرض الشارت التفصيلي
with st.spinner('جاري تحميل الشارت...'):
    df_detail = yf.download(selected_stock, period=period, interval=interval, progress=False)
    df_detail = get_indicators(df_detail)

if df_detail is not None:
    st.subheader(f"📊 تحليل سهم {selected_stock} على فاصل {selected_label}")
    
    # رسم الشموع والمؤشرات
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    # السعر والمتوسطات والبولينجر
    fig.add_trace(go.Candlestick(x=df_detail.index, open=df_detail['Open'], high=df_detail['High'], 
                                 low=df_detail['Low'], close=df_detail['Close'], name="السعر"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['SMA20'], name="SMA 20", line=dict(color='yellow', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['Upper_Band'], name="المقاومة", line=dict(color='gray', dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['Lower_Band'], name="الدعم", line=dict(color='gray', dash='dot')), row=1, col=1)

    # مؤشر RSI
    fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ لا توجد بيانات كافية لهذا الفاصل الزمني.")

st.caption("إخلاء مسؤولية: هذا التطبيق أداة فنية تعليمية ولا يعتبر نصيحة مالية للشراء أو البيع.")
