"""
서울 생활인구 Parquet 데이터 시각화 스크립트입니다.
EDA_Report.md에 포함될 10개 이상의 시각화 이미지를 생성합니다.
작성자: Antigravity
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
import os

def main():
    os.makedirs('images', exist_ok=True)
    file_path = 'seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet'
    print("Loading data...")
    df = pd.read_parquet(file_path)

    # 데이터 컬럼명 이상 문제 보정
    # 실제 데이터 매핑: 기준일ID -> 시간대, 시간대구분 -> 행정동코드, 행정동코드 -> 총생활인구수, 생활인구수 -> 그룹인구수
    df_renamed = df.rename(columns={
        '기준일ID': '시간(Hour)',
        '시간대구분': '행정동코드_실제',
        '행정동코드': '총생활인구수',
        '생활인구수': '그룹인구수'
    })

    print("Generating Visualizations...")
    
    # 1. 시간대별 총생활인구수 평균 추이 (선 그래프)
    plt.figure(figsize=(10,6))
    time_mean = df_renamed.groupby('시간(Hour)')['총생활인구수'].mean()
    plt.plot(time_mean.index, time_mean.values, marker='o', color='b')
    plt.title('1. 시간대별 총생활인구수 평균 추이')
    plt.xlabel('시간 (0-23)')
    plt.ylabel('평균 총생활인구수')
    plt.grid(True)
    plt.savefig('images/plot1_time_trend.png', bbox_inches='tight')
    plt.close()

    # 2. 성별 그룹인구수 박스플롯 (비교)
    plt.figure(figsize=(8,6))
    df_renamed.boxplot(column='그룹인구수', by='성별', grid=False, color=dict(boxes='g', whiskers='g', medians='r', caps='g'))
    plt.title('2. 성별 그룹 생활인구수 분포')
    plt.suptitle('')
    plt.ylabel('생활인구수')
    plt.savefig('images/plot2_gender_boxplot.png', bbox_inches='tight')
    plt.close()

    # 3. 연령대별 평균 그룹인구수 (바 차트)
    plt.figure(figsize=(12,6))
    age_mean = df_renamed.groupby('연령대')['그룹인구수'].mean().sort_values(ascending=False)
    age_mean.plot(kind='bar', color='orange')
    plt.title('3. 연령대별 평균 그룹 생활인구수')
    plt.xlabel('연령대')
    plt.ylabel('평균 인구수')
    plt.xticks(rotation=45)
    plt.savefig('images/plot3_age_barplot.png', bbox_inches='tight')
    plt.close()

    # 4. 총생활인구수 분포 (히스토그램)
    plt.figure(figsize=(10,6))
    # 데이터가 너무 커서 샘플링하여 시각화
    plt.hist(df_renamed['총생활인구수'].dropna().sample(100000), bins=50, color='skyblue', edgecolor='black')
    plt.title('4. 총생활인구수 분포 (10만 샘플링)')
    plt.xlabel('총생활인구수')
    plt.ylabel('빈도')
    plt.savefig('images/plot4_total_pop_hist.png', bbox_inches='tight')
    plt.close()

    # 5. 시간(Hour) 빈도수 (모든 데이터 포인트 수)
    plt.figure(figsize=(10,6))
    df_renamed['시간(Hour)'].value_counts().sort_index().plot(kind='bar', color='lightgreen')
    plt.title('5. 시간대별 데이터 측정 빈도')
    plt.xlabel('시간 (0-23)')
    plt.ylabel('기록 수')
    plt.savefig('images/plot5_hour_freq.png', bbox_inches='tight')
    plt.close()

    # 6. 상위 15개 행정동코드별 평균 총생활인구 (바 차트)
    plt.figure(figsize=(12,6))
    top_dongs = df_renamed.groupby('행정동코드_실제')['총생활인구수'].mean().sort_values(ascending=False).head(15)
    top_dongs.plot(kind='bar', color='purple')
    plt.title('6. 상위 15개 행정동 평균 총생활인구수')
    plt.xlabel('행정동코드')
    plt.ylabel('평균 인구수')
    plt.xticks(rotation=45)
    plt.savefig('images/plot6_top_dongs.png', bbox_inches='tight')
    plt.close()

    # 7. 그룹인구수와 총생활인구수 산점도 (샘플링)
    plt.figure(figsize=(8,8))
    sample_df = df_renamed.dropna(subset=['그룹인구수', '총생활인구수']).sample(10000)
    plt.scatter(sample_df['총생활인구수'], sample_df['그룹인구수'], alpha=0.3, color='crimson')
    plt.title('7. 총생활인구수 vs 그룹인구수 산점도 (1만 샘플링)')
    plt.xlabel('총생활인구수')
    plt.ylabel('그룹 생활인구수')
    plt.savefig('images/plot7_scatter.png', bbox_inches='tight')
    plt.close()

    # 8. 수치형 변수 상관관계 히트맵
    plt.figure(figsize=(8,6))
    corr = df_renamed[['시간(Hour)', '총생활인구수', '그룹인구수']].corr()
    plt.imshow(corr, cmap='coolwarm', interpolation='nearest', vmin=-1, vmax=1)
    plt.colorbar()
    plt.xticks(range(len(corr.columns)), corr.columns)
    plt.yticks(range(len(corr.columns)), corr.columns)
    plt.title('8. 수치형 변수 상관관계 히트맵')
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", color="black")
    plt.savefig('images/plot8_heatmap.png', bbox_inches='tight')
    plt.close()

    # 9. 성별 및 특정 연령대(20대, 30대) 평균 인구 그룹 바 차트
    plt.figure(figsize=(10,6))
    target_ages = ['20세부터24세', '25세부터29세', '30세부터34세', '35세부터39세']
    age_gender = df_renamed[df_renamed['연령대'].isin(target_ages)].groupby(['연령대', '성별'])['그룹인구수'].mean().unstack()
    age_gender.plot(kind='bar', ax=plt.gca(), color=['#1f77b4', '#ff7f0e'])
    plt.title('9. 2030 연령대별/성별 평균 그룹인구수')
    plt.xlabel('연령대')
    plt.ylabel('평균 인구수')
    plt.xticks(rotation=0)
    plt.savefig('images/plot9_age_gender.png', bbox_inches='tight')
    plt.close()

    # 10. 시간대별 데이터 밀도 플롯 (바이올린 플롯 유사)
    plt.figure(figsize=(12,6))
    target_hours = [0, 6, 12, 18]
    data_to_plot = [df_renamed[df_renamed['시간(Hour)'] == h]['총생활인구수'].dropna().sample(5000) for h in target_hours]
    plt.violinplot(data_to_plot, showmeans=True)
    plt.xticks([1, 2, 3, 4], [f"{h}시" for h in target_hours])
    plt.title('10. 주요 시간대별 총생활인구수 분포 (바이올린 플롯)')
    plt.ylabel('총생활인구수')
    plt.savefig('images/plot10_violin.png', bbox_inches='tight')
    plt.close()

    # 11. TF-IDF 텍스트 마이닝 (연령대 텍스트 기반)
    tfidf = TfidfVectorizer(max_features=30)
    # 연령대 컬럼이 범주형이므로, 해당 고유값을 바탕으로 TF-IDF 추출 시뮬레이션
    tfidf_matrix = tfidf.fit_transform(df_renamed['연령대'].unique())
    keywords = tfidf.get_feature_names_out()
    sums = tfidf_matrix.sum(axis=0)
    keyword_freq = [(keyword, sums[0, idx]) for keyword, idx in tfidf.vocabulary_.items()]
    keyword_freq = sorted(keyword_freq, key=lambda x: x[1], reverse=True)
    kw_df = pd.DataFrame(keyword_freq, columns=['Keyword', 'TF-IDF Score'])
    
    plt.figure(figsize=(10,6))
    plt.bar(kw_df['Keyword'], kw_df['TF-IDF Score'], color='teal')
    plt.title('11. 연령대 텍스트 TF-IDF 상위 키워드')
    plt.xlabel('키워드')
    plt.ylabel('TF-IDF Score')
    plt.xticks(rotation=45)
    plt.savefig('images/plot11_tfidf.png', bbox_inches='tight')
    plt.close()

    print("All visualizations saved in 'images/' folder.")

if __name__ == "__main__":
    main()
