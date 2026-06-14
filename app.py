import requests
import json
from datetime import datetime, timedelta

# 본인의 API 키로 직접 교체해서 테스트하세요
KIS_KEY = "본인의_KIS_APP_KEY"
KIS_SECRET = "본인의_KIS_APP_SECRET"

# 모의투자인지 실전투자인지에 따라 URL이 다릅니다.
# 실전투자
BASE_URL = "https://openapi.koreainvestment.com:9443" 
# 모의투자 (모의투자용 KEY라면 아래 주석을 풀고 사용하세요)
# BASE_URL = "https://openapivts.koreainvestment.com:29443"

def test_kis_api():
    print("1. KIS 접근 토큰 발급 요청 중...")
    url = f"{BASE_URL}/oauth2/tokenP"
    body = {"grant_type": "client_credentials", "appkey": KIS_KEY, "appsecret": KIS_SECRET}
    
    res = requests.post(url, data=json.dumps(body), headers={"Content-Type": "application/json"})
    
    if res.status_code != 200:
        print(f"❌ 토큰 발급 실패! 상태코드: {res.status_code}")
        print(f"응답 메시지: {res.text}")
        return
        
    token = res.json().get("access_token")
    print("✅ 토큰 발급 성공!\n")
    
    print("2. 삼성전자(005930) 실시간 현재가 조회 요청 중...")
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": KIS_KEY,
        "appsecret": KIS_SECRET,
        "custtype": "P",
        "tr_id": "FHKST01010100", # 주식현재가 시세
        "Content-Type": "application/json",
    }
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"}
    
    res_price = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price", 
                             headers=headers, params=params)
                             
    print(f"응답 상태코드: {res_price.status_code}")
    print(f"응답 JSON: {json.dumps(res_price.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_kis_api()
