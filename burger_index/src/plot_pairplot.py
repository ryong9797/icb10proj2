"""
교차표(crosstab_geo_result.csv) 데이터를 바탕으로
각 브랜드별 지역 매장 수 간의 상관관계를 시각화하는 페어플롯(Pairplot) 스크립트입니다.
사용자 요청에 따라 상삼각 행렬만 표시하고, 회귀선과 함께 상관계수를 우측 상단에 표기합니다.
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
    
    print("요청하신 조건(상삼각행렬, 회귀선, 상관계수)을 반영하여 시각화를 생성 중입니다...")

    # 상관계수를 계산하고 회귀선과 함께 그리는 커스텀 함수
    def corrfunc(x, y, **kws):
        # 회귀선 그리기 (regplot)
        ax = sns.regplot(x=x, y=y, **kws)
        
        # 상관계수 계산
        r = x.corr(y)
        
        # 우측 상단에 상관계수 텍스트 추가
        ax.annotate(f'r = {r:.2f}', xy=(0.95, 0.95), xycoords='axes fraction',
                    ha='right', va='top', fontsize=12, fontweight='bold', color='darkblue',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

    # 2. PairGrid 객체 생성
    g = sns.PairGrid(df[target_columns], height=2.5)
    
    # 3. 상삼각 행렬에 커스텀 함수(회귀선 + 상관계수) 매핑
    g.map_upper(corrfunc, scatter_kws={'alpha': 0.5}, line_kws={'color': 'red', 'alpha': 0.8})
    
    # 4. 대각 행렬에 밀도 그래프(kde) 매핑
    g.map_diag(sns.kdeplot, fill=True, color='gray')
    
    # 5. 하삼각 행렬은 마스크 처리 (숨기기)
    for i in range(g.axes.shape[0]):
        for j in range(g.axes.shape[1]):
            if i > j: # 하삼각 행렬인 경우
                g.axes[i, j].set_visible(False)

    g.fig.suptitle("지역별 주요 버거 브랜드 매장 수 상관관계 (상삼각 행렬 & 상관계수)", y=1.05, fontsize=16)
    
    # 6. 이미지 파일로 저장
    output_path = 'burger_index/data/pairplot_brand_advanced.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 개선된 페어플롯 시각화 이미지가 성공적으로 저장되었습니다: {output_path}")
    
    # 7. 화면에 시각화 창 띄우기
    plt.show()

except Exception as e:
    print(f"Error: {e}")
