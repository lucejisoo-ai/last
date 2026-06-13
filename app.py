import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide", page_title="Stock Analysis")

st.title("📈 한국 주식 분석 대시보드")

# 세션 상태 관리
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = ['005930.KS', '000660.KS']

# 종목 검색 및 추가
new_ticker = st.sidebar.text_input("종목코드 입력 (예: 005380.KS)")
if st.sidebar.button("추가"):
    if new_ticker and new_ticker not in st.session_state.my_stocks and len(st.session_state.my_stocks) < 10:
        st.session_state.my_stocks.append(new_ticker)
        st.rerun()

# 데이터 계산
data_list = []
for ticker in st.session_state.my_stocks:
    stock = yf.Ticker(ticker)
    info = stock.info
    eps = info.get('trailingEps', 0)
    price = info.get('currentPrice', 0)
    
    # 지표 계산
    graham = eps * 22.5 * 4.4 / 3.5
    dcf = eps * 1.5 # 간이 DCF
    pv = eps / 0.08
    peg = eps * 15 * 0.1 * 100
    
    data_list.append({
        "종목": info.get('shortName', ticker),
        "현재가": price,
        "PER": info.get('trailingPE', 0),
        "그레이엄": round(graham),
        "DCF": round(dcf),
        "PV": round(pv),
        "PEG": round(peg)
    })

st.table(pd.DataFrame(data_list))
