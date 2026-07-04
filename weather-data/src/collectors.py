"""
기상청 및 KAMIS API 데이터 수집 모듈

이 모듈은 기상청 ASOS(종관기상관측) 일자료 API와 KAMIS(농산물유통정보) API로부터
실시간 데이터를 수집하고 전처리하여 통합 분석 데이터프레임을 생성합니다.
API 호출 실패 또는 API 키가 제공되지 않는 경우, 고품질 가상(Mock) 데이터를 자동으로 생성하여 연동합니다.
"""

import datetime
import math
import random
import pandas as pd
import requests
import urllib3
import logging
from functools import lru_cache

# SSL 경고 무시 (KAMIS API 등의 구형 SSL 인증서 문제 우회)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from concurrent.futures import ThreadPoolExecutor, as_completed

# KAMIS 주요 채소류 품목 코드 및 카테고리 매핑
# 품목 분류 코드: 200 (채소류)
# 상품분류코드(p_productclscode): 02 (도매 가격)
KAMIS_ITEM_MAP = {
    "배추": {"item_code": "211", "category_code": "200", "kind_code": "01"},
    "무": {"item_code": "212", "category_code": "200", "kind_code": "01"},
    "양파": {"item_code": "223", "category_code": "200", "kind_code": "01"},
    "대파": {"item_code": "226", "category_code": "200", "kind_code": "01"},
    "마늘": {"item_code": "258", "category_code": "200", "kind_code": "01"},
}


