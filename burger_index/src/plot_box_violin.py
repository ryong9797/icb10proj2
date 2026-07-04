"""
교차표(crosstab_geo_result.csv) 데이터를 바탕으로
지역별 각 브랜드의 매장 수 분포를 박스플롯(Boxplot)과 바이올린플롯(Violinplot)으로 시각화하는 스크립트입니다.
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
    
    # 전체 합계(총 빈도수)는 단일 값이므로 박스플롯/바이올린플롯을 그릴 수 없습니다.
    # 따라서 지역별 데이터 분포를 볼 수 있도록 마지막 '합계' 행은 제외합니다.
    if '합계' in df['시도시군구명'].values:
        df = df[df['시도시군구명'] != '합계']
        
    target_columns = ['KFC', '롯데리아', '맥도날드', '버거킹']
    
    # 2. 시각화를 위해 화면 분할 (1행 2열)
    print("박스플롯과 바이올린플롯을 생성 중입니다...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Seaborn에서 카테고리별로 편하게 그리기 위해 데이터를 긴 형태(Long-form)로 변환(Melt)
    df_melt = df.melt(id_vars=['시도시군구명'], value_vars=target_columns, 
                      var_name='브랜드', value_name='매장수')
    
    # 3. 박스플롯 (Boxplot) 시각화 - 좌측
    # 이상치(outlier)와 사분위수를 명확하게 보여줍니다.
    sns.boxplot(x='브랜드', y='매장수', data=df_melt, ax=axes[0], palette='Set2')
    axes[0].set_title("지역별 매장 수 분포 (Boxplot)", fontsize=14, pad=10)
    axes[0].set_xlabel("브랜드명", fontsize=12)
    axes[0].set_ylabel("해당 지역 매장 수", fontsize=12)
    
    # 4. 바이올린플롯 (Violinplot) 시각화 - 우측
    # 박스플롯의 정보에 더해 데이터의 밀도(형태)까지 함께 보여줍니다.
    sns.violinplot(x='브랜드', y='매장수', data=df_melt, ax=axes[1], palette='Set3', inner='quartile')
    axes[1].set_title("지역별 매장 수 분포 (Violinplot)", fontsize=14, pad=10)
    axes[1].set_xlabel("브랜드명", fontsize=12)
    axes[1].set_ylabel("해당 지역 매장 수", fontsize=12)
    
    plt.tight_layout()
    
    # 5. 이미지 파일로 저장
    output_path = 'burger_index/data/box_violin_brand.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 박스플롯 & 바이올린플롯 시각화 이미지가 성공적으로 저장되었습니다: {output_path}")
    
    # 6. 화면에 시각화 창 띄우기
    plt.show()

except Exception as e:
    print(f"Error: {e}")
