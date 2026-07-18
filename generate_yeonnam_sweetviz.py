"""
Sweetviz를 이용해 마포구 연남동(행정동코드: 11440710 / 11140710) 데이터만 추출하여 
프로파일링을 진행하는 대체 스크립트입니다.
"""
import os
import pandas as pd
import sweetviz as sv
import webbrowser

def main():
    file_path = 'seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet'
    print(f"Loading data from {file_path}...")
    df = pd.read_parquet(file_path)

    yeonnam_codes = [11440710, 11140710]
    yeonnam_df = df[df['시간대구분'].isin(yeonnam_codes)].copy()

    yeonnam_df = yeonnam_df.rename(columns={
        '기준일ID': '시간(Hour)',
        '시간대구분': '행정동코드_실제',
        '행정동코드': '총생활인구수',
        '생활인구수': '그룹인구수'
    })

    print(f"Total rows for Yeonnam-dong: {len(yeonnam_df)}")
    
    if len(yeonnam_df) == 0:
        print("연남동 데이터가 존재하지 않습니다.")
        return

    print("Generating Sweetviz profiling report...")
    report = sv.analyze(yeonnam_df)
    
    output_html = "seoul-pops/report/yeonnam_sweetviz_profile.html"
    report.show_html(filepath=output_html, open_browser=False)
    print(f"Profile report successfully generated and saved to {output_html}")
    
    # 사용자 로컬 브라우저 강제 띄우기
    abs_path = os.path.abspath(output_html)
    print(f"Opening browser for {abs_path}...")
    webbrowser.open(f"file:///{abs_path}")

if __name__ == "__main__":
    main()
