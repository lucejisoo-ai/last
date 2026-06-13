import streamlit as st
import requests
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="한국 주식 분석", layout="wide")

# 사람처럼 보이게 하는 헤더 추가
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finance.naver.com/"
}

@st.cache_data(ttl=30)
def get_stock_data(code):
    url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        return None
    return None

st.title("📈 한국 주식 분석")

# 테스트할 종목들
stock_codes = ['005930', '000660'] 
data_list = []

for code in stock_codes:
    data = get_stock_data(code)
    if data and 'result' in data:
        item = data['result']['areas'][0]['datas'][0]
        data_list.append({
            "종목": item['nm'],
            "현재가": item['nv'],
            "등락률": f"{item['cr']}%"
        })

if data_list:
    df = pd.DataFrame(data_list)
    st.table(df)
else:
    st.error("데이터를 가져오는 데 실패했습니다. 잠시 후 새로고침(Rerun) 해주세요.")

st.write("실시간 데이터가 로딩되었습니다.")
