"""
iherb 스포츠 특가 상품 스크래퍼 (iherb/docs/sports_specials_scraping_prompt.md 기반)
- 1페이지부터 마지막 페이지까지 수집
- 수집된 데이터를 iherb/data/sports_specials.csv 로 저장
작성자: Antigravity
"""

import urllib.request
import urllib.parse
import json
import csv
import time
import os

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            # 리스트는 문자열로 변환하여 저장
            if isinstance(v, list):
                v = ", ".join(map(str, v))
            items.append((new_key, v))
    return dict(items)

def run_scraper():
    base_url = "https://catalog.app.iherb.com/category/sports/specials"
    headers = {
        "origin": "https://kr.iherb.com",
        "referer": "https://kr.iherb.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    }

    all_products = []
    page = 1
    page_size = 18

    while True:
        print(f"{page}페이지 수집 중...")
        params = {
            "isMobile": "false",
            "page": str(page),
            "pageSize": str(page_size)
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"{page}페이지 요청 실패: {e}")
            break
            
        products = data.get("products", [])
        if not products:
            print("더 이상 상품이 없습니다. 수집을 종료합니다.")
            break
            
        for p in products:
            all_products.append(flatten_dict(p))
            
        print(f" - {len(products)}개 상품 수집됨.")
        
        if len(products) < page_size:
            print("마지막 페이지에 도달했습니다.")
            break
            
        page += 1
        time.sleep(1)

    if not all_products:
        print("수집된 상품이 없습니다.")
        return

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "sports_specials.csv")
    
    headers_csv = set()
    for p in all_products:
        headers_csv.update(p.keys())
    
    headers_csv = sorted(list(headers_csv))
    
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers_csv)
        writer.writeheader()
        for p in all_products:
            writer.writerow(p)
            
    print(f"총 {len(all_products)}개 상품이 {csv_path} 에 저장되었습니다.")

if __name__ == "__main__":
    run_scraper()
