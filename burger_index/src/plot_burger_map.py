"""
이 스크립트는 버거지수가 높은 지역을 지도 위에 시각화하는 역할을 합니다.
- 조건 1: 버거지수 1.5 이상인 지역 필터링
- 조건 2: 위도_중간값, 경도_중간값을 기반으로 지도에 마커 표시
- 조건 3: 버거지수에 비례하여 마커 크기 및 색상 설정
- 결과물: 인터랙티브 HTML 지도 (Plotly)
작성일: 2026-07-04
"""

import pandas as pd
import numpy as np
import plotly.express as px
import os

# 1. 데이터 불러오기 (실행 위치에 상관없이 절대 경로로 파일 찾기)
# 현재 스크립트 위치가 src 안에 있을 경우 상위 상위 폴더로 이동하여 data 경로를 찾음
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
file_path = os.path.join(base_dir, 'burger_index', 'data', 'crosstab_geo_result.csv')

df = pd.read_csv(file_path)

# 2. 전처리 및 필터링
# 결측치(NaN) 제거
df = df.dropna(subset=['버거지수', '위도_중간값', '경도_중간값'])
# 무한대(inf) 값 제거 (롯데리아 매장이 0개여서 inf가 된 경우 제외)
df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['버거지수'])

# 버거지수가 1.5 이상인 데이터만 필터링
high_burger_df = df[df['버거지수'] >= 1.5].copy()

# 3. Plotly Mapbox를 이용한 인터랙티브 산점도 시각화
fig = px.scatter_mapbox(
    high_burger_df,
    lat="위도_중간값",
    lon="경도_중간값",
    hover_name="시도시군구명",          # 마우스 오버 시 지역명 표시
    hover_data={"버거지수": True, "위도_중간값": False, "경도_중간값": False},
    color="버거지수",                 # 버거지수에 따라 마커 색상 다르게
    size="버거지수",                  # 버거지수에 비례하여 마커 크기 설정
    color_continuous_scale=px.colors.sequential.YlOrRd,  # 색상 팔레트 (노랑 -> 빨강)
    size_max=25,                    # 마커 최대 크기
    zoom=6,                         # 초기 줌 레벨
    center={"lat": 35.9, "lon": 127.7},  # 대한민국 대략적인 중심 좌표
    mapbox_style="carto-positron",  # 외부 토큰 없이 무료로 쓸 수 있는 지도 스타일
    title="🍔 버거지수 1.5 이상 고밀도 지역 지도 시각화"
)

# 여백 조정
fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

# 4. 결과물을 HTML 파일로 저장 (스크립트가 위치한 폴더에 저장)
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'burger_index_map.html')
fig.write_html(output_path)
print(f"✅ 시각화 완료! '{output_path}' 파일을 더블클릭하여 웹 브라우저에서 열어보세요.")
