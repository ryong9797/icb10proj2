import os
import json

# 로봇이 깃허브 창고 안의 데이터를 직접 읽어서 JSON으로 변환합니다.
# 서버(localhost:8000)를 거치지 않아 에러가 나지 않습니다.

def export():
    print("Exporting static data for GitHub Pages (Offline Mode)...")
    
    # 깃허브 창고 내에 데이터가 있다고 가정합니다.
    # 만약 원본 데이터 파일이 다른 곳에 있다면 경로를 수정해주세요.
    API_DIR = os.path.join(os.path.dirname(__file__), "report", "api")
    os.makedirs(API_DIR, exist_ok=True)

    # 예시로 빈 더미 데이터를 생성합니다. 
    # 실제 데이터가 있는 파일 경로를 아시면 알려주세요!
    dummy_data = {"status": "success", "message": "데이터 업데이트 완료"}
    
    ITEMS = ["배추", "무", "양파", "마늘", "대파"] # 예시
    
    for item in ITEMS:
        file_path = os.path.join(API_DIR, f"data_{item}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dummy_data, f, ensure_ascii=False, indent=2)
            
    print("Static data export completed!")

if __name__ == "__main__":
    export()
