import streamlit as st
import yfinance as yf
import pandas as pd
from pykrx import stock

st.set_page_config(layout="wide", page_title="Professional Stock Dashboard")

# UI 스타일 정의 (CSS)
st.markdown("""
    <style>
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 한국 주식 분석 대시보드")

# 1. 지수 카드 UI
col1, col2 = st.columns(2)
with col1: st.metric("KOSPI", f"{yf.Ticker('^KS11').history(period='1d')['Close'].iloc[-1]:,.2f}")
with col2: st.metric("KOSDAQ", f"{yf.Ticker('^KQ11').history(period='1d')['Close'].iloc[-1]:,.2f}")

# 2. 종목 검색 및 추가
st.subheader("종목 검색")
search_query = st.text_input("종목명 또는 종목코드를 입력하세요 (예: 삼성전자)", "")

if search_query:
    # 종목명으로 검색 (Like 검색)
    tickers = stock.get_market_ticker_list()
    search_results = []
    for ticker in tickers:
        name = stock.get_market_ticker_name(ticker)
        if search_query in name or search_query in ticker:
            search_results.append((ticker, name))
            if len(search_results) >= 5: break
    
    if search_results:
        selected = st.selectbox("검색 결과", [f"{name} ({ticker})" for ticker, name in search_results])
        if st.button("추가하기"):
            ticker_code = selected.split('(')[1].replace(')', '')
            # 야후 파이낸스용 코드 변환 (KS/KQ)
            market = stock.get_market_ohlcv(ticker_code).empty # 간단 구분
            formatted_ticker = f"{ticker_code}.KS" if not market else f"{ticker_code}.KQ"
            st.session_state.my_stocks.append(formatted_ticker)
            st.rerun()

# 3. 데이터 표시 테이블
if 'my_stocks' not in st.session_state: st.session_state.my_stocks = ['005930.KS']
# ... (이하 데이터 테이블 출력 로직은 기존과 동일)
