# 네이버 검색 - 카페글 검색 API 가이드

네이버 카페의 공개 게시판 글을 검색할 수 있는 API입니다.

---

## 1. 기본 정보

* **요청 URL**: 
  * `https://openapi.naver.com/v1/search/cafearticle.json` (JSON 포맷 반환)
  * `https://openapi.naver.com/v1/search/cafearticle.xml` (XML 포맷 반환)
* **프로토콜**: HTTPS
* **HTTP 메서드**: `GET`
* **인증 방식**: 비로그인 방식 (Client ID, Client Secret 필요)
* **일일 호출 한도**: 25,000회 (전체 검색 API 공통)

## 2. 요청 파라미터 (Query String)

| 파라미터명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :---: | :--- |
| `query` | string | Y | - | 검색어 (UTF-8로 인코딩 필요) |
| `display` | integer | N | 10 | 한 번에 표시할 검색 결과 개수 (최소 1, 최대 100) |
| `start` | integer | N | 1 | 검색 시작 위치 (최소 1, 최대 1000) |
| `sort` | string | N | `sim` | 정렬 방식 (`sim`: 정확도순 내림차순, `date`: 날짜순 내림차순) |

## 3. 응답 데이터 구조 (JSON 기준)

| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `lastBuildDate` | string | 검색 결과를 생성한 시간 |
| `total` | integer | 총 검색 결과 개수 |
| `start` | integer | 검색 시작 위치 |
| `display` | integer | 표시된 검색 결과 개수 |
| `items` | array | 개별 카페글 리스트 |
| `items.title` | string | 카페 게시글 제목 (매칭 단어는 `<b>` 태그 처리) |
| `items.link` | string | 카페 게시글 상세 URL |
| `items.description` | string | 카페 게시글 본문 요약 (매칭 단어는 `<b>` 태그 처리) |
| `items.cafename` | string | 게시글이 작성된 카페의 이름 |
| `items.cafeurl` | string | 게시글이 작성된 카페의 주소 URL |

## 4. 호출 예시 (Python)

```python
import urllib.request
import urllib.parse
import json

client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
query_text = urllib.parse.quote("캠핑 용품")

url = f"https://openapi.naver.com/v1/search/cafearticle.json?query={query_text}&display=5"

request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", client_id)
request.add_header("X-Naver-Client-Secret", client_secret)

try:
    response = urllib.request.urlopen(request)
    if response.getcode() == 200:
        response_body = response.read()
        data = json.loads(response_body.decode('utf-8'))
        for item in data.get('items', []):
            print(f"카페글 제목: {item['title']}")
            print(f"카페명: {item['cafename']}")
            print(f"링크: {item['link']}\n")
except Exception as e:
    print(f"Error: {e}")
```
