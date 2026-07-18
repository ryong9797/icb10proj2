# 서울 생활인구 데이터 (LOCAL_PEOPLE_DONG) EDA 대시보드 구축 계획

본 프로젝트는 `seoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet` 데이터를 활용하여 파이썬 Streamlit 기반의 기본 탐색적 데이터 분석(EDA) 대시보드를 구축하는 것입니다.
시스템 상의 권한 문제로 직접 코드를 실행하여 데이터를 사전에 확인할 수 없으므로, 대시보드는 동적 컬럼 인식을 기반으로 유연하게 설계됩니다.

## User Review Required
> [!IMPORTANT]
> 윈도우 환경 문제로 백그라운드에서 직접 데이터를 조회할 수 없는 상황입니다. 따라서 데이터의 정확한 컬럼명 구조(예: '총생활인구수', '행정동코드' 등)를 사전에 확정하기 어렵습니다. 
> 본 대시보드는 파케이(Parquet) 파일을 읽어와 동적으로 데이터 구조를 파악하고 시각화할 수 있도록 범용적인 EDA 기능에 맞춰 구현할 예정입니다. 

## Open Questions
> [!QUESTION]
> 1. 제공된 `행정동코드_매핑정보_20241218.xlsx` 파일을 파케이 데이터의 `행정동코드`와 조인(Join)하여 대시보드에 행정동 이름으로 표시해도 될까요? 
> 2. 대시보드를 실행할 진입점 파일의 경로를 `seoul-pops/src/app.py`로 설정해도 괜찮으신가요?

## Proposed Changes

### Streamlit Dashboard (seoul-pops/src)

#### [NEW] [app.py](file:///c:/Users/admin/Desktop/icb10proj2/seoul-pops/src/app.py)
Streamlit 대시보드 메인 파일.
- **데이터 로딩 최적화**: `@st.cache_data`를 활용한 대용량 파케이(Parquet) 파일 로딩 및 엑셀(Excel) 행정동 매핑 정보 조인.
- **사이드바 UI**: 데이터 분석 항목(Overview, 단일 변수 분석, 상관관계 분석)을 탐색할 수 있는 메뉴 제공.
- **Overview (데이터 구조/품질 분석)**:
  - 데이터프레임 미리보기 (상단 N개 행)
  - 결측치 비율 및 데이터 타입 명시
  - 요약 통계량 (평균, 중앙값, 최빈값, 최소/최대 등)
- **단일 항목 분포 (Item Analysis)**:
  - 수치형 변수: Plotly를 이용한 히스토그램(Histogram) 및 박스플롯(Boxplot)으로 분포 및 이상치 확인
  - 범주형 변수: Plotly Bar 차트를 통한 빈도 확인
- **상관성 분석 (Correlation Analysis)**:
  - 수치형 컬럼 간의 피어슨 상관계수(Correlation Matrix) 히트맵
  - 두 변수를 선택하여 비교하는 산점도(Scatter plot) 지원

#### [NEW] [utils.py](file:///c:/Users/admin/Desktop/icb10proj2/seoul-pops/src/utils.py)
데이터 전처리 및 공통 기능 함수.
- 데이터 로더 함수 (결측치 처리, 데이터 타입 최적화)
- 기초 통계 및 왜도/첨도 계산 등 통계 분석 유틸리티

## Verification Plan

### Manual Verification
- 사용자께서 승인해주시면 코드를 작성할 것이며, 작성 후 `uv run streamlit run seoul-pops/src/app.py` 명령어를 통해 대시보드를 직접 실행하여 데이터 로딩, 시각화, 상관관계 분석 기능이 올바르게 동작하는지 테스트해주시면 됩니다.
