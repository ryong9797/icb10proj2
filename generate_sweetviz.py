"""
Sweetviz를 이용한 대체 데이터 프로파일링 스크립트입니다.
fg-data-profiling 설치 실패(llvmlite 빌드 오류)에 대한 대안으로 작성되었습니다.
"""
import pandas as pd
import sweetviz as sv

def main():
    file_path = 'seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet'
    print(f"Loading data from {file_path}...")
    df = pd.read_parquet(file_path)

    print("Sampling 10,000 rows for faster profiling...")
    sample_df = df.sample(10000, random_state=42)

    sample_df = sample_df.rename(columns={
        '기준일ID': '시간(Hour)',
        '시간대구분': '행정동코드_실제',
        '행정동코드': '총생활인구수',
        '생활인구수': '그룹인구수'
    })

    print("Generating Sweetviz profiling report...")
    report = sv.analyze(sample_df)
    
    output_html = "seoul-pops/report/sweetviz_profile.html"
    report.show_html(filepath=output_html, open_browser=False)
    print(f"Profile report successfully generated and saved to {output_html}")

if __name__ == "__main__":
    main()
