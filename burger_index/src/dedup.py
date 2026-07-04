"""
버거 인덱스 데이터를 읽어와서 상가업소번호 기준으로 중복을 제거하고
정규식 패턴을 사용하여 상호명 기반 '브랜드' 파생변수를 생성한 뒤
전체 매장 수와 브랜드별 매장 수를 집계하여 출력하고 저장하는 스크립트입니다.
"""
import pandas as pd
import re

file_path = 'burger_index/data/burger.csv'

try:
    # 1. 데이터 로드
    df = pd.read_csv(file_path)
    initial_count = len(df)
    
    # 2. 브랜드 파생변수 생성 (정규식 패턴 사용)
    pattern = r"(버거킹|burger\s*king|burger_king|burgerking|맥도날드|mcdonald|kfc|롯데리아|lotteria|맘스터치|mom's\s*touch|momstouch)"
    
    def extract_brand(name):
        name = str(name).lower() # 소문자로 변환하여 비교
        match = re.search(pattern, name)
        if match:
            matched_str = match.group(1).replace(" ", "").replace("_", "")
            if matched_str in ["버거킹", "burgerking"]:
                return "버거킹"
            elif matched_str in ["맥도날드", "mcdonald"]:
                return "맥도날드"
            elif matched_str == "kfc":
                return "KFC"
            elif matched_str in ["롯데리아", "lotteria"]:
                return "롯데리아"
            elif matched_str in ["맘스터치", "momstouch", "mom'stouch"]:
                return "맘스터치"
        return "기타"
        
    df['브랜드'] = df['상호명'].apply(extract_brand)
    
    # 3. 중복 제거 (상가업소번호가 아닌 '브랜드'와 '도로명주소' 기준으로 실제 매장 단위 중복 제거)
    df_dedup = df.drop_duplicates(subset=['브랜드', '도로명주소']).copy()
    final_count = len(df_dedup)
    
    # 4. 파일 저장
    df_dedup.to_csv(file_path, index=False)
    
    # 5. 결과 집계 및 출력
    print(f"초기 데이터 수: {initial_count}개")
    print(f"브랜드+도로명주소 기준 중복 제거 후 전체 매장 수: {final_count}개")
    print("\n[브랜드별 매장 수]")
    
    # 강사님 표 대상 4개 브랜드
    target_brands = ['KFC', '롯데리아', '맥도날드', '버거킹']
    
    brand_counts = df_dedup['브랜드'].value_counts()
    for brand, count in brand_counts.items():
        if brand in target_brands:
            print(f"- {brand}: {count}개")
            
    print("\n[상권업종대분류명 별 교차표]")
    df_target = df_dedup[df_dedup['브랜드'].isin(target_brands)]
    cross_tab = pd.crosstab(df_target['상권업종대분류명'], df_target['브랜드'], margins=True, margins_name='합계')
    print(cross_tab)
        
except Exception as e:
    print(f"Error: {e}")
