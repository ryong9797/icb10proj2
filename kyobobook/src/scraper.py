"""
교보문고 종합 베스트셀러 1위 ~ 1000위 도서 데이터를 스크래핑하는 스크립트입니다.
Playwright를 이용해 교보문고 주간 베스트셀러 페이지를 순회하며 
도서명, 저자, 출판사, 가격, 출간일, 평점, 리뷰수 등의 정보를 수집하여
kyobobook_bestseller.csv 파일로 저장합니다.
"""
import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright

def run():
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for page_num in range(1, 11):
            url = f"https://store.kyobobook.co.kr/bestseller/total/weekly?page={page_num}&per=100"
            print(f"[{page_num}/10] 데이터 수집 중: {url}")
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"페이지 로딩 실패: {e}")
                continue
                
            # 데이터 로드를 위한 대기 (10초 타임아웃)
            try:
                page.wait_for_selector(".prod_item", timeout=10000)
            except Exception as e:
                print(f"[{page_num}/10] 대기 시간 초과 또는 항목 없음: {e}")
                continue
            
            # 스크롤을 끝까지 내려 모든 이미지/정보 지연 로드 처리
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            items = page.locator(".prod_item")
            count = items.count()
            
            for i in range(count):
                item = items.nth(i)
                
                # 순위
                rank = (page_num - 1) * 100 + i + 1
                
                # 도서명
                try:
                    title = item.locator(".prod_name").inner_text().strip()
                except:
                    title = ""
                
                # 저자/출판사/출간일
                try:
                    author_area = item.locator(".prod_author").inner_text().strip()
                    parts = [part.strip() for part in author_area.split("·")]
                    if len(parts) >= 3:
                        author = parts[0]
                        publisher = parts[1]
                        pub_date = parts[2].replace(".", "-")
                    elif len(parts) == 2:
                        author = parts[0]
                        publisher = parts[1]
                        pub_date = ""
                    else:
                        author = parts[0]
                        publisher = ""
                        pub_date = ""
                except:
                    author = ""
                    publisher = ""
                    pub_date = ""
                    
                # 가격
                try:
                    price_str = item.locator(".price .val").first.inner_text().strip()
                    price = int(price_str.replace(",", ""))
                except:
                    price = 0
                    
                # 평점
                try:
                    rating_str = item.locator(".review_klover .text").first.inner_text().strip()
                    rating = float(rating_str)
                except:
                    rating = 0.0
                    
                # 리뷰수
                try:
                    review_count_str = item.locator(".review_klover .review_quotes").first.inner_text().strip()
                    review_count = int(review_count_str.replace("(", "").replace(")", "").replace(",", ""))
                except:
                    review_count = 0
                
                results.append({
                    "순위": rank,
                    "도서명": title,
                    "저자": author,
                    "출판사": publisher,
                    "가격": price,
                    "출간일": pub_date,
                    "평점": rating,
                    "리뷰수": review_count
                })
                
            time.sleep(1) # 차단 방지를 위한 휴식
            
        browser.close()
        
    df = pd.DataFrame(results)
    
    # 데이터 폴더 확인 및 파일 저장
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    csv_path = os.path.join(data_dir, "kyobobook_bestseller.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n총 {len(df)}권의 데이터 수집 완료. '{csv_path}' 파일에 저장했습니다.")

if __name__ == "__main__":
    run()
