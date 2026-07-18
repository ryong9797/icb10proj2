import pandas as pd
import os

parquet_path = "seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet"
excel_path = "seoul-pops/data/행정동코드_매핑정보_20241218.xlsx"

print("--- Parquet Columns ---")
try:
    df = pd.read_parquet(parquet_path)
    print(df.columns.tolist())
    print("\n--- Parquet Head ---")
    print(df.head(2))
except Exception as e:
    print("Error reading parquet:", e)

print("\n--- Excel Columns ---")
try:
    map_df = pd.read_excel(excel_path)
    print(map_df.columns.tolist())
    print("\n--- Excel Head ---")
    print(map_df.head(2))
except Exception as e:
    print("Error reading excel:", e)
