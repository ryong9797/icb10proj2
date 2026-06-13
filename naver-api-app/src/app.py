"""
네이버 오픈 API 종합 분석 대시보드

이 애플리케이션은 네이버 개발자 API를 활용하여 통합 검색어 트렌드, 쇼핑 검색어 트렌드, 
블로그, 뉴스, 카페글, 쇼핑 검색 데이터를 실시간으로 수집하고 분석하는 Streamlit 대시보드입니다.

주요 기능:
- 네이버 API Client ID/Secret을 이용한 사용자 인증 (사이드바 입력)
- 쉼표로 구분된 다중 검색어 및 날짜 기간 필터링 기능
- 통합 검색어 트렌드 및 쇼핑 검색어 트렌드 분석 (데이터랩 API)
- 블로그, 뉴스, 카페글, 쇼핑 검색 데이터 수집 및 텍스트/시계열/통계 분석
- Plotly를 활용한 고품질 인터랙티브 시각화

작성자: Antigravity AI
생성일: 2026-06-08
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timedelta
import re
from email.utils import parsedate_to_datetime

# -----------------------------------------------------------------------------
# 1. UI 설정 및 테마
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="네이버 API 종합 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 스타일 적용 (CSS)
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1EC800;
        font-family: 'Outfit', sans-serif;
    }
    h2, h3 {
        color: #2F3E46;
    }
    div.stButton > button:first-child {
        background-color: #1EC800;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #179b00;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #1EC800;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 (API 인증 및 조건 설정)
# -----------------------------------------------------------------------------
import os
from dotenv import load_dotenv

# 1. Streamlit Secrets에서 API 키 로드 시도 (배포 환경)
client_id = None
client_secret = None
loaded_from_secrets = False

try:
    client_id = st.secrets.get("NAVER_CLIENT_ID", None)
    client_secret = st.secrets.get("NAVER_CLIENT_SECRET", None)
    loaded_from_secrets = True if client_id and client_secret else False
except Exception:
    pass

# 2. st.secrets에 없으면 로컬 .env 파일 로드 시도
if not loaded_from_secrets:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(current_dir, "..", ".env")
    load_dotenv(dotenv_path)
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

st.sidebar.title("🔑 네이버 API 설정")
if client_id and client_secret:
    source = "Streamlit 설정(Secrets)" if loaded_from_secrets else ".env 파일"
    st.sidebar.success(f"✅ {source}에서 API 인증 키가 로드되었습니다.")
    # 보안을 위해 마스킹하여 표시
    st.sidebar.text(f"ID: {client_id[:4]}***")
else:
    st.sidebar.error("❌ API 인증 키를 찾을 수 없습니다. (.env 혹은 Streamlit Secrets)")
    client_id = st.sidebar.text_input("Naver Client ID", placeholder="Client ID를 입력하세요")
    client_secret = st.sidebar.text_input("Naver Client Secret", placeholder="Client Secret을 입력하세요", type="password")

# 수집기 인스턴스 초기화
from collectors import CollectorFactory
collector = None
if client_id and client_secret:
    collector = CollectorFactory.get_collector("naver", {"client_id": client_id, "client_secret": client_secret})

st.sidebar.markdown("---")
st.sidebar.title("🔍 검색 조건")

# 검색어 입력
keywords_input = st.sidebar.text_input("검색어 (쉼표 ','로 구분)", "아이폰, 갤럭시")
keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

# 상세 분석 키워드 선택 (단일 검색어 종합 분석용)
selected_keyword = None
if keywords:
    selected_keyword = st.sidebar.selectbox("🎯 상세 분석 키워드 선택", keywords, index=0)

# 검색 기간 설정
today = datetime.today()
default_start_date = today - timedelta(days=90)
start_date = st.sidebar.date_input("시작일", default_start_date)
end_date = st.sidebar.date_input("종료일", today)

# 데이터랩용 주기 설정
time_unit = st.sidebar.selectbox("데이터랩 분석 주기", ["date", "week", "month"], index=0)

# 페이지 분기
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "📊 대시보드 페이지",
    [
        "1. 통합 검색어 트렌드 (데이터랩)",
        "2. 쇼핑 검색어 트렌드 (데이터랩)",
        "3. 블로그 검색 분석",
        "4. 뉴스 검색 분석",
        "5. 카페글 검색 분석",
        "6. 쇼핑 상품 및 가격 분석",
        "7. 검색어 원스톱 종합 분석 (Unified View)"
    ]
)

# -----------------------------------------------------------------------------
# 3. 유틸리티 함수 (API 호출 및 데이터 처리)
# -----------------------------------------------------------------------------
def check_api_keys():
    if not client_id or not client_secret:
        st.warning("👈 왼쪽 사이드바에서 Naver Client ID와 Client Secret을 입력해 주세요.")
        return False
    return True

# 텍스트 형태소 및 단어 빈도 분석
def get_word_frequencies(texts):
    stop_words = {"및", "그", "이", "그것", "저", "또는", "의", "를", "을", "은", "는", "가", "이", "에", "로", "으로", "과", "와", "에서", "합니다", "있습니다", "하는", "할", "한", "등"}
    words = []
    for text in texts:
        clean_text = re.sub(r'<[^>]+>', '', text)  # HTML 태그 제거
        clean_text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', clean_text)  # 특수문자 제거
        tokens = clean_text.split()
        for token in tokens:
            if len(token) >= 2 and token not in stop_words:
                words.append(token)
    return pd.Series(words).value_counts().head(15)

# 날짜 파싱 유틸리티
def parse_pubdate(date_str):
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        try:
            return pd.to_datetime(date_str)
        except Exception:
            return None

def parse_postdate(date_str):
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except Exception:
        return None

# -----------------------------------------------------------------------------
# 4. 페이지별 렌더링
# -----------------------------------------------------------------------------
st.title("💚 네이버 API 종합 분석 대시보드")
st.markdown("네이버 개발자 API를 통해 수집된 실시간 데이터를 심층 분석하고 시각화합니다.")

if check_api_keys():
    if not keywords:
        st.info("💡 사이드바에 분석할 검색어를 입력해 주세요.")
    else:
        # --- 1페이지: 통합 검색어 트렌드 ---
        if page == "1. 통합 검색어 트렌드 (데이터랩)":
            st.header("📈 네이버 통합 검색어 트렌드 분석")
            st.markdown("주제어별 네이버 검색 추이의 상대적 비율을 시각화합니다. (가장 검색량이 많았던 시점 = 100)")
            
            if len(keywords) > 5:
                st.warning("⚠️ 데이터랩 API는 한 번에 최대 5개의 검색어만 비교 가능합니다. 앞의 5개 검색어로 분석을 시작합니다.")
            
            with st.spinner("네이버 데이터랩 API 호출 중..."):
                status, data = collector.fetch_trend(keywords, start_date, end_date, time_unit=time_unit, trend_type="search")
                
            if status == 200:
                results = data.get('results', [])
                if results:
                    # 데이터프레임 빌드
                    all_df_list = []
                    for group in results:
                        title = group['title']
                        df_group = pd.DataFrame(group['data'])
                        if not df_group.empty:
                            df_group['period'] = pd.to_datetime(df_group['period'])
                            df_group['ratio'] = df_group['ratio'].astype(float)
                            df_group['keyword'] = title
                            all_df_list.append(df_group)
                            
                    if all_df_list:
                        df_all = pd.concat(all_df_list, ignore_index=True)
                        
                        # Plotly 라인 차트 시각화
                        fig = px.line(
                            df_all, 
                            x="period", 
                            y="ratio", 
                            color="keyword", 
                            title="검색어 트렌드 변화 추이 (상대 비율)",
                            labels={"period": "기간", "ratio": "검색량 비율 (%)", "keyword": "검색어"},
                            template="plotly_white"
                        )
                        fig.update_layout(hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 기술통계 검증 및 요약
                        st.subheader("📊 검색어별 기술통계 요약")
                        stats_list = []
                        for kw in keywords[:5]:
                            df_kw = df_all[df_all['keyword'] == kw]
                            if not df_kw.empty:
                                stats_list.append({
                                    "검색어": kw,
                                    "평균 비율": round(df_kw['ratio'].mean(), 2),
                                    "중앙값": round(df_kw['ratio'].median(), 2),
                                    "최대값": df_kw['ratio'].max(),
                                    "최소값": df_kw['ratio'].min(),
                                    "왜도(Skewness)": round(df_kw['ratio'].skew(), 2),
                                    "표준편차": round(df_kw['ratio'].std(), 2)
                                })
                        
                        st.dataframe(pd.DataFrame(stats_list), use_container_width=True)
                    else:
                        st.info("조회된 트렌드 데이터가 없습니다. 기간을 변경해 보세요.")
                else:
                    st.info("결과 데이터가 존재하지 않습니다.")
            else:
                st.error(f"오류가 발생했습니다. (HTTP {status})\n메시지: {data.get('message', '알 수 없는 에러')}")

        # --- 2페이지: 쇼핑 검색어 트렌드 ---
        elif page == "2. 쇼핑 검색어 트렌드 (데이터랩)":
            st.header("🛍️ 쇼핑 검색어 트렌드 분석")
            st.markdown("네이버 쇼핑 서비스 내에서의 카테고리별 검색어 트렌드를 비교합니다.")
            
            # 카테고리 설정
            categories = {
                "패션의류": "50000000",
                "패션잡화": "50000001",
                "화장품/미용": "50000002",
                "디지털/가전": "50000003",
                "가구/인테리어": "50000004",
                "출산/육아": "50000005",
                "식품": "50000006",
                "스포츠/레저": "50000007",
                "생활/건강": "50000008",
                "여가/생활편의": "50000009",
                "면세점": "50000010",
                "도서": "50005542"
            }
            selected_cat = st.selectbox("쇼핑 대분류 카테고리 선택", list(categories.keys()), index=3) # 기본 디지털/가전
            cat_code = categories[selected_cat]
            
            if len(keywords) > 5:
                st.warning("⚠️ 데이터랩 API는 한 번에 최대 5개의 검색어만 비교 가능합니다. 앞의 5개 검색어로 분석을 시작합니다.")
                
            with st.spinner("네이버 쇼핑트렌드 API 호출 중..."):
                status, data = collector.fetch_trend(keywords, start_date, end_date, time_unit=time_unit, trend_type="shopping", category_code=cat_code)
                
            if status == 200:
                results = data.get('results', [])
                if results:
                    all_df_list = []
                    for group in results:
                        title = group['title']
                        df_group = pd.DataFrame(group['data'])
                        if not df_group.empty:
                            df_group['period'] = pd.to_datetime(df_group['period'])
                            df_group['ratio'] = df_group['ratio'].astype(float)
                            df_group['keyword'] = title
                            all_df_list.append(df_group)
                            
                    if all_df_list:
                        df_all = pd.concat(all_df_list, ignore_index=True)
                        
                        fig = px.line(
                            df_all, 
                            x="period", 
                            y="ratio", 
                            color="keyword", 
                            title=f"쇼핑 내 [{selected_cat}] 분야 검색 트렌드 추이",
                            labels={"period": "기간", "ratio": "쇼핑 검색 비율 (%)", "keyword": "검색어"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 데이터 요약
                        st.subheader("📊 쇼핑 통계 요약")
                        stats_list = []
                        for kw in keywords[:5]:
                            df_kw = df_all[df_all['keyword'] == kw]
                            if not df_kw.empty:
                                stats_list.append({
                                    "검색어": kw,
                                    "평균 쇼핑 지수": round(df_kw['ratio'].mean(), 2),
                                    "중앙값": round(df_kw['ratio'].median(), 2),
                                    "최대값": df_kw['ratio'].max(),
                                    "왜도": round(df_kw['ratio'].skew(), 2),
                                    "표준편차": round(df_kw['ratio'].std(), 2)
                                })
                        st.dataframe(pd.DataFrame(stats_list), use_container_width=True)
                    else:
                        st.info("조회된 쇼핑 트렌드 데이터가 없습니다.")
                else:
                    st.info("결과 데이터가 존재하지 않습니다.")
            else:
                st.error(f"오류가 발생했습니다. (HTTP {status})\n메시지: {data.get('message', '알 수 없는 에러')}")

        # --- 3페이지: 블로그 검색 분석 ---
        elif page == "3. 블로그 검색 분석":
            st.header("📝 블로그 검색 데이터 입체 분석")
            st.markdown("네이버 블로그에서 최근 작성된 포스트 데이터를 수집하여 등록 흐름 및 키워드를 비교 분석합니다.")
            
            all_blogs = []
            with st.spinner("블로그 검색 데이터 수집 중..."):
                for kw in keywords:
                    status, data = collector.fetch_search_data("blog", kw, display=100)
                    if status == 200:
                        items = data.get('items', [])
                        for item in items:
                            item['search_keyword'] = kw
                            all_blogs.append(item)
                            
            if all_blogs:
                df = pd.DataFrame(all_blogs)
                df['parsed_date'] = df['postdate'].apply(parse_postdate)
                
                # 날짜 유효 기간 필터링
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['parsed_date'] >= start_dt) & (df['parsed_date'] <= end_dt)]
                
                if df.empty:
                    st.warning("⚠️ 선택하신 검색 기간 내에 작성된 블로그 데이터가 없습니다.")
                else:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 1. 시계열 등록 추이
                        df_trend = df.groupby(['parsed_date', 'search_keyword']).size().reset_index(name='count')
                        fig_trend = px.line(
                            df_trend, 
                            x="parsed_date", 
                            y="count", 
                            color="search_keyword",
                            title="일자별 블로그 작성 추이",
                            labels={"parsed_date": "작성일", "count": "작성 건수", "search_keyword": "검색어"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                        
                    with col2:
                        # 2. 블로그 채널 점유율 (상위 블로그명 분포)
                        df_blogger = df.groupby(['bloggername', 'search_keyword']).size().reset_index(name='count')
                        df_blogger = df_blogger.sort_values(by="count", ascending=False).head(15)
                        fig_blogger = px.bar(
                            df_blogger,
                            x="count",
                            y="bloggername",
                            color="search_keyword",
                            orientation="h",
                            title="상위 활동 블로그 채널 분포",
                            labels={"count": "글 수", "bloggername": "블로그명", "search_keyword": "검색어"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_blogger, use_container_width=True)
                        
                    # 3. 텍스트 분석 (주요 출현 키워드 빈도)
                    st.subheader("🔤 주요 매칭 키워드 빈도 분석")
                    word_cols = st.columns(len(keywords))
                    for idx, kw in enumerate(keywords):
                        with word_cols[idx]:
                            st.write(f"**[{kw}] 관련 주요 단어**")
                            df_sub = df[df['search_keyword'] == kw]
                            if not df_sub.empty:
                                titles_desc = df_sub['title'] + " " + df_sub['description']
                                freqs = get_word_frequencies(titles_desc.tolist())
                                if not freqs.empty:
                                    fig_word = px.bar(
                                        x=freqs.values,
                                        y=freqs.index,
                                        orientation="h",
                                        labels={"x": "빈도수", "y": "단어"},
                                        template="plotly_white",
                                        color_discrete_sequence=["#1EC800"]
                                    )
                                    fig_word.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
                                    st.plotly_chart(fig_word, use_container_width=True)
                                else:
                                    st.write("분석할 단어가 없습니다.")
                                    
                    # 데이터 테이블 표기
                    st.subheader("📋 수집 데이터 상세보기")
                    st.dataframe(
                        df[['search_keyword', 'title', 'bloggername', 'postdate', 'link']].rename(
                            columns={"search_keyword": "검색어", "title": "제목", "bloggername": "블로그명", "postdate": "작성일"}
                        ),
                        use_container_width=True
                    )
            else:
                st.info("수집된 블로그 데이터가 없습니다.")

        # --- 4페이지: 뉴스 검색 분석 ---
        elif page == "4. 뉴스 검색 분석":
            st.header("📰 실시간 뉴스 및 미디어 분석")
            st.markdown("네이버 뉴스 검색결과를 바탕으로 주요 언론 동향 및 키워드 빈도를 비교 분석합니다.")
            
            all_news = []
            with st.spinner("뉴스 데이터 수집 중..."):
                for kw in keywords:
                    status, data = collector.fetch_search_data("news", kw, display=100)
                    if status == 200:
                        items = data.get('items', [])
                        for item in items:
                            item['search_keyword'] = kw
                            all_news.append(item)
                            
            if all_news:
                df = pd.DataFrame(all_news)
                df['parsed_date'] = df['pubDate'].apply(parse_pubdate)
                
                # 날짜 유효 기간 필터링
                start_dt = pd.to_datetime(start_date).tz_localize('Asia/Seoul')
                end_dt = pd.to_datetime(end_date).tz_localize('Asia/Seoul')
                df['parsed_date'] = df['parsed_date'].dt.tz_convert('Asia/Seoul')
                df = df[(df['parsed_date'] >= start_dt) & (df['parsed_date'] <= end_dt)]
                
                if df.empty:
                    st.warning("⚠️ 선택하신 검색 기간 내에 보도된 뉴스 데이터가 없습니다.")
                else:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 1. 일자별 뉴스 보도량 추이
                        df['date_only'] = df['parsed_date'].dt.date
                        df_trend = df.groupby(['date_only', 'search_keyword']).size().reset_index(name='count')
                        fig_trend = px.line(
                            df_trend, 
                            x="date_only", 
                            y="count", 
                            color="search_keyword",
                            title="일자별 뉴스 보도 추이",
                            labels={"date_only": "보도일", "count": "기사 수", "search_keyword": "검색어"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                        
                    with col2:
                        # 2. 뉴스 핵심 키워드 빈도 비교
                        st.write("**뉴스 헤드라인 키워드 분포**")
                        # 전체 검색어에 대해 병합하여 분석
                        freqs = get_word_frequencies((df['title'] + " " + df['description']).tolist())
                        if not freqs.empty:
                            fig_word = px.bar(
                                x=freqs.values,
                                y=freqs.index,
                                orientation="h",
                                labels={"x": "빈도수", "y": "단어"},
                                title="전체 뉴스 주요 키워드 상위 15",
                                template="plotly_white",
                                color_discrete_sequence=["#007A87"]
                            )
                            st.plotly_chart(fig_word, use_container_width=True)
                            
                    # 데이터 테이블 제공
                    st.subheader("📋 뉴스 기사 목록")
                    st.dataframe(
                        df[['search_keyword', 'title', 'pubDate', 'originallink']].rename(
                            columns={"search_keyword": "검색어", "title": "기사 제목", "pubDate": "보도시간", "originallink": "원문 링크"}
                        ),
                        use_container_width=True
                    )
            else:
                st.info("수집된 뉴스 데이터가 없습니다.")

        # --- 5페이지: 카페글 검색 분석 ---
        elif page == "5. 카페글 검색 분석":
            st.header("💬 카페 커뮤니티 여론 분석")
            st.markdown("네이버 카페에 등록된 공개 게시글 데이터를 수집하고, 주요 활성화 커뮤니티와 키워드를 분석합니다.")
            st.info("ℹ️ 카페글 검색 API는 날짜 정보(작성일)를 제공하지 않으므로, 기간 필터링이 적용되지 않으며 최근 작성된 데이터 기준으로 분석됩니다.")
            
            all_cafes = []
            with st.spinner("카페글 데이터 수집 중..."):
                for kw in keywords:
                    status, data = collector.fetch_search_data("cafearticle", kw, display=100)
                    if status == 200:
                        items = data.get('items', [])
                        for item in items:
                            item['search_keyword'] = kw
                            all_cafes.append(item)
                            
            if all_cafes:
                df = pd.DataFrame(all_cafes)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 1. 카페 브랜드 점유율 (상위 카페명 분포)
                    df_name = df.groupby(['cafename', 'search_keyword']).size().reset_index(name='count')
                    df_name = df_name.sort_values(by="count", ascending=False).head(15)
                    fig_name = px.bar(
                        df_name,
                        x="count",
                        y="cafename",
                        color="search_keyword",
                        orientation="h",
                        title="글이 많이 올라온 카페 순위",
                        labels={"count": "글 수", "cafename": "카페명", "search_keyword": "검색어"},
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_name, use_container_width=True)
                    
                with col2:
                    # 2. 카페글 핵심 키워드
                    st.write("**카페 커뮤니티 주요 키워드**")
                    freqs = get_word_frequencies((df['title'] + " " + df['description']).tolist())
                    if not freqs.empty:
                        fig_word = px.bar(
                            x=freqs.values,
                            y=freqs.index,
                            orientation="h",
                            labels={"x": "빈도수", "y": "단어"},
                            title="전체 카페글 주요 키워드 상위 15",
                            template="plotly_white",
                            color_discrete_sequence=["#FF5A5F"]
                        )
                        st.plotly_chart(fig_word, use_container_width=True)
                        
                # 데이터 테이블 제공
                st.subheader("📋 카페글 목록")
                st.dataframe(
                    df[['search_keyword', 'title', 'cafename', 'link']].rename(
                        columns={"search_keyword": "검색어", "title": "글 제목", "cafename": "카페명"}
                    ),
                    use_container_width=True
                )
            else:
                st.info("수집된 카페글 데이터가 없습니다.")

        # --- 6페이지: 쇼핑 상품 및 가격 분석 ---
        elif page == "6. 쇼핑 상품 및 가격 분석":
            st.header("🛒 쇼핑 상품 가격 및 시장 비교 분석")
            st.markdown("네이버 쇼핑 등록 상품의 가격 분포, 제조사 점유율, 최저가/최고가 통계를 시각적으로 분석합니다.")
            
            all_products = []
            with st.spinner("쇼핑 데이터 수집 중..."):
                for kw in keywords:
                    status, data = collector.fetch_search_data("shopping", kw, display=100)
                    if status == 200:
                        items = data.get('items', [])
                        for item in items:
                            item['search_keyword'] = kw
                            all_products.append(item)
                            
            if all_products:
                df = pd.DataFrame(all_products)
                df['lprice'] = pd.to_numeric(df['lprice'], errors='coerce').fillna(0).astype(int)
                df['hprice'] = pd.to_numeric(df['hprice'], errors='coerce').fillna(0).astype(int)
                
                # 0원 가격 데이터 제외
                df = df[df['lprice'] > 0]
                
                if df.empty:
                    st.warning("⚠️ 분석 가능한 가격 정보가 포함된 상품 데이터가 없습니다.")
                else:
                    # 1. 가격 분포 분석 (상자 그림 Box Plot)
                    st.subheader("💵 검색어별 상품 가격 분포 (통계 이상치 확인)")
                    fig_box = px.box(
                        df, 
                        x="search_keyword", 
                        y="lprice", 
                        color="search_keyword",
                        points="outliers",
                        title="최저가 분포 및 통계 이상값 비교",
                        labels={"search_keyword": "검색어", "lprice": "최저 가격(원)"},
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_box, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 2. 평균 가격 비교
                        df_price_mean = df.groupby('search_keyword')['lprice'].mean().reset_index(name='mean_price')
                        fig_mean = px.bar(
                            df_price_mean,
                            x="search_keyword",
                            y="mean_price",
                            color="search_keyword",
                            title="검색어별 평균 최저가 비교",
                            labels={"search_keyword": "검색어", "mean_price": "평균 가격(원)"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_mean, use_container_width=True)
                        
                    with col2:
                        # 3. 쇼핑 카테고리 분포
                        df_cat = df.groupby(['category1', 'search_keyword']).size().reset_index(name='count')
                        fig_cat = px.sunburst(
                            df_cat, 
                            path=['search_keyword', 'category1'], 
                            values='count',
                            title="대분류 카테고리 구성 비율",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_cat, use_container_width=True)
                        
                    # 4. 제조사/브랜드 점유율
                    st.subheader("🏭 주요 브랜드/제조사 점유율")
                    df_brand = df[df['brand'] != ''].groupby(['brand', 'search_keyword']).size().reset_index(name='count')
                    df_brand = df_brand.sort_values(by="count", ascending=False).head(15)
                    
                    if not df_brand.empty:
                        fig_brand = px.bar(
                            df_brand,
                            x="count",
                            y="brand",
                            color="search_keyword",
                            orientation="h",
                            title="상위 브랜드 점유 분포",
                            labels={"count": "상품 수", "brand": "브랜드명", "search_keyword": "검색어"},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_brand, use_container_width=True)
                    else:
                        st.write("브랜드 정보가 풍부하지 않아 점유율을 시각화할 수 없습니다.")
                        
                    # 데이터 요약
                    st.subheader("📊 가격 통계 수치 요약")
                    price_summary = []
                    for kw in keywords:
                        df_kw = df[df['search_keyword'] == kw]
                        if not df_kw.empty:
                            price_summary.append({
                                "검색어": kw,
                                "상품 건수": len(df_kw),
                                "평균 가격": f"{int(df_kw['lprice'].mean()):,}원",
                                "중앙 가격": f"{int(df_kw['lprice'].median()):,}원",
                                "최고 가격": f"{df_kw['lprice'].max():,}원",
                                "최저 가격": f"{df_kw['lprice'].min():,}원",
                                "표준편차(가격)": f"{int(df_kw['lprice'].std()):,}원"
                            })
                    st.dataframe(pd.DataFrame(price_summary), use_container_width=True)
                    
                    # 데이터 테이블 제공
                    st.subheader("📋 쇼핑 상품 목록")
                    st.dataframe(
                        df[['search_keyword', 'title', 'lprice', 'mallName', 'brand', 'link']].rename(
                            columns={"search_keyword": "검색어", "title": "상품명", "lprice": "최저가", "mallName": "판매처", "brand": "브랜드"}
                        ),
                        use_container_width=True
                    )
            else:
                st.info("수집된 쇼핑 상품 데이터가 없습니다.")

        # --- 7페이지: 검색어 원스톱 종합 분석 (Unified View) ---
        elif page == "7. 검색어 원스톱 종합 분석 (Unified View)":
            st.header(f"🎯 [{selected_keyword}] 원스톱 종합 분석 대시보드")
            st.markdown(f"선택하신 단일 검색어 **'{selected_keyword}'**에 대한 블로그, 카페, 뉴스, 쇼핑 데이터를 다각도로 실시간 수집하여 종합 분석합니다.")
            
            if not selected_keyword:
                st.warning("분석할 키워드를 선택해 주세요.")
            else:
                # 데이터 수집 (네이버 검색 API 호출)
                with st.spinner(f"[{selected_keyword}] 관련 데이터 수집 중 (블로그, 뉴스, 카페, 쇼핑)..."):
                    b_status, b_data = collector.fetch_search_data("blog", selected_keyword, display=100)
                    n_status, n_data = collector.fetch_search_data("news", selected_keyword, display=100)
                    c_status, c_data = collector.fetch_search_data("cafearticle", selected_keyword, display=100)
                    s_status, s_data = collector.fetch_search_data("shopping", selected_keyword, display=100)
                
                # 데이터프레임 변환
                df_blog = pd.DataFrame(b_data.get('items', [])) if b_status == 200 else pd.DataFrame()
                df_news = pd.DataFrame(n_data.get('items', [])) if n_status == 200 else pd.DataFrame()
                df_cafe = pd.DataFrame(c_data.get('items', [])) if c_status == 200 else pd.DataFrame()
                df_shop = pd.DataFrame(s_data.get('items', [])) if s_status == 200 else pd.DataFrame()
                
                # 1. 상단 핵심 요약 지표 (Metrics)
                st.subheader("📊 데이터 수집 현황 요약")
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                
                with m_col1:
                    st.metric("수집된 블로그 수", len(df_blog))
                with m_col2:
                    st.metric("수집된 뉴스 기사 수", len(df_news))
                with m_col3:
                    st.metric("수집된 카페 게시글 수", len(df_cafe))
                with m_col4:
                    if not df_shop.empty and 'lprice' in df_shop.columns:
                        df_shop['lprice'] = pd.to_numeric(df_shop['lprice'], errors='coerce').fillna(0).astype(int)
                        # 0원 가격 제외
                        df_shop_filtered = df_shop[df_shop['lprice'] > 0]
                        if not df_shop_filtered.empty:
                            mean_price = int(df_shop_filtered['lprice'].mean())
                            st.metric("쇼핑 상품 평균가", f"{mean_price:,}원")
                        else:
                            st.metric("쇼핑 상품 평균가", "N/A")
                    else:
                        st.metric("쇼핑 상품 평균가", "N/A")
                
                st.markdown("---")
                
                # 2. 미디어 및 소셜 여론 트렌드 비교 (뉴스 vs 블로그 시계열)
                st.subheader("📈 미디어(뉴스) 및 여론(블로그) 트렌드 비교")
                
                # 날짜 처리
                df_blog_trend = pd.DataFrame()
                if not df_blog.empty and 'postdate' in df_blog.columns:
                    df_blog['parsed_date'] = df_blog['postdate'].apply(parse_postdate)
                    df_blog_trend = df_blog.groupby('parsed_date').size().reset_index(name='블로그 글 수')
                    df_blog_trend.rename(columns={'parsed_date': 'date'}, inplace=True)
                
                df_news_trend = pd.DataFrame()
                if not df_news.empty and 'pubDate' in df_news.columns:
                    df_news['parsed_date'] = df_news['pubDate'].apply(parse_pubdate)
                    if not df_news['parsed_date'].empty:
                        df_news['date_only'] = pd.to_datetime(df_news['parsed_date']).dt.date
                        df_news_trend = df_news.groupby('date_only').size().reset_index(name='뉴스 기사 수')
                        df_news_trend.rename(columns={'date_only': 'date'}, inplace=True)
                        df_news_trend['date'] = pd.to_datetime(df_news_trend['date'])
                
                # 데이터 병합하여 하나의 차트에 렌더링
                if not df_blog_trend.empty or not df_news_trend.empty:
                    if df_blog_trend.empty:
                        df_merged = df_news_trend
                    elif df_news_trend.empty:
                        df_merged = df_blog_trend
                    else:
                        df_merged = pd.merge(df_blog_trend, df_news_trend, on='date', how='outer').fillna(0)
                    
                    df_merged = df_merged.sort_values(by='date')
                    
                    # 날짜 기간 필터 적용
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    df_merged = df_merged[(df_merged['date'] >= start_dt) & (df_merged['date'] <= end_dt)]
                    
                    if df_merged.empty:
                        st.info("선택한 분석 기간 내에 수집된 블로그/뉴스 트렌드 데이터가 없습니다.")
                    else:
                        fig_combined = go.Figure()
                        if '뉴스 기사 수' in df_merged.columns:
                            fig_combined.add_trace(go.Scatter(x=df_merged['date'], y=df_merged['뉴스 기사 수'], mode='lines+markers', name='뉴스 기사 수', line=dict(color='#007A87', width=2)))
                        if '블로그 글 수' in df_merged.columns:
                            fig_combined.add_trace(go.Scatter(x=df_merged['date'], y=df_merged['블로그 글 수'], mode='lines+markers', name='블로그 글 수', line=dict(color='#1EC800', width=2)))
                        
                        fig_combined.update_layout(
                            title="일자별 뉴스 보도량 vs 블로그 작성량 추이 비교",
                            xaxis_title="날짜",
                            yaxis_title="수집 건수",
                            template="plotly_white",
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig_combined, use_container_width=True)
                else:
                    st.info("시계열 트렌드 데이터를 시각화할 수 없습니다.")
                
                # 3. 주요 키워드 분석 및 쇼핑 분포 (2열 구성)
                st.subheader("🗣️ 여론 키워드 및 시장 분석")
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("**통합 여론 키워드 빈도 (블로그 + 뉴스 + 카페)**")
                    combined_texts = []
                    if not df_blog.empty:
                        combined_texts.extend((df_blog['title'] + " " + df_blog['description']).tolist())
                    if not df_news.empty:
                        combined_texts.extend((df_news['title'] + " " + df_news['description']).tolist())
                    if not df_cafe.empty:
                        combined_texts.extend((df_cafe['title'] + " " + df_cafe['description']).tolist())
                    
                    if combined_texts:
                        freqs = get_word_frequencies(combined_texts)
                        if not freqs.empty:
                            fig_word = px.bar(
                                x=freqs.values,
                                y=freqs.index,
                                orientation="h",
                                labels={"x": "빈도수", "y": "단어"},
                                template="plotly_white",
                                color_discrete_sequence=["#FF5A5F"]
                            )
                            fig_word.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig_word, use_container_width=True)
                        else:
                            st.write("분석할 텍스트 키워드가 부족합니다.")
                    else:
                        st.write("수집된 텍스트 데이터가 없습니다.")
                
                with col_right:
                    st.markdown("**쇼핑 상품 최저가 가격 분포**")
                    if not df_shop.empty and 'lprice' in df_shop.columns:
                        df_shop['lprice'] = pd.to_numeric(df_shop['lprice'], errors='coerce').fillna(0).astype(int)
                        df_shop_filtered = df_shop[df_shop['lprice'] > 0]
                        if not df_shop_filtered.empty:
                            fig_box = px.box(
                                df_shop_filtered,
                                y="lprice",
                                points="outliers",
                                labels={"lprice": "최저가 (원)"},
                                template="plotly_white",
                                color_discrete_sequence=["#1EC800"]
                            )
                            fig_box.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig_box, use_container_width=True)
                        else:
                            st.write("유효한 가격 정보를 가진 상품이 없습니다.")
                    else:
                        st.write("수집된 쇼핑 데이터가 없습니다.")
                
                # 4. 통합 원문 상세 링크 뷰어 (st.tabs 사용)
                st.subheader("📋 수집 데이터 통합 뷰어")
                tab_news, tab_blog, tab_cafe, tab_shop = st.tabs(["뉴스", "블로그", "카페글", "쇼핑 상품"])
                
                with tab_news:
                    if not df_news.empty:
                        st.dataframe(
                            df_news[['title', 'pubDate', 'originallink']].rename(
                                columns={"title": "기사 제목", "pubDate": "보도시간", "originallink": "원문 링크"}
                            ),
                            use_container_width=True
                        )
                    else:
                        st.info("수집된 뉴스 기사가 없습니다.")
                
                with tab_blog:
                    if not df_blog.empty:
                        st.dataframe(
                            df_blog[['title', 'bloggername', 'postdate', 'link']].rename(
                                columns={"title": "글 제목", "bloggername": "블로그명", "postdate": "작성일", "link": "링크"}
                            ),
                            use_container_width=True
                        )
                    else:
                        st.info("수집된 블로그 글이 없습니다.")
                
                with tab_cafe:
                    if not df_cafe.empty:
                        st.dataframe(
                            df_cafe[['title', 'cafename', 'link']].rename(
                                columns={"title": "글 제목", "cafename": "카페명", "link": "링크"}
                            ),
                            use_container_width=True
                        )
                    else:
                        st.info("수집된 카페글이 없습니다.")
                
                with tab_shop:
                    if not df_shop.empty:
                        st.dataframe(
                            df_shop[['title', 'lprice', 'mallName', 'brand', 'link']].rename(
                                columns={"title": "상품명", "lprice": "최저가", "mallName": "판매처", "brand": "브랜드", "link": "링크"}
                            ),
                            use_container_width=True
                        )
                    else:
                        st.info("수집된 쇼핑 상품이 없습니다.")
