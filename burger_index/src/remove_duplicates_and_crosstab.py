"""
이 스크립트는 burger.csv 파일에서 중복 데이터를 제거하고(고유 식별자 기준 하나만 유지),
다시 한 번 브랜드명과 상권업종대분류명 간의 교차표(빈도수 기준)를 구해 출력합니다.
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
    
    # 중복 데이터 제거 (상가업소번호 기준 첫 번째 데이터만 남기고 제거)
    df = df.drop_duplicates(subset=['상가업소번호'], keep='first')
    
    final_count = len(df)
    removed_count = initial_count - final_count
    
    # 만약 중복이 있어 실제로 제거되었다면 다시 파일 덮어쓰기
    if removed_count > 0:
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
    # 브랜드명 파생변수 생성
    def get_brand(name):
        name = str(name).lower()
        if '버거킹' in name or 'burger king' in name or 'burgerking' in name:
            return '버거킹'
        elif '맥도날드' in name or 'mcdonald' in name:
            return '맥도날드'
        elif 'kfc' in name or '케이에프씨' in name:
            return 'KFC'
        elif '롯데리아' in name or 'lotteria' in name:
            return '롯데리아'
        else:
            return '기타'
            
    df['브랜드명'] = df['상호명'].apply(get_brand)
    df = df[df['브랜드명'] != '기타']
    
    # 교차표 생성
    crosstab = pd.crosstab(index=df['브랜드명'], columns=df['상권업종대분류명'], margins=True, margins_name='총합')
    
    # 결과 출력
    print("\n[중복 제거 및 정제 완료 보고]")
    print("=" * 60)
    print(f"기존 데이터 수: {initial_count}건")
    print(f"제거된 중복 데이터 수: {removed_count}건")
    print(f"최종 남은 데이터 수: {final_count}건")
    print("=" * 60)
    
    print("\n[최종 브랜드별 상권업종대분류명 교차표 (빈도수)]")
    print("-" * 60)
    print(crosstab)
    print("-" * 60)

if __name__ == "__main__":
    main()
