"""
이 스크립트는 burger.csv 파일에서 '과학·기술', '교육' 업종으로 분류된 매장명(상호명)을 찾아 출력합니다.
"""
import pandas as pd

def main():
    file_path = r"c:\Users\admin\Desktop\icb10proj2\burger_index\data\burger.csv"
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return
    
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
    
    target_categories = ['과학·기술', '교육']
    target_df = df[df['상권업종대분류명'].isin(target_categories)]
    
    print("\n[과학·기술 및 교육 업종에 해당하는 매장명]")
    print("=" * 60)
    for idx, row in target_df.iterrows():
        print(f"[{row['상권업종대분류명']}] (분류된 브랜드: {row['브랜드명']}) -> 매장명: {row['상호명']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
