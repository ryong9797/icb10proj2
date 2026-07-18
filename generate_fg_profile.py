"""
fg-data-profiling을 이용한 데이터 프로파일링 스크립트입니다.
LOCAL_PEOPLE_DONG 데이터셋의 크기(854만 건)를 고려하여 랜덤 1만 개 샘플링을 수행한 후,
프로파일링 결과를 HTML로 출력합니다.
"""
import pandas as pd
from data_profiling import ProfileReport

def main():
    file_path = 'seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet'
    print(f"Loading data from {file_path}...")
    df = pd.read_parquet(file_path)

    # 전체 데이터를 프로파일링하면 시간이 너무 오래 걸리므로 1만건 샘플링
    print("Sampling 10,000 rows for faster profiling...")
    sample_df = df.sample(10000, random_state=42)

    # 컬럼 네이밍 아노말리 보정 (EDA 분석 내용과 통일)
    sample_df = sample_df.rename(columns={
        '기준일ID': '시간(Hour)',
        '시간대구분': '행정동코드_실제',
        '행정동코드': '총생활인구수',
        '생활인구수': '그룹인구수'
    })

    print("Generating profiling report. This may take a moment...")
    profile = ProfileReport(sample_df, title="Seoul Pops FG Data Profiling Report", explorative=True)
    
    output_html = "seoul-pops/report/fg_profile.html"
    profile.to_file(output_html)
    print(f"Profile report successfully generated and saved to {output_html}")

if __name__ == "__main__":
    main()
