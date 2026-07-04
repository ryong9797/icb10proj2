"""
Trip.com API 호텔 리뷰 수집 및 CSV 저장 스크립트

이 스크립트는 `scraping_prompt.md`에 명시된 Trip.com 내부 API(getHotelCommentInfo)에
직접 POST 요청을 전송하여, 페이지 렌더링 없이 구조화된 리뷰 데이터를 수집합니다.
브라우저와 동일한 HTTP 헤더(User-Agent, sec-ch-ua 등)를 사용하여 차단을 우회하며,
첫 페이지 수집 확인 후 전체 리뷰를 순회하여 지정된 CSV 파일(`reviews.csv`)에 안전하게 저장합니다.
"""

import json
import csv
import sys
import time
import os
import urllib.request
import urllib.error

# API 엔드포인트
API_URL = "https://kr.trip.com/restapi/soa2/34308/getHotelCommentInfo"

# 실제 브라우저 요청과 동일한 헤더 설정
HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "sec-ch-ua": "\"Google Chrome\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "w-payload-source": "1.0.9@102!Nudtz1KLhCAbOX4SO6An9PKnG2KLOSqZOlbn+6FaG6OaKSbpKET2OSVbOrK2+ET5+rApbbbpOSknKr42+rG2KlqIbEVbKtb5+rbSOEb2KE4p+rKpOr4nKrq/K5bpOSqL+rk/OSKZKrVpQlVROShDKFO3GVd3hbb=",
    "x-ctx-country": "KR",
    "x-ctx-currency": "KRW",
    "x-ctx-locale": "ko-KR",
    "x-ctx-ubt-pageid": "10320668147",
    "x-ctx-ubt-pvid": "7",
    "x-ctx-ubt-sid": "9",
    "x-ctx-ubt-vid": "1754985737191.9877n1SlbHlt",
    "x-ctx-user-recognize": "NON_EU",
    "x-ctx-wclient-req": "0af33fe7acb74bcfe9f82cf404544b46"
}

# 데이터베이스(CSV) 저장 경로
CSV_PATH = "C:/Users/admin/Desktop/icb10proj2/trip_com/data/reviews.csv"

def init_csv():
    """CSV 파일을 초기화하고 헤더(컬럼명)를 작성합니다."""
    # 상위 폴더가 없다면 생성
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['제목', '내용', '별점'])

def append_to_csv(reviews):
    """리뷰 데이터를 CSV 파일에 추가합니다."""
    with open(CSV_PATH, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        for r in reviews:
            writer.writerow([r['title'], r['content'], r['rating']])

def fetch_reviews(page_index):
    """지정된 페이지(page_index)의 호텔 리뷰 데이터를 API로 요청합니다."""
    payload = {
        "hotelId": 58635410,
        "commentFilterOptions": {
            "pageIndex": page_index,
            "pageSize": 10,
            "repeatComment": 1
        },
        "sceneTypes": ["CommentList"],
        "head": {
            "platform": "PC",
            "cver": "0",
            "cid": "1754985737191.9877n1SlbHlt",
            "bu": "IBU",
            "group": "trip",
            "locale": "ko-KR",
            "timezone": "9",
            "currency": "KRW",
            "pageId": "10320668147",
            "vid": "1754985737191.9877n1SlbHlt",
            "isSSR": False
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, headers=HEADERS, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.URLError as e:
        print(f"[오류] API 요청 실패 (페이지 {page_index}): {e}")
        return None

def extract_review_info(api_response):
    """API JSON 응답에서 제목, 내용, 별점 정보를 추출하여 리스트로 반환합니다."""
    reviews = []
    if not api_response:
        return reviews
        
    try:
        # Trip.com API 응답 구조: data -> commentTagList, 또는 commentList
        data = api_response.get('data', {})
        comment_list = data.get('commentList') or data.get('comments') or data.get('commentTagList') or []
        
        if not isinstance(comment_list, list):
            comment_list = []
            
        for item in comment_list:
            title = item.get('title', '')
            content = item.get('content', '')
            rating = str(item.get('rating', '')) or str(item.get('score', ''))
            
            # 본문이나 제목이 있는 경우만 수집 대상으로 간주
            if content or title:
                reviews.append({
                    "title": title.strip(),
                    "content": content.strip(),
                    "rating": rating.strip()
                })
    except Exception as e:
        print(f"[오류] 데이터 파싱 중 문제 발생: {e}")
        
    return reviews

def main():
    print("Trip.com API 리뷰 수집을 시작합니다 (CSV 저장 모드)...")
    init_csv()
    
    # 1. 첫 페이지 테스트 요청
    print("첫 페이지 데이터를 요청하는 중입니다...")
    res = fetch_reviews(1)
    
    if not res:
        print("첫 페이지 요청에 실패했습니다. 종료합니다.")
        return
        
    reviews = extract_review_info(res)
    if not reviews:
        print("정상적인 API 응답을 받았으나, 리뷰 데이터를 찾지 못했습니다.")
        return
        
    print(f"\n--- 첫 페이지 수집 확인 ({len(reviews)}건) ---")
    for idx, r in enumerate(reviews[:3]):
        print(f"\n[리뷰 {idx+1}]")
        print(f"별점: {r['rating']}")
        print(f"제목: {r['title']}")
        print(f"내용: {r['content'][:100]}...")
        
    # 2. 전체 페이지 수집 계속 여부 확인 (대화형 또는 인자 처리)
    auto_yes = '--auto-yes' in sys.argv
    if auto_yes:
        print("\n[Auto-yes] 자동으로 전체 리뷰 수집 및 CSV 저장을 진행합니다.")
        user_input = 'y'
    else:
        user_input = input("\n위와 같이 첫 페이지 리뷰가 정상적으로 수집되었습니다. 전체 리뷰를 CSV 파일에 저장하시겠습니까? (y/n): ")
        
    if user_input.strip().lower() != 'y':
        print("전체 수집을 취소합니다.")
        return
        
    # 3. 전체 페이지 반복 수집
    print(f"\n전체 리뷰 수집 및 '{CSV_PATH}' 저장을 시작합니다...")
    page_index = 1
    total_inserted = 0
    
    while True:
        if page_index > 1:
            res = fetch_reviews(page_index)
            if not res:
                break
            reviews = extract_review_info(res)
            
        # 리뷰가 빈 리스트면 수집 종료 (마지막 페이지 도달)
        if not reviews:
            print(f"데이터가 더 이상 없습니다. 수집을 종료합니다. (종료 페이지: {page_index})")
            break
            
        # CSV 추가 저장
        append_to_csv(reviews)
            
        total_inserted += len(reviews)
        print(f" > {page_index}페이지 수집 완료... 누적: {total_inserted}건 저장됨")
        
        page_index += 1
        time.sleep(1) # API 부하 방지용 지연 (1초)
        
    print(f"\n모든 작업이 완료되었습니다! 총 {total_inserted}건의 리뷰를 '{CSV_PATH}'에 성공적으로 저장했습니다.")

if __name__ == "__main__":
    main()
