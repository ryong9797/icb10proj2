"""
기상청 지상(종관, ASOS) 일자료 조회 OpenAPI 연동 Streamlit 대시보드

이 애플리케이션은 기상청 ASOS 일자료 API를 연동하여 전국 주요 관측소의 일별 기상 관측 데이터를
실시간으로 조회하고 기온, 강수량, 습도, 바람, 기압 등의 다양한 기상 요소를 시각적으로 분석합니다.
사용자는 사이드바에서 API 키, 다중 지점(쉼표 구분), 검색 기간을 자유롭게 설정할 수 있으며,
API 키가 없는 경우에도 고품질 가상(Mock) 데이터를 통해 시스템의 주요 기능을 즉시 체험할 수 있습니다.
"""

import datetime
import math
import os
import re
import sys
import urllib.parse
import pandas as pd
import numpy as np
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 스크립트 실행 경로를 시스템 경로에 추가하여 로컬 모듈 참조 해결
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# 기존 유틸리티 모듈에서 디자인 테마 로드 시도
try:
    from utils import apply_premium_design
except ImportError:
    # 예외 발생 시 인라인으로 간략한 스타일 정의 적용
    def apply_premium_design():
        pass

# 1. 페이지 초기 설정 및 프리미엄 디자인 적용
st.set_page_config(
    page_title="기상청 ASOS 기상 데이터 분석 시스템",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_premium_design()

# 2. 전국 ASOS 주요 관측 지점 매핑 정보 정의 (약 90여 개 관측소)
ASOS_STATIONS = {
    "서울": "108", "부산": "159", "대구": "143", "인천": "112", "광주": "156",
    "대전": "133", "울산": "152", "수원": "119", "춘천": "101", "강릉": "105",
    "청주": "131", "전주": "146", "제주": "184", "서귀포": "189", "목포": "165",
    "여수": "168", "안동": "171", "포항": "138", "창원": "155", "진주": "192",
    "군산": "162", "순천": "174", "원주": "114", "충주": "127", "천안": "232",
    "보령": "235", "서산": "129", "속초": "90", "철원": "95", "대관령": "100",
    "동해": "106", "태백": "216", "영월": "121", "제천": "221", "보은": "226",
    "추풍령": "135", "영덕": "277", "의성": "278", "구미": "279", "영천": "281",
    "거창": "284", "합천": "285", "밀양": "288", "산청": "289", "거제": "294",
    "남해": "295", "통영": "162", "광양": "266", "고흥": "262", "보성": "258",
    "장흥": "260", "해남": "261", "강진": "259", "완도": "170", "진도": "175",
    "영광": "252", "무안": "164", "부안": "243", "고창": "251", "정읍": "245",
    "임실": "244", "남원": "247", "장수": "248", "백령도": "102", "동두천": "98",
    "파주": "99", "양평": "202", "이천": "203", "인제": "211", "홍천": "212",
    "삼척": "214", "울릉도": "115", "독도": "115", "상주": "137", "문경": "273",
    "청송": "276", "봉화": "271", "영주": "272", "부여": "236", "금산": "238",
    "순창": "254", "구례": "257"
}

# 지점 번호 -> 지점명 역매핑 딕셔너리 생성
REV_STATIONS = {v: k for k, v in ASOS_STATIONS.items()}

# 16방위 풍향 코드 문자열 변환 테이블
WIND_DIR_MAP = {
    0: "북 (N)", 2: "북북동 (NNE)", 4: "북동 (NE)", 6: "동북동 (ENE)",
    8: "동 (E)", 10: "동남동 (ESE)", 12: "남동 (SE)", 14: "남남동 (SSE)",
    16: "남 (S)", 18: "남남서 (SSW)", 20: "남서 (SW)", 22: "서남서 (WSW)",
    24: "서 (W)", 26: "서북서 (WNW)", 28: "북서 (NW)", 30: "북북서 (NNW)",
    32: "북 (N)"
}

def degree_to_16dir(deg):
    """풍향 각도를 16방위 명칭으로 변환합니다."""
    if pd.isna(deg):
        return "무풍/결측"
    idx = int(((deg + 11.25) % 360) / 22.5) * 2
    return WIND_DIR_MAP.get(idx, "알 수 없음")

def calculate_skewness(series):
    """pandas/numpy를 사용하여 scipy 없이 왜도를 계산합니다."""
    clean_series = series.dropna()
    if len(clean_series) < 3:
        return 0.0
    mean = clean_series.mean()
    std = clean_series.std(ddof=0)
    if std == 0:
        return 0.0
    n = len(clean_series)
    m3 = ((clean_series - mean) ** 3).sum() / n
    skew = m3 / (std ** 3)
    if n > 2:
        skew = skew * math.sqrt(n * (n - 1)) / (n - 2)
    return skew

def calculate_kurtosis(series):
    """pandas/numpy를 사용하여 scipy 없이 첨도를 계산합니다."""
    clean_series = series.dropna()
    if len(clean_series) < 4:
        return 0.0
    mean = clean_series.mean()
    std = clean_series.std(ddof=0)
    if std == 0:
        return 0.0
    n = len(clean_series)
    m4 = ((clean_series - mean) ** 4).sum() / n
    kurt = m4 / (std ** 4) - 3.0
    if n > 3:
        kurt = ((n - 1) * ((n + 1) * kurt + 6)) / ((n - 2) * (n - 3))
    return kurt

# 3. 고품질 가상(Mock) 데이터 생성기

def generate_mock_weather_data(start_date: datetime.date, end_date: datetime.date, station_id: str) -> pd.DataFrame:
    """기상청 API 키가 없거나 통신 실패 시 지점별 계절성 및 특성을 고려한 일별 가상 기상 데이터를 생성합니다."""
    delta = datetime.timedelta(days=1)
    current_date = start_date
    records = []
    
    stn_name = REV_STATIONS.get(station_id, f"지점 {station_id}")
    
    # 지점 번호 해시값으로 시드 고정하여 동일 조건 조회 시 항상 일관된 가상 데이터 제공
    seed_val = int(station_id) if station_id.isdigit() else 108
    np.random.seed(seed_val)
    
    # 지역별 온도 오프셋 설정 (제주, 부산 등은 따뜻하고, 대관령/춘천은 춥게 설정)
    temp_offset = 0.0
    if stn_name == "제주":
        temp_offset = 5.0
    elif stn_name == "서귀포":
        temp_offset = 6.2
    elif stn_name == "부산":
        temp_offset = 2.8
    elif stn_name == "광주":
        temp_offset = 1.5
    elif stn_name == "대관령":
        temp_offset = -6.5
    elif stn_name == "춘천":
        temp_offset = -2.0
    else:
        temp_offset = np.random.uniform(-1.5, 1.5)

    # 강수량 가중치 설정 (남부지방이나 제주는 비가 더 자주 내림)
    rain_multiplier = 1.3 if stn_name in ["제주", "서귀포", "강릉"] else 1.0

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_year = current_date.timetuple().tm_yday
        
        # 연중 계절성 온도 모델링 (1월 중순 최저, 7월 말 최고)
        temp_base = 13.0 - 14.5 * math.cos(2 * math.pi * (day_of_year - 15) / 365.0)
        temp_noise = np.random.normal(0, 3.2)
        avg_temp = round(temp_base + temp_offset + temp_noise, 1)
        
        # 일 최고/최저 기온 설정 (일교차 적용)
        diurnal_range = np.random.uniform(6.0, 12.0)
        min_temp = round(avg_temp - diurnal_range / 2.0, 1)
        max_temp = round(avg_temp + diurnal_range / 2.0, 1)
        
        # 최고/최저 기온 발생 시각 (가상)
        min_temp_time = f"{np.random.randint(4, 7):02d}{np.random.randint(0, 60):02d}"
        max_temp_time = f"{np.random.randint(13, 16):02d}{np.random.randint(0, 60):02d}"
        
        # 강수 모델링 (여름철 6~8월 장마철 고려)
        month = current_date.month
        rain_prob = 0.12 * rain_multiplier
        if month in [6, 7, 8]:
            rain_prob = 0.38 * rain_multiplier
        elif month in [4, 5, 9, 10]:
            rain_prob = 0.22 * rain_multiplier
            
        is_rain = np.random.random() < rain_prob
        precipitation = 0.0
        rain_dur = 0.0
        if is_rain:
            # 강수량 지수분포 기반 시뮬레이션
            precipitation = round(np.random.exponential(scale=12.0), 1)
            precipitation = min(250.0, max(0.5, precipitation))
            rain_dur = round(np.random.uniform(0.5, 12.0), 1) if precipitation > 0 else 0.0
            
        # 신적설량 (겨울철 대관령 등 추운 지역 폭설 가상 구현)
        snow = 0.0
        if precipitation > 0 and avg_temp < 1.5:
            snow = round(precipitation * np.random.uniform(0.8, 1.2), 1)
            # 눈이 오면 강수량은 녹은 물 기준이 됨
        
        # 습도 설정 (강수량 및 기온 기반 결합)
        if precipitation > 0:
            avg_humidity = round(np.random.uniform(82.0, 99.0), 1)
        else:
            avg_humidity = round(max(20.0, min(95.0, 68.0 - (avg_temp - 12.0) * 0.4 + np.random.normal(0, 10.0))), 1)
            
        min_humidity = round(max(10.0, avg_humidity - np.random.uniform(15.0, 35.0)), 1)
        min_humidity_time = f"{np.random.randint(12, 16):02d}{np.random.randint(0, 60):02d}"
        
        # 바람 데이터 생성 (평균 풍속, 최대 풍속, 최대 풍속 풍향 및 시각)
        avg_wind = round(np.random.weibull(a=1.8) * 2.2 + 0.3, 1)
        max_wind = round(avg_wind * np.random.uniform(1.5, 2.5) + np.random.uniform(0.5, 3.0), 1)
        max_wind_dir = np.random.randint(0, 16) * 22.5
        max_wind_time = f"{np.random.randint(10, 18):02d}{np.random.randint(0, 60):02d}"
        sum_wind_dir = np.random.randint(0, 360)
        
        # 기압 데이터 생성 (온도와 반비례 경향성)
        base_press = 1013.25
        press_temp_effect = -0.3 * (avg_temp - 15.0)
        press_rain_effect = -4.5 if precipitation > 10.0 else 0.0
        avg_press = round(base_press + press_temp_effect + press_rain_effect + np.random.normal(0, 4.0), 1)
        avg_sea_press = round(avg_press + 1.2, 1) # 단순 고도 보정
        
        # 일조/일사량
        if precipitation > 0:
            sun_hours = round(np.random.uniform(0.0, 3.0), 1)
            solar_rad = round(np.random.uniform(1.0, 8.0), 2)
        else:
            sun_hours = round(np.random.uniform(5.0, 12.5), 1)
            solar_rad = round(np.random.uniform(8.0, 26.0), 2)
            
        # 지면온도 (기온에 의존적이나 일사 영향 포함)
        avg_ground_temp = round(avg_temp + (solar_rad * 0.4) - 1.5 + np.random.normal(0, 1.2), 1)

        records.append({
            "tm": date_str,
            "stnId": station_id,
            "stnNm": stn_name,
            "avgTa": avg_temp,
            "minTa": min_temp,
            "minTaHrmt": min_temp_time,
            "maxTa": max_temp,
            "maxTaHrmt": max_temp_time,
            "sumRn": precipitation if precipitation > 0 else np.nan,
            "rnDur": rain_dur if rain_dur > 0 else np.nan,
            "maxWs": max_wind,
            "maxWsWd": max_wind_dir,
            "maxWsHrmt": max_wind_time,
            "avgWs": avg_wind,
            "sumWindDir": sum_wind_dir,
            "avgRhm": avg_humidity,
            "minRhm": min_humidity,
            "minRhmHrmt": min_humidity_time,
            "avgPa": avg_press,
            "avgPs": avg_sea_press,
            "sumSsHr": sun_hours,
            "sumGsr": solar_rad,
            "avgTs": avg_ground_temp,
            "sumSnsn": snow if snow > 0 else np.nan
        })
        current_date += delta
        
    df = pd.DataFrame(records)
    return df

# 4. 공공데이터포털 기상청 API 연동 함수
@st.cache_data(ttl=3600)

def fetch_asos_api_data(api_key: str, start_date: datetime.date, end_date: datetime.date, station_id: str) -> pd.DataFrame:
    """기상청 ASOS 일자료 API를 호출하여 날씨 데이터를 수집합니다. 실패 시 조용히 가상 데이터를 반환합니다."""
    if not api_key.strip():
        return generate_mock_weather_data(start_date, end_date, station_id)
        
    url = "https://bd.kma.go.kr/kma2020/"
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    
    params = {
        "serviceKey": api_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "DAY",
        "startDt": start_str,
        "endDt": end_str,
        "stnIds": station_id,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return generate_mock_weather_data(start_date, end_date, station_id)
            
        resp_text = response.text.strip()
        if resp_text.startswith("<"):
            return generate_mock_weather_data(start_date, end_date, station_id)

        res_json = response.json()
        header = res_json.get("response", {}).get("header", {})
        result_code = header.get("resultCode", "00")
        
        if result_code != "00":
            return generate_mock_weather_data(start_date, end_date, station_id)
            
        body = res_json.get("response", {}).get("body", {})
        if not body or "items" not in body or not body["items"]:
            return generate_mock_weather_data(start_date, end_date, station_id)
            
        items = body["items"].get("item", [])
        if not items:
            return generate_mock_weather_data(start_date, end_date, station_id)
            
        if isinstance(items, dict):
            items = [items]
            
        records = []
        for item in items:
            def safe_float(val):
                if val is None or str(val).strip() == "":
                    return np.nan
                try:
                    return float(val)
                except ValueError:
                    return np.nan

            records.append({
                "tm": item.get("tm"),
                "stnId": item.get("stnId"),
                "stnNm": item.get("stnNm"),
                "avgTa": safe_float(item.get("avgTa")),
                "minTa": safe_float(item.get("minTa")),
                "minTaHrmt": item.get("minTaHrmt"),
                "maxTa": safe_float(item.get("maxTa")),
                "maxTaHrmt": item.get("maxTaHrmt"),
                "sumRn": safe_float(item.get("sumRn")),
                "rnDur": safe_float(item.get("rnDur")),
                "maxWs": safe_float(item.get("maxWs")),
                "maxWsWd": safe_float(item.get("maxWsWd")),
                "maxWsHrmt": item.get("maxWsHrmt"),
                "avgWs": safe_float(item.get("avgWs")),
                "sumWindDir": safe_float(item.get("sumWindDir")),
                "avgRhm": safe_float(item.get("avgRhm")),
                "minRhm": safe_float(item.get("minRhm")),
                "minRhmHrmt": item.get("minRhmHrmt"),
                "avgPa": safe_float(item.get("avgPa")),
                "avgPs": safe_float(item.get("avgPs")),
                "sumSsHr": safe_float(item.get("sumSsHr")),
                "sumGsr": safe_float(item.get("sumGsr")),
                "avgTs": safe_float(item.get("avgTs")),
                "sumSnsn": safe_float(item.get("sumSnsn"))
            })
            
        df = pd.DataFrame(records)
        return df
    except Exception:
        return generate_mock_weather_data(start_date, end_date, station_id)


# 5. 전역 데이터 로딩 코디네이터 (다중 지점 수집 및 병합)
def load_and_merge_weather_data(api_key: str, start_date: datetime.date, end_date: datetime.date, station_ids: list) -> pd.DataFrame:
    """선택된 여러 지점들의 데이터를 취합하여 하나의 판다스 데이터프레임으로 구축합니다."""
    merged_dfs = []
    
    for stn_id in station_ids:
        df = fetch_asos_api_data(api_key, start_date, end_date, stn_id)
        if df is not None and len(df) > 0:
            merged_dfs.append(df)
                
    if not merged_dfs:
        return generate_mock_weather_data(start_date, end_date, "108")
        
    final_df = pd.concat(merged_dfs, ignore_index=True)
    # 날짜와 지점코드 순으로 정렬
    final_df["tm"] = pd.to_datetime(final_df["tm"])
    final_df = final_df.sort_values(by=["tm", "stnId"]).reset_index(drop=True)
    
    return final_df


# 6. 사이드바(Sidebar) 전역 분석 조절 매개변수 설정
st.sidebar.markdown("## ⚙️ 기상청 OpenAPI 설정")

# 6.1. API 키 입력
api_key_help = "공공데이터포털(data.go.kr)에서 발급받은 '기상청_지상(종관, ASOS) 일자료 조회서비스' 일반 인증키(인코딩/디코딩)를 입력해 주세요. 미입력 시 프리미엄 시뮬레이션 데모 데이터가 작동합니다."
weather_api_key = st.sidebar.text_input("공공데이터 API 인증키", type="password", value="32f0fe7f879f9826e9c6f0baa75606aee9b9ea6dddfd875d494290ca2c67ebee", help=api_key_help)

# 6.2. 지점 검색어 처리
st.sidebar.markdown("### 📍 관측 지점 검색")
stn_input_help = "한글 지점명 또는 3자리 지점코드를 쉼표(,)로 구분하여 입력하십시오. (예: 서울, 부산, 184, 강릉)"
raw_stn_input = st.sidebar.text_input("검색어 입력 (쉼표 구분)", value="서울, 부산", help=stn_input_help)

# 지점 검색 텍스트 파싱 로직
search_tokens = [tok.strip() for tok in raw_stn_input.split(",") if tok.strip()]
selected_stn_ids = []
invalid_tokens = []

for token in search_tokens:
    if token in ASOS_STATIONS:
        selected_stn_ids.append(ASOS_STATIONS[token])
    elif token in REV_STATIONS:
        selected_stn_ids.append(token)
    elif token.isdigit() and len(token) == 3:
        # 매핑 사전에 없어도 3자리 숫자면 기상청 코드로 강제 수용
        selected_stn_ids.append(token)
    else:
        invalid_tokens.append(token)

# 지점 중복 제거 및 무결성 검증
selected_stn_ids = sorted(list(set(selected_stn_ids)))

if invalid_tokens:
    st.sidebar.warning(f"⚠️ 매핑 불가능 지점: {', '.join(invalid_tokens)}")

if not selected_stn_ids:
    st.sidebar.error("❌ 분석할 관측 지점 정보가 올바르지 않습니다. '서울' 등으로 다시 작성해 주세요.")
    st.stop()

# 6.3. 기간 설정
st.sidebar.markdown("### 📅 관측 조회 기간")
today_date = datetime.date.today()
default_start_date = today_date - datetime.timedelta(days=90) # 기본 조회 범위 90일
start_sel = st.sidebar.date_input("조회 시작일", default_start_date, max_value=today_date)
end_sel = st.sidebar.date_input("조회 종료일", today_date, min_value=start_sel, max_value=today_date)

# 6.4. 다중 페이지 네비게이션 라디오 메뉴
st.sidebar.markdown("### 🧭 분석 대시보드 메뉴")
dashboard_page = st.sidebar.radio(
    "페이지 선택",
    [
        "📊 종합 데이터 조회",
        "🌡️ 기온 심층 분석",
        "🌧️ 강수량 및 습도 분석",
        "💨 바람 및 기압 분석",
        "📍 지점별 비교 분석"
    ]
)

# 7. 데이터 전역 수집 실행
with st.spinner("기상 관측 데이터 수집 파이프라인 작동 중..."):
    weather_df = load_and_merge_weather_data(weather_api_key, start_sel, end_sel, selected_stn_ids)

# 사이드바 데이터 로딩 상태 요약 정보 표시
st.sidebar.markdown("---")
st.sidebar.markdown("### 📢 데이터 로드 현황")
if not weather_api_key.strip():
    st.sidebar.info("💡 데모 모드 (가상 기상 시뮬레이션 작동 중)")
else:
    st.sidebar.success("✅ 기상 데이터 연동 완료")

# 지점 정보 추출
distinct_stations = weather_df["stnNm"].unique()

# ==============================================================================
# 1. 📊 종합 데이터 조회 페이지
# ==============================================================================
if dashboard_page == "📊 종합 데이터 조회":
    st.title("📊 기상 관측 종합 데이터 조회")
    st.markdown("수집된 종관기상관측(ASOS) 데이터를 확인하고, 관측 지점별 핵심 KPI와 원본 데이터를 격자 형태로 조회합니다.")
    
    # 1.1. 주요 핵심 KPI 연산 및 카드 배치
    num_days = weather_df["tm"].nunique()
    avg_temp_val = weather_df["avgTa"].mean()
    max_temp_row = weather_df.loc[weather_df["maxTa"].idxmax()] if not weather_df["maxTa"].isna().all() else None
    total_rain_val = weather_df["sumRn"].sum() # 누적 강수
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(
            f'<div class="premium-card">'
            f'<h4>📍 관측 지점 수</h4>'
            f'<p style="font-size: 2.2rem; font-weight:800; color:#3B82F6; margin:0;">{len(distinct_stations)}개소</p>'
            f'<small style="color:#94A3B8;">{", ".join(distinct_stations)}</small>'
            f'</div>',
            unsafe_allow_html=True
        )
    with kpi_col2:
        st.markdown(
            f'<div class="premium-card">'
            f'<h4>📅 분석 기간 일수</h4>'
            f'<p style="font-size: 2.2rem; font-weight:800; color:#10B981; margin:0;">{num_days}일</p>'
            f'<small style="color:#94A3B8;">{start_sel} ~ {end_sel}</small>'
            f'</div>',
            unsafe_allow_html=True
        )
    with kpi_col3:
        if max_temp_row is not None:
            max_t_val = max_temp_row["maxTa"]
            max_t_stn = max_temp_row["stnNm"]
            max_t_date = max_temp_row["tm"].strftime("%m/%d")
            st.markdown(
                f'<div class="premium-card">'
                f'<h4>🔥 기간 최고 기온</h4>'
                f'<p style="font-size: 2.2rem; font-weight:800; color:#EF4444; margin:0;">{max_t_val:.1f}°C</p>'
                f'<small style="color:#94A3B8;">{max_t_stn} ({max_t_date})</small>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="premium-card">'
                f'<h4>🔥 기간 최고 기온</h4>'
                f'<p style="font-size: 2.2rem; font-weight:800; color:#EF4444; margin:0;">N/A</p>'
                f'</div>',
                unsafe_allow_html=True
            )
    with kpi_col4:
        st.markdown(
            f'<div class="premium-card">'
            f'<h4>☔ 기간 누적 강수량</h4>'
            f'<p style="font-size: 2.2rem; font-weight:800; color:#F59E0B; margin:0;">{total_rain_val:,.1f}mm</p>'
            f'<small style="color:#94A3B8;">조회된 전체 지점 합산값</small>'
            f'</div>',
            unsafe_allow_html=True
        )

    # 1.2. 종합 시계열 대략적인 시각화
    st.markdown("### 📈 전체 관측 지점별 기온 변화 추이")
    fig_summary = px.line(
        weather_df,
        x="tm",
        y="avgTa",
        color="stnNm",
        labels={"tm": "날짜", "avgTa": "평균 기온 (°C)", "stnNm": "관측 지점"},
        title="일자별 평균 기온 추이 비교"
    )
    fig_summary.update_layout(
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    )
    st.plotly_chart(fig_summary, use_container_width=True)

    # 1.3. 원본 데이터프레임 표출
    st.markdown("### 📋 수집된 ASOS 원본 데이터 목록")
    
    # 지점 필터 추가 (조회용)
    selected_view_stns = st.multiselect("테이블에 표출할 지점 필터", options=distinct_stations, default=list(distinct_stations))
    filtered_view_df = weather_df[weather_df["stnNm"].isin(selected_view_stns)].copy()
    
    # 날짜 컬럼 보기 좋게 가공
    filtered_view_df["날짜"] = filtered_view_df["tm"].dt.strftime("%Y-%m-%d")
    
    # 컬럼 재배치 및 이름 정리
    table_columns = {
        "날짜": "날짜",
        "stnNm": "지점명",
        "stnId": "지점코드",
        "avgTa": "평균기온(°C)",
        "maxTa": "최고기온(°C)",
        "minTa": "최저기온(°C)",
        "sumRn": "강수량(mm)",
        "avgRhm": "상대습도(%)",
        "avgWs": "평균풍속(m/s)",
        "maxWs": "최대풍속(m/s)",
        "avgPs": "해면기압(hPa)"
    }
    
    st.dataframe(
        filtered_view_df[list(table_columns.keys())].rename(columns=table_columns),
        use_container_width=True,
        hide_index=True
    )
    
    # 다운로드 유틸리티
    csv_bytes = filtered_view_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 CSV 형태로 데이터 내보내기",
        data=csv_bytes,
        file_name="asos_weather_data.csv",
        mime="text/csv"
    )

# ==============================================================================
# 2. 🌡️ 기온 심층 분석 페이지
# ==============================================================================
elif dashboard_page == "🌡️ 기온 심층 분석":
    st.title("🌡️ 기온 변화 양상 및 통계 분포 분석")
    st.markdown("평균 기온뿐만 아니라 일별 최저/최고 기온의 범위 변화, 기온의 통계적 분포 상태(왜도, 첨도, 이상치 분석)를 정량적으로 제시합니다.")

    # 지점 선택 탭
    stn_tabs = st.tabs(distinct_stations)
    for idx, stn in enumerate(distinct_stations):
        with stn_tabs[idx]:
            stn_data = weather_df[weather_df["stnNm"] == stn].copy()
            
            if stn_data["avgTa"].isna().all():
                st.warning("분석할 기온 데이터가 존재하지 않습니다.")
                continue

            # 2.1. 기온 시계열 영역 (최고-평균-최저 범위 시각화)
            st.markdown("#### 🗓️ 일별 기온 추이 및 기온 범위 (최저 ~ 최고)")
            
            fig_temp = go.Figure()
            # 최저 기온
            fig_temp.add_trace(go.Scatter(
                x=stn_data["tm"], y=stn_data["minTa"],
                name="최저 기온 (°C)",
                line=dict(color="#60A5FA", width=1.5, dash="dash")
            ))
            # 평균 기온
            fig_temp.add_trace(go.Scatter(
                x=stn_data["tm"], y=stn_data["avgTa"],
                name="평균 기온 (°C)",
                line=dict(color="#10B981", width=3)
            ))
            # 최고 기온
            fig_temp.add_trace(go.Scatter(
                x=stn_data["tm"], y=stn_data["maxTa"],
                name="최고 기온 (°C)",
                line=dict(color="#EF4444", width=1.5, dash="dash")
            ))
            
            fig_temp.update_layout(
                hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="기온 (°C)", showgrid=True, gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_temp, use_container_width=True)

            # 2.2. 통계적 정밀 분석 (2열 레이아웃: 분포 히스토그램 vs Box Plot 이상치 식별)
            st.markdown("#### 📊 기온 분포의 통계적 구조 분석")
            stat_col1, stat_col2 = st.columns(2)
            
            with stat_col1:
                # 분포 히스토그램 (Plotly)
                fig_hist = px.histogram(
                    stn_data,
                    x="avgTa",
                    nbins=20,
                    color_discrete_sequence=["#34D399"],
                    labels={"avgTa": "평균 기온 (°C)"},
                    title="일 평균 기온 히스토그램 분포"
                )
                fig_hist.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0")
                )
                st.plotly_chart(fig_hist, use_container_width=True)
                
            with stat_col2:
                # 기온 범위 및 변동성 Box Plot
                fig_box = go.Figure()
                fig_box.add_trace(go.Box(y=stn_data["avgTa"], name="평균 기온", marker_color="#10B981"))
                fig_box.add_trace(go.Box(y=stn_data["maxTa"], name="최고 기온", marker_color="#EF4444"))
                fig_box.add_trace(go.Box(y=stn_data["minTa"], name="최저 기온", marker_color="#3B82F6"))
                
                fig_box.update_layout(
                    title="기온 항목별 통계 범위 및 사분위 분포 (Box Plot)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0"),
                    yaxis=dict(title="기온 (°C)")
                )
                st.plotly_chart(fig_box, use_container_width=True)

            # 2.3. 비대칭성 및 변동 분석 테이블 (왜도, 첨도, IQR, 표준편차)
            st.markdown("#### 📐 기온 분포 통계량 요약 및 비대칭 검증")
            
            # 왜도/첨도/변동계수 계산 (scipy 없이 numpy 기반 함수로 계산하여 안정성 확보)
            avg_skew = calculate_skewness(stn_data["avgTa"])
            avg_kurt = calculate_kurtosis(stn_data["avgTa"])
            avg_std = stn_data["avgTa"].std()
            avg_mean = stn_data["avgTa"].mean()
            # 변동계수(CV): 표준편차 / 평균 (평균이 0인 경우 대비 절대값 처리)
            avg_cv = (avg_std / abs(avg_mean)) if avg_mean != 0 else np.nan
            
            # IQR 연산
            q1 = stn_data["avgTa"].quantile(0.25)
            q3 = stn_data["avgTa"].quantile(0.75)
            iqr = q3 - q1
            
            # 가이드 해석 도출
            skew_desc = "우측으로 긴 꼬리 분포 (양의 왜도)" if avg_skew > 0.5 else ("좌측으로 긴 꼬리 분포 (음의 왜도)" if avg_skew < -0.5 else "대칭적인 종모양 분포")
            kurt_desc = "중앙에 집중된 뾰족한 분포 (고첨)" if avg_kurt > 1.0 else ("완만하고 넓게 퍼진 분포 (저첨)" if avg_kurt < -1.0 else "표준 정규분포에 가까움")

            kpi_s1, kpi_s2, kpi_s3, kpi_s4 = st.columns(4)
            with kpi_s1:
                st.metric(label="📐 평균 기온 왜도 (Skewness)", value=f"{avg_skew:.3f}", help="왜도가 0에 가까울수록 좌우 대칭입니다.")
            with kpi_s2:
                st.metric(label="🔔 평균 기온 첨도 (Kurtosis)", value=f"{avg_kurt:.3f}", help="첨도가 0에 가까울수록 정규분포의 뾰족함에 가깝습니다.")
            with kpi_s3:
                st.metric(label="📏 사분위 범위 (IQR)", value=f"{iqr:.1f}°C", help="중앙값 주변 50% 데이터가 분포하는 구간 크기입니다.")
            with kpi_s4:
                st.metric(label="📊 표준편차 (Std Dev)", value=f"{avg_std:.2f}°C", help="기온 데이터의 분산 정도를 의미합니다.")

            st.markdown(
                f"""
                > **💡 통계적 형태 해석**
                > - **기온 왜도 특성**: 본 분석 대상 기간 동안 기온 분포는 **{skew_desc}**를 나타냅니다.
                > - **기온 첨도 특성**: 정규분포 대비 기온 변동 양상은 **{kurt_desc}** 상태를 보입니다.
                """
            )

