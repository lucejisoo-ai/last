import streamlit as st
import yfinance as yf
import pandas as pd
import dart_fss as dart
import requests
from bs4 import BeautifulSoup

# DART API 키 (본인의 키로 교체하세요)
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

st.set_page_config(layout="wide", page_title="통합 분석 대시보드")
st.title("📈 기업 가치 및 투자자 현황 분석")

# 네이버 매매 현황 크롤링 함수
def get_naver_investor(code):
    url = f"https://finance.naver.com/item/frgn.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    return pd.read_html(res.text)[1].head(5)

# 관심종목 리스트
if 'watch_list' not in st.session_state: st.session_state.watch_list = []

# 검색 및 추가
ticker = st.sidebar.text_input("종목코드 입력 (예: 005930)")
if st.sidebar.button("추가"):
    if ticker and len(st.session_state.watch_list) < 10:
        st.session_state.watch_list.append(ticker)
        st.rerun()

# 분석 화면
for code in st.session_state.watch_list:
    st.divider()
    # 1. DART 재무 분석
    corp = dart.get_corp_list().find_by_ticker(code)
    if corp:
        fs = corp[0].extract_fs(bgn_de='20250101')[0] # 최근 재무제표
        eps = fs.loc['당기순이익(손실)'].iloc[0] / 100000000 # 예시: 간단 계산
        
        # 4가지 적정주가 비교
        analysis = pd.DataFrame({
            "지표": ["현재가", "PER", "그레이엄", "DCF", "PV", "PEG"],
            "값": [yf.Ticker(f"{code}.KS").info.get('currentPrice'), 
                 yf.Ticker(f"{code}.KS").info.get('trailingPE'),
                 round(eps*22.5*4.4/3.5), round(eps*1.5), round(eps/0.08), round(eps*15*0.1*100)]
        })
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(f"재무 분석 ({code})")
        st.table(analysis if 'analysis' in locals() else "데이터 로딩중")
    with col2:
        st.subheader("투자자 매매 현황")
        st.table(get_naver_investor(code))
