import streamlit as st
import pandas as pd
import dart_fss as dart
import plotly.express as px

# DART API 설정
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

st.set_page_config(layout="wide", page_title="DART Professional Analysis")

st.title("김지수의 주식 연구소")

# 1. 종목 리스트 초기화 및 검색
if 'watch_list' not in st.session_state: st.session_state.watch_list = []
corp_list = dart.get_corp_list()
all_corps = {c.corp_name: c.corp_code for c in corp_list}

with st.sidebar:
    search = st.selectbox("종목 검색", [""] + list(all_corps.keys()))
    if st.button("추가") and search:
        if search not in st.session_state.watch_list:
            st.session_state.watch_list.append(search)
            st.rerun()

# 2. DART 통합 분석 로직
def get_dart_data(name):
    try:
        corp = corp_list.find_by_corp_name(name)[0]
        # 재무제표 추출
        fs = corp.extract_fs(bgn_de='20250101')[0]
        # 당기순이익
        net_income = fs.loc['당기순이익(손실)'].iloc[0]
        # DART 실시간 주가 (extract_price 사용)
        price_df = corp.extract_price(bgn_de='20260601') 
        current_price = price_df['종가'].iloc[-1]
        
        # 주식 수(지분율 기준 등)는 DART에서 매핑 필요하지만 예시값 사용
        eps = net_income / 100000000 
        per = current_price / eps if eps != 0 else 0
        
        return {
            "종목": name, "현재가": round(current_price), "PER": round(per, 2),
            "그레이엄": round(eps * 22.5), "DCF": round(eps * 1.5)
        }
    except:
        return {"종목": name, "현재가": 0, "PER": "계산불가", "그레이엄": 0, "DCF": 0}

# 3. 테이블 및 분석 화면
if st.session_state.watch_list:
    results = [get_dart_data(name) for name in st.session_state.watch_list]
    st.table(pd.DataFrame(results))

# 4. 수급 및 차트 (기존 기능 유지)
st.divider()
st.subheader("시장 투자자 동향")
chart_data = pd.DataFrame({'개인': [100, 200, 150, 300, 250, 400, 350], '외국인': [-50, -100, 20, 100, 50, -20, 30]})
st.plotly_chart(px.line(chart_data), use_container_width=True)
