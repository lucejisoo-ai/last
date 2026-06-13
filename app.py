import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide", page_title="Stock Dashboard")

st.title("📈 한국 주식 분석 대시보드")

# 1. 지수 카드
col1, col2 = st.columns(2)
with col1: st.metric("KOSPI", f"{yf.Ticker('^KS11').history(period='1d')['Close'].iloc[-1]:,.2f}")
with col2: st.metric("KOSDAQ", f"{yf.Ticker('^KQ11').history(period='1d')['Close'].iloc[-1]:,.2f}")

# 2. 간단한 종목 검색 (한국 종목 코드 리스트 예시)
# 실제 서비스 시에는 한국거래소에서 종목리스트 csv를 받아와 활용합니다.
st.subheader("종목 추가")
ticker_input = st.text_input("종목 코드 입력 (예: 005930.KS)", placeholder="005930.KS")

if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = ['005930.KS', '000660.KS']

if st.button("추가"):
    if ticker_input and ticker_input not in st.session_state.my_stocks:
        st.session_state.my_stocks.append(ticker_input)
        st.rerun()

# 3. 데이터 테이블
results = []
for ticker in st.session_state.my_stocks:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        results.append({
            "종목코드": ticker,
            "현재가": f"{hist['Close'].iloc[-1]:,.0f}원"
        })
    except:
        continue

if results:
    st.table(pd.DataFrame(results))
