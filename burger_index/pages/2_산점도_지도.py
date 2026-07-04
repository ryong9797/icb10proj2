"""
이 스크립트는 버거지수를 활용한 산점도 지도를 보여주는 Streamlit 페이지입니다.
- 역할: Folium을 사용해 위도/경도 기준으로 버거지수를 나타내는 CircleMarker 시각화
- 작성일: 2026-07-04
"""
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import os

st.title("📍 2. 산점도 지도 (Folium)")

# 데이터 로드
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'crosstab_geo_result.csv')
    df = pd.read_csv(file_path)
    df = df.dropna(subset=['버거지수', '위도_중간값', '경도_중간값'])
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['버거지수'])
    return df

df = load_data()

# 사이드바 필터
min_index = st.slider("최소 버거지수 필터", min_value=0.0, max_value=float(df['버거지수'].max()), value=1.0, step=0.1)

filtered_df = df[df['버거지수'] >= min_index]

st.write(f"버거지수가 **{min_index}** 이상인 지역의 수: **{len(filtered_df)}**개")

# 지도 중심 설정
map_center = [35.9, 127.7]
m = folium.Map(location=map_center, zoom_start=7, tiles='CartoDB positron')

for idx, row in filtered_df.iterrows():
    folium.CircleMarker(
        location=[row['위도_중간값'], row['경도_중간값']],
        radius=row['버거지수'] * 5, # 버거지수에 비례하는 크기
        popup=f"{row['시도시군구명']}<br>버거지수: {row['버거지수']:.2f}",
        tooltip=row['시도시군구명'],
        color="crimson",
        fill=True,
        fill_color="crimson",
        fill_opacity=0.6,
    ).add_to(m)

# 지도를 Streamlit에 출력
st_data = st_folium(m, width=800, height=600)
