"""
이 스크립트는 매핑 엑셀 파일에서 '연남동'과 '성수동'의 코드를 추출하고,
Parquet 데이터에서 해당 행정동을 필터링한 후, 시간대별 및 행정동별 생활인구수 선그래프를 연령대별 서브플롯으로 시각화합니다.
"""
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
import sys

def main():
    excel_path = r"../data/행정동코드_매핑정보_20241218.xlsx"
    parquet_path = r"../data/LOCAL_PEOPLE_DONG_202606.parquet"
    output_image = r"../images/population_lineplot.png"
    
    # 이미지 저장 경로 확인
    os.makedirs(os.path.dirname(output_image), exist_ok=True)
    
    print("1. 행정동코드 매핑정보 불러오기 및 타겟 행정동 필터링...")
    try:
        df_map = pd.read_excel(excel_path)
    except Exception as e:
        print(f"엑셀 파일을 읽는 데 실패했습니다. 'openpyxl'이 설치되어 있는지 확인하세요: {e}")
        sys.exit(1)
        
    # 컬럼 찾기 유연하게 처리
    dong_cols = [c for c in df_map.columns if '동명' in str(c) or '행정동' in str(c)]
    dong_col = dong_cols[-1] if len(dong_cols) > 0 else df_map.columns[2]
        
    haeng_cols = [c for c in df_map.columns if '행자부' in str(c)]
    stat_cols = [c for c in df_map.columns if '통계청' in str(c)]
    
    # 연남동, 성수동 문자열 포함 필터링
    target_mask = df_map[dong_col].astype(str).str.contains('연남|성수', na=False)
    target_dongs = df_map[target_mask].copy()
    
    print(f"추출된 타겟 동 목록:\n{target_dongs[dong_col].tolist()}")
    
    print("\n2. Parquet 데이터 로드 및 필터링...")
    df_pq = pd.read_parquet(parquet_path)
    pq_code_col = '행정동코드'
    
    # Parquet에 저장된 코드의 자릿수를 파악하여 8자리(통계청) 또는 10자리(행자부) 등 매핑 맞춤 처리
    sample_code = df_pq[pq_code_col].dropna().iloc[0]
    sample_len = len(str(int(sample_code)))
    
    code_col = None
    if sample_len == 8 and len(stat_cols) > 0:
        code_col = stat_cols[0]
        print("Parquet 데이터가 통계청 코드(8자리) 형식을 사용하므로 통계청 코드로 매핑합니다.")
    elif len(haeng_cols) > 0:
        code_col = haeng_cols[0]
        print("행자부 코드로 매핑을 시도합니다.")
    else:
        code_col = df_map.columns[0]
        print("기본 코드 컬럼으로 매핑을 시도합니다.")
        
    # 코드: 동명 딕셔너리 생성
    dong_mapping = dict(zip(target_dongs[code_col].astype(int), target_dongs[dong_col]))
    target_codes = list(dong_mapping.keys())
    
    # Parquet 필터링
    df_filtered = df_pq[df_pq[pq_code_col].isin(target_codes)].copy()
    
    if df_filtered.empty:
        print("경고: 코드가 일치하는 데이터가 Parquet 파일에 없습니다! 매핑 방식을 확인해 주세요.")
        print(f"매핑 시도 코드 목록: {target_codes}")
        sys.exit(1)
        
    df_filtered['행정동명'] = df_filtered[pq_code_col].map(dong_mapping)
    print(f"데이터 추출 완료! 필터링된 건수: {len(df_filtered):,}")
    
    print("\n3. 데이터 시각화 시작...")
    # 시간대별, 행정동별, 연령대별 평균 생활인구수 집계
    df_agg = df_filtered.groupby(['시간대구분', '행정동명', '연령대'], observed=True)['생활인구수'].mean().reset_index()
    
    age_groups = sorted(df_agg['연령대'].unique())
    dongs = df_agg['행정동명'].unique()
    
    # "y축에는 연령대, x축에는 시간대가 그려지도록" 요청을 반영하기 위해,
    # 연령대별로 Y축을 분할하는 서브플롯(Grid)을 생성하여 수직 방향(Y축)으로 연령대를 배치합니다.
    fig, axes = plt.subplots(nrows=len(age_groups), ncols=1, figsize=(10, 2 * len(age_groups)), sharex=True)
    if len(age_groups) == 1:
        axes = [axes]
        
    color_map = dict(zip(dongs, plt.cm.tab10.colors[:len(dongs)]))
    
    for ax, age in zip(axes, age_groups):
        df_sub = df_agg[df_agg['연령대'] == age]
        for dong in dongs:
            df_dong = df_sub[df_sub['행정동명'] == dong]
            if not df_dong.empty:
                ax.plot(df_dong['시간대구분'], df_dong['생활인구수'], marker='o', markersize=4, 
                        label=dong, color=color_map[dong])
        
        ax.set_ylabel(f'{age}\n인구수', rotation=0, labelpad=40, ha='center', va='center')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # 첫 번째 플롯에만 범례 추가
        if ax == axes[0]:
            ax.legend(title='행정동명', loc='upper right', bbox_to_anchor=(1.2, 1.0))
            
    axes[-1].set_xlabel('시간대구분 (시)', fontsize=12)
    fig.suptitle('시간대별 / 행정동별 / 연령대별 생활인구수 비교', fontsize=18, y=1.01)
    
    plt.tight_layout()
    plt.savefig(output_image, bbox_inches='tight', dpi=150)
    print(f"\n그래프 시각화가 완료되었습니다!\n이미지 저장 경로: {os.path.abspath(output_image)}")

if __name__ == "__main__":
    main()
