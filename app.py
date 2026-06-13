import streamlit as st
import yfinance as yf
import pandas as pd
import dart_fss as dart
import requests
from bs4 import BeautifulSoup
import plotly.express as px

# DART 설정
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

st.set_page_config(layout="wide", page_title="Professional Stock Analysis")

# --- 1. 상단 지수 카드 ---
st.title("📈 기업 가치 분석 대시보드")
c1, c2 = st.columns(2)
kospi = yf.Ticker("^KS11").history(period="1d")['Close'].iloc[-1]
kosdaq = yf.Ticker("^KQ11").history(period="1d")['Close'].iloc[-1]
c1.metric("KOSPI", f"{kospi:,.2f}")
c2.metric("KOSDAQ", f"{kosdaq:,.2f}")

# --- 2. 관심 종목 관리 ---
if 'watch_list' not in st.session_state: st.session_state.watch_list = []
corp_list = dart.get_corp_list()
all_corps = {c.corp_name: c.corp_code for c in corp_list}

with st.sidebar:
    search = st.selectbox("종목 검색", [""] + list(all_corps.keys()))
    if st.button("추가") and search and len(st.session_state.watch_list) < 10:
        if search not in st.session_state.watch_list:
            st.session_state.watch_list.append(search)
            st.rerun()

# --- 3. 종목별 가치 분석 테이블 ---
if st.session_state.watch_list:
    for idx, name in enumerate(st.session_state.watch_list):
        c_left, c_right = st.columns([0.9, 0.1])
        # (간이 계산 로직 - 실제 EPS는 DART에서 가져오도록 확장 가능)
        eps = 2500 # 예시값
        data = {"종목": name, "PER": 15.2, "그레이엄": round(eps*22.5*4.4/3.5), "DCF": round(eps*1.5)}
        c_left.table(pd.DataFrame([data]))
        if c_right.button("❌", key=f"del_{idx}"):
            st.session_state.watch_list.pop(idx)
            st.rerun()

# --- 4. 하단 시장 수급 현황 (네이버 크롤링) ---
st.divider()
st.subheader("시장 수급 동향 (개인/외인/기관 상위 종목)")

def get_market_rank():
    # 네이버 금융에서 수급 상위 종목 데이터를 가져오는 예시 URL
    url = "https://finance.naver.com/sise/sise_quant.naver" # 거래량 상위 등
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    return pd.read_html(res.text)[1].dropna().head(5)

col1, col2 = st.columns(2)
with col1:
    st.write("매수 상위 종목 5")
    st.table(get_market_rank())
with col2:
    st.write("매도 상위 종목 5")
    st.table(get_market_rank())

# 5. 수급 추이 그래프 (Plotly)
st.subheader("최근 1주일 투자자 매매 추이")
chart_data = pd.DataFrame({'개인': [100, 200, 150, 300, 250, 400, 350], 
                           '외국인': [-50, -100, 20, 100, 50, -20, 30], 
                           '기관': [20, 50, -30, 80, 100, 120, 90]})
fig = px.line(chart_data)
st.plotly_chart(fig, use_container_width=True)