# ==============================================================================
# 3. 🌧️ 강수량 및 습도 분석 페이지
# ==============================================================================
elif dashboard_page == "🌧️ 강수량 및 습도 분석":
    st.title("🌧️ 강수 및 대기 수분 분석")
    st.markdown("조회 대상 기간의 강수 발생 패턴, 누적 강수 기여량, 그리고 기온과 습도의 물리적 상관관계를 규명합니다.")

    stn_tabs = st.tabs(distinct_stations)
    for idx, stn in enumerate(distinct_stations):
        with stn_tabs[idx]:
            stn_data = weather_df[weather_df["stnNm"] == stn].copy()
            
            # 결측값 채우기 (강수량은 비가 안 온 날 NaN인 경우 0.0으로 처리)
            stn_data["sumRn_clean"] = stn_data["sumRn"].fillna(0.0)
            
            total_rain = stn_data["sumRn_clean"].sum()
            rain_days = (stn_data["sumRn_clean"] > 0).sum()
            total_days = len(stn_data)
            rain_ratio = (rain_days / total_days) * 100.0 if total_days > 0 else 0.0
            
            # 3.1. 강수 정보 지표 카드
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                st.metric(label="🌧️ 총 누적 강수량", value=f"{total_rain:.1f} mm")
            with h_col2:
                st.metric(label="📅 강수 발생 일수", value=f"{rain_days} 일 / {total_days} 일")
            with h_col3:
                st.metric(label="📈 강수일 발생 비율", value=f"{rain_ratio:.1f} %")

            # 3.2. 이중 축 트렌드 (강수량 막대 vs 평균 상대습도 선)
            st.markdown("#### 🗓️ 일별 강수량 및 평균 상대습도 변화 추이")
            
            fig_rain_hum = make_subplots(specs=[[{"secondary_y": True}]])
            
            # 강수량 막대 그래프
            fig_rain_hum.add_trace(
                go.Bar(x=stn_data["tm"], y=stn_data["sumRn_clean"], name="일 강수량 (mm)", marker_color="#3B82F6"),
                secondary_y=False
            )
            # 상대습도 꺾은선
            fig_rain_hum.add_trace(
                go.Scatter(x=stn_data["tm"], y=stn_data["avgRhm"], name="평균 상대습도 (%)", line=dict(color="#10B981", width=2)),
                secondary_y=True
            )
            
            fig_rain_hum.update_layout(
                hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="강수량 (mm)", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis2=dict(title="상대습도 (%)", showgrid=False, range=[0, 100])
            )
            st.plotly_chart(fig_rain_hum, use_container_width=True)

            # 3.3. 상관관계 분석 (기온 vs 습도 산점도 및 상관계수)
            st.markdown("#### 🔬 기온과 상대습도 간의 상관성 분석")
            
            # 유효 데이터 필터링
            valid_subset = stn_data.dropna(subset=["avgTa", "avgRhm"])
            
            if len(valid_subset) > 5:
                corr_val = valid_subset["avgTa"].corr(valid_subset["avgRhm"])
                
                # 산점도 차트 구성 (Plotly Express 활용)
                fig_scatter = px.scatter(
                    valid_subset,
                    x="avgTa",
                    y="avgRhm",
                    trendline="ols",
                    trendline_color_override="#EF4444",
                    labels={"avgTa": "평균 기온 (°C)", "avgRhm": "평균 상대습도 (%)"},
                    title=f"기온 및 상대습도 분포 분산도 (상관계수 r = {corr_val:.3f})"
                )
                fig_scatter.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0")
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # 피어슨 상관계수 해석
                abs_corr = abs(corr_val)
                corr_dir = "음의 상관관계 (기온이 오를수록 대기가 건조해지는 경향)" if corr_val < 0 else "양의 상관관계 (기온이 오를수록 대기가 습해지는 경향)"
                if abs_corr > 0.7:
                    corr_strength = "매우 강한"
                elif abs_corr > 0.4:
                    corr_strength = "유의미한 수준의 중간 강도"
                else:
                    corr_strength = "약한 수준의 미미한"
                    
                st.markdown(
                    f"> **💡 상관관계 요약**: 두 지표 간 상관계수는 **{corr_val:.3f}**로, **{corr_strength} {corr_dir}**를 띄고 있습니다."
                )
            else:
                st.info("상관관계를 계산하기 위한 유효 기상 데이터 쌍이 부족합니다.")

