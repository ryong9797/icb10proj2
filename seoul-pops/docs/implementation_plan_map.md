# 서울 생활인구 데이터 (LOCAL_PEOPLE_DONG) 지도 시각화 추가 계획

본 계획서는 기존 Streamlit 대시보드에 **Folium 기반 코로플리스(Choropleth) 맵**을 추가하여 시간대별 행정동/구별 생활인구 밀도를 시각화하는 기능을 구현하기 위한 문서입니다.

## User Review Required
> [!WARNING]
> **스킬 제약 사항 충돌 (Plotly vs Folium)**
> `py-streamlit` 스킬 규칙에는 "반드시 Plotly만 사용하라"는 매우 엄격한 제약이 존재합니다. 하지만 사용자님께서 명시적으로 `folium 코로플리스 맵`을 요청하셨으므로, **지도 시각화에 한해서만 예외적으로 `folium` 및 `streamlit-folium` 패키지를 사용**하여 구현하고자 합니다. 승인해 주시면 진행하겠습니다.

## Open Questions
> [!QUESTION]
> 1. 현재 워크스페이스 내에 서울시 행정구역 경계 데이터(`GeoJSON` 등)가 존재하지 않습니다. 따라서 앱 실행 시 깃허브 등 공개된 **서울시 GeoJSON URL을 동적으로 불러와서 매핑**하는 방식을 채택해도 괜찮으신가요?
> 2. 생활인구 밀도를 표현할 때 엑셀 매핑 정보의 수준(행정동 단위인지 시군구 단위인지)에 따라, 지도 표현 수준을 유연하게 맞추어 코딩하도록 하겠습니다.

## Proposed Changes

### Streamlit Dashboard (seoul-pops/src/app.py 및 report/app.py)

#### [MODIFY] [app.py](file:///c:/Users/admin/Desktop/icb10proj2/seoul-pops/report/app.py)
메인 대시보드 파일에 지도 시각화 탭을 추가합니다.
- **Folium 모듈 임포트**: `import folium` 및 `from streamlit_folium import st_folium` 추가.
- **사이드바 메뉴 추가**: "Map (지도 시각화)" 탭 추가.
- **시간대 슬라이더(Time Slider)**: 0시부터 23시까지 선택할 수 있는 `st.slider` 추가 (컬럼명 '시간대구분' 등 동적 탐지).
- **데이터 집계 로직**: 선택된 시간대에 해당하는 데이터만 필터링하여 행정동/구 단위로 `총생활인구수`(또는 밀도)를 집계.
- **코로플리스 맵(Choropleth) 렌더링**: `folium.Choropleth`를 이용하여 지도에 색상으로 인구 밀도를 시각화하고 `st_folium`으로 렌더링.

### 유틸리티 기능 (seoul-pops/src/utils.py 및 report/utils.py)

#### [MODIFY] [utils.py](file:///c:/Users/admin/Desktop/icb10proj2/seoul-pops/report/utils.py)
- **GeoJSON 로더 추가**: `requests` 라이브러리를 통해 서울시 GeoJSON 데이터를 캐싱하여 불러오는 유틸리티 함수 `load_geojson()` 추가.

## Verification Plan

### Manual Verification
1. 코드가 반영된 후 터미널에서 서버를 재시작(`uv run streamlit run seoul-pops/report/app.py`)합니다.
2. 좌측 메뉴에서 'Map (지도 시각화)'를 선택합니다.
3. 시간대 슬라이더를 움직였을 때, 지도(Folium) 상의 행정동별 색상(인구 밀도)이 알맞게 변하는지 확인합니다.
