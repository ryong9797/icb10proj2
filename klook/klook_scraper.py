"""
Klook 검색 결과를 스크래핑하여 SQLite 데이터베이스에 저장하는 스크립트입니다.
지정된 프롬프트를 바탕으로 API에 요청을 보내고, 1페이지부터 10페이지까지의
결과를 'klook_data.db' 파일에 저장합니다.
"""

import requests
import json
import sqlite3
import time
import os

def setup_database(db_path):
    """SQLite 데이터베이스 및 테이블을 생성합니다."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS klook_search_results')
    cursor.execute('''
        CREATE TABLE klook_search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page INTEGER,
            item_index INTEGER,
            raw_data TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def scrape_klook_pages(conn):
    """Klook API에서 1~10페이지의 데이터를 수집하여 데이터베이스에 저장합니다."""
    url = "https://www.klook.com/v1/cardinfocenterservicesrv/search/platform/complete_search_v3"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-klook-market": "global",
        "x-platform": "desktop",
        "x-requested-with": "XMLHttpRequest"
    }

    cursor = conn.cursor()
    
    # 1페이지부터 10페이지까지 전체 수집
    for page in range(1, 11):
        # API의 start 파라미터가 offset이 아닌 실제 페이지 번호를 의미하는 것으로 추정하여
        # start 값에 페이지 번호를 그대로 사용합니다.
        start_val = page
        
        params = {
            "location": "158,157,156,25723,5031,8928",
            "sort": "most_relevant",
            "tab_key": "0",
            "start": str(start_val), 
            "query": "대한민국",
            "size": "15",
            "search_scope": "main_search",
            "k_lang": "ko_KR",
            "k_currency": "KRW"
        }

        print(f"{page}페이지 (start={start_val}) 수집 중...")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            cards = data.get("result", {}).get("search_result", {}).get("cards", [])
            if not cards:
                print(f"{page}페이지에 더 이상 결과가 없습니다.")
                break
                
            for idx, card in enumerate(cards):
                # JSON 형태로 직렬화하여 저장
                raw_data_str = json.dumps(card, ensure_ascii=False)
                cursor.execute('''
                    INSERT INTO klook_search_results (page, item_index, raw_data)
                    VALUES (?, ?, ?)
                ''', (page, idx + 1, raw_data_str))
                
            conn.commit()
            print(f"{page}페이지 수집 완료: {len(cards)}개 아이템 저장")
            
        except requests.exceptions.RequestException as e:
            print(f"{page}페이지 수집 중 오류 발생: {e}")
            break
            
        # 서버 부하를 방지하기 위해 잠시 대기
        time.sleep(1)

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "klook_data.db")
    print(f"데이터베이스 파일: {db_file}")
    
    connection = setup_database(db_file)
    try:
        scrape_klook_pages(connection)
    finally:
        connection.close()
    
    print("스크래핑 작업이 완료되었습니다.")
