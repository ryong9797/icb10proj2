"""
YES24 베스트셀러 데이터를 스크래핑하여 CSV 파일로 저장하는 스크립트입니다.
지정된 HTTP 요청 정보를 바탕으로 42페이지에 달하는 전체 베스트셀러 도서 데이터를 루프하며 수집하고,
서버 부하를 막기 위해 요청당 1초의 딜레이를 부여합니다.
"""
import os
import csv
import time
import requests
from bs4 import BeautifulSoup

def scrape_yes24_bestsellers():
    url = "https://www.yes24.com/product/category/BestSellerContents"
    parsed_books = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    total_pages = 42
    print(f"YES24 베스트셀러 IT/모바일 카테고리 전체 {total_pages}페이지 수집 시작...")
    
    for page in range(1, total_pages + 1):
        params = {
            "categoryNumber": "001001003",
            "sumGb": "06",
            "sex": "A",
            "age": "255",
            "goodsTp": "0",
            "addOptionTp": "0",
            "excludeTp": "2",
            "pageNumber": str(page),
            "pageSize": "24",
            "goodsStatGb": "06",
            "eBookTp": "0",
            "bestType": "YES24_BESTSELLER",
            "type": "",
            "saleYear": "0",
            "saleMonth": "0",
            "weekNo": "0",
            "saleDts": "",
            "viewMode": "",
            "freeYn": ""
        }
        
        print(f"[{page}/{total_pages}] 페이지 수집 중 (주소: {url}?pageNumber={page})...")
        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"  [오류] {page}페이지 HTTP 상태 코드 {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select("div.itemUnit")
            
            if not items:
                print(f"  [경고] {page}페이지에서 도서 데이터를 찾을 수 없습니다. (HTML 구조 또는 세션 만료 확인 필요)")
                continue
                
            for idx, item in enumerate(items, 1):
                # 순위 추출
                rank_elem = item.select_one("div.item_img em.rank")
                rank = rank_elem.text.strip() if rank_elem else str((page - 1) * 24 + idx)
                
                # 도서명 추출
                title_elem = item.select_one("div.info_name a.gd_name")
                title = title_elem.text.strip() if title_elem else ""
                
                # 도서 링크 및 ID 추출
                book_id = ""
                if title_elem and "href" in title_elem.attrs:
                    href = title_elem.attrs["href"]
                    book_id = href.split("/")[-1] if "/" in href else ""
                
                # 부제 추출
                subtitle_elem = item.select_one("div.info_name span.gd_nameE")
                subtitle = subtitle_elem.text.strip() if subtitle_elem else ""
                
                # 저자 추출
                author_elem = item.select_one("span.info_auth a")
                author = author_elem.text.strip() if author_elem else ""
                
                # 출판사 추출
                pub_elem = item.select_one("span.info_pub a")
                publisher = pub_elem.text.strip() if pub_elem else ""
                
                # 출간일 추출
                date_elem = item.select_one("span.info_date")
                pub_date = date_elem.text.strip() if date_elem else ""
                
                # 판매가 추출
                price_elem = item.select_one("div.info_price strong.txt_num em.yes_b")
                sale_price = price_elem.text.strip().replace(",", "") if price_elem else ""
                
                # 정가 추출
                original_price_elem = item.select_one("div.info_price span.dash em.yes_m")
                original_price = original_price_elem.text.strip().replace(",", "") if original_price_elem else ""
                
                # 할인율 추출
                discount_elem = item.select_one("div.info_price span.txt_sale em.num")
                discount_rate = discount_elem.text.strip() if discount_elem else ""
                
                # 판매지수 추출
                sale_num_elem = item.select_one("div.info_rating span.saleNum")
                sale_index = ""
                if sale_num_elem:
                    sale_index = sale_num_elem.text.replace("판매지수", "").strip().replace(",", "")
                    
                # 평점 추출
                rating_elem = item.select_one("div.info_rating span.rating_grade em.yes_b")
                rating = rating_elem.text.strip() if rating_elem else ""
                
                # 리뷰 건수 추출
                review_elem = item.select_one("div.info_rating span.rating_rvCount em.txC_blue")
                review_count = review_elem.text.strip().replace(",", "") if review_elem else "0"
                
                book_info = {
                    "rank": rank,
                    "book_id": book_id,
                    "title": title,
                    "subtitle": subtitle,
                    "author": author,
                    "publisher": publisher,
                    "pub_date": pub_date,
                    "original_price": original_price,
                    "sale_price": sale_price,
                    "discount_rate": discount_rate,
                    "sale_index": sale_index,
                    "rating": rating,
                    "review_count": review_count
                }
                parsed_books.append(book_info)
                
            print(f"  -> {page}페이지 완료 (현재 누적 수집 도서: {len(parsed_books)}권)")
            
        except Exception as e:
            print(f"  [에러] {page}페이지 수집 중 오류 발생: {e}")
            continue
            
        # 서버 부하 방지를 위한 딜레이 추가 (1초)
        time.sleep(1)

    # 3. CSV 파일로 저장
    output_dir = os.path.join("yes24", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "yes24_bestsellers.csv")
    
    # CSV 헤더 설정
    headers = [
        "rank", "book_id", "title", "subtitle", "author", "publisher", 
        "pub_date", "original_price", "sale_price", "discount_rate", 
        "sale_index", "rating", "review_count"
    ]
    
    try:
        # Excel 한글 깨짐 방지를 위해 utf-8-sig 인코딩 사용
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(parsed_books)
        print(f"\n성공적으로 전체 데이터를 수집하고 저장했습니다: {output_file} (총 {len(parsed_books)}권)")
    except Exception as e:
        print(f"CSV 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    scrape_yes24_bestsellers()
