import pandas as pd

df = pd.read_parquet('seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet')
print("INFO:")
df.info()
print("\nHEAD:")
print(df.head())
