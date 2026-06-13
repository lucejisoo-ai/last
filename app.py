import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="주식 대시보드", layout="wide")

st.title("📈 한국 주식 실시간 분석 대시보드")

# 1. KOSPI/KOSDAQ 지수 정보
st.subheader("지수 실시간")
indices = {'KOSPI': '^KS11', 'KOSDAQ': '^KQ11'}
idx_cols = st.columns(2)
for i, (name, ticker) in enumerate(indices.items()):
    data = yf.Ticker(ticker).history(period="1d")
    price = data['Close'].iloc[-1]
    idx_cols[i].metric(name, f"{price:,.2f}")

st.divider()

# 2. 종목 추가 기능
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = ['005930.KS', '000660.KS']

new_ticker = st.text_input("종목코드 입력 (예: 005380.KS - 현대차)", placeholder="005380.KS")
if st.button("추가"):
    if new_ticker and new_ticker not in st.session_state.my_stocks:
        st.session_state.my_stocks.append(new_ticker)
        st.rerun()

# 3. 데이터 표시
st.subheader("관심 종목 리스트")
results = []
for ticker in st.session_state.my_stocks:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1d")
        results.append({
            "종목코드": ticker,
            "종목명": info.get('shortName', '-'),
            "현재가": f"{hist['Close'].iloc[-1]:,.0f}원",
            "PER": info.get('trailingPE', '-')
        })
    except:
        continue

if results:
    st.table(pd.DataFrame(results))

if st.button("새로고침"):
    st.rerun()
