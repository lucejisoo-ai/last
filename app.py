import streamlit as st
import pandas as pd
import dart_fss as dart
import requests
import json
import plotly.express as px

# DART API 설정
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

# 1. 한국투자증권 API 설정 (Secrets 호출)
# 주의: Streamlit Settings > Secrets에 KIS_APP_KEY, KIS_APP_SECRET이 저장되어 있어야 합니다.
try:
    KIS_KEY = st.secrets["KIS_APP_KEY"]
    KIS_SECRET = st.secrets["KIS_APP_SECRET"]
    BASE_URL = "https://openapi.koreainvestment.com:9443"
except Exception:
    st.error("API 키 설정이 없습니다. Secrets를 확인하세요.")
    st.stop()

st.set_page_config(layout="wide", page_title="Professional Stock Analysis")
st.title("📈 KIS 실시간 연동 기업 가치 분석")

# 2. KIS 실시간 현재가 조회 함수
@st.cache_data(ttl=60)
def get_kis_price(ticker):
    token_url = f"{BASE_URL}/oauth2/tokenP"
    body = {"grant_type": "client_credentials", "appkey": KIS_KEY, "appsecret": KIS_SECRET}
    token = requests.post(token_url, data=json.dumps(body)).json()['access_token']
    
    headers = {"authorization": f"Bearer {token}", "appKey": KIS_KEY, "appSecret": KIS_SECRET, "tr_id": "FHKST01010100"}
    params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker}
    
    res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price", headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])

# 3. 관심 종목 리스트 및 검색 관리
if 'watch_list' not in st.session_state: st.session_state.watch_list = []
corp_list = dart.get_corp_list()
all_corps = {c.corp_name: c.corp_code for c in corp_list}

with st.sidebar:
    st.header("종목 관리")
    search = st.selectbox("종목 검색", [""] + list(all_corps.keys()))
    if st.button("추가") and search:
        if len(st.session_state.watch_list) >= 10:
            st.warning("관심 종목은 최대 10개까지 추가 가능합니다.")
        elif search not in st.session_state.watch_list:
            st.session_state.watch_list.append(search)
            st.rerun()

# 4. 데이터 분석 로직
def get_analysis_data(name):
    try:
        corp = corp_list.find_by_corp_name(name)[0]
        fs = corp.extract_fs(bgn_de='20250101')[0]
        net_income = fs.loc['당기순이익(손실)'].iloc[0]
        
        # 한국투자증권 실시간 현재가 연동
        current_price = get_kis_price(corp.ticker)
        
        eps = net_income / 100000000 
        per = current_price / eps if eps != 0 else 0
        
        return {
            "종목": name, "현재가": current_price, "PER": round(per, 2),
            "그레이엄": round(eps * 22.5), "DCF": round(eps * 1.5)
        }
    except Exception:
        return {"종목": name, "현재가": 0, "PER": "에러", "그레이엄": 0, "DCF": 0}

# 5. 테이블 출력 및 삭제 기능
if st.session_state.watch_list:
    results = []
    for idx, name in enumerate(st.session_state.watch_list):
        data = get_analysis_data(name)
        
        # 행별 삭제 버튼 배치
        c1, c2 = st.columns([0.9, 0.1])
        c1.table(pd.DataFrame([data]))
        if c2.button("삭제", key=f"del_{idx}"):
            st.session_state.watch_list.pop(idx)
            st.rerun()

# 6. 시장 투자자 동향 (기존 기능 유지)
st.divider()
st.subheader("시장 투자자 동향")
st.plotly_chart(px.line(pd.DataFrame({'개인': [100, 200, 300], '외국인': [-50, 100, 50]})), use_container_width=True)
