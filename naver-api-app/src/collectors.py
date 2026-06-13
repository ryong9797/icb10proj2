"""
네이버 및 다양한 플랫폼의 API 수집기 모듈

이 모듈은 다중 플랫폼(네이버, 향후 구글/유튜브 등) 데이터 수집을 위한
추상 클래스 및 구현 클래스들을 정의하며, 팩토리 패턴을 통해 동적으로
수집 객체를 생성할 수 있도록 지원합니다.

작성자: Antigravity AI
생성일: 2026-06-13
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
import requests
import json
import streamlit as st

# -----------------------------------------------------------------------------
# Streamlit 캐싱을 안전하게 처리하기 위한 독립 함수들
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _fetch_naver_datalab_trend(keywords: List[str], start_date: datetime, end_date: datetime, time_unit: str, client_id: str, client_secret: str):
    url = "https://openapi.naver.com/v1/datalab/search"
    if len(keywords) > 5:
        keywords = keywords[:5]
    keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords]
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups
    }
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }
    response = requests.post(url, data=json.dumps(body), headers=headers)
    return response.status_code, response.json()

@st.cache_data(show_spinner=False)
def _fetch_naver_datalab_shopping_trend(keywords: List[str], start_date: datetime, end_date: datetime, time_unit: str, category_code: str, client_id: str, client_secret: str):
    url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
    if len(keywords) > 5:
        keywords = keywords[:5]
    keywords_param = [{"name": kw, "param": [kw]} for kw in keywords]
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": time_unit,
        "category": category_code,
        "keyword": keywords_param
    }
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }
    response = requests.post(url, data=json.dumps(body), headers=headers)
    return response.status_code, response.json()

@st.cache_data(show_spinner=False)
def _fetch_naver_search_api(api_type: str, query: str, display: int, start: int, client_id: str, client_secret: str):
    url = f"https://openapi.naver.com/v1/search/{api_type}.json"
    params = {"query": query, "display": display, "start": start}
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    response = requests.get(url, headers=headers, params=params)
    return response.status_code, response.json()


# -----------------------------------------------------------------------------
# 추상 Base 수집기 클래스
# -----------------------------------------------------------------------------
class BaseCollector(ABC):
    def __init__(self, config: Dict[str, Any]):
        """
        수집기 초기화 설정
        config 딕셔너리를 유연하게 주입받아 처리합니다.
        """
        self.config = config

    @abstractmethod
    def fetch_trend(self, keywords: List[str], start_date: datetime, end_date: datetime, **kwargs) -> Any:
        """
        플랫폼별 검색어 트렌드 분석 데이터를 호출합니다.
        """
        pass

    @abstractmethod
    def fetch_search_data(self, api_type: str, query: str, display: int = 100, start: int = 1) -> Any:
        """
        플랫폼별 검색 결과(블로그, 뉴스 등) 데이터를 수집합니다.
        """
        pass


# -----------------------------------------------------------------------------
# 네이버 수집기 구현체
# -----------------------------------------------------------------------------
class NaverCollector(BaseCollector):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")

    def fetch_trend(self, keywords: List[str], start_date: datetime, end_date: datetime, **kwargs) -> Any:
        """
        네이버 데이터랩 통합 검색어 트렌드 또는 쇼핑 검색어 트렌드를 호출합니다.
        """
        trend_type = kwargs.get("trend_type", "search")  # 'search' 또는 'shopping'
        time_unit = kwargs.get("time_unit", "date")
        
        if trend_type == "shopping":
            category_code = kwargs.get("category_code", "50000003")
            return _fetch_naver_datalab_shopping_trend(
                keywords, start_date, end_date, time_unit, category_code, self.client_id, self.client_secret
            )
        else:
            return _fetch_naver_datalab_trend(
                keywords, start_date, end_date, time_unit, self.client_id, self.client_secret
            )

    def fetch_search_data(self, api_type: str, query: str, display: int = 100, start: int = 1) -> Any:
        """
        네이버 검색 API(blog, news, cafearticle, shopping 등)를 호출합니다.
        """
        return _fetch_naver_search_api(
            api_type, query, display, start, self.client_id, self.client_secret
        )


# -----------------------------------------------------------------------------
# 수집기 팩토리 클래스
# -----------------------------------------------------------------------------
class CollectorFactory:
    _collectors = {
        "naver": NaverCollector
    }

    @classmethod
    def register_collector(cls, platform: str, collector_class):
        cls._collectors[platform.lower()] = collector_class

    @classmethod
    def get_collector(cls, platform: str, config: Dict[str, Any]) -> BaseCollector:
        collector_class = cls._collectors.get(platform.lower())
        if not collector_class:
            raise ValueError(f"지원하지 않는 수집 플랫폼입니다: {platform}")
        return collector_class(config)
