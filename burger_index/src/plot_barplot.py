"""
교차표(crosstab_geo_result.csv) 데이터를 바탕으로
각 주요 버거 브랜드별 전체 매장 수(총 빈도수)를 막대 그래프로 시각화하는 스크립트입니다.
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 한글 폰트 설정 (Windows 환경 기준 '맑은 고딕')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지

file_path = 'burger_index/data/crosstab_geo_result.csv'

try:
    # 1. 데이터 로드
    df = pd.read_csv(file_path)
    
    # 2. '합계' 행을 찾아 각 브랜드별 총 빈도수 추출
    # 시도시군구명이 '합계'인 행을 필터링합니다.
    total_row = df[df['시도시군구명'] == '합계']
    
    if not total_row.empty:
        # 타겟 브랜드 리스트
        target_brands = ['KFC', '롯데리아', '맥도날드', '버거킹']
        
        # 각 브랜드의 총합 값을 딕셔너리로 추출 후 데이터프레임 변환
        brand_counts = {brand: total_row.iloc[0][brand] for brand in target_brands}
        df_counts = pd.DataFrame(list(brand_counts.items()), columns=['브랜드', '매장수'])
        
        # 매장 수가 많은 순서대로 정렬 (옵션)
        df_counts = df_counts.sort_values(by='매장수', ascending=False)
        
        # 3. 막대 그래프 시각화
        print("브랜드별 총 빈도수 막대그래프를 생성 중입니다...")
        plt.figure(figsize=(8, 6))
        
        # 막대그래프 생성
        ax = sns.barplot(x='브랜드', y='매장수', data=df_counts, palette='Set2')
        
        # 막대 위에 구체적인 숫자(빈도수) 표기
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(f'{int(height)}개', 
                        (p.get_x() + p.get_width() / 2., height), 
                        ha='center', va='bottom', fontsize=12, fontweight='bold',
                        xytext=(0, 5), textcoords='offset points')
            
        plt.title("주요 버거 브랜드별 전국 총 매장 수", fontsize=16, pad=15)
        plt.xlabel("브랜드명", fontsize=13)
        plt.ylabel("매장 수", fontsize=13)
        
        # y축 범위 여유있게 조정 (텍스트가 잘리지 않도록)
        plt.ylim(0, df_counts['매장수'].max() * 1.15)
        
        # 4. 이미지 파일로 저장
        output_path = 'burger_index/data/barplot_brand.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 막대그래프 이미지가 성공적으로 저장되었습니다: {output_path}")
        
        # 5. 화면에 시각화 창 띄우기
        plt.show()
    else:
        print("데이터에서 '합계' 행을 찾을 수 없습니다. 원본 데이터를 확인해 주세요.")

except Exception as e:
    print(f"Error: {e}")
