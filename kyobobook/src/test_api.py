"""
교보문고 베스트셀러 API 응답 구조를 파악하기 위한 테스트 스크립트입니다.
이 스크립트는 API 호출 결과의 첫 번째 데이터를 출력하여 데이터의 계층 구조와 필드를 확인합니다.
"""
import requests
import json

url = "https://store.kyobobook.co.kr/api/gw/best/v2/best-seller/online"
params = {
    "page": 1,
    "per": 50,
    "saleCmdtClstCode": "33",
    "soldOutExcludeYn": "N",
    "saleCmdtDsplDvsnCode": "KOR",
    "period": "002",
    "dsplDvsnCode": "001",
    "dsplTrgtDvsnCode": "004"
}

headers = {
    "host": "store.kyobobook.co.kr",
    "referer": "https://store.kyobobook.co.kr/category/domestic/33/best?page=1&per=50",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "x-api-gw-key": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..i35xkkCOngvXqCRx.0CqToQel6sj5d0qOS2ftoDu37jRwb0vtQwMBd1e_G1ynl7KUrTrH_qPJnygVpkc0tExt4BUX_pJ4RepB5QsxWmKLjC8tEuMELKG8SvRLEVn6ambMnSmDaJ85mLbGtHcM-zFiDBzi.3y1-RnxGHFxeLNMK2dWZoQ"
}

try:
    response = requests.get(url, params=params, headers=headers)
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        best_sellers = data.get("data", {}).get("bestSeller", [])
        print("Total Items:", len(best_sellers))
        if best_sellers:
            first_item = best_sellers[0]
            print("Keys in bestSeller item:", list(first_item.keys()))
            if "product" in first_item:
                print("Keys in product:", list(first_item["product"].keys()))
                print(json.dumps(first_item, indent=2, ensure_ascii=False)[:2000])
    else:
        print("Response Content:", response.text)
except Exception as e:
    print("Error occurred:", e)
