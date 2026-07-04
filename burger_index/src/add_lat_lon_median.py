"""
이 스크립트는 burger.csv 파일에서 시도시군구별 위도와 경도의 중간값을 계산하여,
기존 crosstab_geo_result.csv 파일에 파생변수(위도_중간값, 경도_중간값)로 추가하는 역할을 합니다.
작성일: 2026-07-04
"""
import pandas as pd

# 파일 경로
burger_file = 'burger_index/data/burger.csv'
result_file = 'burger_index/data/crosstab_geo_result.csv'

# 1. 버거 데이터 불러오기
burger_df = pd.read_csv(burger_file)

# 2. 시도시군구명 기준으로 위도와 경도의 중간값(median) 계산
median_geo = burger_df.groupby('시도시군구명')[['위도', '경도']].median().reset_index()
median_geo.rename(columns={'위도': '위도_중간값', '경도': '경도_중간값'}, inplace=True)

# 3. 기존 결과 데이터 불러오기
result_df = pd.read_csv(result_file)

# 4. 데이터 병합 (시도시군구명 기준)
# 합계 행은 시도시군구명이 '합계'이므로, merge시 left join을 사용합니다.
final_df = pd.merge(result_df, median_geo, on='시도시군구명', how='left')

# 5. 결과 저장
final_df.to_csv(result_file, index=False)
print("위도 및 경도 중간값 파생변수 추가가 완료되었습니다!")
