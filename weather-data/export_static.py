"""
정적 데이터 추출 모듈

GitHub Pages 등 정적 웹 호스팅 환경에 배포하기 위해, 
동적 파이썬 백엔드(FastAPI)의 API 응답을 미리 호출하여 정적 JSON 파일로 저장합니다.
"""

import os
import json
import requests
import time

ITEMS = [
    "배추", "무", "양파", "마늘", "대파", "시금치", "상추", 
    "깻잎", "고추", "토마토", "딸기", "수박", "참외", 
    "포도", "감귤", "배", "사과", "감자", "고구마", "당근"
]

BASE_URL = "http://localhost:8000"
API_DIR = os.path.join(os.path.dirname(__file__), "report", "api")

os.makedirs(API_DIR, exist_ok=True)

def export():
    print("Exporting static data for GitHub Pages...")
    
    # 1. Export dashboard initial data (if needed)
    # The dashboard currently calls /api/analyze with item_name
    
    for item in ITEMS:
        try:
            print(f"Fetching data for {item}...")
            url = f"{BASE_URL}/api/data?items={item}"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                file_path = os.path.join(API_DIR, f"data_{item}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                print(f"Failed to fetch {item}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Error fetching {item}: {e}")
            
    print("Static data export completed! You can now deploy the 'report' folder to GitHub Pages.")

if __name__ == "__main__":
    export()