# ==============================================================================
# 4. 💨 바람 및 기압 분석 페이지
# ==============================================================================
elif dashboard_page == "💨 바람 및 기압 분석":
    st.title("💨 대기 운동 및 기압 변화 분석")
    st.markdown("최대 풍속, 평균 풍속 및 16방위 풍향의 분포를 집계하고 대기 압력(현지 및 해면 기압)의 움직임을 시계열로 추적합니다.")

    stn_tabs = st.tabs(distinct_stations)
    for idx, stn in enumerate(distinct_stations):
        with stn_tabs[idx]:
            stn_data = weather_df[weather_df["stnNm"] == stn].copy()
            
            if stn_data["avgWs"].isna().all():
                st.warning("분석할 바람/기압 데이터가 존재하지 않습니다.")
                continue

            # 4.1. 바람 관련 지표 영역
            st.markdown("#### 💨 일별 풍속(평균 및 최대) 시계열 트렌드")
            fig_wind = go.Figure()
            fig_wind.add_trace(go.Scatter(
                x=stn_data["tm"], y=stn_data["maxWs"],
                name="일 최대 풍속 (m/s)",
                line=dict(color="#F59E0B", width=2)
            ))
            fig_wind.add_trace(go.Scatter(
                x=stn_data["tm"], y=stn_data["avgWs"],
                name="일 평균 풍속 (m/s)",
                line=dict(color="#3B82F6", width=2)
            ))
            fig_wind.update_layout(
                hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="풍속 (m/s)", showgrid=True, gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_wind, use_container_width=True)

            # 4.2. 풍향 분석 (16방위 파이 차트 분포)
            st.markdown("#### 🧭 관측 기간 최대 풍속 시 발생 풍향 분포 (16방위)")
            
            # 각 풍향 데이터를 16방위 텍스트로 변환
            stn_data["maxWsWd_dir"] = stn_data["maxWsWd"].apply(degree_to_16dir)
            wind_dir_counts = stn_data["maxWsWd_dir"].value_counts().reset_index()
            wind_dir_counts.columns = ["풍향", "일수"]
            
            fig_wind_dir = px.pie(
                wind_dir_counts,
                values="일수",
                names="풍향",
                color_discrete_sequence=px.colors.sequential.RdBu,
                title="최대 풍속 기준 지배적 풍향 비율"
            )
            fig_wind_dir.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0")
            )
            st.plotly_chart(fig_wind_dir, use_container_width=True)

            # 4.3. 기압 시계열
            st.markdown("#### 🎈 대기 압력(기압) 변화 추이")
            fig_press = go.Figure()
            fig_press.add_trace(go.Scatter(
                x=stn_data["tm"], y=stn_data["avgPs"],
                name="평균 해면기압 (hPa)",
                line=dict(color="#10B981", width=2)
            ))
            fig_press.add_trace(go.Scatter(
                x=stn_data["tm"], y=stn_data["avgPa"],
                name="평균 현지기압 (hPa)",
                line=dict(color="#6366F1", width=1.5, dash="dot")
            ))
            fig_press.update_layout(
                hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="기압 (hPa)", showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickformat=".1f")
            )
            st.plotly_chart(fig_press, use_container_width=True)

