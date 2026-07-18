"""
이 파일은 서울 생활인구 데이터 탐색적 데이터 분석(EDA) Streamlit 대시보드의 메인 진입점입니다.
사용자 인터페이스(UI), 데이터 개요, 단일 변수 분석, 변수 간 상관관계 분석 기능을 제공합니다.
작성자: Antigravity
생성일: 2026-07-11
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import folium
from streamlit_folium import st_folium

# utils.py 가져오기
import importlib
sys.path.append(os.path.dirname(__file__))
import utils
importlib.reload(utils)
from utils import load_data, get_missing_values_summary, get_descriptive_stats, load_seoul_geojson, get_db_metadata, load_map_data_from_db

# 페이지 설정
st.set_page_config(page_title="서울 생활인구 데이터 EDA", page_icon="📊", layout="wide")

# 데이터 경로 설정 (현재 파일 위치 기준 상대 경로)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PARQUET_PATH = os.path.join(BASE_DIR, 'data', 'LOCAL_PEOPLE_DONG_202606.parquet')
EXCEL_PATH = os.path.join(BASE_DIR, 'data', '행정동코드_매핑정보_20241218.xlsx')

# 메인 타이틀
st.title("📊 서울 생활인구 데이터(LOCAL_PEOPLE_DONG) EDA 대시보드")

# 데이터 로딩
with st.spinner("데이터를 로딩 중입니다. 파일 크기에 따라 시간이 걸릴 수 있습니다..."):
    if not os.path.exists(PARQUET_PATH):
        st.error(f"데이터 파일이 존재하지 않습니다: {PARQUET_PATH}")
        st.stop()
    
    df = load_data(PARQUET_PATH, EXCEL_PATH, cache_buster=2)
    
    if df.empty:
        st.warning("데이터프레임이 비어 있습니다. 데이터를 올바르게 불러오지 못했습니다.")
        st.stop()

# 컬럼 분류
numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()

# 📌 상단 고정 KPI 카드 (모든 탭에서 노출)
st.markdown("### 🎯 데이터 요약 (KPI)")
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
kpi_col1.metric("총 데이터 행(Row) 수", f"{len(df):,}")
kpi_col2.metric("총 데이터 열(Column) 수", f"{len(df.columns):,}")
total_missing = df.isnull().sum().sum()
kpi_col3.metric("전체 결측치 수", f"{total_missing:,}")
st.divider()

# 사이드바
st.sidebar.header("탐색 메뉴")
menu = st.sidebar.radio("분석 탭을 선택하세요:", ["Overview (데이터 개요)", "Item Analysis (단일 항목 분석)", "Correlation (상관성 분석)", "Map (지도 시각화)"])

if menu == "Overview (데이터 개요)":
    st.header("1. 데이터 구조 및 품질 분석 (Overview)")
    
    st.subheader("데이터 미리보기")
    st.dataframe(df.head(100), use_container_width=True)
    
    col4, col5 = st.columns(2)
    with col4:
        st.subheader("컬럼별 데이터 타입")
        dtypes_df = pd.DataFrame(df.dtypes, columns=['Data Type']).reset_index().rename(columns={'index': 'Column'})
        st.dataframe(dtypes_df, use_container_width=True)
    
    with col5:
        st.subheader("결측치 (Missing Values)")
        missing_df = get_missing_values_summary(df)
        if not missing_df.empty:
            st.dataframe(missing_df, use_container_width=True)
        else:
            st.success("데이터셋에 결측치가 존재하지 않습니다.")
            
    st.subheader("수치형 데이터 요약 통계량")
    if numeric_cols:
        st.dataframe(df.describe(), use_container_width=True)
    else:
        st.info("수치형 컬럼이 존재하지 않습니다.")

elif menu == "Item Analysis (단일 항목 분석)":
    st.header("2. 단일 항목 분포 및 기술 통계 (Item Analysis)")
    
    selected_col = st.selectbox("분석할 컬럼을 선택하세요:", df.columns)
    
    if selected_col in numeric_cols:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("데이터 분포 시각화 (히스토그램 & 박스플롯)")
            tab1, tab2 = st.tabs(["히스토그램 (Histogram)", "박스플롯 (Boxplot)"])
            
            # 데이터 샘플링 (성능 고려)
            plot_df = df.sample(min(100000, len(df))) if len(df) > 100000 else df
            
            with tab1:
                fig_hist = px.histogram(plot_df, x=selected_col, nbins=50, marginal="box", title=f"{selected_col} 분포")
                st.plotly_chart(fig_hist, use_container_width=True)
            with tab2:
                fig_box = px.box(plot_df, y=selected_col, title=f"{selected_col} 이상치 확인")
                st.plotly_chart(fig_box, use_container_width=True)
                
        with col2:
            st.subheader("기술 통계량")
            stats = get_descriptive_stats(df, selected_col)
            stats_df = pd.DataFrame(list(stats.items()), columns=['항목', '값'])
            st.dataframe(stats_df, use_container_width=True)
            
            # 왜도/첨도 경고
            if abs(stats['왜도 (Skewness)']) > 1:
                st.warning("비대칭 분포 (왜도 > 1 또는 < -1).")
            if stats['첨도 (Kurtosis)'] > 3:
                st.warning("분포 꼬리가 두꺼움 (첨도 > 3).")
    else:
        st.subheader("범주형 데이터 분포 시각화")
        value_counts = df[selected_col].value_counts().reset_index()
        value_counts.columns = [selected_col, 'Count']
        
        col1, col2 = st.columns([2, 1])
        with col1:
            fig_bar = px.bar(value_counts.head(50), x=selected_col, y='Count', title=f"{selected_col} 상위 50개 빈도수")
            st.plotly_chart(fig_bar, use_container_width=True)
        with col2:
            st.dataframe(value_counts, use_container_width=True)

elif menu == "Correlation (상관성 분석)":
    st.header("3. 항목 간 관계 및 상관성 분석 (Correlation)")
    
    if len(numeric_cols) < 2:
        st.warning("상관성 분석을 위한 수치형 컬럼이 2개 이상 필요합니다.")
    else:
        tab1, tab2 = st.tabs(["상관행렬 히트맵 (Correlation Matrix)", "산점도 (Scatter Plot)"])
        
        with tab1:
            st.subheader("수치형 변수 간 상관행렬")
            st.write("다중공선성 경고: 상관계수가 지나치게 높은(예: 0.9 이상) 변수들을 유의 깊게 살펴보세요.")
            
            # 상관관계 계산 (변수가 너무 많을 경우를 대비해 일부 샘플링 또는 전체)
            corr_cols = st.multiselect("상관관계 분석에 포함할 변수 선택", numeric_cols, default=numeric_cols[:min(10, len(numeric_cols))])
            if corr_cols:
                corr_matrix = df[corr_cols].corr()
                col1, col2 = st.columns([2, 1])
                with col1:
                    fig_corr = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
                    st.plotly_chart(fig_corr, use_container_width=True)
                with col2:
                    st.dataframe(corr_matrix, use_container_width=True)
                
        with tab2:
            st.subheader("변수 간 산점도")
            
            col_x = st.selectbox("X축 변수:", numeric_cols, index=0)
            col_y = st.selectbox("Y축 변수:", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
            
            # 데이터 샘플링 (성능 고려)
            plot_df = df.sample(min(10000, len(df))) if len(df) > 10000 else df
            
            col1, col2 = st.columns([2, 1])
            with col1:
                fig_scatter = px.scatter(plot_df, x=col_x, y=col_y, opacity=0.5, title=f"{col_x} vs {col_y} 산점도 (최대 1만개 샘플링)")
                st.plotly_chart(fig_scatter, use_container_width=True)
            with col2:
                st.dataframe(plot_df[[col_x, col_y]], use_container_width=True)

elif menu == "Map (지도 시각화)":
    st.header("4. 지역별 생활인구 지도 시각화 (Map)")
    st.write("시간대별, 지역별(구/동) 생활인구 밀도를 확인합니다.")
    
    # 메타데이터 가져오기
    meta = get_db_metadata()
    if not meta:
        st.warning("⚠️ 사전 집계된 데이터베이스(dashboard.db)가 존재하지 않습니다. 하단 터미널에서 다음 명령어를 실행해주세요: `uv run python seoul-pops/src/build_db.py`")
        st.stop()
        
    min_time, max_time = meta["min_time"], meta["max_time"]
    selected_time = st.slider("시간대 선택 (시)", min_value=min_time, max_value=max_time, value=min_time)
    
    level = st.radio("집계 기준 선택:", ["구별", "동별"], horizontal=True)
    agg_method_label = st.radio("집계 방식:", ["합계(Sum)", "평균(Mean)"], horizontal=True)
    agg_method = 'sum' if '합계' in agg_method_label else 'mean'
    
    # SQLite DB에서 초고속 로드
    agg_df = load_map_data_from_db(level, agg_method, selected_time)
    
    geojson_data = None
    agg_col = None
    if level == "구별":
        geojson_data = load_seoul_geojson('gu')
        agg_col = meta["name_col_gu"]
    else:
        geojson_data = load_seoul_geojson('dong')
        agg_col = meta["name_col_dong"]
        
    if agg_df is not None and not agg_df.empty:
        # 📌 지역 선택 필터 추가
        available_regions = sorted(agg_df[agg_col].dropna().unique().tolist())
        selected_regions = st.multiselect("특정 지역 필터링 (비워두면 전체 표시):", available_regions, default=[])
        
        if selected_regions:
            agg_df = agg_df[agg_df[agg_col].isin(selected_regions)]
            
    if geojson_data and agg_df is not None and not agg_df.empty:
        # 총생활인구수 컬럼 찾기
        pop_col = [c for c in agg_df.columns if '인구' in c]
        if pop_col:
            target_pop_col = st.selectbox("지도에 표시할 인구 데이터 선택:", pop_col)
            
            if agg_col == target_pop_col:
                st.error("지역 이름 컬럼과 인구 데이터 컬럼이 동일하게 선택되었습니다. 올바른 지역 컬럼을 선택해 주세요.")
            else:
                # 데이터 집계 (평균 혹은 합계)
                agg_method = st.radio("집계 방식:", ["합계(Sum)", "평균(Mean)"], horizontal=True)
                if agg_method == "평균(Mean)":
                    agg_df = map_df.groupby(agg_col)[target_pop_col].mean().reset_index()
                else:
                    agg_df = map_df.groupby(agg_col)[target_pop_col].sum().reset_index()
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("코로플리스 맵")
                    # Folium 맵 생성
                    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
                    
                    folium.Choropleth(
                        geo_data=geojson_data,
                        data=agg_df,
                        columns=[agg_col, target_pop_col],
                        key_on='feature.properties.name',
                        fill_color='YlOrRd',
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name=f'{target_pop_col} ({selected_time}시, {agg_method})'
                    ).add_to(m)
                    
                    st_folium(m, use_container_width=True, height=600)
                with col2:
                    st.subheader(f"지역별 {target_pop_col} ({agg_method})")
                    st.dataframe(agg_df.sort_values(by=target_pop_col, ascending=False).reset_index(drop=True), use_container_width=True)
        else:
            st.warning("'인구'가 포함된 수치형 컬럼을 찾을 수 없습니다.")
