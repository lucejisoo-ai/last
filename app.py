import streamlit as st
import yfinance as yf
import pandas as pd
import dart_fss as dart

# DART API 키 설정 (보안을 위해 환경변수 사용 권장)
DART_API_KEY = "본인의_DART_API_KEY"
dart.set_api_key(api_key=DART_API_KEY)

st.set_page_config(layout="wide", page_title="Professional Stock Dashboard")

st.title("📈 기업 가치 분석 대시보드")

# 1. 상단 지수 정보 (KOSPI/KOSDAQ)
col1, col2 = st.columns(2)
with col1:
    kospi = yf.Ticker('^KS11').history(period='1d')['Close'].iloc[-1]
    st.metric("KOSPI 지수", f"{kospi:,.2f}")
with col2:
    kosdaq = yf.Ticker('^KQ11').history(period='1d')['Close'].iloc[-1]
    st.metric("KOSDAQ 지수", f"{kosdaq:,.2f}")

# 2. 종목명/코드 자동완성 검색
corp_list = dart.get_corp_list()
# DART 리스트를 기반으로 이름과 코드 매칭 (실제 환경에선 이 리스트를 캐싱하여 사용)
all_corps = {c.corp_name: c.corp_code for c in corp_list}

st.sidebar.header("종목 검색")
search = st.sidebar.selectbox("종목명 또는 코드를 입력하세요", [""] + list(all_corps.keys()))

if search:
    st.write(f"### {search} 상세 분석")
    # 투자자별 매매 현황 데이터 로직 (네이버 금융 크롤링 혹은 공공데이터 연동 부분)
    # 
    st.subheader("주간 투자자별 매매 현황 (예시)")
    investor_data = pd.DataFrame({
        "투자자": ["기관", "외국인", "개인"],
        "매수": [1500, 3000, 500],
        "매도": [1200, 2800, 800]
    })
    st.table(investor_data)
