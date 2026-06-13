import streamlit as st
import pandas as pd
import dart_fss as dart
import requests
import json
import plotly.express as px

# DART 및 KIS API 설정
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

# 한국투자증권 API 설정 (Secrets에서 불러오기)
KIS_KEY = st.secrets["PSEFbh2guyzQoryCO1GpnaHAEzCphPjk2pvx"]
KIS_SECRET = st.secrets["4BEmQ+aBwwe62bFlZBMnVRbRGcsMqq6GaOnFFb+xLS4ZRWGqCFnhVxYUXPeUnUDZkyPuvB9hXCnP1ijw4j4bd6bGzvGWCvNQcwvG0Taju6M0XE7tr2XD00WKvwjN5s9DHsvolRkGJYriOYSz5nnNIzMD0zUC3XhSe/qUOFuWqQN4j8hqtRM="]
BASE_URL = "https://openapi.koreainvestment.com:9443"

st.set_page_config(layout="wide", page_title="Professional Stock Analysis")
st.title("📈 KIS 실시간 연동 기업 가치 분석")

# 1. KIS 실시간 현재가 조회 함수
@st.cache_data(ttl=60) # 1분마다 캐시 갱신
def get_kis_price(ticker):
    # 1. 토큰 발급
    token_url = f"{BASE_URL}/oauth2/tokenP"
    body = {"grant_type": "client_credentials", "appkey": KIS_KEY, "appsecret": KIS_SECRET}
    token = requests.post(token_url, data=json.dumps(body)).json()['access_token']
    
    # 2. 실시간 시세 조회
    price_url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {"authorization": f"Bearer {token}", "appKey": KIS_KEY, "appSecret": KIS_SECRET, "tr_id": "FHKST01010100"}
    params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker}
    
    res = requests.get(price_url, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])

# 2. 종목 리스트 관리
if 'watch_list' not in st.session_state: st.session_state.watch_list = []
corp_list = dart.get_corp_list()
all_corps = {c.corp_name: c.corp_code for c in corp_list}

with st.sidebar:
    search = st.selectbox("종목 검색", [""] + list(all_corps.keys()))
    if st.button("추가") and search:
        if search not in st.session_state.watch_list:
            st.session_state.watch_list.append(search)
            st.rerun()

# 3. 데이터 분석 로직
def get_analysis_data(name):
    try:
        corp = corp_list.find_by_corp_name(name)[0]
        fs = corp.extract_fs(bgn_de='20250101')[0]
        net_income = fs.loc['당기순이익(손실)'].iloc[0]
        
        # 한국투자증권 실시간 현재가 연동 (ticker 활용)
        current_price = get_kis_price(corp.ticker)
        
        eps = net_income / 100000000 
        per = current_price / eps if eps != 0 else 0
        
        return {
            "종목": name, "현재가": current_price, "PER": round(per, 2),
            "그레이엄": round(eps * 22.5), "DCF": round(eps * 1.5)
        }
    except Exception as e:
        return {"종목": name, "현재가": 0, "PER": "에러", "그레이엄": 0, "DCF": 0}

# 4. 화면 출력
if st.session_state.watch_list:
    results = [get_analysis_data(name) for name in st.session_state.watch_list]
    st.table(pd.DataFrame(results))

# 5. 수급 차트
st.divider()
st.subheader("시장 투자자 동향")
st.plotly_chart(px.line(pd.DataFrame({'개인': [100, 200, 300], '외국인': [-50, 100, 50]})), use_container_width=True)
