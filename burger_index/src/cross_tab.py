"""
이 스크립트는 burger.csv 파일의 '상호명'을 기준으로 브랜드명 파생변수를 생성하고,
브랜드명과 상권업종대분류명 간의 교차표(빈도수)를 출력합니다.
"""
import pandas as pd

def main():
    file_path = r"c:\Users\admin\Desktop\icb10proj2\burger_index\data\burger.csv"
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return
    
    # 브랜드명 파생변수 생성 함수
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
    
    # 정확히 4개 브랜드만 필터링
    df = df[df['브랜드명'] != '기타']
    
    # 교차표 생성 (행: 브랜드명, 열: 상권업종대분류명)
    crosstab = pd.crosstab(index=df['브랜드명'], columns=df['상권업종대분류명'], margins=True, margins_name='총합')
    
    # 결과 출력
    print("\n[브랜드별 상권업종대분류명 교차표 (빈도수)]")
    print("=" * 60)
    print(crosstab)
    print("=" * 60)

if __name__ == "__main__":
    main()
