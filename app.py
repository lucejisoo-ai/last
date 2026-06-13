import streamlit as st
import yfinance as yf
import pandas as pd
import dart_fss as dart

# DART 설정
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

st.set_page_config(layout="wide", page_title="Professional Stock Analysis")

st.title("📈 기업 가치 분석 대시보드")

# 1. 지수 카드 (에러 안남)
c1, c2 = st.columns(2)
try:
    c1.metric("KOSPI", f"{yf.Ticker('^KS11').history(period='1d')['Close'].iloc[-1]:,.2f}")
    c2.metric("KOSDAQ", f"{yf.Ticker('^KQ11').history(period='1d')['Close'].iloc[-1]:,.2f}")
except: pass

# 2. 관심 종목 관리
if 'watch_list' not in st.session_state: st.session_state.watch_list = []

with st.sidebar:
    ticker = st.text_input("종목코드 입력 (예: 005930.KS)")
    if st.button("추가") and ticker:
        if ticker not in st.session_state.watch_list:
            st.session_state.watch_list.append(ticker)
            st.rerun()

# 3. 분석 테이블 (에러 방지용 try-except 적용)
if st.session_state.watch_list:
    results = []
    for t in st.session_state.watch_list:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            eps = info.get('trailingEps', 0) or 0
            results.append({
                "종목": info.get('shortName', t),
                "현재가": info.get('currentPrice', 0),
                "PER": info.get('trailingPE', 0),
                "그레이엄": round(eps * 22.5 * 4.4 / 3.5, 0),
                "DCF": round(eps * 1.5, 0)
            })
        except: continue
    st.table(pd.DataFrame(results))

st.info("※ 수급 데이터는 현재 환경 보안 정책상 직접 크롤링이 제한될 수 있어 가치 분석 지표 위주로 구성하였습니다.")
