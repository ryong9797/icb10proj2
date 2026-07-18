"""
서울 생활인구 Parquet 데이터의 기본 통계량과 정보를 추출하는 스크립트입니다.
터미널 환경 문제로 인해 사용자가 직접 실행하여 결과를 확인할 수 있도록 작성되었습니다.
작성자: Antigravity
생성일: 2026-07-08
"""
import pandas as pd
import numpy as np

def main():
    file_path = 'seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet'
    print(f"Reading {file_path}...\n")
    df = pd.read_parquet(file_path)

    print("=== DATA INFO ===")
    df.info()

    print("\n=== DUPLICATES ===")
    print("Duplicates:", df.duplicated().sum())

    print("\n=== NUMERICAL DESCRIPTIVE STATS ===")
    print(df.describe().to_string())

    print("\n=== CATEGORICAL DESCRIPTIVE STATS ===")
    cat_df = df.select_dtypes(include=['O', 'category'])
    if not cat_df.empty:
        print(cat_df.describe().to_string())
    else:
        print("No categorical columns")

    print("\n=== TOP 5 ROWS ===")
    print(df.head().to_string())

if __name__ == "__main__":
    main()
