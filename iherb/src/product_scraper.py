"""
iherb 스포츠 카테고리 상품 스크래퍼 (iherb/docs/sports_product_scraping_prompt.md 기반)
- 1~10페이지까지 수집 후, 각 페이지 데이터를 SQLite DB에 저장
- DB 파일: iherb/data/sports_products.db
- 테이블: products(product_id TEXT, sku TEXT, title TEXT, price TEXT, rating_info TEXT, url TEXT, image_url TEXT)
작성자: Antigravity
"""

import urllib.request
import urllib.parse
import sqlite3
import time
import os
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup 라이브러리가 필요합니다. 설치 중...")
    import subprocess
    # uv 환경에서는 pip 모듈이 기본적으로 없으므로 uv pip install을 사용합니다.
    try:
        subprocess.check_call(["uv", "pip", "install", "beautifulsoup4"])
    except FileNotFoundError:
        print("uv 명령어를 찾을 수 없습니다. 터미널에서 직접 'uv pip install beautifulsoup4'를 실행해 주세요.")
        sys.exit(1)
    from bs4 import BeautifulSoup

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT,
            sku TEXT,
            title TEXT,
            price TEXT,
            rating_info TEXT,
            url TEXT,
            image_url TEXT
        )
    ''')
    conn.commit()
    return conn

def run_scraper():
    base_url = "https://kr.iherb.com/c/sports"
    headers = {
        "priority": "u=1, i",
        "referer": "https://kr.iherb.com/c/sports",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "sports_products.db")
    conn = init_db(db_path)
    cur = conn.cursor()

    max_pages = 10
    total_inserted = 0
    for page in range(1, max_pages + 1):
        print(f"{page}페이지 수집 중...")
        params = {"p": str(page), "isAjax": "true"}
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')
        except Exception as e:
            print(f"{page}페이지 요청 실패: {e}")
            break
        soup = BeautifulSoup(html, 'html.parser')
        products = soup.find_all('div', class_='product')
        if not products:
            print("더 이상 상품이 없습니다. 수집을 종료합니다.")
            break
        page_items = []
        for p in products:
            item = {
                'product_id': p.get('data-product-id', '') or p.get('id', '').replace('pid_', ''),
                'sku': p.find('div', itemprop='sku').get('content', '').strip() if p.find('div', itemprop='sku') else '',
                'title': p.find('a', class_='product-link').get('title', '').strip() if p.find('a', class_='product-link') else '',
                'price': p.find('span', class_='price').text.strip() if p.find('span', class_='price') else '',
                'rating_info': p.find('a', class_='stars').get('title', '').strip() if p.find('a', class_='stars') else '',
                'url': p.find('a', class_='product-link').get('href', '').strip() if p.find('a', class_='product-link') else '',
                'image_url': p.find('img').get('src', '').strip() if p.find('img') else ''
            }
            page_items.append(item)
        print(f" - {len(page_items)}개 상품 수집됨.")
        # DB에 삽입
        cur.executemany('''
            INSERT INTO products (product_id, sku, title, price, rating_info, url, image_url)
            VALUES (:product_id, :sku, :title, :price, :rating_info, :url, :image_url)
        ''', page_items)
        conn.commit()
        total_inserted += len(page_items)
        # 마지막 페이지 확인 (상품 수가 적으면 종료)
        if len(page_items) < 10:
            print("마지막 페이지에 도달했습니다.")
            break
    conn.close()
    print(f"총 {total_inserted}개 상품을 SQLite DB ({db_path})에 저장했습니다.")

if __name__ == "__main__":
    run_scraper()
