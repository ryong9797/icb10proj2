"""
fg-data-profiling을 이용해 마포구 연남동(행정동코드: 11440710 / 11140710) 데이터만 추출하여 
프로파일링을 진행하는 스크립트입니다.
"""
import pandas as pd
from data_profiling import ProfileReport # 구 ydata_profiling

def main():
    file_path = 'seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet'
    print(f"Loading data from {file_path}...")
    df = pd.read_parquet(file_path)

    # 마포구 연남동 행정동코드 필터링 (컬럼 밀림 아노말리 현상 보정 반영)
    # 일반적인 서울 행정동코드를 감안하여 연남동으로 알려진 두 가지 코드를 모두 포함하여 필터링
    yeonnam_codes = [11440710, 11140710] 
    
    print("Filtering data for Yeonnam-dong...")
    yeonnam_df = df[df['시간대구분'].isin(yeonnam_codes)].copy()

    # 컬럼명 맵핑 교정
    yeonnam_df = yeonnam_df.rename(columns={
        '기준일ID': '시간(Hour)',
        '시간대구분': '행정동코드_실제',
        '행정동코드': '총생활인구수',
        '생활인구수': '그룹인구수'
    })

    print(f"Total rows for Yeonnam-dong: {len(yeonnam_df)}")
    
    if len(yeonnam_df) == 0:
        print("연남동 데이터가 존재하지 않습니다. 코드를 다시 확인해 주세요.")
        return

    print("Generating profiling report. This may take a moment...")
    profile = ProfileReport(yeonnam_df, title="Yeonnam-dong FG Data Profiling Report", explorative=True)
    
    output_html = "seoul-pops/report/yeonnam_profile.html"
    profile.to_file(output_html)
    print(f"Profile report successfully generated and saved to {output_html}")

if __name__ == "__main__":
    main()
