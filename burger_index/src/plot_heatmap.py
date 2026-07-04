"""
교차표(crosstab_geo_result.csv) 데이터를 바탕으로
각 브랜드별 지역 매장 수 간의 상관계수를 히트맵(Heatmap)으로 시각화하는 스크립트입니다.
사용자 요청에 따라 삼각행렬 마스크 처리 없이 전체 행렬을 보여줍니다.
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 한글 폰트 설정 (Windows 환경 기준 '맑은 고딕')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지

file_path = 'burger_index/data/crosstab_geo_result.csv'

try:
    # 1. 데이터 로드 및 전처리
    df = pd.read_csv(file_path)
    if '합계' in df['시도시군구명'].values:
        df = df[df['시도시군구명'] != '합계']
        
    target_columns = ['KFC', '롯데리아', '맥도날드', '버거킹']
    
    # 2. 상관계수 행렬 계산
    corr_matrix = df[target_columns].corr()
    
    # 3. 히트맵 시각화 설정
    print("마스크 처리가 없는 상관계수 히트맵을 생성 중입니다...")
    plt.figure(figsize=(8, 6))
    
    # annot=True 로 수치 표시, cmap='coolwarm' 으로 색상 지정
    # mask 속성을 사용하지 않아 전체 사각형 행렬이 시각화됨
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='Blues', 
                vmin=-1, vmax=1, linewidths=0.5, cbar_kws={"shrink": .8})
    
    plt.title("지역별 주요 버거 브랜드 매장 수 상관계수 히트맵", fontsize=16, pad=15)
    
    # 4. 이미지 파일로 저장
    output_path = 'burger_index/data/heatmap_brand.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 히트맵 시각화 이미지가 성공적으로 저장되었습니다: {output_path}")
    
    # 5. 화면에 시각화 창 띄우기
    plt.show()

except Exception as e:
    print(f"Error: {e}")
