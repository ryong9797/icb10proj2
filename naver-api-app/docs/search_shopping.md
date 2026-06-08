# 네이버 검색 - 쇼핑 검색 API 가이드

네이버 검색의 쇼핑 검색 결과를 조회할 수 있는 API입니다.

---

## 1. 기본 정보

* **요청 URL**: 
  * `https://openapi.naver.com/v1/search/shop.json` (JSON 포맷 반환)
  * `https://openapi.naver.com/v1/search/shop.xml` (XML 포맷 반환)
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
| `sort` | string | N | `sim` | 정렬 방식 (`sim`: 정확도순 내림차순, `date`: 날짜순 내림차순, `asc`: 가격 오름차순, `dsc`: 가격 내림차순) |
| `filter` | string | N | - | 상품 유형 필터 (`naverpay`: 네이버페이 연동 상품) |
| `exclude` | string | N | - | 제외할 상품 유형 (중고:`used`, 렌탈:`rental`, 해외직구/구매대행:`cbshop`) (구분자는 `:` 사용, 예: `used:rental`) |

## 3. 응답 데이터 구조 (JSON 기준)

| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `lastBuildDate` | string | 검색 결과를 생성한 시간 |
| `total` | integer | 총 검색 결과 개수 |
| `start` | integer | 검색 시작 위치 |
| `display` | integer | 표시된 검색 결과 개수 |
| `items` | array | 개별 상품 리스트 |
| `items.title` | string | 상품 이름 (매칭 단어는 `<b>` 태그 처리) |
| `items.link` | string | 상품 정보 URL |
| `items.image` | string | 섬네일 이미지 URL |
| `items.lprice` | integer | 최저가 (최저가 정보가 없으면 0) |
| `items.hprice` | integer | 최고가 (최고가 정보가 없으면 0) |
| `items.mallName` | string | 상품 판매 쇼핑몰 이름 (없으면 "네이버") |
| `items.productId` | string | 네이버 쇼핑 상품 ID |
| `items.productType` | integer | 상품군/종류별 타입 코드 (1 ~ 12) |
| `items.maker` | string | 제조사 이름 |
| `items.brand` | string | 브랜드 이름 |
| `items.category1` | string | 카테고리 대분류 |
| `items.category2` | string | 카테고리 중분류 |
| `items.category3` | string | 카테고리 소분류 |
| `items.category4` | string | 카테고리 세분류 |

## 4. 호출 예시 (Python)

```python
import urllib.request
import urllib.parse
import json

client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
query_text = urllib.parse.quote("노트북")

# 가격순 정렬, 해외직구 상품 제외
url = f"https://openapi.naver.com/v1/search/shop.json?query={query_text}&display=5&sort=asc&exclude=cbshop"

request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", client_id)
request.add_header("X-Naver-Client-Secret", client_secret)

try:
    response = urllib.request.urlopen(request)
    if response.getcode() == 200:
        response_body = response.read()
        data = json.loads(response_body.decode('utf-8'))
        for item in data.get('items', []):
            print(f"상품명: {item['title']}")
            print(f"가격: {item['lprice']}원")
            print(f"쇼핑몰: {item['mallName']}\n")
except Exception as e:
    print(f"Error: {e}")
```
