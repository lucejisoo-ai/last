import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide", page_title="Stock Analysis")

# 1. 한국 주식 데이터 확보 (간이 DB)
STOCK_DB = {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NAVER": "035420.KS", "카카오": "035720.KS"}
stock_names = list(STOCK_DB.keys())

st.title("📈 기업 가치 분석 대시보드")

# 2. 자동완성 검색 및 추가
selected_name = st.selectbox("종목 검색 (종목명 입력)", [""] + stock_names)
if st.button("추가") and selected_name:
    ticker = STOCK_DB[selected_name]
    if ticker not in st.session_state.get('my_stocks', []):
        st.session_state.my_stocks = st.session_state.get('my_stocks', []) + [ticker]
        st.rerun()

# 3. 데이터 로딩 및 삭제 로직
if 'my_stocks' not in st.session_state: st.session_state.my_stocks = ['005930.KS']

data_list = []
for ticker in st.session_state.my_stocks:
    stock = yf.Ticker(ticker)
    info = stock.info
    # 데이터가 없을 경우를 대비한 get(key, 0) 사용
    eps = info.get('trailingEps', 0) or 0
    per = info.get('trailingPE', 0) or 0
    price = info.get('currentPrice', 0)
    
    # 4가지 계산식
    graham = round(eps * 22.5 * 4.4 / 3.5, 0)
    dcf = round(eps * 1.5, 0) 
    
    data_list.append({
        "종목": info.get('shortName', ticker),
        "현재가": price,
        "PER": per,
        "그레이엄": graham,
        "DCF": dcf
    })

# 4. 테이블 및 삭제 버튼 표시
if data_list:
    df = pd.DataFrame(data_list)
    # 삭제 버튼 구현
    for i, row in df.iterrows():
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(row.to_frame().T)
        if col2.button(f"❌ 삭제", key=f"del_{i}"):
            st.session_state.my_stocks.pop(i)
            st.rerun()
