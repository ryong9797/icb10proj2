"""
이 스크립트는 교보문고 베스트셀러 데이터(kyobobook_bestseller.csv)의
탐색적 데이터 분석(EDA)을 수행하기 위해 작성되었습니다.
기초 통계량 추출, 시각화(10종 이상) 및 TF-IDF 키워드 분석을 수행합니다.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# Create images folder
os.makedirs('images', exist_ok=True)

# 1. Load data
df = pd.read_csv('kyobobook/data/kyobobook_bestseller.csv')

with open('eda_results.txt', 'w', encoding='utf-8') as f:
    f.write("=== 1. Basic Info ===\n")
    f.write("Shape: {}\n".format(df.shape))
    f.write("Duplicates: {}\n".format(df.duplicated().sum()))
    
    f.write("\n=== 2. Descriptive Stats (Numerical) ===\n")
    f.write(df.describe().to_string())
    
    f.write("\n\n=== 3. Descriptive Stats (Categorical) ===\n")
    f.write(df.describe(include=['O']).to_string())
    
    f.write("\n\n=== 4. Publishers Frequencies ===\n")
    f.write(df['출판사'].value_counts().head(30).to_string())

# 1. Histogram of Prices
plt.figure(figsize=(10,6))
plt.hist(df['가격'], bins=20, color='skyblue', edgecolor='black')
plt.title('가격 분포 히스토그램')
plt.xlabel('가격')
plt.ylabel('빈도수')
plt.savefig('images/plot1_price_hist.png', bbox_inches='tight')
plt.close()

# 2. Box plot of Prices
plt.figure(figsize=(8,6))
plt.boxplot(df['가격'].dropna(), vert=False)
plt.title('가격 분포 박스 플롯')
plt.xlabel('가격')
plt.savefig('images/plot2_price_box.png', bbox_inches='tight')
plt.close()

# 3. Histogram of Ratings
plt.figure(figsize=(10,6))
plt.hist(df['평점'], bins=20, color='lightgreen', edgecolor='black')
plt.title('평점 분포 히스토그램')
plt.xlabel('평점')
plt.ylabel('빈도수')
plt.savefig('images/plot3_rating_hist.png', bbox_inches='tight')
plt.close()

# 4. Histogram of Review Counts
plt.figure(figsize=(10,6))
plt.hist(df['리뷰수'], bins=20, color='salmon', edgecolor='black')
plt.title('리뷰 수 분포 히스토그램')
plt.xlabel('리뷰수')
plt.ylabel('빈도수')
plt.savefig('images/plot4_review_hist.png', bbox_inches='tight')
plt.close()

# 5. Scatter plot: Price vs Rating
plt.figure(figsize=(10,6))
plt.scatter(df['가격'], df['평점'], alpha=0.5)
plt.title('가격과 평점 산점도')
plt.xlabel('가격')
plt.ylabel('평점')
plt.savefig('images/plot5_price_rating_scatter.png', bbox_inches='tight')
plt.close()

# 6. Scatter plot: Rating vs Review Counts
plt.figure(figsize=(10,6))
plt.scatter(df['평점'], df['리뷰수'], alpha=0.5, color='orange')
plt.title('평점과 리뷰수 산점도')
plt.xlabel('평점')
plt.ylabel('리뷰수')
plt.savefig('images/plot6_rating_review_scatter.png', bbox_inches='tight')
plt.close()

# 7. Top 15 Publishers
top_pubs = df['출판사'].value_counts().head(15)
plt.figure(figsize=(12,8))
top_pubs.plot(kind='bar', color='purple', alpha=0.7)
plt.title('상위 15개 출판사 도서 수')
plt.xlabel('출판사')
plt.ylabel('도서 수')
plt.xticks(rotation=45, ha='right')
plt.savefig('images/plot7_top_publishers.png', bbox_inches='tight')
plt.close()

# 8. Average price by Top 10 publishers
top10_pubs = df['출판사'].value_counts().head(10).index
df_top10 = df[df['출판사'].isin(top10_pubs)]
avg_price_pub = df_top10.groupby('출판사')['가격'].mean().sort_values(ascending=False)

plt.figure(figsize=(12,8))
avg_price_pub.plot(kind='bar', color='teal', alpha=0.7)
plt.title('상위 10개 출판사 평균 도서 가격')
plt.xlabel('출판사')
plt.ylabel('평균 가격')
plt.xticks(rotation=45, ha='right')
plt.savefig('images/plot8_avg_price_by_pub.png', bbox_inches='tight')
plt.close()

with open('eda_results.txt', 'a', encoding='utf-8') as f:
    f.write("\n\n=== 8. Avg Price by Pub ===\n")
    f.write(avg_price_pub.to_string())

# 9. Correlation Heatmap
num_df = df[['순위', '가격', '평점', '리뷰수']].dropna()
corr = num_df.corr()

plt.figure(figsize=(8,6))
plt.imshow(corr, cmap='coolwarm', interpolation='nearest')
plt.colorbar()
plt.xticks(range(len(corr.columns)), corr.columns)
plt.yticks(range(len(corr.columns)), corr.columns)
plt.title('수치형 변수 간 상관관계 히트맵')
for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        text = plt.text(j, i, round(corr.iloc[i, j], 2), ha="center", va="center", color="black")
plt.savefig('images/plot9_corr_heatmap.png', bbox_inches='tight')
plt.close()

with open('eda_results.txt', 'a', encoding='utf-8') as f:
    f.write("\n\n=== 9. Correlation ===\n")
    f.write(corr.to_string())

# 10. TF-IDF Keyword Analysis
tfidf = TfidfVectorizer(max_features=30)
tfidf_matrix = tfidf.fit_transform(df['도서명'].dropna())
keywords = tfidf.get_feature_names_out()
sums = tfidf_matrix.sum(axis=0)

keyword_freq = [(keyword, sums[0, idx]) for keyword, idx in tfidf.vocabulary_.items()]
keyword_freq = sorted(keyword_freq, key=lambda x: x[1], reverse=True)[:30]

kw_df = pd.DataFrame(keyword_freq, columns=['Keyword', 'TF-IDF Score'])

plt.figure(figsize=(12,8))
plt.bar(kw_df['Keyword'], kw_df['TF-IDF Score'], color='coral')
plt.title('도서명 TF-IDF 상위 30개 키워드')
plt.xlabel('키워드')
plt.ylabel('TF-IDF Score')
plt.xticks(rotation=45, ha='right')
plt.savefig('images/plot10_tfidf_keywords.png', bbox_inches='tight')
plt.close()

with open('eda_results.txt', 'a', encoding='utf-8') as f:
    f.write("\n\n=== 10. TF-IDF Keywords ===\n")
    f.write(kw_df.to_string())

# 11. Boxplot of Rating
plt.figure(figsize=(8,6))
plt.boxplot(df['평점'].dropna(), vert=False)
plt.title('평점 분포 박스 플롯')
plt.xlabel('평점')
plt.savefig('images/plot11_rating_box.png', bbox_inches='tight')
plt.close()

print("EDA script completed successfully.")
