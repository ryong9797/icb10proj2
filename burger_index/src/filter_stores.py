"""
이 스크립트는 burger.csv 파일에서 상권업종대분류명이 '음식' 또는 '소매'가 아닌 
데이터(예: 교육, 과학·기술 등)를 제외하고 결과를 다시 저장하는 역할을 수행합니다.
"""
import pandas as pd

def main():
    file_path = r"c:\Users\admin\Desktop\icb10proj2\burger_index\data\burger.csv"
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return
        
    initial_count = len(df)
    
    # '음식', '소매' 업종만 필터링
    valid_categories = ['음식', '소매']
    filtered_df = df[df['상권업종대분류명'].isin(valid_categories)]
    
    final_count = len(filtered_df)
    removed_count = initial_count - final_count
    
    # 기존 파일에 덮어쓰기
    filtered_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    print("\n[데이터 정제 완료]")
    print("=" * 50)
    print(f"기존 매장 수: {initial_count}건")
    print(f"제외된 매장 수: {removed_count}건")
    print(f"정제 후 매장 수: {final_count}건")
    print(f"-> '{file_path}'에 성공적으로 덮어쓰기 저장되었습니다.")
    print("=" * 50)

if __name__ == "__main__":
    main()
