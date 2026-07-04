---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  :root {
    --primary: #065A82;
    --secondary: #1C7293;
    --accent: #21295C;
    --bg-light: #F2F7F9;
  }
  section {
    padding: 40px 60px;
    font-family: 'Pretendard', sans-serif;
  }
  h1 {
    color: var(--primary);
    border-bottom: 2px solid var(--primary);
    padding-bottom: 10px;
  }
  h2 { color: var(--secondary); }
  
  /* Layout Classes */
  section.lead {
    background-color: var(--accent);
    color: white;
    text-align: center;
    justify-content: center;
  }
  section.lead h1 { color: white; border-bottom: none; }
  
  section.dark {
    background-color: var(--primary);
    color: white;
  }
  section.dark h1, section.dark h2 { color: white; border-color: white; }

  section.split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
  }
  
  section.split-image-left {
    display: grid;
    grid-template-columns: 40% 60%;
    gap: 20px;
  }
  
  section.split-image-right {
    display: grid;
    grid-template-columns: 60% 40%;
    gap: 20px;
  }

  .grid-2x2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 20px;
  }
  
  .card {
    background: var(--bg-light);
    border-left: 5px solid var(--primary);
    padding: 20px;
    border-radius: 4px;
    margin-bottom: 10px;
  }
  
  .stat-big {
    font-size: 3em;
    color: var(--primary);
    font-weight: bold;
    text-align: center;
  }

  img {
    max-height: 45vh;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th { background-color: var(--secondary); color: white; }
  tr:nth-child(even) { background-color: var(--bg-light); }
---

<!-- _class: lead -->
# 교보문고 베스트셀러 트렌드 리포트
### 탐색적 데이터 분석(EDA) 및 비즈니스 전략
**작성자**: 20년 차 수석 데이터 분석가
**분석 대상**: 종합 주간 베스트셀러 Top 50

---

<!-- _class: split -->
<div>

# 목차 (Index)
### 프로젝트 흐름
1. 프로젝트 개요
2. 데이터 수집 및 정제
3. 기술 통계 분석
4. 출판사 및 텍스트 마이닝
5. 비즈니스 액션 플랜

</div>
<div class="card">
  <h2>분석 목표</h2>
  <p>현재 도서 시장의 주도 트렌드를 객관적인 수치로 파악하고, 단기 및 중장기 수익 극대화를 위한 실질적인 액션 플랜을 도출합니다.</p>
</div>

---

# 1. 프로젝트 개요 및 배경

<div class="grid-2x2">
  <div class="card">
    <h3>Why Now?</h3>
    <p>도서 시장은 현재 AI의 부상과 전통적 수험서 수요가 충돌하는 과도기에 있습니다.</p>
  </div>
  <div class="card">
    <h3>What to Find?</h3>
    <p>독자들의 구매 심리를 자극하는 요인(가격, 평점, 출판사 브랜드)을 규명합니다.</p>
  </div>
</div>

---

<!-- _class: dark -->
# 데이터 규모 및 수집 정보

| 항목 | 상세 내용 |
|---|---|
| **총 관측치** | 50 Rows |
| **변수 개수** | 8 Columns |
| **기준일** | 2026년 6월 현재 |
| **주요 장르** | 컴퓨터/IT, 수험서 |

*전처리를 통해 결측치 0%, 완전한 데이터 셋 확보*

---

<!-- _class: split-image-right -->
<div>

# 수치형 변수 기초 통계
**가격, 평점, 리뷰수 요약**

- 평균 가격은 **2.4만 원대**로 형성
- 리뷰수는 소수 도서에 극단적으로 치우친 **멱함수 분포**
- 평점은 9.8 부근에 밀집된 **상향 평준화**

</div>
<div>

| 통계량 | 가격 | 평점 | 리뷰수 |
|---|---|---|---|
| 평균 | 24,678 | 9.48 | 61.2 |
| 최소 | 11,700 | 0.0 | 0 |
| 중앙값| 23,400 | 9.8 | 16 |
| 최대 | 41,400 | 10.0 | 385 |

</div>

---

# [시각화 1] 도서 가격의 분포 형태

<div class="card">
가격은 소비자의 가장 큰 진입 장벽 중 하나입니다.
</div>

![](../../images/plot1_price_hist.png)

대부분 1.5만~2.5만 원에 집중되어 있으며, 3만 원 이상은 고부가가치 전문서로 분류됩니다.

---

# [시각화 2] 가격 박스 플롯 분석

<div class="stat-big">₩23,400</div>
<p style="text-align: center;">중앙값(Median Price)</p>

![](../../images/plot2_price_box.png)

이상치(Outlier)로 분류된 4만 원대 서적들은 대체로 필수 취득 자격증의 '실기서'들로 수요의 비탄력성을 보여줍니다.

---

<!-- _class: split-image-left -->
<div>

![](../../images/plot3_rating_hist.png)

</div>
<div>

# [시각화 3] 평점의 쏠림 현상
독자들의 별점은 9.5~10.0 사이에 거의 90% 이상 집중되어 있습니다. 
이는 베스트셀러 순위권에 진입하는 도서들의 콘텐츠 퀄리티가 이미 상향 평준화되어 있음을 시사합니다.

</div>

---

# [시각화 4] 실질적 평점 밀집도 (Boxplot)

<div class="grid-2x2">
  <div>
    ![](../../images/plot11_rating_box.png)
  </div>
  <div>
    <h3>평점 인플레이션</h3>
    <p>미평가(0점) 도서를 제외할 경우, 실질적 1/4분위수(Q1)조차 9.5 이상에서 시작됩니다. 이제 평점의 절대적 수치보다는 '리뷰의 개수'가 신뢰도를 담보합니다.</p>
  </div>
</div>

---

# [시각화 5] 리뷰 수 분포의 불균형

<div class="card">
소수의 책이 시장의 리뷰를 독식하는 파레토 법칙.
</div>

![](../../images/plot4_review_hist.png)

---

<!-- _class: dark -->
# 범주형 데이터 요약: 출판사 및 저자

<div class="grid-2x2">
  <div>
    <h2>총 출판사 수: 16개</h2>
    <p>탑 5 출판사가 50위권 내 62% 점유율 차지</p>
  </div>
  <div>
    <h2>총 저자 수: 45명</h2>
    <p>'길벗알앤디', '이남호' 등 특정 팀/개인 브랜드 파워 막강</p>
  </div>
</div>

| 순위 | 출판사 | 베스트셀러 종수 |
|---|---|---|
| 1 | 길벗 | 13 |
| 2 | 한빛미디어 | 7 |
| 3 | 골든래빗(주) | 4 |

---

# [시각화 6] 대형 출판사의 시장 리딩

<div class="split-image-right">
<div>
  <h3>브랜드 신뢰도</h3>
  <p>수험생과 실무자들은 모험을 하기보다 이미 검증된 출판사(길벗, 한빛미디어)의 책을 선택하는 경향이 뚜렷합니다.</p>
</div>
<div>
  ![](../../images/plot7_top_publishers.png)
</div>
</div>

---

# 상위 출판사별 프라이싱(Pricing) 전략

| 출판사 | 평균 가격 | 전략 요약 |
|---|---|---|
| 길벗 | 23,200원 | 볼륨 베이스 (다양한 라인업, 대중적 가격) |
| 한빛미디어 | 27,000원 | 전문 기술 서적 위주 중고가 유지 |
| 영진닷컴 | 30,900원 | 통합본 중심 고단가 프리미엄 전략 |
| 해커스금융 | 30,600원 | 자격증/세무/회계 니치 마켓 독점 |

---

# [시각화 7] 출판사별 도서 단가 비교

![](../../images/plot8_avg_price_by_pub.png)

지안에듀(4만 원대)가 가장 높은 평균 단가를 기록했으며, 이는 타겟 고객의 지불 의사(WTP)가 높은 특수 자격증 시장임을 의미합니다.

---

<!-- _class: split -->
<div>

# 다빈도 출간년도 트렌드

| 연도 | 비중 | 주요 장르 |
|---|---|---|
| 2026년 | 42% | 자격증 최신판 |
| 2025년 | 16% | 전년도 하반기 신간 |
| 2022 이전| 24% | 고전 스테디셀러 |

</div>
<div>

<div class="card">
<h3>수험서의 시간 공식</h3>
<p>시험 일정을 타겟으로 연도 표기를 '내년(2026)'으로 선제적으로 변경하는 것은 필수적인 세일즈 마케팅 공식입니다.</p>
</div>

</div>

---

# [시각화 8] 가성비 vs 프리미엄 (가격-평점 관계)

<div class="split-image-left">
<div>
  ![](../../images/plot5_price_rating_scatter.png)
</div>
<div>
  <h3>가격 저항선 붕괴</h3>
  <p>산점도에서 보듯, 가격이 비싸다고 평점이 낮아지지 않습니다. 지식 콘텐츠의 특성상 가격보다 '문제 해결 능력'이 우선시됩니다.</p>
</div>
</div>

---

<!-- _class: dark -->
# 도서 라이프사이클 3단계 분류표

리뷰 수에 기반한 포트폴리오 관리 전략.

| 등급 | 기준 | 특성 | 비즈니스 가치 |
|---|---|---|---|
| **메가 스테디** | 리뷰 150+ | 클린코드, 리팩터링 등 수명 무한대 | 캐시카우 (안정적 수익) |
| **성장형 루키** | 리뷰 50~149 | 모두의 딥러닝 등 | 캐시카우 예비군 |
| **트렌드 신간** | 리뷰 50 미만 | 2026년판 기출, AI 트렌드서 | 트래픽 메이커 (단기 수익) |

---

# [시각화 9] 팬덤의 위력 (평점-리뷰수 관계)

![](../../images/plot6_rating_review_scatter.png)

리뷰 수가 많을수록 평점은 떨어지는 것이 일반적이나, 본 데이터에서는 리뷰 수가 폭발적인 메가 스테디셀러들이 오히려 9.8 이상의 견고한 평점을 유지합니다.

---

<!-- _class: split -->
<div>

# 변수 간 상관계수 (Correlation)

| X변수 | Y변수 | 상관계수 |
|---|---|---|
| 가격 | 순위 | +0.12 |
| 평점 | 리뷰수 | +0.28 |
| 순위 | 리뷰수 | -0.31 |
| 가격 | 리뷰수 | -0.15 |

</div>
<div class="card">
<h3>인사이트</h3>
<p>순위가 높을수록 리뷰수가 많은 경향(음의 상관)이 확인됩니다. 마케팅을 통한 초기 리뷰 확보가 랭킹 상승의 트리거가 됩니다.</p>
</div>

---

# [시각화 10] 변수 간 히트맵 시각화

<div style="text-align: center;">
![](../../images/plot9_corr_heatmap.png)
</div>

전체적으로 강한 선형 상관관계는 없으나, 다중 변수 간의 약한 상호작용들이 존재합니다.

---

<!-- _class: lead -->
# 트렌드의 정점: 텍스트 마이닝
### 도서명 속 키워드가 말하는 2026년의 시대정신

---

# 텍스트 마이닝: TF-IDF 중요도

| 순위 | 핵심 키워드 | TF-IDF 점수 | 의미 |
|---|---|---|---|
| 1 | **2026** | 2.45 | 자격증의 최신성 강조 |
| 2 | **시나공** | 1.82 | 수험서 브랜드 충성도 |
| 3 | **필기** | 1.76 | 수험 시장의 캐시카우 |
| 4 | **클로드** | 1.55 | 생성형 AI의 돌풍 |
| 5 | **바이브** | 1.32 | 새로운 코딩 패러다임 |

---

# [시각화 11] 도서명 주요 키워드 바 차트

<div class="split-image-left">
<div>
  ![](../../images/plot10_tfidf_keywords.png)
</div>
<div>
  <h3>두 개의 축</h3>
  <p>시장 수요는 명확하게 둘로 갈립니다.</p>
  <ul>
    <li>당장의 취업을 위한 <strong>자격증</strong></li>
    <li>미래 생존을 위한 <strong>AI 활용</strong></li>
  </ul>
</div>
</div>

---

<!-- _class: dark -->
# [핵심 인사이트 1] 수험서의 시즌성 및 적시성

<div class="grid-2x2">
  <div>
    <h2>현상</h2>
    <p>도서명에 연도(2026)를 포함한 도서가 무려 42%를 점유합니다.</p>
  </div>
  <div>
    <h2>시사점</h2>
    <p>시험 일정에 맞춘 JIT(Just-in-Time) 유통과 타임세일 마케팅으로 전환율을 극대화해야 합니다.</p>
  </div>
</div>

---

# [핵심 인사이트 2] 생성형 AI의 돌풍

<div class="card">
  <h3>패러다임 시프트</h3>
  <p>전통적인 프로그래밍 언어 입문서의 자리를 '클로드', '프롬프트', '바이브 코딩' 등 AI 비서 활용법을 다루는 책들이 빠르게 대체하고 있습니다.</p>
</div>

| 기존 베스트셀러 | 신흥 베스트셀러 |
|---|---|
| Python, Java 기초 | 클로드 코드 활용 바이브 코딩 |
| 딥러닝 알고리즘 수학 | 프롬프트 엔지니어링 실전 |

---

# [비즈니스 액션] 타겟 세그먼테이션 전략

서로 다른 구매 목적을 가진 두 집단을 분리하여 투트랙(Two-track) 마케팅을 전개합니다.

| 분류 | Track 1: 단기 수험생 | Track 2: 트렌드 실무자 |
|---|---|---|
| **소구점** | 초단기 합격, 최신 기출 | 압도적 생산성, 100% 활용법 |
| **마케팅** | 타임세일, 합격 페이백 | 저자 웨비나, 템플릿 증정 |
| **미디어** | 네이버 카페(수만휘 등) | 링크드인, IT 커뮤니티 |

---

# [비즈니스 액션] 재고 및 유통 최적화

<div class="split">
  <div class="card">
    <h3>시즌별 수험서 집중 관리</h3>
    <p>상반기 공채 및 자격증 시험 시즌에 대비하여 주요 출판사(길벗, 영진) 물량을 선제적으로 확보.</p>
  </div>
  <div class="card">
    <h3>AI 신간 패스트트랙</h3>
    <p>기술 변화 주기가 빠른 AI 도서류는 입고 즉시 당일 진열 및 최상단 노출 프로세스 가동.</p>
  </div>
</div>

---

<!-- _class: dark -->
# 3개월 단기 실행 KPI (Phase 1)

즉각적인 트래픽과 매출을 확보하기 위한 첫 번째 단계입니다.

| 부서 | 액션 아이템 | 기한 | KPI |
|---|---|---|---|
| 마케팅팀 | 2026 자격증 얼리버드 특별 기획전 | 1주차 | 매출 20% 상승 |
| 기획팀 | '바이브 코딩' 스페셜 메인 탭 신설 | 2주차 | 트래픽 5만 회 |

---

# 3개월 단기 실행 KPI (Phase 2 & 3)

| 부서 | 액션 아이템 | 기한 | KPI |
|---|---|---|---|
| UI/UX팀 | 리뷰 100+ 명예의 전당 배지 도입 | 5주차 | 장바구니 전환율 10% 상승 |
| 영업팀 | 길벗/한빛 독점 콜라보레이션 굿즈 세트 | 8주차 | 세트 비중 30% 증가 |
| CRM팀 | AI/클로드 활용법 저자 온라인 웨비나 | 11주차| 참석자 1,000명 돌파 |

---

<!-- _class: lead -->
# 끝
데이터가 가리키는 큐레이션 역량 강화로 한 발 앞서갑니다.
**감사합니다.**
