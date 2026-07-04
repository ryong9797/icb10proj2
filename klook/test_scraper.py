import requests
import json

url = "https://www.klook.com/v1/cardinfocenterservicesrv/search/platform/complete_search_v3"
params = {
    "location": "158,157,156,25723,5031,8928",
    "sort": "most_relevant",
    "tab_key": "0",
    "start": "1",
    "query": "대한민국",
    "size": "15",
    "search_scope": "main_search",
    "k_lang": "ko_KR",
    "k_currency": "KRW"
}

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "x-klook-market": "global",
    "x-platform": "desktop",
    "x-requested-with": "XMLHttpRequest"
}

response = requests.get(url, params=params, headers=headers)
print("Status:", response.status_code)
if response.status_code == 200:
    data = response.json()
    cards = data.get("result", {}).get("search_result", {}).get("cards", [])
    if cards:
        print(json.dumps(cards[0], indent=2, ensure_ascii=False))
    else:
        print("No cards found. Check response structure.")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
else:
    print(response.text)
