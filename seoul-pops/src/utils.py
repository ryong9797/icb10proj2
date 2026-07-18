"""
이 파일은 서울 생활인구 데이터 탐색적 데이터 분석(EDA) 대시보드를 위한 유틸리티 함수들을 제공합니다.
데이터 로딩(캐싱 적용), 병합, 기초 통계량 계산(왜도, 첨도 등)과 같은 공통 기능을 포함하고 있습니다.
작성자: Antigravity
생성일: 2026-07-11
"""

import pandas as pd
import streamlit as st
import os
import requests
import json

@st.cache_data
def load_seoul_geojson(level='gu'):
    """
    서울시 행정구역 GeoJSON을 불러오는 함수.
    level='gu': 시군구 단위
    level='dong': 읍면동 단위
    """
    if level == 'gu':
        url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"
    else:
        url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_submunicipalities_geo_simple.json"
        
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"GeoJSON 데이터를 불러오는데 실패했습니다: {e}")
        return None

@st.cache_data
def load_data(parquet_path: str, excel_path: str = None, cache_buster=1) -> pd.DataFrame:
    """
    Parquet 파일과 행정동 매핑 Excel 파일을 로드하고 병합합니다.
    """
    try:
        # Parquet 데이터 로드
        df = pd.read_parquet(parquet_path)
        
        # 📌 [핵심 버그 수정] 컬럼 밀림 현상 복구
        # 만약 '시간대구분' 컬럼에 행정동코드(예: 11110515)가 들어있다면 데이터와 컬럼명이 1칸 어긋난 것입니다.
        if '시간대구분' in df.columns and pd.api.types.is_numeric_dtype(df['시간대구분']):
            if df['시간대구분'].max() > 10000000:
                # 컬럼명을 한 칸씩 왼쪽으로 당겨서 올바른 데이터에 매칭시킵니다.
                df.columns = df.columns.tolist()[1:] + ['unknown_col']
                
        # 행정동 매핑 데이터 로드 (옵션)
        if excel_path and os.path.exists(excel_path):
            mapping_df = pd.read_excel(excel_path)
            
            dong_col_df = next((col for col in df.columns if '행정동' in col or '동코드' in col), None)
            dong_col_map = next((col for col in mapping_df.columns if '행정동' in col or '동코드' in col), None)
            
            if dong_col_df and dong_col_map:
                # 병합을 위해 타입을 문자열로 통일 (소수점 .0 방지를 위해 int 변환 후 str 변환)
                df[dong_col_df] = pd.to_numeric(df[dong_col_df], errors='coerce').fillna(0).astype(int).astype(str)
                mapping_df[dong_col_map] = pd.to_numeric(mapping_df[dong_col_map], errors='coerce').fillna(0).astype(int).astype(str)
                
                # 조인할 이름 컬럼들 모두 가져오기 (시군구명, 행정동명 등)
                cols_to_merge = [c for c in mapping_df.columns if ('명' in c or '이름' in c or '구' in c or '동' in c) and '코드' not in c]
                cols_to_merge = list(set(cols_to_merge + [dong_col_map]))
                
                df = df.merge(mapping_df[cols_to_merge], left_on=dong_col_df, right_on=dong_col_map, how='left')
                
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는데 실패했습니다: {e}")
        return pd.DataFrame()

@st.cache_data
def get_db_metadata():
    """
    SQLite 데이터베이스에서 대시보드 KPI 정보와 지도 시각화를 위한 메타데이터를 가져옵니다.
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dashboard.db")
    if not os.path.exists(db_path):
        return None
        
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # KPI 정보 추출
    try:
        cursor.execute("SELECT total_rows, total_columns, total_missing FROM kpi_stats")
        row = cursor.fetchone()
        kpi = {"total_rows": row[0], "total_columns": row[1], "total_missing": row[2]} if row else {}
    except:
        kpi = {}
        
    # 컬럼 정보 추출 (map_agg_gu_sum 기준)
    try:
        cursor.execute("PRAGMA table_info(map_agg_gu_sum)")
        cols = [info[1] for info in cursor.fetchall()]
        time_col = cols[0]
        name_col_gu = cols[1]
        pop_cols = cols[2:]
        
        # 동 단위 이름 컬럼도 추출
        cursor.execute("PRAGMA table_info(map_agg_dong_sum)")
        dong_cols = [info[1] for info in cursor.fetchall()]
        name_col_dong = dong_cols[1] if len(dong_cols) > 1 else None
        
        # 시간 최소/최대값 조회
        cursor.execute(f"SELECT MIN(`{time_col}`), MAX(`{time_col}`) FROM map_agg_gu_sum")
        row = cursor.fetchone()
        min_time = int(row[0]) if row and row[0] is not None else 0
        max_time = int(row[1]) if row and row[1] is not None else 23
    except:
        conn.close()
        return None
        
    conn.close()
    
    return {
        "kpi": kpi,
        "time_col": time_col,
        "name_col_gu": name_col_gu,
        "name_col_dong": name_col_dong,
        "pop_cols": pop_cols,
        "min_time": min_time,
        "max_time": max_time
    }

@st.cache_data
def load_map_data_from_db(level: str, agg_method: str, selected_time: int) -> pd.DataFrame:
    """
    특정 시간대, 특정 집계 기준의 데이터를 SQLite에서 바로 가져옵니다.
    사전 집계되어 있어 수십만 건의 데이터를 매번 Groupby 할 필요가 없어 즉시 로딩됩니다.
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dashboard.db")
    if not os.path.exists(db_path):
        return None
        
    import sqlite3
    conn = sqlite3.connect(db_path)
    
    table_suffix = "sum" if "합계" in agg_method else "mean"
    table_prefix = "gu" if level == "구별" else "dong"
    table_name = f"map_agg_{table_prefix}_{table_suffix}"
    
    try:
        # 시간대 컬럼명 확인
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        time_col = cursor.fetchall()[0][1]
        
        # 해당 시간대 데이터만 쿼리
        query = f"SELECT * FROM {table_name} WHERE `{time_col}` = ?"
        df = pd.read_sql(query, conn, params=(selected_time,))
    except Exception as e:
        st.error(f"DB 조회 에러: {e}")
        df = None
        
    conn.close()
    return df


def get_missing_values_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임의 결측치 통계를 반환합니다.
    """
    missing_count = df.isnull().sum()
    missing_percent = (missing_count / len(df)) * 100
    missing_df = pd.DataFrame({'결측치 수': missing_count, '결측치 비율 (%)': missing_percent})
    return missing_df[missing_df['결측치 수'] > 0].sort_values(by='결측치 수', ascending=False)

def get_descriptive_stats(df: pd.DataFrame, column: str) -> dict:
    """
    특정 수치형 컬럼의 통계량(평균, 중앙값, 최빈값, 왜도, 첨도)을 계산합니다.
    """
    if pd.api.types.is_numeric_dtype(df[column]):
        stats = {
            '최소값': df[column].min(),
            '최대값': df[column].max(),
            '평균 (Mean)': df[column].mean(),
            '중앙값 (Median)': df[column].median(),
            '최빈값 (Mode)': df[column].mode()[0] if not df[column].mode().empty else None,
            '표준편차': df[column].std(),
            '왜도 (Skewness)': df[column].skew(),
            '첨도 (Kurtosis)': df[column].kurtosis()
        }
        return stats
    return {}