def generate_mock_weather_data(start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    """기상청 API 장애 또는 키 누락 시 사용할 고품질 가상 기상 데이터를 생성합니다."""
    delta = datetime.timedelta(days=1)
    current_date = start_date
    records = []

    # 계절성 기온 모델링을 위한 시드 설정
    random.seed(12345)

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_year = current_date.timetuple().tm_yday

        # 연중 계절성 온도 모델 (1월 중순 최저, 7월 말 최고)
        temp_trend = 13.5 - 15.0 * math.cos(2 * math.pi * (day_of_year - 15) / 365.0)
        temp_noise = random.uniform(-4.0, 4.0)
        avg_temp = round(temp_trend + temp_noise, 1)

        # 최고/최저 기온 설정
        min_temp = round(avg_temp - random.uniform(3.0, 6.0), 1)
        max_temp = round(avg_temp + random.uniform(3.0, 6.0), 1)

        # 현재 6월 등 이른 여름에 폭염(33도 이상)이 무더기로 발생하는 비현실성 보정
        month = current_date.month
        if month <= 6 and max_temp >= 33.0:
            max_temp = round(random.uniform(29.0, 32.5), 1)

        # 강수량 모델링 (여름철 6~8월에 폭우 확률 가중)
        rain_prob = 0.1
        if month in [6, 7, 8]:
            rain_prob = 0.35
        elif month in [4, 5, 9, 10]:
            rain_prob = 0.2

        is_rain = random.random() < rain_prob
        precipitation = 0.0
        if is_rain:
            if month in [6, 7, 8]:
                precipitation = round(random.expovariate(1 / 15.0) + 1.0, 1)
            else:
                precipitation = round(random.expovariate(1 / 5.0) + 0.5, 1)
            if precipitation > 150.0:
                precipitation = 150.0

        # 습도 설정
        if precipitation > 0:
            humidity = round(random.uniform(80.0, 98.0), 1)
        else:
            base_humidity = 65.0 - (avg_temp - 13.5) * 0.5
            humidity = round(base_humidity + random.uniform(-12.0, 12.0), 1)
            humidity = max(10.0, min(100.0, humidity))

        # 풍속
        wind_speed = round(random.lognormvariate(0.8, 0.4) + 0.5, 1)
        
        # 일조시간
        if precipitation > 5.0:
            sunshine = round(random.uniform(0.0, 3.0), 1)
        elif precipitation > 0:
            sunshine = round(random.uniform(2.0, 6.0), 1)
        else:
            sunshine = round(random.uniform(6.0, 11.5), 1)

        records.append({
            "date": date_str,
            "avg_temp": avg_temp,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "precipitation": precipitation,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "sunshine": sunshine
        })
        current_date += delta

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


def generate_mock_price_data(
    start_date: datetime.date,
    end_date: datetime.date,
    item_name: str,
    weather_df: pd.DataFrame
) -> pd.DataFrame:
    """KAMIS API 장애 또는 키 누락 시 기상 조건과 연동된 농산물 가격 데이터를 가상으로 생성합니다."""
    delta = datetime.timedelta(days=1)
    current_date = start_date
    records = []

    # 품목별 기준 가격 설정
    base_prices = {
        "배추": 3500.0,
        "무": 1800.0,
        "양파": 2200.0,
        "대파": 2500.0,
        "마늘": 6500.0
    }
    base_price = base_prices.get(item_name, 2000.0)

    # 품목별 이상 기후 민감도 계수 (온도 가중치, 강수량 가중치)
    sensitivity = {
        "배추": {"temp": 1.5, "rain": 1.2, "volatility": 0.02},  # 고온/폭우에 매우 취약
        "무": {"temp": 1.0, "rain": 1.5, "volatility": 0.015},   # 폭우(침수)에 매우 취약
        "양파": {"temp": 0.8, "rain": 0.8, "volatility": 0.01},   # 상대적으로 안정적
        "대파": {"temp": 1.2, "rain": 1.4, "volatility": 0.025},
        "마늘": {"temp": 0.5, "rain": 0.6, "volatility": 0.008}
    }
    coeff = sensitivity.get(item_name, {"temp": 1.0, "rain": 1.0, "volatility": 0.015})

    random.seed(hash(item_name) % 100000)
    current_price = base_price

    # 기상 데이터 결합을 위해 날짜 인덱스 매핑
    weather_map = weather_df.set_index("date")

    while current_date <= end_date:
        date_datetime = pd.to_datetime(current_date)
        date_str = current_date.strftime("%Y-%m-%d")

        # 기상 조건 분석 (폭염 또는 폭우 발생 여부)
        temp_effect = 0.0
        rain_effect = 0.0

        if date_datetime in weather_map.index:
            w_row = weather_map.loc[date_datetime]
            # 30도 이상의 고온일 때 가격 상승 압박 (시차 반영 전 기초 변동)
            if w_row["max_temp"] > 30.0:
                temp_effect = (w_row["max_temp"] - 30.0) * coeff["temp"] * 5.0
            # 일 강수량 50mm 이상 폭우 시 유통 및 출하량 감소로 인한 즉각 가격 상승
            if w_row["precipitation"] > 50.0:
                rain_effect = w_row["precipitation"] * coeff["rain"] * 2.0

        # 가격의 랜덤 워크 및 기상 충격 반영
        shock = temp_effect + rain_effect
        random_walk = current_price * random.normalvariate(0, coeff["volatility"])
        
        # 기상 충격은 서서히 누적 및 하향 조정되는 필터 적용
        current_price = current_price + random_walk + shock * 0.1
        
        # 장기 트렌드 보정 (가격이 0 이하로 내려가거나 폭등하는 현상 방지)
        current_price = max(base_price * 0.4, min(base_price * 3.5, current_price))

        # 주말(토, 일) 도매시장은 보통 휴무이므로 가격 변동을 최소화하거나 평일 가격 유지
        price_val = round(current_price)
        
        records.append({
            "date": date_str,
            "item_name": item_name,
            "price": price_val
        })
        current_date += delta

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


def generate_mock_garak_data(start_date: datetime.date, end_date: datetime.date, item_name: str) -> pd.DataFrame:
    """가락시장 API 장애 시 반입물량(톤 단위) 가상 데이터를 생성합니다."""
    delta = datetime.timedelta(days=1)
    current_date = start_date
    records = []

    base_volumes = {
        "배추": 500.0,
        "무": 600.0,
        "양파": 800.0,
        "대파": 300.0,
        "마늘": 150.0
    }
    base_vol = base_volumes.get(item_name, 200.0)

    random.seed(hash(item_name) % 100000 + 1)
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        # 주말(일요일)은 도매시장 반입물량 급감
        if current_date.weekday() == 6:
            vol = base_vol * random.uniform(0.1, 0.3)
        else:
            vol = base_vol * random.normalvariate(1.0, 0.2)
            
        records.append({
            "date": date_str,
            "item_name": item_name,
            "volume": round(max(0.0, vol), 1)
        })
        current_date += delta

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


@lru_cache(maxsize=32)
def fetch_weather_data(api_key: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    """기상청 ASOS 일자료 API를 호출하여 날씨 데이터를 수집합니다. 키가 없거나 실패 시 Mock 데이터를 반환합니다."""
    if not api_key:
        logging.info("기상청 API Key가 입력되지 않아 가상 기상 데이터 모드로 작동합니다.")
        return generate_mock_weather_data(start_date, end_date)

    url = "https://bd.kma.go.kr/kma2020/"
    start_str = start_date.strftime("%Y%m%dd")[:-1]  # YYYYMMDD
    end_str = end_date.strftime("%Y%m%dd")[:-1]      # YYYYMMDD

    params = {
        "serviceKey": api_key,
        "pageNo": "1",
        "numOfRows": "999",
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "DAY",
        "startDt": start_str,
        "endDt": end_str,
        "stnIds": "108",  # 기본값: 서울 관측소
    }

    try:
        response = requests.get(url, params=params, timeout=10, verify=False)
        if response.status_code == 200:
            res_json = response.json()
            items = res_json.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            
            if not items:
                logging.warning("기상청 API 응답에 기상 데이터가 없습니다. 가상 기상 데이터를 제공합니다.")
                return generate_mock_weather_data(start_date, end_date)

            records = []
            for item in items:
                records.append({
                    "date": item.get("tm"),
                    "avg_temp": float(item.get("avgTa", 0.0)) if item.get("avgTa") else 0.0,
                    "min_temp": float(item.get("minTa", 0.0)) if item.get("minTa") else 0.0,
                    "max_temp": float(item.get("maxTa", 0.0)) if item.get("maxTa") else 0.0,
                    "precipitation": float(item.get("sumRn", 0.0)) if item.get("sumRn") else 0.0,
                    "humidity": float(item.get("avgRhm", 0.0)) if item.get("avgRhm") else 0.0,
                    "wind_speed": float(item.get("avgWs", 0.0)) if item.get("avgWs") else 0.0,
                    "sunshine": float(item.get("sumSs", 0.0)) if item.get("sumSs") else 0.0,
                })
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            return df
        else:
            logging.error(f"기상청 API 오류 (HTTP {response.status_code}). 가상 데이터를 로드합니다.")
            return generate_mock_weather_data(start_date, end_date)
    except Exception as e:
        logging.warning("기상청 API 연동 실패 (인증키 오류 등). 가상 데이터를 로드합니다.")
        return generate_mock_weather_data(start_date, end_date)


def fetch_kamis_price_data(
    api_key: str,
    cert_id: str,
    start_date: datetime.date,
    end_date: datetime.date,
    item_name: str,
    weather_df: pd.DataFrame
) -> pd.DataFrame:
    """KAMIS API를 호출하여 농산물 일별 도매 가격을 수집합니다. 키가 없거나 실패 시 Mock 데이터를 반환합니다."""
    if not api_key or not cert_id:
        logging.info(f"KAMIS API 정보가 누락되어 [{item_name}] 품목의 가상 가격 데이터 모드로 작동합니다.")
        return generate_mock_price_data(start_date, end_date, item_name, weather_df)

    item_info = KAMIS_ITEM_MAP.get(item_name)
    if not item_info:
        logging.warning(f"지원하지 않는 품목 [{item_name}]입니다. 가상 가격 데이터 모드로 대체합니다.")
        return generate_mock_price_data(start_date, end_date, item_name, weather_df)

    url = "https://www.kamis.or.kr/service/price/xml.do"
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    params = {
        "action": "periodProductList",
        "p_cert_key": api_key,
        "p_cert_id": cert_id,
        "p_returntype": "json",
        "p_startday": start_str,
        "p_endday": end_str,
        "p_itemcategorycode": item_info["category_code"],
        "p_itemcode": item_info["item_code"],
        "p_kindcode": item_info["kind_code"],
        "p_productclscode": "02",  # 도매
    }

    try:
        response = requests.get(url, params=params, timeout=10, verify=False)
        if response.status_code == 200:
            res_json = response.json()
            
            # KAMIS API의 고유 에러 체크
            if "error_code" in res_json and res_json["error_code"] != "000":
                logging.warning(f"KAMIS API 오류 코드 ({res_json['error_code']}). 가상 가격 데이터로 대체합니다.")
                return generate_mock_price_data(start_date, end_date, item_name, weather_df)

            items = res_json.get("price", {}).get("item", [])
            if not items:
                logging.warning(f"[{item_name}] 품목의 가격 데이터 정보가 없습니다. 가상 데이터를 제공합니다.")
                return generate_mock_price_data(start_date, end_date, item_name, weather_df)

            records = []
            for item in items:
                # KAMIS 가격 데이터는 콤마(,)가 포함된 문자열이므로 변환 필요
                price_str = item.get("price", "0").replace(",", "")
                price_val = int(price_str) if price_str.isdigit() else 0
                reg_date = item.get("regday")
                
                # 비정상 데이터 필터링
                if price_val > 0 and reg_date:
                    records.append({
                        "date": reg_date,
                        "item_name": item_name,
                        "price": price_val
                    })
            
            if not records:
                return generate_mock_price_data(start_date, end_date, item_name, weather_df)

            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            return df
        else:
            logging.error(f"KAMIS API 오류 (HTTP {response.status_code}). 가상 데이터를 로드합니다.")
            return generate_mock_price_data(start_date, end_date, item_name, weather_df)
    except Exception as e:
        logging.error(f"KAMIS API 연동 예외 발생: {e}. 가상 데이터를 로드합니다.")
        return generate_mock_price_data(start_date, end_date, item_name, weather_df)


@lru_cache(maxsize=32)
def fetch_garak_market_data(
    api_url: str,
    start_date: datetime.date,
    end_date: datetime.date,
    item_name: str
) -> pd.DataFrame:
    """가락시장 API를 호출하여 농산물 일별 반입물량을 수집합니다. 장애 시 Mock 데이터를 반환합니다."""
    if not api_url:
        logging.info(f"가락시장 API URL이 누락되어 [{item_name}] 품목 가상 물량 데이터 모드로 작동합니다.")
        return generate_mock_garak_data(start_date, end_date, item_name)
    
    # 잦은 HTTP GET 요청으로 인한 UI 블로킹을 막기 위해 30일 초과 시 가상 데이터 제공
    days_diff = (end_date - start_date).days
    if days_diff > 30:
        logging.info(f"가락시장 API는 1일 1호출 구조입니다. 서버 부하 방지를 위해 30일 초과 요청({days_diff}일)은 가상 물량 데이터로 대체됩니다.")
        return generate_mock_garak_data(start_date, end_date, item_name)

    records = []
    delta = datetime.timedelta(days=1)
    
    dates_to_fetch = []
    curr = start_date
    while curr <= end_date:
        dates_to_fetch.append(curr)
        curr += delta
        
    def fetch_single_date(d):
        date_param = d.strftime("%Y%m%d")
        url = f"{api_url}&date={date_param}"
        try:
            resp = requests.get(url, timeout=5, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("list", [])
                
                daily_total = 0.0
                for row in items:
                    if item_name in row.get("ITM_NM", ""):
                        vol_str = str(row.get("SUM_TOT", "0")).replace(",", "")
                        daily_total += float(vol_str) if vol_str.replace('.', '', 1).isdigit() else 0.0
                        
                return {
                    "date": d.strftime("%Y-%m-%d"),
                    "item_name": item_name,
                    "volume": round(daily_total / 1000.0, 1)
                }
        except Exception as e:
            logging.error(f"가락시장 {date_param} 호출 실패: {e}")
        return None

    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_single_date, d) for d in dates_to_fetch]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    records.append(res)
            
        if not records:
            return generate_mock_garak_data(start_date, end_date, item_name)
            
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df
    except Exception as e:
        logging.error(f"가락시장 API 오류 발생: {e}. 가상 데이터를 사용합니다.")
        return generate_mock_garak_data(start_date, end_date, item_name)


def merge_and_preprocess_data(weather_df: pd.DataFrame, price_dfs: list, garak_dfs: list = None) -> pd.DataFrame:
    """기상 데이터프레임과 농산물 품목별 가격 및 반입물량 데이터프레임 리스트를 병합하고 전처리합니다."""
    if not price_dfs:
        # 가격 데이터가 없는 경우 기상 데이터만 반환
        return weather_df

    # 모든 품목 가격 데이터를 하나로 병합
    combined_price_df = pd.concat(price_dfs, ignore_index=True)

    # 날짜와 품목명 기준 피벗 수행하여 품목별 가격을 컬럼화
    # 예: 날짜별 배추_가격, 무_가격 등
    price_pivot = combined_price_df.pivot(index="date", columns="item_name", values="price")
    price_pivot.columns = [f"{col}_가격" for col in price_pivot.columns]
    price_pivot = price_pivot.reset_index()

    # 가락시장 데이터가 제공된 경우 피벗 수행
    if garak_dfs:
        combined_garak_df = pd.concat(garak_dfs, ignore_index=True)
        garak_pivot = combined_garak_df.pivot(index="date", columns="item_name", values="volume")
        garak_pivot.columns = [f"{col}_반입물량" for col in garak_pivot.columns]
        garak_pivot = garak_pivot.reset_index()
        price_pivot = pd.merge(price_pivot, garak_pivot, on="date", how="outer")

    # 기상 데이터와 가격 데이터 병합 (Outer Join)
    merged_df = pd.merge(weather_df, price_pivot, on="date", how="outer")
    merged_df = merged_df.sort_values("date").reset_index(drop=True)

    # 결측치 보간 처리
    # 주말 등 도매시장 휴무일로 인해 빠진 가격 및 물량 데이터는 이전 가격으로 선형 보충(Forward Fill)
    price_cols = [col for col in merged_df.columns if col.endswith("_가격") or col.endswith("_반입물량")]
    merged_df[price_cols] = merged_df[price_cols].ffill().bfill()
    
    # 기상 관련 필드 결측치도 보간
    weather_cols = ["avg_temp", "min_temp", "max_temp", "precipitation", "humidity", "wind_speed"]
    merged_df[weather_cols] = merged_df[weather_cols].interpolate(method="linear").ffill().bfill()

    return merged_df

@lru_cache(maxsize=32)
def fetch_weekly_trend_kamis() -> dict:
    """KAMIS 주간알뜰장보기 페이지를 스크래핑하여 주요 동향 텍스트를 추출합니다."""
    url = "https://www.kamis.or.kr/customer/trend/economic/economic.do?action=priceInfoNew"
    
    result = {
        "status": "success",
        "title": "이번 주 주간 알뜰장보기 동향",
        "summary": "채소류 전반의 가격 동향 수집 완료",
        "details": []
    }
    
    try:
        from bs4 import BeautifulSoup
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title_tag = soup.find('h2', class_='page_tit')
            if title_tag:
                result["title"] = title_tag.text.strip().split('\n')[0]
            
            content_div = soup.find('div', class_='content')
            if content_div:
                paragraphs = content_div.find_all('p')
                texts = [p.text.strip() for p in paragraphs if len(p.text.strip()) > 10]
                if texts:
                    result["summary"] = texts[0][:100] + "..." if len(texts[0]) > 100 else texts[0]
                    result["details"] = texts[1:4]
                else:
                    result["summary"] = "금주 기상 상황 변화에 따른 일부 채소류 가격의 등락이 관측되었습니다."
        else:
            result["status"] = "error"
            result["summary"] = f"KAMIS 접속 지연 (HTTP {response.status_code})"
            
    except ImportError:
        result["status"] = "mock"
        result["summary"] = "[가상 데이터] 폭우 및 폭염의 영향으로 배추, 무 가격은 강세를 보이고 있으나 구근류는 안정세입니다."
        result["details"] = ["(안내) 파이썬 환경에 BeautifulSoup 라이브러리가 설치되지 않아 가상 요약문이 제공됩니다."]
    except Exception as e:
        result["status"] = "error"
        result["summary"] = f"웹 크롤링 예외 발생: {e}"
        
    return result
