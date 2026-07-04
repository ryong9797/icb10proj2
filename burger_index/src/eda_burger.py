"""
burger.csv 파일이 원본 데이터(소상공인 상권정보)에서 
어떤 기준으로 필터링되었는지 역추적하기 위한 스크립트입니다.
"""
import pandas as pd
import re

file_path = 'burger_index/data/burger.csv'

try:
    df = pd.read_csv(file_path)
    print("=== burger.csv 전처리 기준 역추적 결과 ===")
    print(f"총 데이터 수: {len(df)}개\n")

    print("1. [상권업종대분류명] 고유값 및 빈도:")
    print(df['상권업종대분류명'].value_counts())
    print()

    print("2. [상권업종중분류명] 고유값 및 빈도:")
    print(df['상권업종중분류명'].value_counts())
    print()

    print("3. [상권업종소분류명] 고유값 및 빈도:")
    print(df['상권업종소분류명'].value_counts())
    print()

    # 우리가 짠 정규식에 걸리지 않은 '기타' 브랜드 상호명 확인
    pattern = r"(버거킹|burger\s*king|burger_king|burgerking|맥도날드|mcdonald|kfc|롯데리아|lotteria)"
    def extract_brand(name):
        name = str(name).lower()
        if re.search(pattern, name):
            return "매칭됨"
        return "기타"
    
    df['매칭여부'] = df['상호명'].apply(extract_brand)
    기타_df = df[df['매칭여부'] == '기타']
    
    print("4. 정규식(4대 브랜드)에 매칭되지 않은 상호명 예시 (최대 20개):")
    print(기타_df['상호명'].unique()[:20])

except Exception as e:
    print(f"Error: {e}")
