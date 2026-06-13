import streamlit as st
import dart_fss as dart
import pandas as pd

# DART API 키 설정 (본인의 키를 넣으세요!)
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

st.title("📊 DART 기반 기업 가치 분석")

# 1. 기업 찾기
corp_name = st.text_input("분석할 기업명을 입력하세요 (예: 삼성전자)")
if st.button("데이터 분석"):
    corp = dart.get_corp_list().find_by_corp_name(corp_name, exactly=True)[0]
    
    # 2. 가장 최근 사업보고서 재무제표 로드
    fs = corp.extract_fs(bgn_de='20250101') 
    df = fs[0] # 연결재무제표
    
    # 3. 데이터 추출 (예시: 당기순이익)
    # DART 데이터는 '당기순이익' 등을 추출하여 계산식에 적용
    st.write(df)
    st.success("데이터 로딩 완료!")

# 적정주가 계산식 로직은 여기에 DART에서 가져온 값을 변수로 넣으면 됩니다.
