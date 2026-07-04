"""
강사님의 결과와 중복 제거 갯수 차이가 발생하는 원인을 분석하기 위해,
다양한 기준(상가업소번호, 상호명+도로명주소, 브랜드명+도로명주소 등)으로 
중복을 제거해보고 결과를 비교 출력하는 테스트 스크립트입니다.
"""
import pandas as pd
import re

file_path = 'burger_index/data/burger.csv'

# 1. 데이터 로드
df = pd.read_csv(file_path)

# 정규식 패턴 생성 (강사님 패턴 적용)
pattern = r"(버거킹|burger\s*king|맥도날드|mcdonald|kfc|롯데리아|lotteria)"

def extract_brand(name):
    name = str(name).lower()
    match = re.search(pattern, name)
    if match:
        matched_str = match.group(1).replace(" ", "")
        if matched_str in ["버거킹", "burgerking"]: return "버거킹"
        elif matched_str in ["맥도날드", "mcdonald"]: return "맥도날드"
        elif matched_str == "kfc": return "KFC"
        elif matched_str in ["롯데리아", "lotteria"]: return "롯데리아"
    return "기타"

# 모든 행에 대해 브랜드 파생변수 생성
df['브랜드명'] = df['상호명'].apply(extract_brand)

# ---------------------------------------------------------
# 테스트 1: 상가업소번호 기준 중복 제거 (기존 방식)
df_dedup_1 = df.drop_duplicates(subset=['상가업소번호'])

# 테스트 2: 모든 컬럼이 완전히 동일한 행 중복 제거
df_dedup_2 = df.drop_duplicates()

# 테스트 3: '상호명', '도로명주소' 가 동일한 경우 중복 제거
df_dedup_3 = df.drop_duplicates(subset=['상호명', '도로명주소'])

# 테스트 4: '브랜드명', '도로명주소' 가 동일한 경우 중복 제거 (지점명이 다르더라도 같은 브랜드가 같은 주소에 있으면 중복)
df_dedup_4 = df.drop_duplicates(subset=['브랜드명', '도로명주소'])

print("=== 중복 제거 기준별 맥도날드 매장 수 비교 ===")
print(f"1. 상가업소번호 기준: {len(df_dedup_1[df_dedup_1['브랜드명'] == '맥도날드'])}")
print(f"2. 모든 컬럼 완전 동일: {len(df_dedup_2[df_dedup_2['브랜드명'] == '맥도날드'])}")
print(f"3. 상호명+도로명주소 기준: {len(df_dedup_3[df_dedup_3['브랜드명'] == '맥도날드'])}")
print(f"4. 브랜드명+도로명주소 기준: {len(df_dedup_4[df_dedup_4['브랜드명'] == '맥도날드'])}")
print("강사님 결과: 542\n")

print("=== [테스트 4] 적용 시 브랜드별 전체 빈도수 (교차표) ===")
# 강사님 표와 동일하게 나오는지 확인
target_brands = ['KFC', '롯데리아', '맥도날드', '버거킹']
df_target = df_dedup_4[df_dedup_4['브랜드명'].isin(target_brands)]

cross_tab = pd.crosstab(df_target['상권업종대분류명'], df_target['브랜드명'], margins=True, margins_name='합계')
print(cross_tab)
