"""
이 스크립트는 행정구역별(Choropleth) 지도를 보여주는 Streamlit 페이지입니다.
- 역할: Folium Choropleth를 사용하여 행정구역별 버거지수 밀도 시각화
- GeoJSON: southkorea-maps 저장소 데이터 활용
- 작성일: 2026-07-04
"""
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import requests
import os

st.title("🗺️ 3. 행정구역별 지도 (Choropleth)")

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_municipalities_geo_simple.json"
    r = requests.get(url)
    return r.json()

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'crosstab_geo_result.csv')
    df = pd.read_csv(file_path)
    df = df.dropna(subset=['버거지수'])
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['버거지수'])
    return df

with st.spinner("데이터와 지도를 불러오는 중입니다..."):
    try:
        geo_data = load_geojson()
        df = load_data()
        
        # GeoJSON에 있는 모든 name 추출
        geo_names = [f['properties']['name'] for f in geo_data['features']]
        
        # 이름 매핑 함수
        def get_match_name(full_name):
            parts = full_name.split()
            if not parts: return full_name
            
            # 1. 마지막 단어 (예: 서귀포시, 종로구) 매칭
            if parts[-1] in geo_names:
                return parts[-1]
            
            # 2. 마지막 두 단어 (예: 수원시 권선구) 매칭
            if len(parts) >= 2:
                combined = parts[-2] + ' ' + parts[-1]
                if combined in geo_names:
                    return combined
                # 3. 구 대신 시 이름으로 매칭 (수원시 권선구 -> 수원시)
                if parts[-2] in geo_names:
                    return parts[-2]
                    
            return full_name

        df['match_name'] = df['시도시군구명'].apply(get_match_name)
        
        # 매칭 성공률 확인
        matched_count = df['match_name'].isin(geo_names).sum()
        st.write(f"총 {len(df)}개의 행정구역 중 **{matched_count}**개가 지도 데이터와 매칭되었습니다.")

        # Folium 지도 생성
        map_center = [35.9, 127.7]
        m = folium.Map(location=map_center, zoom_start=7, tiles='CartoDB positron')

        # Choropleth 레이어 추가
        folium.Choropleth(
            geo_data=geo_data,
            name='choropleth',
            data=df,
            columns=['match_name', '버거지수'],
            key_on='feature.properties.name',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='버거지수'
        ).add_to(m)

        # 지도를 Streamlit에 출력
        st_data = st_folium(m, width=800, height=600)
    except Exception as e:
        st.error(f"지도 렌더링 중 오류가 발생했습니다: {e}")
