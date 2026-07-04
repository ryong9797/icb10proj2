"""
이 스크립트는 대한민국 시군구 단위 격자 지도(카토그램)를 이용해 버거지수를 시각화하는 페이지입니다.
- 역할: draw_korea 격자 데이터와 버거지수를 결합하여 블록 맵 시각화
- 작성일: 2026-07-04
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
import requests

st.title("🔲 4. 전국 시군구단위 버거지수 카토그램")
st.write("각 시군구를 동일한 크기의 블록으로 표시하여, 한눈에 전국적인 버거지수 분포를 비교할 수 있는 카토그램 지도입니다.")

@st.cache_data
def load_draw_korea():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    file_path = os.path.join(data_dir, 'draw_korea.csv')
    
    if not os.path.exists(file_path):
        url = "https://raw.githubusercontent.com/PinkWink/DataScience/master/data/05.%20draw_korea.csv"
        r = requests.get(url)
        with open(file_path, 'wb') as f:
            f.write(r.content)
            
    return pd.read_csv(file_path)

@st.cache_data
def load_burger_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'crosstab_geo_result.csv')
    df = pd.read_csv(file_path)
    return df

def get_cartogram_id(full_name):
    sido_dict = {
        '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
        '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
        '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
        '강원특별자치도': '강원', '강원도': '강원', '충청북도': '충북', '충청남도': '충남',
        '전라북도': '전북', '전북특별자치도': '전북', '전라남도': '전남', 
        '경상북도': '경북', '경상남도': '경남', '제주특별자치도': '제주'
    }
    parts = full_name.split()
    if not parts: return ""
    
    sido = sido_dict.get(parts[0], parts[0][:2])
    if len(parts) == 1: return sido
    
    sigungu = parts[1]
    if sigungu == '고성군':
        return '고성(강원)' if '강원' in sido else '고성(경남)'
    
    if sido == '세종': return '세종'
    
    if parts[1] == '미추홀구' and sido == '인천': return '인천 남'
    
    if sido in ['서울', '부산', '대구', '인천', '광주', '대전', '울산']:
        if len(parts) >= 2:
            return sido + ' ' + parts[1][:-1]
            
    # 특정 시(구 단위로 나뉘어 있으나 카토그램은 시 단위로 통합하는 곳들)
    if len(parts) >= 3 and sigungu.endswith('시'):
        return sigungu[:-1]
        
    return sigungu[:-1]

with st.spinner("카토그램을 그리는 중입니다..."):
    draw_korea = load_draw_korea()
    burger_df = load_burger_data()
    
    burger_df['ID'] = burger_df['시도시군구명'].apply(get_cartogram_id)
    
    # 구 단위 데이터가 시 단위로 통합되는 경우(예: 수원시) 평균 산출
    agg_df = burger_df.groupby('ID')[['버거지수']].mean().reset_index()
    
    # 격자 맵과 병합
    map_data = pd.merge(draw_korea, agg_df, how='left', on='ID')
    
    # 맵 그리기 로직
    fig, ax = plt.subplots(figsize=(9, 12))
    
    # 블록 채우기 (결측치는 회색)
    # y축이 아래로 갈수록 커지도록 invert
    map_pivot = map_data.pivot(index='y', columns='x', values='버거지수')
    masked_map = np.ma.masked_where(np.isnan(map_pivot), map_pivot)
    
    # vmin, vmax 설정
    vmin = map_data['버거지수'].min()
    vmax = map_data['버거지수'].max()
    
    c = ax.pcolor(masked_map, cmap='Blues', edgecolor='#aaaaaa', linewidth=0.5, vmin=vmin, vmax=vmax)
    
    # 텍스트 추가
    whitelabelmin = (vmax - vmin) * 0.4 + vmin
    for idx, row in map_data.iterrows():
        # 이름 분리 (예: '서울 종로' -> '서울\n종로')
        dispname = row['ID']
        if len(dispname.split()) == 2:
            dispname = f"{dispname.split()[0]}\n{dispname.split()[1]}"
            
        annocolor = 'black'
        if not np.isnan(row['버거지수']) and row['버거지수'] > whitelabelmin:
            annocolor = 'white'
            
        ax.annotate(dispname, (row['x']+0.5, row['y']+0.5), weight='bold',
                    fontsize=9, ha='center', va='center', color=annocolor)
                    
    ax.invert_yaxis()
    ax.axis('off')
    
    # 컬러바 추가
    cb = fig.colorbar(c, ax=ax, shrink=0.3, aspect=10)
    cb.set_label('버거지수')
    
    st.pyplot(fig)
    
    st.markdown("**(참고)** 회색 블록은 데이터가 없는 지역입니다. 행정구역 개편(미추홀구 등)이나 통합 시(수원시 등) 데이터는 최대한 맵핑되도록 전처리하였습니다.")
