"""
이상 기후 대응 농산물 가격 예측 다중 페이지 Streamlit 대시보드

이 모듈은 이상 기후 데이터와 농산물 도매가격의 관계를 탐색하고 가격 예측 시뮬레이션을 수행하는
Streamlit 웹 애플리케이션의 메인 파일입니다.
"""

import datetime
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 모듈별 임포트
from collectors import fetch_weather_data, fetch_kamis_price_data, fetch_garak_market_data, merge_and_preprocess_data, fetch_weekly_trend_kamis
from models import CropPricePredictor
from utils import apply_premium_design, format_krw, show_metric_delta

# 1. 페이지 초기 설정 및 디자인 레이아웃 정의
st.set_page_config(
    page_title="이상 기후 농산물 영향 분석 시스템",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 프리미엄 다크모드 및 글래스모피즘 스타일 적용
apply_premium_design()

# 2. 사이드바(Sidebar) 전역 입력 설정
st.sidebar.markdown("## ⚙️ 설정 및 인증")

# API 인증 영역 (.env 파일 기반 상시 로그인)
with st.sidebar.expander("🔑 공공데이터 API 인증 정보 (자동 연동됨)", expanded=False):
    weather_key = st.text_input("기상청 API Key", type="password", help="공공데이터포털 기상청 ASOS API 키", value=os.getenv("WEATHER_API_KEY", ""))
    kamis_key = st.text_input("KAMIS API Key", type="password", help="농산물유통정보 API 인증키", value=os.getenv("KAMIS_API_KEY", ""))
    kamis_id = st.text_input("KAMIS Cert ID", type="password", help="농산물유통정보 회원 아이디", value=os.getenv("KAMIS_CERT_ID", ""))
    garak_url = st.text_input("가락시장 API URL", type="password", help="가락시장 반입물량 데이터 호출 URL", value=os.getenv("GARAK_API_URL", ""))

# 품목 다중 입력 영역
st.sidebar.markdown("### 🥦 분석 대상 농산물")
raw_items = st.sidebar.text_input("한글 품목명 입력 (쉼표 구분)", value="배추, 무, 양파", help="지원 품목: 배추, 무, 양파, 대파, 마늘")
item_names = [x.strip() for x in raw_items.split(",") if x.strip()]

# 기간 설정 영역
st.sidebar.markdown("### 📅 분석 대상 기간")
today = datetime.date.today()
default_start = today - datetime.timedelta(days=365)  # 기본값: 최근 1년
start_date = st.sidebar.date_input("시작일", default_start, max_value=today)
end_date = st.sidebar.date_input("종료일", today, min_value=start_date, max_value=today)

# 다중 페이지 내비게이션 라디오 버튼
st.sidebar.markdown("### 🧭 페이지 이동")
page = st.sidebar.radio(
    "메뉴 선택",
    ["데이터 수집 및 조회", "EDA 및 상관관계 분석", "가격 예측 시뮬레이션"]
)

# 3. 데이터 로딩 및 전처리 파이프라인 (캐싱 활용)
@st.cache_data(show_spinner="전체 데이터셋 로딩 및 통합 전처리 중...")
def load_all_dashboard_data(
    w_key, k_key, k_id, g_url, start_d, end_d, items
) -> pd.DataFrame:
    """기상청, KAMIS 도매가격, 가락시장 반입물량 데이터를 수집하고 병합한 통합 데이터프레임을 반환합니다."""
    # 기상 데이터 수집
    weather_df = fetch_weather_data(w_key, start_d, end_d)
    
    # 품목별 가격 및 물량 데이터 수집
    price_dfs = []
    garak_dfs = []
    for item in items:
        p_df = fetch_kamis_price_data(k_key, k_id, start_d, end_d, item, weather_df)
        price_dfs.append(p_df)
        
        g_df = fetch_garak_market_data(g_url, start_d, end_d, item)
        garak_dfs.append(g_df)
        
    # 데이터 병합 및 결측치 보간
    merged_df = merge_and_preprocess_data(weather_df, price_dfs, garak_dfs)
    return merged_df


# 전역 데이터 로드 진행
try:
    if not item_names:
        st.error("분석할 농산물 품목명을 최소 하나 이상 입력해 주세요.")
        st.stop()
        
    df = load_all_dashboard_data(weather_key, kamis_key, kamis_id, garak_url, start_date, end_date, item_names)
except Exception as e:
    st.error(f"데이터 로드 및 초기화 과정 중 예외가 발생했습니다: {e}")
    st.stop()

# 4. 각 기능 페이지별 UI 렌더링 파이프라인

# ==========================================
# PAGE 1: 데이터 수집 및 조회
# ==========================================
if page == "데이터 수집 및 조회":
    st.title("🌾 데이터 수집 및 실시간 조회")
    st.markdown("기상청 기상 정보와 농산물유통정보(KAMIS) 도매 가격 데이터를 실시간으로 연동하여 날짜 기준으로 정렬된 테이블을 조회합니다.")

    # 주요 요약 지표 시각화 (KPI Cards)
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(
            f'<div class="premium-card">'
            f'<h4>📅 총 분석 일수</h4>'
            f'<p style="font-size: 2rem; font-weight:800; color:#3B82F6; margin:0;">{len(df):,}일</p>'
            f'</div>',
            unsafe_allow_html=True
        )
    with kpi2:
        avg_temp_val = df["avg_temp"].mean()
        st.markdown(
            f'<div class="premium-card">'
            f'<h4>🌡️ 기간 평균 기온</h4>'
            f'<p style="font-size: 2rem; font-weight:800; color:#10B981; margin:0;">{avg_temp_val:.1f}°C</p>'
            f'</div>',
            unsafe_allow_html=True
        )
    with kpi3:
        total_rain = df["precipitation"].sum()
        st.markdown(
            f'<div class="premium-card">'
            f'<h4>☔ 기간 누적 강수량</h4>'
            f'<p style="font-size: 2rem; font-weight:800; color:#F59E0B; margin:0;">{total_rain:,.1f}mm</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    # 주간 알뜰장보기 동향 섹션
    st.markdown("### 📰 KAMIS 주간 알뜰장보기 동향")
    weekly_trend = fetch_weekly_trend_kamis()
    
    details_html = "".join([f'<p style="color: #475569; font-size: 0.95rem; margin-top: 4px;">- {d}</p>' for d in weekly_trend.get('details', [])])
    
    st.markdown(
        f"""
        <div class="premium-card" style="margin-bottom: 24px; padding: 24px; background: rgba(59, 130, 246, 0.05); border-left: 4px solid #3B82F6;">
            <h4 style="color: #1e40af; margin-top: 0; margin-bottom: 12px;">{weekly_trend['title']}</h4>
            <p style="font-size: 1.1rem; color: #334155; margin-bottom: 8px;">{weekly_trend['summary']}</p>
            {details_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 데이터 프레임 표출 영역
    st.markdown("### 📊 통합 연동 데이터프레임 (정렬 완료)")
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "date": st.column_config.DateColumn("날짜", format="YYYY-MM-DD"),
            "avg_temp": st.column_config.NumberColumn("평균 기온 (°C)", format="%.1f"),
            "min_temp": st.column_config.NumberColumn("최저 기온 (°C)", format="%.1f"),
            "max_temp": st.column_config.NumberColumn("최고 기온 (°C)", format="%.1f"),
            "precipitation": st.column_config.NumberColumn("강수량 (mm)", format="%.1f"),
            "humidity": st.column_config.NumberColumn("상대습도 (%)", format="%.1f"),
            "wind_speed": st.column_config.NumberColumn("풍속 (m/s)", format="%.1f"),
        }
    )

    # CSV 다운로드 기능 제공
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 통합 데이터 CSV 다운로드",
        data=csv_data,
        file_name="weather_crop_price_data.csv",
        mime="text/csv"
    )

# ==========================================
# PAGE 2: EDA 및 상관관계 분석
# ==========================================
elif page == "EDA 및 상관관계 분석":
    st.title("📈 EDA 및 시차(Lag) 상관관계 분석")
    st.markdown("기상 조건(기온, 강수량)의 변동과 농산물 가격 추이를 직관적으로 비교하고, 기상 재해가 발생한 일정 시차(Lag) 이후 농산물 가격에 주는 영향을 규명합니다.")

    # 2.1. 시계열 이중 축 차트 시각화
    st.markdown("### 🗓️ 기상 요소 vs 농산물 가격 시계열 비교")
    
    # 탭을 통해 품목별로 차트를 각각 보기 좋게 띄움
    tabs = st.tabs(item_names)
    for idx, item in enumerate(item_names):
        with tabs[idx]:
            price_col = f"{item}_가격"
            if price_col not in df.columns:
                st.warning(f"데이터셋에 [{item}] 품목의 가격 컬럼이 없습니다.")
                continue

            # 이중 축 차트 생성 (Plotly Subplots 활용)
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # 1. 가격 데이터 (라인 차트)
            fig.add_trace(
                go.Scatter(x=df["date"], y=df[price_col], name=f"{item} 가격 (원)", line=dict(color="#3B82F6", width=3)),
                secondary_y=False
            )

            # 2. 최고 기온 데이터 (라인 차트, 보조 축)
            fig.add_trace(
                go.Scatter(x=df["date"], y=df["max_temp"], name="일 최고 기온 (°C)", line=dict(color="#EF4444", width=1.5, dash="dot")),
                secondary_y=True
            )

            # 3. 강수량 데이터 (막대 차트, 보조 축)
            fig.add_trace(
                go.Bar(x=df["date"], y=df["precipitation"], name="일 강수량 (mm)", marker_color="rgba(59, 130, 246, 0.3)"),
                secondary_y=True
            )

            # 차트 스타일링 정의
            fig.update_layout(
                title_text=f"[{item}] 가격 및 기상 요인 추이 비교 (이중 축)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="도매 가격 (원)", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis2=dict(title="기온(°C) / 강수량(mm)", showgrid=False)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    # 2.2. 시차(Lag) 상관관계 히트맵 시각화
    st.markdown("### 🗺️ 이상 기후 충격의 시차(Lag) 상관관계 히트맵")
    st.markdown("기온 상승 및 강수 발생 시점으로부터 농산물 가격 상승까지의 지연 효과(7일, 14일, 21일 뒤 영향)를 파악하기 위한 시차 상관계수 분석입니다.")

    # 시차 데이터 생성용 데이터프레임 구축
    lag_records = []
    
    # 분석에 쓸 핵심 기상 독립 변수 정의
    weather_vars = ["avg_temp", "max_temp", "precipitation", "humidity"]
    
    for item in item_names:
        price_col = f"{item}_가격"
        if price_col not in df.columns:
            continue
            
        # 기상 변수와 품목 가격의 시차 간 상관계수 계산
        for w_var in weather_vars:
            # 0일(동시), 7일후, 14일후, 21일후 시차 가격 생성 및 상관계수 도출
            r_0 = df[w_var].corr(df[price_col])
            r_7 = df[w_var].corr(df[price_col].shift(-7))
            r_14 = df[w_var].corr(df[price_col].shift(-14))
            r_21 = df[w_var].corr(df[price_col].shift(-21))
            
            # 국문 명칭 보정
            w_var_kor = {
                "avg_temp": "평균 기온",
                "max_temp": "최고 기온",
                "precipitation": "강수량",
                "humidity": "습도"
            }.get(w_var, w_var)

            lag_records.append({
                "품목": item,
                "기상 요인": w_var_kor,
                "당일 영향 (Lag 0)": round(r_0, 3) if not np.isnan(r_0) else 0.0,
                "1주 뒤 영향 (Lag 7)": round(r_7, 3) if not np.isnan(r_7) else 0.0,
                "2주 뒤 영향 (Lag 14)": round(r_14, 3) if not np.isnan(r_14) else 0.0,
                "3주 뒤 영향 (Lag 21)": round(r_21, 3) if not np.isnan(r_21) else 0.0
            })

    if lag_records:
        lag_corr_df = pd.DataFrame(lag_records)
        
        # 품목별 히트맵 탭 시각화
        item_tabs = st.tabs(item_names)
        for i_idx, item in enumerate(item_names):
            with item_tabs[i_idx]:
                item_corr = lag_corr_df[lag_corr_df["품목"] == item].drop(columns="품목").set_index("기상 요인")
                
                # Plotly Heatmap을 활용한 프리미엄 디자인
                fig_hm = px.imshow(
                    item_corr,
                    labels=dict(x="시차 (Lag)", y="기상 요인", color="상관계수"),
                    x=item_corr.columns,
                    y=item_corr.index,
                    color_continuous_scale="RdBu_r", # 양의 상관관계 빨간색, 음의 상관관계 파란색
                    text_auto=True,
                    zmin=-1.0,
                    zmax=1.0
                )
                
                fig_hm.update_layout(
                    title_text=f"[{item}] 기상 조건별 시차(Lag) 상관계수 매트릭스",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0"),
                    coloraxis_colorbar=dict(title="상관계수")
                )
                
                st.plotly_chart(fig_hm, use_container_width=True)
                st.markdown(
                    "> **💡 해석 가이드**: 상관계수 값이 **+1.0에 가까울수록** 해당 기상 요인이 발생한 후 기재된 시차 뒤에 **가격이 상승**하는 경향이 있음을 뜻하며, **-1.0에 가까울수록 가격이 하락**함을 나타냅니다."
                )

# ==========================================
# PAGE 3: 가격 예측 시뮬레이션
# ==========================================
elif page == "가격 예측 시뮬레이션":
    st.title("🤖 이상 기후 조건별 가격 예측 시뮬레이션")
    st.markdown("Scikit-learn의 Random Forest Regressor 모델을 학습시켜 가상 기상 조건 변화에 따른 가격 변동 및 변동률을 실시간으로 추론하고 예측합니다.")

    # 3.1. 예측 모델 학습 진행
    predictor = CropPricePredictor(df, item_names)

    # 3.2. 가상 조건 설정 슬라이더 패널 (2열 레이아웃)
    st.markdown("### 🎛️ 가상 시나리오 기상 매개변수 조절")
    col1, col2 = st.columns(2)
    with col1:
        sim_avg_temp = st.slider("🌡️ 가상 30일 평균 기온 (°C)", 5.0, 40.0, 22.0, 0.5)
        sim_sum_rain = st.slider("☔ 가상 30일 누적 강수량 (mm)", 0.0, 800.0, 150.0, 10.0)
        sim_humidity = st.slider("💧 가상 30일 평균 상대습도 (%)", 20.0, 100.0, 70.0, 1.0)
    with col2:
        sim_heatwave_days = st.slider("🔥 가상 30일 중 폭염 일수 (최고 33°C 이상)", 0, 30, 3, 1)
        sim_heavyrain_days = st.slider("🌊 가상 30일 중 폭우 일수 (일 강수 50mm 이상)", 0, 15, 1, 1)

    # 3.3. 시뮬레이션 결과 표출
    st.markdown("### 🔮 품목별 실시간 가격 예측 시뮬레이션 결과")
    sim_tabs = st.tabs(item_names)
    
    for s_idx, item in enumerate(item_names):
        with sim_tabs[s_idx]:
            # 시뮬레이션 추론 실행
            result = predictor.simulate_price(
                item,
                sim_avg_temp,
                sim_sum_rain,
                sim_heatwave_days,
                sim_heavyrain_days,
                sim_humidity
            )

            # 예측 메트릭 출력부 (st.metric 및 가독성 카드 결합)
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric(
                    label="📊 최종 시뮬레이션 예측 가격",
                    value=format_krw(result["predicted_price"]),
                    delta=show_metric_delta(result["predicted_price"], result["base_price"]),
                    delta_color="inverse"  # 도매가격 상승 시 붉은색(위험) 경고 유도
                )
            with m_col2:
                st.metric(
                    label="📉 기준 이전 거래가",
                    value=format_krw(result["base_price"])
                )
            with m_col3:
                # 작동 알고리즘 구분 표출
                algo_str = "Random Forest Regressor (ML)" if result["is_ml_mode"] else "Rule-based Fallback Model"
                st.metric(
                    label="⚙️ 연산 메커니즘",
                    value=algo_str
                )

            # 3.4. 학습된 머신러닝 모델의 변수 중요도 및 R^2 스코어 제공
            model_info = predictor.metrics.get(item, {"r2": 0.0, "status": "알 수 없음"})
            st.markdown(f"**💡 모델 학습 상태**: `{model_info['status']}`")

            # 피처 중요도 차트 (Plotly Bar Chart)
            feat_imp = predictor.feature_importances.get(item)
            if feat_imp:
                # 데이터를 데이터프레임으로 변환 후 바 차트 시각화
                imp_df = pd.DataFrame(list(feat_imp.items()), columns=["기상 요인", "중요도"]).sort_values("중요도", ascending=True)
                
                # 국문 명칭으로 레이블 변경
                imp_df["기상 요인"] = imp_df["기상 요인"].map({
                    "rolling_avg_temp": "30일 평균 기온",
                    "rolling_sum_rain": "30일 누적 강수량",
                    "rolling_heatwave_days": "30일 폭염 일수",
                    "rolling_heavyrain_days": "30일 폭우 일수",
                    "rolling_humidity": "30일 평균 상대습도"
                })

                fig_imp = px.bar(
                    imp_df,
                    x="중요도",
                    y="기상 요인",
                    orientation="h",
                    color="중요도",
                    color_continuous_scale="Blues",
                    title=f"[{item}] 가격 예측에 기여하는 기상 변수 중요도 (Feature Importance)"
                )
                fig_imp.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0"),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_imp, use_container_width=True)
