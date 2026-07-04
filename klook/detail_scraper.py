"""
Klook 상세 페이지 403 Forbidden(Cloudflare 봇 탐지) 우회를 위해
여러 가지 브라우저 지문과 검색엔진 봇 User-Agent를 번갈아가며 테스트하여 뚫는 스크립트입니다.
"""

import sqlite3
import os
import re
import time
import requests as std_requests

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

def get_html_with_bypass(url):
    """여러 가지 우회 전략을 순차적으로 시도하여 HTML을 가져옵니다."""
    strategies = [
        # 1. Googlebot 위장 (가장 흔하게 웹방화벽을 통과하는 검색엔진 봇 방식)
        {
            "type": "std",
            "headers": {
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        },
        # 2. Bingbot 위장
        {
            "type": "std",
            "headers": {
                "User-Agent": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        },
        # 3. curl_cffi chrome116 버전 위장
        {
            "type": "cffi",
            "impersonate": "chrome116"
        },
        # 4. curl_cffi safari15_5 버전 위장
        {
            "type": "cffi",
            "impersonate": "safari15_5"
        },
        # 5. 아이폰(모바일) 위장
        {
            "type": "std",
            "headers": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9"
            }
        }
    ]
    
    last_error = None
    for i, strategy in enumerate(strategies):
        try:
            if strategy["type"] == "std":
                resp = std_requests.get(url, headers=strategy["headers"], timeout=15)
                if resp.status_code == 200:
                    print(f"      - 전략 {i+1} 성공!")
                    return resp.text
                last_error = f"HTTP {resp.status_code}"
            elif strategy["type"] == "cffi" and cffi_requests:
                resp = cffi_requests.get(url, impersonate=strategy["impersonate"], timeout=15)
                if resp.status_code == 200:
                    print(f"      - 전략 {i+1} 성공!")
                    return resp.text
                last_error = f"HTTP {resp.status_code}"
        except Exception as e:
            last_error = str(e)
            
        # 차단 당했을 경우 잠시 대기 후 다음 전략 시도
        time.sleep(1)
        
    raise Exception(f"모든 우회 전략 실패 (최근 에러: {last_error})")

def extract_meta_content(html, property_name):
    # 정규표현식으로 SEO 메타 태그의 content 추출
    pattern1 = re.compile(rf'<meta[^>]*property=[\'"]{property_name}[\'"][^>]*content=[\'"]([^\'"]*)[\'"]', re.IGNORECASE)
    pattern2 = re.compile(rf'<meta[^>]*name=[\'"]{property_name}[\'"][^>]*content=[\'"]([^\'"]*)[\'"]', re.IGNORECASE)
    pattern3 = re.compile(rf'<meta[^>]*content=[\'"]([^\'"]*)[\'"][^>]*property=[\'"]{property_name}[\'"]', re.IGNORECASE)
    
    for pat in [pattern1, pattern2, pattern3]:
        match = pat.search(html)
        if match:
            return match.group(1)
    return None

def setup_detail_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS klook_product_details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            url TEXT,
            page_title TEXT,
            meta_description TEXT,
            meta_image TEXT,
            raw_html TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES parsed_klook_data (id)
        )
    ''')

def scrape_top_10_details(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    setup_detail_table(cursor)
    
    cursor.execute('''
        SELECT id, deep_link 
        FROM parsed_klook_data 
        WHERE deep_link IS NOT NULL AND deep_link != ''
        ORDER BY id ASC
        LIMIT 10
    ''')
    products = cursor.fetchall()
    
    if not products:
        print("수집할 deep_link가 없습니다.")
        conn.close()
        return

    print(f"상위 {len(products)}개의 상품 상세 페이지 수집을 시작합니다. (우회 자동 전환 모드)")

    for product_id, deep_link in products:
        if deep_link.startswith('/'):
            url = f"https://www.klook.com{deep_link}"
        elif not deep_link.startswith('http'):
            url = f"https://www.klook.com/{deep_link}"
        else:
            url = deep_link
            
        print(f"\n[{product_id}] 수집 중: {url}")
        
        try:
            raw_html = get_html_with_bypass(url)
            
            # 페이지 타이틀
            title_match = re.search(r'<title>(.*?)</title>', raw_html, re.IGNORECASE | re.DOTALL)
            page_title = title_match.group(1).strip() if title_match else ""
            
            # 메타 디스크립션
            meta_desc = extract_meta_content(raw_html, "description") or extract_meta_content(raw_html, "og:description")
                
            # 메타 이미지
            meta_img = extract_meta_content(raw_html, "og:image")
            
            cursor.execute('''
                INSERT INTO klook_product_details (product_id, url, page_title, meta_description, meta_image, raw_html)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (product_id, url, page_title, meta_desc, meta_img, raw_html))
            conn.commit()
            
            print(f" -> 최종 성공: {page_title[:40]}...")
            
        except Exception as e:
            print(f" -> 최종 실패: {e}")
            
        # 봇 차단 방지를 위해 랜덤 딜레이
        time.sleep(2)
        
    conn.close()
    print("\n상세 페이지 수집이 완료되었습니다.")

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "data", "klook_data.db")
    if not os.path.exists(db_file):
        print(f"DB 파일을 찾을 수 없습니다: {db_file}")
    else:
        scrape_top_10_details(db_file)
