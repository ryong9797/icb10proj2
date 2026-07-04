"""
Klook 검색 결과를 전체 페이지 수집하여 CSV 파일로 저장하는 스크립트입니다.
지정된 HTTP 헤더와 요청 URL을 사용하여 제품의 상세 데이터(data)를 수집합니다.
페이징 처리를 위해 start 파라미터를 동적으로 변경합니다.
작성일: 2026-06-24
"""
import requests
import json
import csv
import os
import time

def scrape_klook_all():
    base_url = "https://www.klook.com/v1/cardinfocenterservicesrv/search/platform/complete_search_v3"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.klook.com/ko/search/result/?query=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD&search_scope=main_search&location=158,157,156,25723,5031,8928&sort=most_relevant&tab_key=0&start=1",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-klook-channel-level-one": "SEM",
        "x-klook-host": "www.klook.com",
        "x-klook-market": "global",
        "x-klook-traffic-channel": "google_sem",
        "x-klook-user-residence": "10_KR",
        "x-platform": "desktop",
        "x-requested-with": "XMLHttpRequest"
    }

    extracted_data = []
    # Klook API에서는 보통 start가 페이지 번호를 의미합니다.
    start = 1
    size = 15
    total_items = None
    
    while True:
        params = {
            "location": "158,157,156,25723,5031,8928",
            "sort": "most_relevant",
            "tab_key": "0",
            "start": start,
            "query": "대한민국",
            "size": size,
            "search_scope": "main_search",
            "k_lang": "ko_KR",
            "k_currency": "KRW"
        }
        
        print(f"Fetching page {start}...")
        
        try:
            response = requests.get(base_url, headers=headers, params=params)
        except Exception as e:
            print(f"Error fetching data at page {start}: {e}")
            break
            
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            break
            
        data = response.json()
        search_result = data.get("result", {}).get("search_result", {})
        cards = search_result.get("cards", [])
        
        if total_items is None:
            total_items = search_result.get("total", 0)
            print(f"Total items available: {total_items}")
            
        if not cards:
            print("No more cards found.")
            break
            
        for card in cards:
            card_data = card.get("data", {})
            if card_data:
                extracted_data.append(card_data)
                
        print(f" -> Collected {len(cards)} items (Total collected: {len(extracted_data)})")
                
        if len(cards) < size:
            print("Reached the last page.")
            break
            
        if total_items and len(extracted_data) >= total_items:
            print("Collected all available items.")
            break
            
        # 다음 페이지로 이동
        start += 1
        
        # 서버 부하를 줄이기 위해 1초 대기
        time.sleep(1)

    if not extracted_data:
        print("No data extracted.")
        return
        
    all_keys = set()
    for item in extracted_data:
        all_keys.update(item.keys())
        
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "klook_products.csv")
    csv_path = os.path.abspath(csv_path)
    
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(all_keys))
        writer.writeheader()
        for item in extracted_data:
            row = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in item.items()}
            writer.writerow(row)
            
    print(f"Successfully saved {len(extracted_data)} items to {csv_path}")

if __name__ == "__main__":
    scrape_klook_all()
