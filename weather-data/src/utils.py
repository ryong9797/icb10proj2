"""
대시보드 프리미엄 UI 디자인 및 헬퍼 유틸리티 모듈

이 모듈은 대시보드 화면에 세련된 다크모드/글래스모피즘 스타일 CSS를 적용하고,
가격 데이터의 통화 포맷팅 등 UI 편의 기능을 제공합니다.
"""

import streamlit as st


def apply_premium_design():
    """대시보드에 고품격(Premium) 비주얼 디자인 CSS를 반영합니다."""
    st.markdown(
        """
        <style>
        /* 구글 폰트 Outfit 적용 */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', 'Noto Sans KR', sans-serif;
        }

        /* 메인 배경 그라디언트 및 글래스모피즘 스타일 */
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: #1e293b;
        }

        /* 사이드바 스타일링 */
        [data-testid="stSidebar"] {
            background-color: rgba(241, 245, 249, 0.85) !important;
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(0, 0, 0, 0.05);
        }

        /* 카드 컴포넌트 클래스 디자인 */
        .premium-card {
            background: rgba(255, 255, 255, 0.85);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 1);
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
            transition: transform 0.2s ease, border 0.2s ease;
            color: #334155;
        }
        
        .premium-card:hover {
            transform: translateY(-2px);
            border: 1px solid rgba(59, 130, 246, 0.4);
            box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);
        }

        /* 헤더 텍스트 디자인 */
        h1 {
            font-weight: 800 !important;
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.05em;
        }
        
        h2, h3 {
            font-weight: 600 !important;
            color: #1e3a8a !important;
            letter-spacing: -0.03em;
        }

        /* 경고/알림 컴포넌트 세련된 테두리 */
        .stAlert {
            border-radius: 12px !important;
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(0, 0, 0, 0.05) !important;
            color: #334155 !important;
        }
        
        /* 메트릭 폰트 크기 및 색상 최적화 */
        [data-testid="stMetricValue"] {
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            color: #1d4ed8 !important;
        }
        
        [data-testid="stMetricDelta"] svg {
            fill: #10b981 !important;
        }
        
        /* 탭 디자인 커스텀 */
        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            color: #64748b;
            border-bottom-width: 2px;
            padding-bottom: 10px;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #2563eb;
        }
        .stTabs [aria-selected="true"] {
            color: #1d4ed8 !important;
            border-bottom-color: #1d4ed8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_krw(value: int) -> str:
    """정수형 금액을 쉼표가 들어간 원화 포맷 문자열로 변환합니다."""
    return f"{value:,.0f}원"


def show_metric_delta(predicted: int, base: int) -> tuple:
    """이전 가격 대비 변동폭과 화살표 기호를 계산하여 메트릭용 정보로 리턴합니다."""
    diff = predicted - base
    rate = (diff / base) * 100.0 if base > 0 else 0.0
    
    if diff > 0:
        delta_str = f"+{diff:,.0f}원 (+{rate:.2f}%)"
    elif diff < 0:
        delta_str = f"-{abs(diff):,.0f}원 ({rate:.2f}%)"
    else:
        delta_str = "변동 없음 (0.0%)"
        
    return delta_str
