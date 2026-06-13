import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide", page_title="Professional Stock Analysis")

st.title("📈 기업 가치 분석 대시보드")

# 1. 종목 데이터 (한국거래소 종목 리스트 로드)
@st.cache_data
def get_stock_list():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv" # 예시용
    # 실제 환경에서는 한국거래소 상장종목 리스트 csv를 사용하세요.
    return {"005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", "035720": "카카오"}

# 2. 분석 계산식
def calculate_metrics(eps, growth_rate=0.05):
    graham = eps * 22.5 * 4.4 / 3.5  # 벤저민 그레이엄
    dcf = eps * ((1 + growth_rate)**10) / (1.08**10) / 0.08 # DCF 간이 계산
    pv = eps / 0.08 # 절대가치
    peg = eps * 15 * growth_rate * 100 # PEG 간이 계산
    return graham, dcf, pv, peg

# 3. 사이드바 - 종목 검색 및 추가
st.sidebar.header("종목 추가 (최대 10개)")
if 'my_stocks' not in st.session_state: st.session_state.my_stocks = []

search = st.sidebar.text_input("종목코드 또는 종목명 검색")
if st.sidebar.button("추가"):
    if len(st.session_state.my_stocks) < 10:
        # 여기에 검색 로직 연동
        code = f"{search}.KS" if not search.endswith('.KS') else search
        st.session_state.my_stocks.append(code)
        st.rerun()
    else:
        st.sidebar.error("최대 10개까지만 가능합니다.")

# 4. 결과 테이블 표시
if st.session_state.my_stocks:
    data_list = []
    for ticker in st.session_state.my_stocks:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1d")
            eps = info.get('trailingEps', 0)
            g, d, p, peg = calculate_metrics(eps)
            
            data_list.append({
                "종목명": info.get('shortName'),
                "현재가": hist['Close'].iloc[-1],
                "PER": info.get('trailingPE'),
                "그레이엄": round(g),
                "DCF": round(d),
                "PV": round(p),
                "PEG": round(peg)
            })
        except: continue
    
    st.table(pd.DataFrame(data_list))
