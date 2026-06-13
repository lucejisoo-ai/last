import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="주식 분석 대시보드", layout="wide")

st.title("📈 야후 파이낸스 주식 분석 대시보드")

# 종목 코드 입력 (야후는 한국 주식 뒤에 .KS나 .KQ를 붙여야 합니다)
# 삼성전자: 005930.KS, SK하이닉스: 000660.KS
tickers = ['005930.KS', '000660.KS', '058970.KS']

@st.cache_data(ttl=600)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1d")
    return {
        "종목명": info.get('shortName'),
        "현재가": hist['Close'].iloc[-1],
        "시가총액": info.get('marketCap'),
        "PER": info.get('trailingPE')
    }

results = []
for t in tickers:
    data = get_data(t)
    if data:
        results.append(data)

if results:
    df = pd.DataFrame(results)
    st.table(df)
else:
    st.error("데이터를 불러올 수 없습니다.")

st.info("데이터 출처: Yahoo Finance")
