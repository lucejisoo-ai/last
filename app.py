import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide")

# 네이버 금융 데이터 크롤링 함수
def get_investor_data(ticker_code):
    # 예: https://finance.naver.com/item/frgn.naver?code=005930
    url = f"https://finance.naver.com/item/frgn.naver?code={ticker_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    # 네이버 테이블 구조에서 데이터 추출 (간략화)
    data = pd.read_html(res.text)[1] 
    return data.head(5) # 최근 5일간 매매 현황

st.title("📈 올인원 실시간 주식 분석 대시보드")

# 관심종목 관리 (세션 상태)
if 'watch_list' not in st.session_state: st.session_state.watch_list = []

# 검색 및 추가
ticker_code = st.sidebar.text_input("종목코드 입력 (예: 005930)")
if st.sidebar.button("추가"):
    if len(st.session_state.watch_list) < 10:
        st.session_state.watch_list.append(ticker_code)
        st.rerun()

# 데이터 분석 및 출력
for code in st.session_state.watch_list:
    st.divider()
    col1, col2 = st.columns([1, 1])
    
    # 1. 재무 분석 (기존 기능)
    stock = yf.Ticker(f"{code}.KS")
    info = stock.info
    eps = info.get('trailingEps', 0) or 0
    
    with col1:
        st.subheader(f"{info.get('shortName', code)} 분석")
        analysis = pd.DataFrame({
            "지표": ["현재가", "PER", "그레이엄", "DCF", "PV", "PEG"],
            "값": [info.get('currentPrice'), info.get('trailingPE'), 
                 round(eps*22.5*4.4/3.5), round(eps*1.5), round(eps/0.08), round(eps*15*0.1*100)]
        })
        st.table(analysis)

    # 2. 네이버 금융 실시간 매매 현황 (신규 기능)
    with col2:
        st.subheader("주간 투자자 매매 현황")
        try:
            investor_df = get_investor_data(code)
            st.table(investor_df)
        except:
            st.error("데이터 로딩 실패")
