import streamlit as st
import yfinance as yf
import pandas as pd
import dart_fss as dart

# DART API 설정
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176" # Secrets에 저장 권장
dart.set_api_key(api_key=DART_API_KEY)

st.set_page_config(layout="wide", page_title="Professional Stock Analysis")

st.title("📈 관심 종목 가치 분석 대시보드")

# 1. 관심종목 리스트 초기화 (세션 상태)
if 'watch_list' not in st.session_state:
    st.session_state.watch_list = []

# 2. 검색 및 추가 로직
corp_list = dart.get_corp_list()
all_corps = {c.corp_name: c.corp_code for c in corp_list}

with st.sidebar:
    st.header("종목 추가")
    search = st.selectbox("종목명 검색", [""] + list(all_corps.keys()))
    if st.button("관심종목 추가"):
        if search and len(st.session_state.watch_list) < 10:
            if search not in st.session_state.watch_list:
                st.session_state.watch_list.append(search)
                st.rerun()
        else:
            st.warning("10개까지만 추가 가능합니다.")

# 3. 데이터 계산 로직
def get_analysis_data(name):
    # 실제로는 DART/Yahoo 결합하여 데이터 추출
    # 여기서는 예시를 위해 가상 데이터를 매핑 (실제 데이터 호출로 대체 필요)
    ticker = "005930.KS" # 예시 코드
    stock = yf.Ticker(ticker)
    info = stock.info
    eps = info.get('trailingEps', 1000) or 1000
    
    # 4가지 계산법
    graham = eps * 22.5 * 4.4 / 3.5
    dcf = eps * 1.5 
    pv = eps / 0.08
    peg = eps * 15 * 0.1 * 100
    
    return {
        "종목": name,
        "현재가": info.get('currentPrice', 0),
        "PER": info.get('trailingPE', 0),
        "그레이엄": round(graham),
        "DCF": round(dcf),
        "PV": round(pv),
        "PEG": round(peg)
    }

# 4. 결과 테이블 출력
if st.session_state.watch_list:
    analysis_results = [get_analysis_data(name) for name in st.session_state.watch_list]
    df = pd.DataFrame(analysis_results)
    
    # 삭제 버튼 포함한 테이블 구성
    for idx, row in df.iterrows():
        cols = st.columns([0.8, 0.2])
        cols[0].table(pd.DataFrame([row]))
        if cols[1].button("삭제", key=f"del_{idx}"):
            st.session_state.watch_list.pop(idx)
            st.rerun()
