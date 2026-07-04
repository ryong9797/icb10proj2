"""
이 스크립트는 기본 EDA(탐색적 데이터 분석) 결과를 보여주는 Streamlit 페이지입니다.
- 역할: 기존 생성된 시각화 이미지를 화면에 배치
- 작성일: 2026-07-04
"""
import streamlit as st
import os

st.title("📊 1. 기본 EDA (탐색적 데이터 분석)")

# 이미지 경로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
image_dir = os.path.join(base_dir, "images")

images = [
    ("브랜드별 매장 수 (Barplot)", "barplot_brand.png"),
    ("브랜드별 분포 (Box/Violin Plot)", "box_violin_brand.png"),
    ("상관관계 히트맵 (Heatmap)", "heatmap_brand.png"),
    ("쌍체 산점도 (Pairplot)", "pairplot_brand.png"),
    ("고급 쌍체 산점도 (Pairplot Advanced)", "pairplot_brand_advanced.png")
]

st.write("버거 브랜드별 기초 통계 및 시각화 결과입니다.")

for title, file_name in images:
    img_path = os.path.join(image_dir, file_name)
    if os.path.exists(img_path):
        st.subheader(title)
        st.image(img_path, use_container_width=True)
    else:
        st.warning(f"이미지 파일을 찾을 수 없습니다: {file_name}")
