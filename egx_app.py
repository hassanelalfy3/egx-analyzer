import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(page_title="EGX Ultimate Scanner", layout="wide")

# قائمة الأسهم المراقبة
EGX_LIST = ["COMI.CA", "FWRY.CA", "TMGH.CA", "EKHO.CA", "ABUK.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "ORAS.CA", "PHDC.CA"]

def get_indicators(df):
    if df.empty or len(df) < 50: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # Moving Averages
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    return df

# --- وظيفة المسح الشامل ---
def run_market_scanner():
    results = []
    for ticker in EGX_LIST:
        data = yf.download(ticker, period="60d", interval="1d", progress=False)
        df = get_indicators(data)
        if df is not None:
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            signal = "Neutral ⚪"
            if last['RSI'] < 30: signal = "Oversold/BUY 🟢"
            elif last['RSI'] > 70: signal = "Overbought/SELL 🔴"
            elif prev['SMA20'] < prev['SMA50'] and last['SMA20'] > last['SMA50']: signal = "Golden Cross 🔥"
            
            results.append({
                "Symbol": ticker.replace(".CA", ""),
                "Price": round(float(last['Close']), 2),
                "RSI": round(float(last['RSI']), 2),
                "Signal": signal
            })
    return pd.DataFrame(results)

# --- واجهة التطبيق ---
st.title("🚀 رادار البورصة المصرية - النسخة الاحترافية")

# 1. قسم الماسح الضوئي (Scanner)
with st.expander("🔍 فحص سريع للسوق (Market Scanner)", expanded=True):
    if st.button("تحديث الفحص الآن"):
        scanner_df = run_market_scanner()
        
        # تنسيق الجدول بالألوان
        def color_signal(val):
            color = 'white'
            if 'BUY' in val or 'Golden' in val: color = '#90ee90' # أخضر فاتح
            elif 'SELL' in val: color = '#ffcccb' # أحمر فاتح
            return f'background-color: {color}; color: black'

        st.table(scanner_df.style.applymap(color_signal, subset=['Signal']))
    else:
        st.info("اضغط على الزر أعلاه لفحص الأسهم العشرة حالياً.")

st.divider()

# 2. قسم التحليل التفصيلي (القديم المطوّر)
st.subheader("📊 التحليل التفصيلي لسهم محدد")
selected_stock = st.selectbox("اختر السهم للعرض الفني:", EGX_LIST)

with st.spinner('جاري جلب بيانات الشارت...'):
    df_detail = yf.download(selected_stock, period="1y", interval="1d", progress=False)
    df_detail = get_indicators(df_detail)

if df_detail is not None:
    # الشارت
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df_detail.index, open=df_detail['Open'], high=df_detail['High'], low=df_detail['Low'], close=df_detail['Close'], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['SMA20'], name="SMA 20", line=dict(color='yellow')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['RSI'], name="RSI", line=dict(color='orange')), row=2, col=1)
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
