"""
이 스크립트는 버거지수를 계산하여 원본 CSV 파일에 새로운 파생변수로 추가하는 역할을 합니다.
- 수식: (버거킹 + 맥도날드 + KFC) / 롯데리아
- 대상 파일: burger_index/data/crosstab_geo_result.csv
"""
import pandas as pd

file_path = 'burger_index/data/crosstab_geo_result.csv'
df = pd.read_csv(file_path)

# Calculate Burger Index
df['버거지수'] = (df['버거킹'] + df['맥도날드'] + df['KFC']) / df['롯데리아']

# Optionally, round to 2 decimal places for better readability
df['버거지수'] = df['버거지수'].round(2)

df.to_csv(file_path, index=False)
print("버거지수 생성 완료!")
