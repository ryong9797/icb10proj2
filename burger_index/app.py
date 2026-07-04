"""
이 스크립트는 버거지수 대시보드의 메인 진입점 역할을 합니다.
- 역할: Streamlit Multi-page 구성을 위한 네비게이션 설정
- 작성일: 2026-07-04
"""
import streamlit as st

st.set_page_config(page_title="버거지수 대시보드", page_icon="🍔", layout="wide")

st.title("🍔 대한민국 버거지수 대시보드")
st.markdown("왼쪽 사이드바에서 메뉴를 선택하여 다양한 분석 결과를 확인하세요.")

import os

base_dir = os.path.dirname(os.path.abspath(__file__))

pages = {
    "버거지수 분석": [
        st.Page(os.path.join(base_dir, "pages", "1_기본_EDA.py"), title="1. 기본 EDA", icon="📊"),
        st.Page(os.path.join(base_dir, "pages", "2_산점도_지도.py"), title="2. 산점도 지도", icon="📍"),
        st.Page(os.path.join(base_dir, "pages", "3_행정구역별_지도.py"), title="3. 행정구역별 지도", icon="🗺️"),
        st.Page(os.path.join(base_dir, "pages", "4_카토그램.py"), title="4. 카토그램 지도", icon="🔲"),
    ]
}

pg = st.navigation(pages)
pg.run()
