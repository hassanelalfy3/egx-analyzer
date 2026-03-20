{\rtf1\ansi\ansicpg1252\cocoartf2868
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier;\f1\fnil\fcharset0 Menlo-Regular;\f2\fmodern\fcharset0 Courier-Oblique;
\f3\fnil\fcharset0 Menlo-Italic;}
{\colortbl;\red255\green255\blue255;\red195\green123\blue90;\red23\green23\blue26;\red174\green176\blue183;
\red103\green107\blue114;\red152\green54\blue29;\red89\green158\blue96;\red71\green149\blue242;\red117\green114\blue185;
\red38\green157\blue169;\red78\green112\blue88;}
{\*\expandedcolortbl;;\csgenericrgb\c76471\c48235\c35294;\csgenericrgb\c9020\c9020\c10196;\csgenericrgb\c68235\c69020\c71765;
\csgenericrgb\c40392\c41961\c44706;\csgenericrgb\c59608\c21176\c11373;\csgenericrgb\c34902\c61961\c37647;\csgenericrgb\c27843\c58431\c94902;\csgenericrgb\c45882\c44706\c72549;
\csgenericrgb\c14902\c61569\c66275;\csgenericrgb\c30588\c43922\c34510;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs26 \cf2 \cb3 import \cf4 streamlit \cf2 as \cf4 st\
\cf2 import \cf4 yfinance \cf2 as \cf4 yf\
\cf2 import \cf4 pandas \cf2 as \cf4 pd\
\cf2 import \cf4 plotly.graph_objects \cf2 as \cf4 go\
\cf2 from \cf4 plotly.subplots \cf2 import \cf4 make_subplots\
\
\cf5 # 
\f1 \uc0\u1573 \u1593 \u1583 \u1575 \u1583 \u1575 \u1578  \u1575 \u1604 \u1589 \u1601 \u1581 \u1577 \

\f0 \cf4 st.set_page_config(\cf6 page_title\cf4 =\cf7 "EGX Pro Advisor"\cf4 , \cf6 layout\cf4 =\cf7 "wide"\cf4 )\
\
\
\cf2 def \cf8 add_indicators\cf4 (df):\
    \cf5 # 
\f1 \uc0\u1573 \u1589 \u1604 \u1575 \u1581  \u1605 \u1588 \u1603 \u1604 \u1577  \u1575 \u1604 \u1571 \u1593 \u1605 \u1583 \u1577  \u1575 \u1604 \u1605 \u1578 \u1583 \u1575 \u1582 \u1604 \u1577  \u1601 \u1610 
\f0  yfinance\
    \cf2 if \cf9 isinstance\cf4 (df.columns, pd.MultiIndex):\
        df.columns = df.columns.get_level_values(\cf10 0\cf4 )\
\
    \cf5 # 
\f1 \uc0\u1581 \u1587 \u1575 \u1576 
\f0  RSI\
    \cf4 delta = df[\cf7 'Close'\cf4 ].diff()\
    gain = (delta.where(delta > \cf10 0\cf4 , \cf10 0\cf4 )).rolling(\cf6 window\cf4 =\cf10 14\cf4 ).mean()\
    loss = (-delta.where(delta < \cf10 0\cf4 , \cf10 0\cf4 )).rolling(\cf6 window\cf4 =\cf10 14\cf4 ).mean()\
    rs = gain / loss\
    df[\cf7 'RSI'\cf4 ] = \cf10 100 \cf4 - (\cf10 100 \cf4 / (\cf10 1 \cf4 + rs))\
\
    \cf5 # 
\f1 \uc0\u1575 \u1604 \u1605 \u1578 \u1608 \u1587 \u1591 \u1575 \u1578  \u1575 \u1604 \u1605 \u1578 \u1581 \u1585 \u1603 \u1577 \
    
\f0 \cf4 df[\cf7 'SMA20'\cf4 ] = df[\cf7 'Close'\cf4 ].rolling(\cf6 window\cf4 =\cf10 20\cf4 ).mean()\
    df[\cf7 'SMA50'\cf4 ] = df[\cf7 'Close'\cf4 ].rolling(\cf6 window\cf4 =\cf10 50\cf4 ).mean()\
\
    \cf5 # 
\f1 \uc0\u1576 \u1608 \u1604 \u1610 \u1606 \u1580 \u1585  \u1576 \u1575 \u1606 \u1583 \u1586 \
    
\f0 \cf4 df[\cf7 'StdDev'\cf4 ] = df[\cf7 'Close'\cf4 ].rolling(\cf6 window\cf4 =\cf10 20\cf4 ).std()\
    df[\cf7 'Upper_Band'\cf4 ] = df[\cf7 'SMA20'\cf4 ] + (df[\cf7 'StdDev'\cf4 ] * \cf10 2\cf4 )\
    df[\cf7 'Lower_Band'\cf4 ] = df[\cf7 'SMA20'\cf4 ] - (df[\cf7 'StdDev'\cf4 ] * \cf10 2\cf4 )\
    \cf2 return \cf4 df\
\
\
\cf2 def \cf8 get_recommendation\cf4 (df):\
    
\f2\i \cf11 """
\f3 \uc0\u1583 \u1575 \u1604 \u1577  \u1604 \u1573 \u1606 \u1578 \u1575 \u1580  \u1578 \u1608 \u1589 \u1610 \u1577  \u1584 \u1603 \u1610 \u1577  \u1576 \u1606 \u1575 \u1569 \u1611  \u1593 \u1604 \u1609  \u1575 \u1604 \u1605 \u1572 \u1588 \u1585 \u1575 \u1578 
\f2 """\
    
\f0\i0 \cf4 last = df.iloc[-\cf10 1\cf4 ]\
    price = \cf9 float\cf4 (last[\cf7 'Close'\cf4 ])\
    rsi = \cf9 float\cf4 (last[\cf7 'RSI'\cf4 ])\
\
    rec = \{\cf7 "action"\cf4 : \cf7 "HOLD 
\f1 \uc0\u9898 
\f0 "\cf4 , \cf7 "tp1"\cf4 : \cf7 "-"\cf4 , \cf7 "tp2"\cf4 : \cf7 "-"\cf4 , \cf7 "sl"\cf4 : \cf7 "-"\cf4 , \cf7 "reason"\cf4 : \cf7 "
\f1 \uc0\u1575 \u1604 \u1587 \u1593 \u1585  \u1601 \u1610  \u1605 \u1606 \u1591 \u1602 \u1577  \u1605 \u1581 \u1575 \u1610 \u1583 \u1577  \u1581 \u1575 \u1604 \u1610 \u1575 \u1611 
\f0 ."\cf4 \}\
\
    \cf5 # 
\f1 \uc0\u1573 \u1588 \u1575 \u1585 \u1577  \u1588 \u1585 \u1575 \u1569 
\f0  (Buy Signal)\
    \cf2 if \cf4 rsi <= \cf10 35 \cf2 or \cf4 price <= last[\cf7 'Lower_Band'\cf4 ]:\
        rec[\cf7 "action"\cf4 ] = \cf7 "BUY 
\f1 \uc0\u55357 \u57314 
\f0 "\
        \cf4 rec[\cf7 "sl"\cf4 ] = \cf9 round\cf4 (price * \cf10 0.95\cf4 , \cf10 2\cf4 )  \cf5 # 
\f1 \uc0\u1608 \u1602 \u1601  \u1582 \u1587 \u1575 \u1585 \u1577  \u1593 \u1606 \u1583 
\f0  5% 
\f1 \uc0\u1578 \u1581 \u1578  \u1575 \u1604 \u1587 \u1593 \u1585 \
        
\f0 \cf4 rec[\cf7 "tp1"\cf4 ] = \cf9 round\cf4 (last[\cf7 'SMA20'\cf4 ], \cf10 2\cf4 )  \cf5 # 
\f1 \uc0\u1575 \u1604 \u1607 \u1583 \u1601  \u1575 \u1604 \u1571 \u1608 \u1604  \u1593 \u1606 \u1583  \u1575 \u1604 \u1605 \u1578 \u1608 \u1587 \u1591 
\f0  20\
        \cf4 rec[\cf7 "tp2"\cf4 ] = \cf9 round\cf4 (last[\cf7 'Upper_Band'\cf4 ], \cf10 2\cf4 )  \cf5 # 
\f1 \uc0\u1575 \u1604 \u1607 \u1583 \u1601  \u1575 \u1604 \u1579 \u1575 \u1606 \u1610  \u1593 \u1606 \u1583  \u1587 \u1602 \u1601  \u1575 \u1604 \u1576 \u1608 \u1604 \u1610 \u1606 \u1580 \u1585 \
        
\f0 \cf4 rec[\cf7 "reason"\cf4 ] = \cf7 "
\f1 \uc0\u1578 \u1588 \u1576 \u1593  \u1576 \u1610 \u1593 \u1610  \u1608 \u1575 \u1590 \u1581 
\f0  (RSI 
\f1 \uc0\u1605 \u1606 \u1582 \u1601 \u1590 
\f0 ) 
\f1 \uc0\u1571 \u1608  \u1605 \u1604 \u1575 \u1605 \u1587 \u1577  \u1583 \u1593 \u1605  \u1575 \u1604 \u1576 \u1608 \u1604 \u1610 \u1606 \u1580 \u1585  \u1575 \u1604 \u1587 \u1601 \u1604 \u1610 
\f0 ."\
\
    \cf5 # 
\f1 \uc0\u1573 \u1588 \u1575 \u1585 \u1577  \u1576 \u1610 \u1593 
\f0  (Sell Signal)\
    \cf2 elif \cf4 rsi >= \cf10 70 \cf2 or \cf4 price >= last[\cf7 'Upper_Band'\cf4 ]:\
        rec[\cf7 "action"\cf4 ] = \cf7 "SELL 
\f1 \uc0\u55357 \u56628 
\f0 "\
        \cf4 rec[\cf7 "reason"\cf4 ] = \cf7 "
\f1 \uc0\u1578 \u1588 \u1576 \u1593  \u1588 \u1585 \u1575 \u1574 \u1610  \u1605 \u1585 \u1578 \u1601 \u1593  \u1571 \u1608  \u1605 \u1604 \u1575 \u1605 \u1587 \u1577  \u1605 \u1602 \u1575 \u1608 \u1605 \u1577  \u1575 \u1604 \u1576 \u1608 \u1604 \u1610 \u1606 \u1580 \u1585  \u1575 \u1604 \u1593 \u1604 \u1608 \u1610 \u1577 
\f0 ."\
\
    \cf2 return \cf4 rec\
\
\
\cf5 # --- 
\f1 \uc0\u1608 \u1575 \u1580 \u1607 \u1577  \u1575 \u1604 \u1605 \u1587 \u1578 \u1582 \u1583 \u1605 
\f0  ---\
\cf4 st.title(\cf7 "
\f1 \uc0\u55356 \u57337  \u1605 \u1587 \u1578 \u1588 \u1575 \u1585 \u1603  \u1575 \u1604 \u1584 \u1603 \u1610  \u1604 \u1604 \u1576 \u1608 \u1585 \u1589 \u1577  \u1575 \u1604 \u1605 \u1589 \u1585 \u1610 \u1577 
\f0 "\cf4 )\
st.markdown(\cf7 "---"\cf4 )\
\
egx_list = [\cf7 "COMI.CA"\cf4 , \cf7 "FWRY.CA"\cf4 , \cf7 "TMGH.CA"\cf4 , \cf7 "EKHO.CA"\cf4 , \cf7 "ABUK.CA"\cf4 , \cf7 "SWDY.CA"\cf4 , \cf7 "ETEL.CA"\cf4 , \cf7 "AMOC.CA"\cf4 , \cf7 "ORAS.CA"\cf4 ,\
            \cf7 "PHDC.CA"\cf4 ]\
selected_stock = st.sidebar.selectbox(\cf7 "
\f1 \uc0\u1575 \u1582 \u1578 \u1585  \u1575 \u1604 \u1587 \u1607 \u1605  \u1604 \u1578 \u1581 \u1604 \u1610 \u1604 \u1607 
\f0 :"\cf4 , egx_list)\
period = st.sidebar.selectbox(\cf7 "
\f1 \uc0\u1601 \u1578 \u1585 \u1577  \u1593 \u1585 \u1590  \u1575 \u1604 \u1588 \u1575 \u1585 \u1578 
\f0 :"\cf4 , [\cf7 "3mo"\cf4 , \cf7 "6mo"\cf4 , \cf7 "1y"\cf4 ], \cf6 index\cf4 =\cf10 1\cf4 )\
\
\cf5 # 
\f1 \uc0\u1587 \u1581 \u1576  \u1575 \u1604 \u1576 \u1610 \u1575 \u1606 \u1575 \u1578 \

\f0 \cf2 with \cf4 st.spinner(\cf7 '
\f1 \uc0\u1580 \u1575 \u1585 \u1610  \u1578 \u1581 \u1583 \u1610 \u1579  \u1576 \u1610 \u1575 \u1606 \u1575 \u1578  \u1575 \u1604 \u1587 \u1608 \u1602 
\f0 ...'\cf4 ):\
    df = yf.download(selected_stock, \cf6 period\cf4 =\cf7 "1y"\cf4 , \cf6 interval\cf4 =\cf7 "1d"\cf4 , \cf6 progress\cf4 =\cf2 False\cf4 )\
\
\cf2 if not \cf4 df.empty:\
    df = add_indicators(df)\
    rec = get_recommendation(df)\
\
    \cf5 # 
\f1 \uc0\u1593 \u1585 \u1590  \u1575 \u1604 \u1578 \u1608 \u1589 \u1610 \u1577  \u1601 \u1610  \u1605 \u1585 \u1576 \u1593 \u1575 \u1578  \u1605 \u1604 \u1608 \u1606 \u1577 
\f0  (Metrics)\
    \cf4 c1, c2, c3, c4 = st.columns(\cf10 4\cf4 )\
    c1.metric(\cf7 "
\f1 \uc0\u1575 \u1604 \u1578 \u1608 \u1589 \u1610 \u1577  \u1575 \u1604 \u1581 \u1575 \u1604 \u1610 \u1577 
\f0 "\cf4 , rec[\cf7 "action"\cf4 ])\
    c2.metric(\cf7 "
\f1 \uc0\u1575 \u1604 \u1607 \u1583 \u1601  \u1575 \u1604 \u1571 \u1608 \u1604 
\f0  (TP1)"\cf4 , rec[\cf7 "tp1"\cf4 ])\
    c3.metric(\cf7 "
\f1 \uc0\u1575 \u1604 \u1607 \u1583 \u1601  \u1575 \u1604 \u1579 \u1575 \u1606 \u1610 
\f0  (TP2)"\cf4 , rec[\cf7 "tp2"\cf4 ])\
    c4.metric(\cf7 "
\f1 \uc0\u1608 \u1602 \u1601  \u1575 \u1604 \u1582 \u1587 \u1575 \u1585 \u1577 
\f0  (SL)"\cf4 , rec[\cf7 "sl"\cf4 ])\
\
    st.info(\cf7 f"
\f1 \uc0\u55357 \u56481 
\f0  **
\f1 \uc0\u1578 \u1581 \u1604 \u1610 \u1604  \u1575 \u1604 \u1582 \u1576 \u1610 \u1585  \u1575 \u1604 \u1570 \u1604 \u1610 
\f0 :** \cf2 \{\cf4 rec[\cf7 'reason'\cf4 ]\cf2 \}\cf7 "\cf4 )\
\
    \cf5 # --- 
\f1 \uc0\u1585 \u1587 \u1605  \u1575 \u1604 \u1588 \u1575 \u1585 \u1578 
\f0  ---\
    \cf4 fig = make_subplots(\cf6 rows\cf4 =\cf10 2\cf4 , \cf6 cols\cf4 =\cf10 1\cf4 , \cf6 shared_xaxes\cf4 =\cf2 True\cf4 ,\
                        \cf6 vertical_spacing\cf4 =\cf10 0.05\cf4 , \cf6 row_heights\cf4 =[\cf10 0.7\cf4 , \cf10 0.3\cf4 ])\
\
    \cf5 # 
\f1 \uc0\u1573 \u1590 \u1575 \u1601 \u1577  \u1575 \u1604 \u1587 \u1593 \u1585  \u1608 \u1602 \u1606 \u1575 \u1577  \u1575 \u1604 \u1576 \u1608 \u1604 \u1610 \u1606 \u1580 \u1585 \
    
\f0 \cf4 fig.add_trace(go.Candlestick(\cf6 x\cf4 =df.index, \cf6 open\cf4 =df[\cf7 'Open'\cf4 ], \cf6 high\cf4 =df[\cf7 'High'\cf4 ],\
                                 \cf6 low\cf4 =df[\cf7 'Low'\cf4 ], \cf6 close\cf4 =df[\cf7 'Close'\cf4 ], \cf6 name\cf4 =\cf7 "Price"\cf4 ), \cf6 row\cf4 =\cf10 1\cf4 , \cf6 col\cf4 =\cf10 1\cf4 )\
\
    fig.add_trace(go.Scatter(\cf6 x\cf4 =df.index, \cf6 y\cf4 =df[\cf7 'Upper_Band'\cf4 ], \cf6 name\cf4 =\cf7 "
\f1 \uc0\u1605 \u1602 \u1575 \u1608 \u1605 \u1577  \u1576 \u1608 \u1604 \u1610 \u1606 \u1580 \u1585 
\f0 "\cf4 ,\
                             \cf6 line\cf4 =\cf9 dict\cf4 (\cf6 color\cf4 =\cf7 'rgba(255,255,255,0.2)'\cf4 , \cf6 dash\cf4 =\cf7 'dot'\cf4 )), \cf6 row\cf4 =\cf10 1\cf4 , \cf6 col\cf4 =\cf10 1\cf4 )\
    fig.add_trace(go.Scatter(\cf6 x\cf4 =df.index, \cf6 y\cf4 =df[\cf7 'Lower_Band'\cf4 ], \cf6 name\cf4 =\cf7 "
\f1 \uc0\u1583 \u1593 \u1605  \u1576 \u1608 \u1604 \u1610 \u1606 \u1580 \u1585 
\f0 "\cf4 ,\
                             \cf6 line\cf4 =\cf9 dict\cf4 (\cf6 color\cf4 =\cf7 'rgba(255,255,255,0.2)'\cf4 , \cf6 dash\cf4 =\cf7 'dot'\cf4 )), \cf6 row\cf4 =\cf10 1\cf4 , \cf6 col\cf4 =\cf10 1\cf4 )\
\
    \cf5 # 
\f1 \uc0\u1573 \u1590 \u1575 \u1601 \u1577  \u1593 \u1604 \u1575 \u1605 \u1577  \u1587 \u1607 \u1605  \u1593 \u1606 \u1583  \u1578 \u1608 \u1589 \u1610 \u1577  \u1575 \u1604 \u1588 \u1585 \u1575 \u1569 \
    
\f0 \cf2 if \cf4 rec[\cf7 "action"\cf4 ] == \cf7 "BUY 
\f1 \uc0\u55357 \u57314 
\f0 "\cf4 :\
        fig.add_annotation(\cf6 x\cf4 =df.index[-\cf10 1\cf4 ], \cf6 y\cf4 =df[\cf7 'Low'\cf4 ].iloc[-\cf10 1\cf4 ], \cf6 text\cf4 =\cf7 "
\f1 \uc0\u1583 \u1582 \u1608 \u1604 
\f0 "\cf4 ,\
                           \cf6 showarrow\cf4 =\cf2 True\cf4 , \cf6 arrowhead\cf4 =\cf10 1\cf4 , \cf6 bgcolor\cf4 =\cf7 "green"\cf4 , \cf6 font\cf4 =\cf9 dict\cf4 (\cf6 color\cf4 =\cf7 "white"\cf4 ), \cf6 row\cf4 =\cf10 1\cf4 , \cf6 col\cf4 =\cf10 1\cf4 )\
\
    \cf5 # 
\f1 \uc0\u1573 \u1590 \u1575 \u1601 \u1577 
\f0  RSI\
    \cf4 fig.add_trace(go.Scatter(\cf6 x\cf4 =df.index, \cf6 y\cf4 =df[\cf7 'RSI'\cf4 ], \cf6 name\cf4 =\cf7 "RSI"\cf4 , \cf6 line\cf4 =\cf9 dict\cf4 (\cf6 color\cf4 =\cf7 'orange'\cf4 )), \cf6 row\cf4 =\cf10 2\cf4 , \cf6 col\cf4 =\cf10 1\cf4 )\
    fig.add_hline(\cf6 y\cf4 =\cf10 70\cf4 , \cf6 line_dash\cf4 =\cf7 "dash"\cf4 , \cf6 line_color\cf4 =\cf7 "red"\cf4 , \cf6 row\cf4 =\cf10 2\cf4 , \cf6 col\cf4 =\cf10 1\cf4 )\
    fig.add_hline(\cf6 y\cf4 =\cf10 30\cf4 , \cf6 line_dash\cf4 =\cf7 "dash"\cf4 , \cf6 line_color\cf4 =\cf7 "green"\cf4 , \cf6 row\cf4 =\cf10 2\cf4 , \cf6 col\cf4 =\cf10 1\cf4 )\
\
    \cf5 # 
\f1 \uc0\u1578 \u1581 \u1583 \u1610 \u1579  \u1575 \u1604 \u1578 \u1589 \u1605 \u1610 \u1605 
\f0  (
\f1 \uc0\u1607 \u1606 \u1575  \u1603 \u1575 \u1606  \u1575 \u1604 \u1582 \u1591 \u1571 
\f0 )\
    \cf4 fig.update_layout(\cf6 height\cf4 =\cf10 800\cf4 , \cf6 template\cf4 =\cf7 "plotly_dark"\cf4 , \cf6 xaxis_rangeslider_visible\cf4 =\cf2 False\cf4 )\
    st.plotly_chart(fig, \cf6 use_container_width\cf4 =\cf2 True\cf4 )\
\
\cf2 else\cf4 :\
    st.error(\cf7 "
\f1 \uc0\u1604 \u1605  \u1610 \u1578 \u1605  \u1575 \u1604 \u1593 \u1579 \u1608 \u1585  \u1593 \u1604 \u1609  \u1576 \u1610 \u1575 \u1606 \u1575 \u1578  \u1604 \u1607 \u1584 \u1575  \u1575 \u1604 \u1587 \u1607 \u1605 
\f0 . 
\f1 \uc0\u1578 \u1571 \u1603 \u1583  \u1605 \u1606  \u1575 \u1578 \u1589 \u1575 \u1604  \u1575 \u1604 \u1573 \u1606 \u1578 \u1585 \u1606 \u1578 
\f0 ."\cf4 )\
}