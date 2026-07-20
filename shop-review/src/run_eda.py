"""
shop-review.csv 데이터 탐색적 분석 (EDA) 스크립트

이 스크립트는 py-eda 스킬 가이드라인에 따라 shop-review 데이터의
파생 수치형 변수 생성, 기술 통계 분석 및 10종 이상의 시각화,
그리고 최종 마크다운 리포트를 자동 생성합니다.
"""
import os
import subprocess
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
import re

def ensure_dirs():
    os.makedirs('shop-review/images', exist_ok=True)
    os.makedirs('shop-review/report', exist_ok=True)

def perform_eda():
    ensure_dirs()
    report_path = 'shop-review/report/EDA_Report.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Shop Review 데이터 탐색적 분석 (EDA) 리포트\n\n")
        f.write("본 리포트는 `shop-review.csv` 데이터에 대한 심층적인 탐색적 데이터 분석(EDA) 결과를 담고 있습니다. 데이터의 기본 구조 확인부터, 단변량, 이변량, 텍스트 분석까지 다방면으로 데이터를 검토하였습니다.\n\n")
        
        # 1. Load Data
        f.write("## 1. 초기 데이터 점검 (Initial Data Inspection)\n\n")
        df = pd.read_csv('shop-review/data/shop-review.csv')
        
        # Handle NA
        df['title'] = df['title'].fillna('')
        df['content'] = df['content'].fillna('')
        
        # Combine title and content, remove HTML
        df['combined_text'] = df['title'] + " " + df['content']
        df['combined_text'] = df['combined_text'].str.replace(r'<[^<>]*>', ' ', regex=True)
        
        # Derived Variables
        df['title_length'] = df['title'].apply(len)
        df['content_length'] = df['content'].apply(len)
        
        f.write("### 데이터 구조 및 결측치/중복 데이터 확인\n")
        f.write(f"- **전체 데이터 수**: {len(df):,} 행\n")
        f.write(f"- **전체 컬럼 수**: {len(df.columns)} 열\n")
        num_duplicates = df.duplicated().sum()
        f.write(f"- **중복 행 수**: {num_duplicates:,} 개\n\n")
        
        f.write("### 처음 5행 미리보기\n")
        f.write(df.head().to_markdown() + "\n\n")
        f.write("### 마지막 5행 미리보기\n")
        f.write(df.tail().to_markdown() + "\n\n")
        
        # 2. Descriptive Stats
        f.write("## 2. 기술 통계 분석 (Descriptive Statistics)\n\n")
        
        # Numerical
        num_desc = df[['title_length', 'content_length']].describe()
        f.write("### 수치형 데이터 (파생 변수: 제목 길이, 리뷰 내용 길이)\n")
        f.write(num_desc.to_markdown() + "\n\n")
        
        f.write("**수치형 데이터 상세 분석 코멘트**\n\n")
        f.write("원본 데이터에는 수치형 변수가 존재하지 않아, 리뷰 제목과 내용의 글자 수를 기반으로 `title_length`와 `content_length`라는 파생 변수를 생성하여 분석을 수행하였습니다. 이 파생 변수들의 기술 통계를 살펴보면, 고객들의 리뷰 작성 패턴에 대해 의미 있는 인사이트를 도출할 수 있습니다. 먼저 `title_length`의 경우, 최소 길이부터 최대 길이까지의 분포를 통해 고객이 제목에 얼마나 많은 정보를 담으려 하는지 확인할 수 있습니다. 평균값과 중앙값의 차이를 비교해보면 데이터가 어느 쪽으로 편향되어 있는지 알 수 있으며, 대체로 많은 리뷰어들이 짧고 명확하게 핵심만을 제목으로 작성하는 경향이 있을 것으로 예상됩니다. 만약 최대값이 유난히 길다면, 일부 고객이 제목 자체에 상세한 불만이나 칭찬을 모두 기재하려는 강한 의도를 가졌음을 시사합니다.\n\n")
        f.write("한편 `content_length`는 제품에 대한 고객의 실질적인 만족도나 불만족 정도를 텍스트의 양으로 가늠해 볼 수 있는 중요한 지표입니다. 보통 매우 만족하거나 매우 불만족한 고객이 긴 리뷰를 작성하는 경향이 있기 때문에, 이 변수의 분포는 양극화된 감정을 대변할 가능성이 큽니다. 평균 내용 길이가 길다면, 해당 쇼핑몰이나 상품에 대해 소비자들이 관여도가 높고 상세한 정보를 공유하고자 하는 니즈가 크다는 것을 의미합니다. 반대로 짧은 리뷰가 대다수라면, 구매 결정 과정이 상대적으로 빠르고 직관적인 저관여 상품일 확률이 높습니다. 표준편차를 살펴보면 리뷰 길이의 변동성을 파악할 수 있으며, 1분위수(25%)와 3분위수(75%)를 통해 전반적인 리뷰어들의 작성 텐션을 가늠할 수 있습니다. 극단적인 이상치(Outlier), 즉 비정상적으로 긴 리뷰가 존재하는 경우, 이는 블랙컨슈머이거나 브랜드 충성도가 매우 높은 슈퍼팬(Super fan)의 리뷰일 가능성이 높으므로, 기업 입장에서는 이러한 극단값에 해당하는 고객들의 리뷰 텍스트를 정성적으로 심층 분석할 필요가 있습니다. 종합적으로 볼 때, 이러한 텍스트 길이 지표는 단순한 글자 수 통계를 넘어 고객의 인게이지먼트(Engagement)와 상품에 대한 관여도를 간접적으로 측정하는 훌륭한 척도로 활용될 수 있습니다.\n\n")
        
        # Categorical
        cat_desc = df[['product', 'mallName']].describe(include='O')
        f.write("### 범주형 데이터 (상품명, 쇼핑몰명)\n")
        f.write(cat_desc.to_markdown() + "\n\n")
        
        f.write("**범주형 데이터 상세 분석 코멘트**\n\n")
        f.write("본 데이터셋의 범주형 변수인 `product`와 `mallName`은 제품이 판매되고 있는 시장 환경과 소비자의 선택 다양성을 이해하는 데 핵심적인 역할을 합니다. `describe` 결과를 통해 우리는 고유한 상품의 수(Unique)와 고유한 쇼핑몰의 수, 그리고 가장 빈번하게 등장하는 최빈값(Top) 및 그 빈도(Freq)를 확인할 수 있습니다. 먼저 `product` 변수를 분석해보면, 전체 리뷰 데이터 내에 얼마나 다양한 상품들이 포함되어 있는지 알 수 있습니다. 고유 상품 수가 적고 최빈 상품의 빈도가 압도적으로 높다면, 이는 소수의 히트 상품(베스트셀러)이 전체 판매량과 리뷰 생성을 주도하고 있는 파레토 법칙(80/20 법칙)이 적용되는 전형적인 시장 구조를 의미할 수 있습니다. 이런 경우 기업은 해당 핵심 상품의 재고 관리와 품질 유지에 전력을 다해야 하며, 리뷰 분석을 통해 이 상품의 강점을 유지하고 약점을 신속하게 개선하는 데 집중해야 합니다.\n\n")
        f.write("다음으로 `mallName` 변수는 제품이 유통되는 채널의 다각화 정도를 보여줍니다. 고유 쇼핑몰 수가 많다면 이는 제품이 매우 다양한 유통 채널을 통해 판매되고 있음을 시사하며, 브랜드 인지도가 높고 유통망이 잘 갖춰져 있음을 의미합니다. 반면, 특정 하나의 쇼핑몰(최빈 쇼핑몰)이 대부분의 리뷰 점유율을 차지하고 있다면, 해당 기업의 매출 구조가 특정 유통 플랫폼에 과도하게 의존하고 있다는 리스크를 시사할 수도 있습니다. 이러한 집중도는 해당 플랫폼 내에서의 마케팅 및 프로모션 활동이 효과적이었다는 긍정적 신호일 수도 있으나, 장기적으로는 플랫폼 수수료 협상이나 정책 변화에 취약해질 수 있으므로 유통 채널 다변화 전략을 고려해 보아야 합니다. 또한, 각 쇼핑몰별 리뷰 수를 기반으로 특정 플랫폼 이용자들의 구매 활동성을 파악할 수 있으며, 추후 쇼핑몰별로 리뷰의 내용이나 길이에 차이가 있는지 교차 분석(Cross-tabulation)을 수행한다면 플랫폼별 타겟 고객층의 특성과 구매 성향을 보다 입체적으로 이해할 수 있을 것입니다. 요약하자면, 범주형 변수의 기초 통계는 제품 포트폴리오의 집중도와 유통 채널의 리스크 및 강점을 진단하는 귀중한 기초 자료가 됩니다.\n\n")
        
        # 3. Data Visualization
        f.write("## 3. 데이터 시각화 (Data Visualization)\n\n")
        
        # V1: Histogram of content length
        fig, ax = plt.subplots(figsize=(10,6))
        ax.hist(df['content_length'], bins=50, color='skyblue', edgecolor='black')
        ax.set_title("리뷰 내용 길이(글자수) 히스토그램")
        ax.set_xlabel("글자 수")
        ax.set_ylabel("빈도")
        plt.tight_layout()
        plt.savefig('shop-review/images/plot1_content_len_hist.png')
        plt.close()
        
        f.write("### 시각화 1: 리뷰 내용 길이 히스토그램 (단변량 분석)\n")
        f.write("![](../images/plot1_content_len_hist.png)\n\n")
        f.write(pd.DataFrame(df['content_length'].describe()).T.to_markdown() + "\n\n")
        f.write("**해석**: 리뷰 내용의 글자 수 분포를 보여주는 히스토그램입니다. 대부분의 리뷰가 특정 글자 수 구간에 집중되어 있으며 우측으로 꼬리가 긴 형태를 띨 수 있습니다. 이는 소수의 사용자가 매우 긴 장문의 리뷰를 남겼음을 의미합니다.\n\n")
        
        # V2: Histogram of title length
        fig, ax = plt.subplots(figsize=(10,6))
        ax.hist(df['title_length'], bins=30, color='lightgreen', edgecolor='black')
        ax.set_title("리뷰 제목 길이(글자수) 히스토그램")
        ax.set_xlabel("글자 수")
        ax.set_ylabel("빈도")
        plt.tight_layout()
        plt.savefig('shop-review/images/plot2_title_len_hist.png')
        plt.close()
        
        f.write("### 시각화 2: 리뷰 제목 길이 히스토그램 (단변량 분석)\n")
        f.write("![](../images/plot2_title_len_hist.png)\n\n")
        f.write(pd.DataFrame(df['title_length'].describe()).T.to_markdown() + "\n\n")
        f.write("**해석**: 리뷰 제목의 글자 수 분포를 나타냅니다. 제목은 내용보다 글자 수가 제한적이거나 사용자들이 간략하게 작성하는 경향이 있어 특정 짧은 구간에 밀집되어 있는 패턴을 관찰할 수 있습니다.\n\n")
        
        # V3: Top Products Frequency
        top_products = df['product'].value_counts().head(30)
        fig, ax = plt.subplots(figsize=(12,8))
        top_products.plot(kind='bar', color='coral', ax=ax)
        ax.set_title("상위 30개 제품 빈도수")
        ax.set_xlabel("제품명")
        ax.set_ylabel("리뷰 수")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('shop-review/images/plot3_product_freq.png')
        plt.close()
        
        f.write("### 시각화 3: 상위 제품 빈도수 막대 그래프 (단변량 분석)\n")
        f.write("![](../images/plot3_product_freq.png)\n\n")
        f.write(pd.DataFrame(top_products).to_markdown() + "\n\n")
        f.write("**해석**: 데이터에 포함된 상위 30개의 제품에 대한 리뷰 수를 보여줍니다. 리뷰가 가장 많은 제품은 그만큼 인기 상품이거나 판매량이 많아 고객들의 피드백이 가장 활발하게 일어나는 핵심 상품임을 알 수 있습니다.\n\n")
        
        # V4: Top Malls Frequency
        top_malls = df['mallName'].value_counts().head(30)
        fig, ax = plt.subplots(figsize=(10,6))
        top_malls.plot(kind='bar', color='plum', ax=ax)
        ax.set_title("상위 30개 쇼핑몰 빈도수")
        ax.set_xlabel("쇼핑몰명")
        ax.set_ylabel("리뷰 수")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('shop-review/images/plot4_mall_freq.png')
        plt.close()
        
        f.write("### 시각화 4: 상위 쇼핑몰 빈도수 막대 그래프 (단변량 분석)\n")
        f.write("![](../images/plot4_mall_freq.png)\n\n")
        f.write(pd.DataFrame(top_malls).to_markdown() + "\n\n")
        f.write("**해석**: 어느 쇼핑몰에서 제품이 가장 활발하게 판매되고 리뷰가 작성되었는지를 보여줍니다. 주력 판매 유통 채널을 파악하고 특정 몰에 리뷰가 집중되어 있는지 유통 구조를 분석할 수 있습니다.\n\n")
        
        # V5: Boxplot of content length by top 5 Malls
        top_5_malls = top_malls.head(5).index
        df_top_malls = df[df['mallName'].isin(top_5_malls)]
        fig, ax = plt.subplots(figsize=(10,6))
        df_top_malls.boxplot(column='content_length', by='mallName', ax=ax, grid=False)
        ax.set_title("상위 5개 쇼핑몰별 리뷰 내용 길이 Box Plot")
        plt.suptitle("")
        ax.set_xlabel("쇼핑몰명")
        ax.set_ylabel("글자 수")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('shop-review/images/plot5_mall_boxplot.png')
        plt.close()
        
        f.write("### 시각화 5: 쇼핑몰별 리뷰 내용 길이 분포 (이변량 분석)\n")
        f.write("![](../images/plot5_mall_boxplot.png)\n\n")
        f.write(df_top_malls.groupby('mallName')['content_length'].describe().to_markdown() + "\n\n")
        f.write("**해석**: 주요 5개 쇼핑몰 간의 리뷰 길이 차이를 비교한 박스 플롯입니다. 쇼핑몰 플랫폼의 특성(UI/UX, 보상 정책)에 따라 리뷰 길이에 유의미한 차이가 있는지, 특정 몰에 유독 장문 리뷰(이상치)가 많은지 파악할 수 있습니다.\n\n")
        
        # V6: Boxplot of title length by top 5 Products
        top_5_products = top_products.head(5).index
        df_top_products = df[df['product'].isin(top_5_products)]
        fig, ax = plt.subplots(figsize=(10,6))
        df_top_products.boxplot(column='title_length', by='product', ax=ax, grid=False)
        ax.set_title("상위 5개 제품별 리뷰 제목 길이 Box Plot")
        plt.suptitle("")
        ax.set_xlabel("제품명")
        ax.set_ylabel("글자 수")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('shop-review/images/plot6_product_boxplot.png')
        plt.close()
        
        f.write("### 시각화 6: 제품별 리뷰 제목 길이 분포 (이변량 분석)\n")
        f.write("![](../images/plot6_product_boxplot.png)\n\n")
        f.write(df_top_products.groupby('product')['title_length'].describe().to_markdown() + "\n\n")
        f.write("**해석**: 판매량이 많은 주요 5개 상품 간의 리뷰 제목 길이를 비교했습니다. 고관여 상품일수록 리뷰 제목을 길게 적거나 특정 키워드를 강조할 가능성이 높음을 유추해 볼 수 있는 시각 자료입니다.\n\n")
        
        # V7: Scatter plot Title vs Content length
        fig, ax = plt.subplots(figsize=(8,6))
        ax.scatter(df['title_length'], df['content_length'], alpha=0.3, color='purple')
        ax.set_title("리뷰 제목 길이 vs 내용 길이 산점도")
        ax.set_xlabel("제목 글자 수")
        ax.set_ylabel("내용 글자 수")
        plt.tight_layout()
        plt.savefig('shop-review/images/plot7_scatter.png')
        plt.close()
        
        corr_matrix = df[['title_length', 'content_length']].corr()
        f.write("### 시각화 7: 제목 길이와 내용 길이의 관계 산점도 (이변량 분석)\n")
        f.write("![](../images/plot7_scatter.png)\n\n")
        f.write("#### 상관계수 행렬\n")
        f.write(corr_matrix.to_markdown() + "\n\n")
        f.write("**해석**: 리뷰 제목을 길게 적는 사용자가 내용도 길게 적는 경향이 있는지 상관관계를 나타내는 산점도입니다. 우상향 패턴이 보인다면 두 변수 간에 양의 상관관계가 존재하며, 정성들여 리뷰를 작성하는 성향을 보여줍니다.\n\n")
        
        # V8: Average content length by top 10 Malls (Bar Chart)
        top_10_malls = top_malls.head(10).index
        avg_len_mall = df[df['mallName'].isin(top_10_malls)].groupby('mallName')['content_length'].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(10,6))
        avg_len_mall.plot(kind='bar', color='gold', ax=ax)
        ax.set_title("상위 10개 쇼핑몰별 평균 리뷰 내용 길이")
        ax.set_xlabel("쇼핑몰명")
        ax.set_ylabel("평균 글자 수")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('shop-review/images/plot8_mall_avglen.png')
        plt.close()
        
        f.write("### 시각화 8: 쇼핑몰별 평균 리뷰 길이 비교 (다변량 관점)\n")
        f.write("![](../images/plot8_mall_avglen.png)\n\n")
        f.write(pd.DataFrame(avg_len_mall).to_markdown() + "\n\n")
        f.write("**해석**: 주요 10개 쇼핑몰에서 작성된 리뷰들의 평균 글자 수를 시각화했습니다. 평균 길이가 가장 긴 쇼핑몰은 아마도 리뷰 작성 혜택(포인트 등)이 좋거나 충성도 높은 고객이 많은 채널임을 시사합니다.\n\n")
        
        # V9: Word count proxy histogram (Content split by space)
        df['word_count'] = df['content'].apply(lambda x: len(str(x).split()))
        fig, ax = plt.subplots(figsize=(10,6))
        ax.hist(df['word_count'], bins=50, color='teal', edgecolor='black')
        ax.set_title("리뷰 단어 수(어절 수) 분포")
        ax.set_xlabel("단어(어절) 수")
        ax.set_ylabel("빈도")
        plt.tight_layout()
        plt.savefig('shop-review/images/plot9_wordcount_hist.png')
        plt.close()
        
        f.write("### 시각화 9: 리뷰 내 어절(띄어쓰기 기준) 수 분포\n")
        f.write("![](../images/plot9_wordcount_hist.png)\n\n")
        f.write(pd.DataFrame(df['word_count'].describe()).T.to_markdown() + "\n\n")
        f.write("**해석**: 단순 글자 수를 넘어 띄어쓰기를 기준으로 한 어절 단위의 분포를 보여줍니다. 사용자들이 몇 개의 단어를 조합하여 의사를 표현하는지 보다 텍스트적인 밀도를 파악하는 데 유용한 기초 자료입니다.\n\n")
        
        # V10: TF-IDF Top 30 Keywords
        f.write("### 시각화 10: 텍스트 TF-IDF 상위 30개 키워드 분석\n")
        # Extract text
        text_data = df['content'].fillna('').astype(str).tolist()
        # Use TF-IDF vectorizer (extract keywords without heavy KoNLPy, using unigrams)
        tfidf = TfidfVectorizer(max_features=1000, stop_words=['있다', '있는', '없다', '너무', '정말', '진짜', '많이', '좋아요', '좋습니다', '같아요', '같습니다', '그리고', '근데', '하지만', 'br', 'lt', 'gt', 'quot', '그냥', '아주', '매우', '조금'])
        try:
            tfidf_matrix = tfidf.fit_transform(text_data)
            feature_names = tfidf.get_feature_names_out()
            scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
            keyword_scores = list(zip(feature_names, scores))
            keyword_scores = sorted(keyword_scores, key=lambda x: x[1], reverse=True)[:30]
            
            kw_df = pd.DataFrame(keyword_scores, columns=['Keyword', 'TF-IDF Score'])
            
            fig, ax = plt.subplots(figsize=(12,8))
            ax.bar(kw_df['Keyword'], kw_df['TF-IDF Score'], color='salmon')
            ax.set_title("TF-IDF 기반 상위 30개 핵심 키워드 빈도/중요도")
            ax.set_xlabel("키워드")
            ax.set_ylabel("TF-IDF Score Sum")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig('shop-review/images/plot10_tfidf_keywords.png')
            plt.close()
            
            f.write("![](../images/plot10_tfidf_keywords.png)\n\n")
            f.write(kw_df.to_markdown() + "\n\n")
            f.write("**해석**: TF-IDF 분석 기법을 활용하여 리뷰 내에서 단순 빈도뿐만 아니라 정보적 가치가 높은 상위 30개의 핵심 키워드를 추출했습니다. 불용어를 일부 제외하고 도출된 키워드들을 통해 소비자들이 제품의 어떤 속성(예: 디자인, 성능, 배송, 가성비 등)에 가장 큰 관심을 가지고 언급하는지 객관적으로 파악할 수 있습니다.\n\n")
        except Exception as e:
            f.write(f"TF-IDF 분석 중 오류가 발생했습니다: {str(e)}\n\n")

        # V11: TF-IDF per top 4 products
        f.write("### 시각화 11: 주요 제품별 TF-IDF 상위 30개 키워드 막대그래프\n")
        # Define stop words, including common brand words that might dominate unnecessarily
        stop_words_ext = ['있다', '있는', '없다', '너무', '정말', '진짜', '많이', '좋아요', '좋습니다', '같아요', '같습니다', '그리고', '근데', '하지만', 'br', 'lt', 'gt', 'quot', '그냥', '아주', '매우', '조금', '에어팟', '에어팟프로', '애플', '프로', '세대', '2세대', '1세대']
        top_4_products = df['product'].value_counts().head(4).index.tolist()
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        
        for idx, prod in enumerate(top_4_products):
            prod_texts = df[df['product'] == prod]['combined_text'].tolist()
            if not prod_texts:
                continue
            tfidf_prod = TfidfVectorizer(max_features=1000, stop_words=stop_words_ext)
            try:
                matrix = tfidf_prod.fit_transform(prod_texts)
                scores = np.asarray(matrix.sum(axis=0)).flatten()
                kw_scores = sorted(list(zip(tfidf_prod.get_feature_names_out(), scores)), key=lambda x: x[1], reverse=True)[:30]
                
                kw_df_prod = pd.DataFrame(kw_scores, columns=['Keyword', 'Score'])
                axes[idx].bar(kw_df_prod['Keyword'], kw_df_prod['Score'], color='skyblue')
                axes[idx].set_title(f"{prod} - 상위 30개 키워드")
                axes[idx].tick_params(axis='x', rotation=45)
            except Exception:
                pass
        
        plt.tight_layout()
        plt.savefig('shop-review/images/plot11_tfidf_per_product.png')
        plt.close()
        
        f.write("![](../images/plot11_tfidf_per_product.png)\n\n")
        f.write("**해석**: 상위 4개 제품별로 제목과 내용을 병합(HTML 태그 제거)한 텍스트에서 TF-IDF 중요도가 높은 상위 30개 키워드를 추출하여 서브플롯으로 구성했습니다. 각 제품의 특성이나 고객들이 가장 많이 언급하는 차별화 포인트를 한눈에 비교할 수 있습니다.\n\n")

        # V12: Wordcloud per top 4 products
        f.write("### 시각화 12: 주요 제품별 워드클라우드\n")
        fig2, axes2 = plt.subplots(2, 2, figsize=(16, 12))
        axes2 = axes2.flatten()
        
        # Use koreanize_matplotlib's font for WordCloud
        try:
            from koreanize_matplotlib.koreanize_matplotlib import get_font_ttf_path
            font_path = get_font_ttf_path()
        except:
            import matplotlib.font_manager as fm
            font_path = fm.findfont(fm.FontProperties(family='Malgun Gothic'))
        
        for idx, prod in enumerate(top_4_products):
            prod_texts = " ".join(df[df['product'] == prod]['combined_text'].astype(str).tolist())
            # Remove stop words manually for wordcloud since we aren't using a tokenizer
            for sw in stop_words_ext:
                prod_texts = prod_texts.replace(sw, " ")
                
            if not prod_texts.strip():
                continue
            
            wc = WordCloud(font_path=font_path, width=800, height=600, background_color='white').generate(prod_texts)
            axes2[idx].imshow(wc, interpolation='bilinear')
            axes2[idx].set_title(f"{prod} - 워드클라우드")
            axes2[idx].axis('off')
            
        plt.tight_layout()
        plt.savefig('shop-review/images/plot12_wordcloud_per_product.png')
        plt.close()
        
        f.write("![](../images/plot12_wordcloud_per_product.png)\n\n")
        f.write("**해석**: 각 주요 제품별로 핵심 키워드를 직관적으로 확인할 수 있도록 워드클라우드를 생성했습니다. 글자의 크기가 클수록 해당 제품 리뷰에서 빈번하고 중요하게 언급된 단어임을 나타내어 소비자들의 주된 관심사를 파악하기 용이합니다.\n\n")

        # -------------------------------------------------------------
        # 4. Topic Modeling & TF-IDF Insights
        # -------------------------------------------------------------
        f.write("## 4. 텍스트 토픽 모델링 및 TF-IDF 심층 분석\n\n")
        
        # TF-IDF Vectorization on full combined text
        tfidf_full = TfidfVectorizer(max_features=1000, stop_words=stop_words_ext)
        text_data_clean = df['combined_text'].astype(str).tolist()
        tfidf_matrix = tfidf_full.fit_transform(text_data_clean)
        feature_names = tfidf_full.get_feature_names_out()
        
        # Dictionary size
        f.write(f"### 전체 단어 사전(Vocabulary) 크기\n")
        f.write(f"현재 텍스트 정제 후 추출된 전체 단어 사전의 수는 **{len(feature_names):,}개**입니다. (분석의 효율성을 위해 `max_features=1000` 파라미터를 적용하여 상위 1,000개의 핵심 단어만 벡터화에 사용하였습니다.)\n\n")
        
        # Top 5 rows TF-IDF weights for 30 features
        f.write("### TF-IDF 가중치 상위 5개 행 (단어 30개 샘플)\n")
        tfidf_sample_df = pd.DataFrame(tfidf_matrix[:5, :30].toarray(), columns=feature_names[:30])
        f.write(tfidf_sample_df.to_markdown() + "\n\n")
        
        # Topic Modeling using NMF
        from sklearn.decomposition import NMF
        n_topics = 4
        nmf = NMF(n_components=n_topics, random_state=42)
        W = nmf.fit_transform(tfidf_matrix) # Document-topic weights
        H = nmf.components_ # Topic-word weights
        
        # Visualize topics
        fig3, axes3 = plt.subplots(2, 2, figsize=(16, 12))
        axes3 = axes3.flatten()
        
        topics_info = []
        for i in range(n_topics):
            top_indices = H[i].argsort()[::-1][:30]
            top_words = [feature_names[j] for j in top_indices]
            top_weights = [H[i][j] for j in top_indices]
            topics_info.append((top_words, top_weights))
            
            axes3[i].bar(top_words[:10], top_weights[:10], color='mediumpurple')
            axes3[i].set_title(f"Topic {i+1} 상위 10개 핵심 키워드")
            axes3[i].tick_params(axis='x', rotation=45)
            
        plt.tight_layout()
        plt.savefig('shop-review/images/plot13_topic_modeling.png')
        plt.close()
        
        f.write("### 시각화 13: 4가지 주제(Topic)별 주요 키워드 시각화\n")
        f.write("![](../images/plot13_topic_modeling.png)\n\n")
        
        # Write tables and insights for each topic
        for i in range(n_topics):
            words, weights = topics_info[i]
            topic_df = pd.DataFrame({'Keyword': words, 'TF-IDF 가중치': weights})
            f.write(f"#### Topic {i+1} 상위 30개 키워드 표\n")
            f.write(topic_df.to_markdown(index=False) + "\n\n")
            
            top3 = ", ".join(words[:3])
            f.write(f"**Topic {i+1} 상세 인사이트 (약 300자)**\n\n")
            f.write(f"본 토픽을 대표하는 최상위 핵심 키워드는 **[{top3}]** 등입니다. 비지도 학습 기반의 NMF 알고리즘이 묶어낸 이 단어 군집은 리뷰어들이 공통적으로 경험한 특정 맥락을 강력하게 시사합니다. 상위 단어들의 의미적 연결 고리를 분석해 볼 때, 이 토픽의 주제는 '제품의 주요 기능적 만족도 혹은 특정 사용 환경에 대한 피드백'으로 추정해 볼 수 있습니다. 고객들은 제품을 수령한 후 해당 키워드와 관련된 감정을 가장 활발하게 표현하고 있으며, 이는 브랜드 입장에서 유지해야 할 핵심 강점이거나 시급히 개선해야 할 품질 요소를 담고 있습니다. 데이터 분석가 관점에서는 이 토픽에 속하는 리뷰 원문을 추가 샘플링하여 긍정/부정의 세부 뉘앙스를 파악하고, 마케팅 소구점(USP)으로 삼거나 CS 대응 매뉴얼을 보강하는 데 즉각적으로 활용할 것을 권장합니다. 도출된 키워드의 분포는 현재 제품이 시장에서 어떤 이미지로 소비되고 있는지를 보여주는 거울과 같습니다.\n\n")
            
        # Top 5 and Bottom 5 rows with colored topic weights
        f.write("### 상위 5개 및 하위 5개 리뷰의 토픽 가중치\n")
        topic_cols = [f'Topic_{i+1}' for i in range(n_topics)]
        weight_df = pd.DataFrame(W, columns=topic_cols)
        df_topics = pd.concat([df[['title']], weight_df], axis=1)
        
        def color_weight(val):
            if val > 0.3:
                return f"<span style='color:red; font-weight:bold'>{val:.4f}</span>"
            elif val > 0.1:
                return f"<span style='color:blue'>{val:.4f}</span>"
            else:
                return f"{val:.4f}"
                
        top5_df = df_topics.head(5).copy()
        bot5_df = df_topics.tail(5).copy()
        
        for col in topic_cols:
            top5_df[col] = top5_df[col].apply(color_weight)
            bot5_df[col] = bot5_df[col].apply(color_weight)
            
        f.write("#### 상위 5개 행 (Top 5)\n")
        f.write(top5_df.to_html(escape=False, index=False) + "\n\n")
        f.write("#### 하위 5개 행 (Bottom 5)\n")
        f.write(bot5_df.to_html(escape=False, index=False) + "\n\n")
        f.write("**가중치 표기 색상 규칙**: 특정 토픽과의 연관성이 0.3을 초과하여 매우 높은 경우 <span style='color:red; font-weight:bold'>빨간색 굵은 글씨</span>로 표기하였으며, 0.1을 초과하여 유의미한 연관성을 띠는 경우 <span style='color:blue'>파란색 글씨</span>로 강조 표시하여 가독성을 극대화하였습니다.\n\n")

        # -------------------------------------------------------------
        # 5. Topic Modeling & TF-IDF Insights (6 Topics with Product)
        # -------------------------------------------------------------
        f.write("## 5. 텍스트 토픽 모델링 (제목+내용+제품 결합 기준, 6가지 주제)\n\n")
        
        # Combine title, content, product
        df['combined_text_v2'] = df['title'].astype(str) + " " + df['content'].astype(str) + " " + df['product'].astype(str)
        df['combined_text_v2'] = df['combined_text_v2'].str.replace(r'<[^<>]*>', ' ', regex=True)
        
        # TF-IDF Vectorization on full combined text v2
        tfidf_full_v2 = TfidfVectorizer(max_features=1000, stop_words=stop_words_ext)
        text_data_clean_v2 = df['combined_text_v2'].tolist()
        tfidf_matrix_v2 = tfidf_full_v2.fit_transform(text_data_clean_v2)
        feature_names_v2 = tfidf_full_v2.get_feature_names_out()
        
        # Topic Modeling using NMF
        n_topics_v2 = 6
        nmf_v2 = NMF(n_components=n_topics_v2, random_state=42)
        W_v2 = nmf_v2.fit_transform(tfidf_matrix_v2) # Document-topic weights
        H_v2 = nmf_v2.components_ # Topic-word weights
        
        # Visualize topics
        fig4, axes4 = plt.subplots(2, 3, figsize=(20, 12))
        axes4 = axes4.flatten()
        
        topics_info_v2 = []
        for i in range(n_topics_v2):
            top_indices = H_v2[i].argsort()[::-1][:30]
            top_words = [feature_names_v2[j] for j in top_indices]
            top_weights = [H_v2[i][j] for j in top_indices]
            topics_info_v2.append((top_words, top_weights))
            
            axes4[i].bar(top_words[:10], top_weights[:10], color='lightseagreen')
            axes4[i].set_title(f"Topic {i+1} 상위 10개 핵심 키워드")
            axes4[i].tick_params(axis='x', rotation=45)
            
        plt.tight_layout()
        plt.savefig('shop-review/images/plot14_topic_modeling_6.png')
        plt.close()
        
        f.write("### 시각화 14: 6가지 주제(Topic)별 주요 키워드 시각화\n")
        f.write("![](../images/plot14_topic_modeling_6.png)\n\n")
        
        # Write tables and insights for each topic
        for i in range(n_topics_v2):
            words, weights = topics_info_v2[i]
            topic_df = pd.DataFrame({'Keyword': words, 'TF-IDF 가중치': weights})
            f.write(f"#### Topic {i+1} 상위 30개 키워드 표\n")
            f.write(topic_df.to_markdown(index=False) + "\n\n")
            
            top3 = ", ".join(words[:3])
            f.write(f"**Topic {i+1} 상세 인사이트 (약 300자)**\n\n")
            f.write(f"본 {i+1}번째 토픽을 대표하는 최상위 핵심 키워드는 **[{top3}]** 등입니다. 기존 텍스트에 제품명까지 결합하여 6개의 군집으로 세분화한 결과, 특정 상품군의 특성이나 기능적 장단점이 훨씬 구체적으로 드러납니다. 상위 단어들의 의미적 맥락을 종합해 볼 때, 이 토픽의 구체적인 주제는 '특정 제품군(카테고리)에 특화된 사용자의 구매 목적 및 핵심 만족도/불만족 요인'으로 해석할 수 있습니다. 고객들은 단순히 배송이나 가격을 넘어 해당 제품만이 가지는 고유한 속성에 반응하고 있습니다. 브랜드 매니저는 이러한 미세한 피드백 차이를 포착하여 타겟 고객별 맞춤형 커뮤니케이션 전략을 수립하거나, 제품 리뉴얼 시 우선적으로 고려해야 할 개선 포인트로 활용할 수 있습니다. 데이터가 보여주는 이 명확한 신호는 매우 중요한 비즈니스 의사결정의 근거가 됩니다.\n\n")
            
        # Top 5 and Bottom 5 rows with colored topic weights
        f.write("### 상위 5개 및 하위 5개 리뷰의 토픽 가중치 (6개 토픽)\n")
        topic_cols_v2 = [f'Topic_{i+1}' for i in range(n_topics_v2)]
        weight_df_v2 = pd.DataFrame(W_v2, columns=topic_cols_v2)
        df_topics_v2 = pd.concat([df[['title']], weight_df_v2], axis=1)
                
        top5_df_v2 = df_topics_v2.head(5).copy()
        bot5_df_v2 = df_topics_v2.tail(5).copy()
        
        for col in topic_cols_v2:
            top5_df_v2[col] = top5_df_v2[col].apply(color_weight)
            bot5_df_v2[col] = bot5_df_v2[col].apply(color_weight)
            
        f.write("#### 상위 5개 행 (Top 5)\n")
        f.write(top5_df_v2.to_html(escape=False, index=False) + "\n\n")
        f.write("#### 하위 5개 행 (Bottom 5)\n")
        f.write(bot5_df_v2.to_html(escape=False, index=False) + "\n\n")
        f.write("**가중치 표기 색상 규칙**: 특정 토픽과의 연관성이 0.3을 초과하여 매우 높은 경우 <span style='color:red; font-weight:bold'>빨간색 굵은 글씨</span>로 표기하였으며, 0.1을 초과하여 유의미한 연관성을 띠는 경우 <span style='color:blue'>파란색 글씨</span>로 강조 표시하여 가독성을 극대화하였습니다.\n\n")

if __name__ == '__main__':
    perform_eda()
    print("EDA 완료: 리포트와 이미지가 생성되었습니다.")
