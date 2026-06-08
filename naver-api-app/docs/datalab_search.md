# 네이버 데이터랩 - 통합 검색어 트렌드 API 가이드

주제어로 묶은 검색어들에 대해 네이버 통합검색에서의 검색 추이 데이터를 조회할 수 있는 API입니다.

---

## 1. 기본 정보

* **요청 URL**: `https://openapi.naver.com/v1/datalab/search`
* **프로토콜**: HTTPS
* **HTTP 메서드**: `POST`
* **인증 방식**: 비로그인 방식 (Client ID, Client Secret 필요)
* **일일 호출 한도**: 1,000회

## 2. 요청 파라미터 (JSON Body)

요청 시 데이터를 JSON 포맷으로 Body에 담아 전송해야 합니다.

| 파라미터명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `startDate` | string | Y | 조회 기간 시작 날짜 (`yyyy-mm-dd` 형식, 2016-01-01부터 가능) |
| `endDate` | string | Y | 조회 기간 종료 날짜 (`yyyy-mm-dd` 형식) |
| `timeUnit` | string | Y | 구간 단위 (`date`: 일간, `week`: 주간, `month`: 월간) |
| `keywordGroups` | array | Y | 주제어와 대표 검색어 묶음 쌍의 배열 (최대 5개 쌍) |
| `keywordGroups.groupName` | string | Y | 주제어 (검색어 그룹을 대표하는 이름) |
| `keywordGroups.keywords` | array | Y | 주제어에 속하는 검색어 배열 (최대 20개) |
| `device` | string | N | 검색 기기 필터 (설정 안 함: 전체, `pc`: PC, `mo`: 모바일) |
| `gender` | string | N | 검색 성별 필터 (설정 안 함: 전체, `m`: 남성, `f`: 여성) |
| `ages` | array | N | 연령대 필터 (`1`: 0~12세 ~ `11`: 60세 이상) |

## 3. 응답 데이터 구조 (JSON)

API 요청 성공 시 JSON 형식의 검색량 상대 비율 데이터가 반환됩니다.

| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `startDate` | string | 조회 기간 시작 날짜 |
| `endDate` | string | 조회 기간 종료 날짜 |
| `timeUnit` | string | 구간 단위 |
| `results` | array | 주제어별 검색 추이 데이터 결과 배열 |
| `results.title` | string | 주제어 (groupName) |
| `results.keywords` | array | 주제어에 해당했던 검색어 목록 |
| `results.data` | array | 일자별/구간별 검색 비율 배열 |
| `results.data.period` | string | 해당 구간의 시작 날짜 |
| `results.data.ratio` | number | 검색량 상대 비율 (가장 검색량이 많았던 시점을 100으로 기준한 비율) |

## 4. 호출 예시 (Python)

```python
import urllib.request
import json

client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
url = "https://openapi.naver.com/v1/datalab/search"

body = {
    "startDate": "2023-01-01",
    "endDate": "2023-12-31",
    "timeUnit": "month",
    "keywordGroups": [
        {
            "groupName": "인공지능",
            "keywords": ["AI", "Artificial Intelligence", "인공지능"]
        }
    ]
}
request_body = json.dumps(body).encode("utf-8")

request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", client_id)
request.add_header("X-Naver-Client-Secret", client_secret)
request.add_header("Content-Type", "application/json")

try:
    response = urllib.request.urlopen(request, data=request_body)
    if response.getcode() == 200:
        response_body = response.read()
        print(response_body.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
```
