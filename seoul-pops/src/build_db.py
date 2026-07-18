"""
서울 생활인구 데이터를 사전에 집계하여 SQLite DB로 저장하는 스크립트입니다.
대시보드의 로딩 속도 및 지도 렌더링 속도를 최적화하기 위해 사용됩니다.
작성자: Antigravity
생성일: 2026-07-11
"""

import pandas as pd
import sqlite3
import os

def build_database():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    parquet_path = os.path.join(base_dir, "data", "LOCAL_PEOPLE_DONG_202606.parquet")
    excel_path = os.path.join(base_dir, "data", "행정동코드_매핑정보_20241218.xlsx")
    db_path = os.path.join(base_dir, "data", "dashboard.db")
    
    print("1. 데이터를 로딩하고 밀림 현상을 보정합니다...")
    df = pd.read_parquet(parquet_path)
    
    if '시간대구분' in df.columns and pd.api.types.is_numeric_dtype(df['시간대구분']):
        if df['시간대구분'].max() > 10000000:
            df.columns = df.columns.tolist()[1:] + ['unknown_col']
            
    real_time_col = None
    real_dong_col = None
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].min() >= 0 and df[col].max() <= 23 and len(df[col].dropna().unique()) <= 24:
                real_time_col = col
            elif df[col].min() >= 11000000 and df[col].max() < 12000000:
                real_dong_col = col

    if real_dong_col:
        mapping_df = pd.read_excel(excel_path)
        
        dong_col_map = None
        for col in mapping_df.columns:
            if mapping_df[col].astype(str).str.startswith('11').any() and pd.api.types.is_numeric_dtype(mapping_df[col]):
                if mapping_df[col].max() > 11000000:
                    dong_col_map = col
                    break
        if not dong_col_map:
            dong_col_map = next((col for col in mapping_df.columns if '코드' in col and ('동' in col or '행정' in col)), None)
            
        if dong_col_map:
            df[real_dong_col] = pd.to_numeric(df[real_dong_col], errors='coerce').fillna(0).astype(int).astype(str)
            mapping_df[dong_col_map] = pd.to_numeric(mapping_df[dong_col_map], errors='coerce').fillna(0).astype(int).astype(str)
            
            cols_to_merge = [c for c in mapping_df.columns if ('명' in c or '이름' in c or '구' in c or '동' in c) and '코드' not in c]
            cols_to_merge = list(set(cols_to_merge + [dong_col_map]))
            df = df.merge(mapping_df[cols_to_merge], left_on=real_dong_col, right_on=dong_col_map, how='left')

    print("2. 집계할 컬럼을 분류합니다...")
    pop_cols = [c for c in df.columns if '인구' in c and pd.api.types.is_numeric_dtype(df[c])]
    name_cols = [c for c in df.columns if ('명' in c or '이름' in c or '구' in c or '동' in c) and '인구' not in c and '코드' not in c]
    name_cols = [c for c in name_cols if df[c].dtype == 'object' or df[c].dtype.name in ['category', 'string']]
    
    gu_cols = [c for c in name_cols if '구' in c]
    dong_cols = [c for c in name_cols if '동' in c]
    
    gu_col = gu_cols[0] if gu_cols else None
    dong_col = dong_cols[0] if dong_cols else None
    
    conn = sqlite3.connect(db_path)
    
    print("3. KPI 통계를 계산하고 저장합니다...")
    kpi_data = pd.DataFrame([{
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "total_missing": int(df.isnull().sum().sum())
    }])
    kpi_data.to_sql('kpi_stats', conn, if_exists='replace', index=False)
    
    if real_time_col and gu_col:
        print(f"4. 구 단위({gu_col}) 사전 집계를 시작합니다...")
        agg_gu_sum = df.groupby([real_time_col, gu_col])[pop_cols].sum().reset_index()
        agg_gu_mean = df.groupby([real_time_col, gu_col])[pop_cols].mean().reset_index()
        agg_gu_sum.to_sql('map_agg_gu_sum', conn, if_exists='replace', index=False)
        agg_gu_mean.to_sql('map_agg_gu_mean', conn, if_exists='replace', index=False)
        
    if real_time_col and dong_col:
        print(f"5. 동 단위({dong_col}) 사전 집계를 시작합니다...")
        agg_dong_sum = df.groupby([real_time_col, dong_col])[pop_cols].sum().reset_index()
        agg_dong_mean = df.groupby([real_time_col, dong_col])[pop_cols].mean().reset_index()
        agg_dong_sum.to_sql('map_agg_dong_sum', conn, if_exists='replace', index=False)
        agg_dong_mean.to_sql('map_agg_dong_mean', conn, if_exists='replace', index=False)

    conn.close()
    print("✅ 데이터베이스 생성 완료:", db_path)

if __name__ == "__main__":
    build_database()
