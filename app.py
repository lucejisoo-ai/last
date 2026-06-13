import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide", page_title="Professional Stock Dashboard")

# 1. 한글 종목명과 코드 매칭 딕셔너리 (필요한 만큼 추가하세요)
STOCK_MAP = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NAVER": "035420.KS",
    "카카오": "035720.KS", "현대차": "005380.KS", "LG에너지솔루션": "373220.KS"
}

st.title("📈 한국 주식 실시간 분석")

# 세션 관리
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = ['005930.KS']

# 2. 검색 및 추가 UI
with st.sidebar:
    st.header("종목 관리")
    query = st.text_input("종목명 또는 코드 입력", placeholder="예: 삼성전자")
    if st.button("추가"):
        # 매칭 로직: 한글 입력 시 딕셔너리에서 찾기
        ticker = STOCK_MAP.get(query, query if ".KS" in query or ".KQ" in query else f"{query}.KS")
        if ticker not in st.session_state.my_stocks:
            st.session_state.my_stocks.append(ticker)
            st.rerun()

    st.divider()
    st.subheader("종목 삭제")
    delete_target = st.selectbox("삭제할 종목 선택", st.session_state.my_stocks)
    if st.button("삭제"):
        st.session_state.my_stocks.remove(delete_target)
        st.rerun()

# 3. 데이터 표시 및 계산
data_list = []
for ticker in st.session_state.my_stocks:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        eps = info.get('trailingEps', 0)
        
        # 계산식
        graham = eps * 22.5 * 4.4 / 3.5
        
        data_list.append({
            "종목": info.get('shortName', ticker),
            "현재가": info.get('currentPrice', 0),
            "PER": info.get('trailingPE', 0),
            "그레이엄적정가": round(graham)
        })
    except: continue

if data_list:
    st.table(pd.DataFrame(data_list))