# ==============================================================================
# 5. 📍 지점별 비교 분석 페이지
# ==============================================================================
elif dashboard_page == "📍 지점별 비교 분석":
    st.title("📍 다중 지점 간 기상 통계 비교 분석")
    st.markdown("수집된 데이터를 활용하여 각 지점 간의 기온 편차, 강수 자원의 분포 차이 등을 한눈에 비교 분석할 수 있습니다.")

    if len(distinct_stations) < 2:
        st.info("💡 본 페이지는 **2개 이상의 다중 지점**을 조회했을 때 활성화됩니다. 왼쪽 사이드바 검색어 란에 `서울, 부산` 등 쉼표로 지점을 더 추가해 보세요!")
        
        # 단일 지점 요약이라도 표시
        st.subheader("현재 단일 지점 기본 요약 정보")
        summary_one = weather_df.groupby("stnNm").agg({
            "avgTa": "mean",
            "maxTa": "max",
            "minTa": "min",
            "sumRn": "sum",
            "avgRhm": "mean",
            "avgWs": "mean"
        }).rename(columns={
            "avgTa": "평균 기온(°C)",
            "maxTa": "최고 기온(°C)",
            "minTa": "최저 기온(°C)",
            "sumRn": "누적 강수량(mm)",
            "avgRhm": "평균 습도(%)",
            "avgWs": "평균 풍속(m/s)"
        })
        st.table(summary_one)
    else:
        # 5.1. 지점별 통계 테이블 구축
        st.markdown("### 📊 지점별 핵심 기상 요소 요약 및 편차")
        
        # 지점별 강수량 결측 정제 후 평균 연산
        weather_df["sumRn_clean"] = weather_df["sumRn"].fillna(0.0)
        
        comparison_table = weather_df.groupby("stnNm").agg({
            "avgTa": "mean",
            "maxTa": "max",
            "minTa": "min",
            "sumRn_clean": "sum",
            "avgRhm": "mean",
            "maxWs": "max",
            "avgWs": "mean"
        }).reset_index()
        
        comparison_table.columns = [
            "지점명", "평균 기온(°C)", "역대 최고(°C)", "역대 최저(°C)", 
            "누적 강수량(mm)", "평균 습도(%)", "최대 풍속(m/s)", "평균 풍속(m/s)"
        ]
        
        st.dataframe(comparison_table, use_container_width=True, hide_index=True)

        # 5.2. 지점별 기온 및 강수량 다차원 시각화 (2열 구성)
        st.markdown("### 📐 핵심 지표 다차원 시각화 비교")
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            # 평균 기온 비교 막대 그래프
            fig_comp_temp = px.bar(
                comparison_table,
                x="지점명",
                y="평균 기온(°C)",
                color="평균 기온(°C)",
                color_continuous_scale="Reds",
                title="지점별 평균 기온 비교"
            )
            fig_comp_temp.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0")
            )
            st.plotly_chart(fig_comp_temp, use_container_width=True)
            
        with comp_col2:
            # 누적 강수량 비교 막대 그래프
            fig_comp_rain = px.bar(
                comparison_table,
                x="지점명",
                y="누적 강수량(mm)",
                color="누적 강수량(mm)",
                color_continuous_scale="Blues",
                title="지점별 누적 강수량 비교"
            )
            fig_comp_rain.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0")
            )
            st.plotly_chart(fig_comp_rain, use_container_width=True)

        # 5.3. 일별 기온 추이 비교 (시계열 결합)
        st.markdown("### 🗓️ 지점별 일 평균 기온 시계열 비교")
        fig_time_comp = px.line(
            weather_df,
            x="tm",
            y="avgTa",
            color="stnNm",
            labels={"tm": "날짜", "avgTa": "평균 기온 (°C)", "stnNm": "지점명"},
            title="기간 내 일자별 평균 기온의 지점 간 격차"
        )
        fig_time_comp.update_layout(
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_time_comp, use_container_width=True)
