import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- [نفس الإعدادات السابقة] ---
st.set_page_config(page_title="EGX Pro Terminal", layout="wide")

# دالة التنظيف لضمان عدم حدوث ValueError
def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# --- الدالة المحدثة لإضافة أرقام التداول (Buy/TP/SL) ---
@st.cache_data(ttl=600)
def get_market_summary():
    results = []
    # قائمة أوسع للأسهم لتظهر نتائج حقيقية في الجداول
    TICKERS_LIST = ["COMI.CA", "FWRY.CA", "TMGH.CA", "ESRS.CA", "ABUK.CA", "EKHO.CA", "SWDY.CA", "ETEL.CA", "AMOC.CA", "PHDC.CA", "HELI.CA", "ORAS.CA", "BTEL.CA", "CCAP.CA"]
    
    for t in TICKERS_LIST:
        try:
            # جلب بيانات كافية للحسابات الفنية (60 يوم)
            d = clean_df(yf.download(t, period="60d", progress=False))
            if d.empty or len(d) < 2: continue
            
            close_now = float(d['Close'].iloc[-1])
            close_prev = float(d['Close'].iloc[-2])
            change = ((close_now - close_prev) / close_prev) * 100
            
            # حسابات فنية سريعة للأهداف والوقف
            # نستخدم تذبذب السهم (High - Low) لتقدير الوقف والهدف
            volatility = (d['High'] - d['Low']).rolling(10).mean().iloc[-1]
            
            buy_range = f"{round(close_now * 0.985, 2)} - {round(close_now, 2)}"
            take_profit = round(close_now + (volatility * 1.5), 2)
            stop_loss = round(close_now - (volatility * 1.2), 2)

            results.append({
                "Ticker": t.replace(".CA", ""),
                "Price": round(close_now, 2),
                "Change %": round(float(change), 2),
                "Buy Range": buy_range,
                "TP (Target)": take_profit,
                "SL (Stop)": stop_loss,
                "Volume": int(d['Volume'].iloc[-1])
            })
        except Exception as e:
            continue
    return pd.DataFrame(results)

# --- عرض الجداول في التبويبات ---
st.title("EGX Today 🛡️")
# (هنا تضع كود الـ Scorecards الذي كتبناه سابقاً)

st.write("### Market Summary & Signals")
df_market = get_market_summary()

if not df_market.empty:
    tab_gain, tab_loss, tab_active = st.tabs(["🔥 Top Gainers", "❄️ Top Losers", "📊 Most Active"])
    
    # تنسيق الألوان للجدول
    with tab_gain:
        st.dataframe(
            df_market.sort_values(by="Change %", ascending=False).head(10),
            use_container_width=True,
            hide_index=True
        )
    
    with tab_loss:
        st.dataframe(
            df_market.sort_values(by="Change %", ascending=True).head(10),
            use_container_width=True,
            hide_index=True
        )
        
    with tab_active:
        st.dataframe(
            df_market.sort_values(by="Volume", ascending=False).head(10),
            use_container_width=True,
            hide_index=True
        )

# --- [تكملة كود الشارت والتحليل كما في السابق] ---
