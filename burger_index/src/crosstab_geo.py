"""
시도명과 시군구명을 합쳐 '시도시군구명' 파생변수를 만들고,
해당 지역별 브랜드 매장 수 교차표를 생성하는 스크립트입니다.
"""
import pandas as pd

file_path = 'burger_index/data/burger.csv'

try:
    # 1. 데이터 로드
    df = pd.read_csv(file_path)
    
    # 2. 시도시군구명 파생변수 생성
    # 빈 값(NaN)이 있을 수 있으므로 문자열로 변환하여 합칩니다.
    df['시도시군구명'] = df['시도명'].astype(str) + " " + df['시군구명'].astype(str)
    
    # 원본 파일에도 '시도시군구명' 파생변수를 포함하여 덮어쓰기 저장
    df.to_csv(file_path, index=False)
    print(f"✅ '시도시군구명' 컬럼이 추가된 데이터가 {file_path}에 저장되었습니다.")
    
    # 3. 주요 4대 브랜드 파생변수 생성 (안전하게 자체적으로 다시 생성)
    import re
    pattern = r"(버거킹|burger\s*king|burger_king|burgerking|맥도날드|mcdonald|kfc|롯데리아|lotteria)"
    def extract_brand(name):
        name = str(name).lower()
        match = re.search(pattern, name)
        if match:
            matched_str = match.group(1).replace(" ", "").replace("_", "")
            if matched_str in ["버거킹", "burgerking"]: return "버거킹"
            elif matched_str in ["맥도날드", "mcdonald"]: return "맥도날드"
            elif matched_str == "kfc": return "KFC"
            elif matched_str in ["롯데리아", "lotteria"]: return "롯데리아"
        return "기타"
        
    df['브랜드명'] = df['상호명'].apply(extract_brand)
    
    # 4. 주요 4대 브랜드 필터링
    target_brands = ['KFC', '롯데리아', '맥도날드', '버거킹']
    df_target = df[df['브랜드명'].isin(target_brands)]
    
    # 원본 파일에도 '시도시군구명', '브랜드명' 파생변수를 포함하여 덮어쓰기 저장
    df.to_csv(file_path, index=False)
    print(f"✅ '시도시군구명', '브랜드명' 컬럼이 추가된 데이터가 {file_path}에 저장되었습니다.")
    
    # 5. 교차표 생성
    cross_tab = pd.crosstab(df_target['시도시군구명'], df_target['브랜드명'], margins=True, margins_name='합계')
    
    # 5. 결과 출력
    print("=== 시도시군구명 vs 브랜드 교차표 (상위 20개 행) ===")
    print(cross_tab.head(20)) # 데이터가 길 수 있으므로 일부만 출력
    print("\n...\n")
    print("=== 전체 합계 부분 ===")
    print(cross_tab.tail())
    
    # 전체 결과를 보기 편하게 CSV 파일로 저장
    output_path = 'burger_index/data/crosstab_geo_result.csv'
    cross_tab.to_csv(output_path, encoding='utf-8-sig')
    print(f"\n✅ 전체 교차표 결과가 파일로 저장되었습니다: {output_path}")

except Exception as e:
    print(f"Error: {e}")
