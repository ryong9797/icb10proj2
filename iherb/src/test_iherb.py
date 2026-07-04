import requests
import json

url = "https://catalog.app.iherb.com/category/sports/specials?isMobile=false&page=1&pageSize=18"
headers = {
    "origin": "https://kr.iherb.com",
    "referer": "https://kr.iherb.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)
if response.status_code == 200:
    data = response.json()
    print("Keys in response:", data.keys())
    if "products" in data:
        print("Number of products:", len(data["products"]))
        print("First product keys:", data["products"][0].keys() if data["products"] else "No products")
    if "pagination" in data:
        print("Pagination:", data["pagination"])
    
    with open("sample.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
else:
    print(response.text)
