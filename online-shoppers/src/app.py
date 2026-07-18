"""
Online Shoppers Purchasing Intention 데이터를 분석하고 시각화하는 Streamlit 대시보드 애플리케이션입니다.
구매 완료 여부(Revenue)를 기준으로 수치형 및 범주형 변수의 기술 통계와 분포 차이를 비교하며,
Plotly 서브플롯과 통계 검정(T-test, Chi-square)을 활용하여 다각도로 분석합니다.
추가적으로, 의사결정나무(Decision Tree) 기반 및 랜덤 포레스트(Random Forest) & 그라디언트 부스팅(Gradient Boosting) 기반의
구매 여부(Revenue) 예측 머신러닝 모델을 구축하고 평가할 수 있는 별도의 페이지들을 제공합니다.
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 머신러닝 라이브러리 추가
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score, 
    roc_auc_score, 
    confusion_matrix, 
    roc_curve, 
    precision_recall_curve, 
    auc
)
import matplotlib.pyplot as plt
try:
    import koreanize_matplotlib
except ImportError:
    pass

# scipy.stats 라이브러리 예외 처리 로드 (통계 검정용)
try:
    from scipy import stats
    scipy_available = True
except ImportError:
    scipy_available = False

# 페이지 레이아웃 설정
st.set_page_config(
    page_title="🛍️ Online Shoppers Intent Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 소스 정보
DATA_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00468/online_shoppers_intention.csv"
DATA_PATH = os.path.join("online-shoppers", "data", "online_shoppers_intention.csv")

# 1. 데이터 로드 및 자동 다운로드 기능
@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        # 웹에서 직접 읽어서 로컬에 저장
        df = pd.read_csv(DATA_URL)
        df.to_csv(DATA_PATH, index=False)
    else:
        df = pd.read_csv(DATA_PATH)
    
    # 데이터 타입 가공 및 정리
    # Revenue, Weekend를 범주형 분석에 맞게 문자열이나 불리언 형태로 명확히 정의
    df['Revenue_Str'] = df['Revenue'].map({True: '구매 완료 (True)', False: '미구매 (False)'})
    df['Weekend_Str'] = df['Weekend'].map({True: '주말 (True)', False: '평일 (False)'})
    
    return df

# ==================== 머신러닝 예측 페이지 렌더링 함수 정의 ====================
def render_machine_learning_page(df):
    """
    Revenue(구매 완료 여부)를 예측하는 의사결정나무 모델의 학습, 평가, 시각화를 수행하는 페이지입니다.
    오버샘플링(Oversampling)과 임계값(Threshold) 조절을 통해 Recall을 높이고, Train/Test 점수 격차를 통해 과적합 여부를 진단합니다.
    """
    st.title("🤖 고객 구매 의도(Revenue) 예측 머신러닝 모델")
    st.markdown("""
    이 페이지에서는 고객들의 다양한 세션 정보와 환경 변수를 활용하여 **최종 구매 완료 여부(Revenue)**를 예측하는 의사결정나무(Decision Tree) 모델을 학습하고 평가합니다.
    사이드바의 하이퍼파라미터를 변경하면서 모델의 예측력 변화와 나무의 의사결정 규칙이 어떻게 변하는지 실시간으로 관찰할 수 있습니다.
    """)

    # 1. 머신러닝 프로세스 흐름 시각화 (Mermaid)
    st.write("---")
    st.subheader("🔗 1. 머신러닝 모델링 및 평가 프로세스")
    st.markdown("""
    본 예측 모델의 전반적인 작업 흐름은 다음과 같습니다.
    """)
    st.markdown("""
    ```mermaid
    graph TD
        A[1. 데이터 로드 및 결측치 확인] --> B[2. 원핫인코딩 & Target 수치화]
        B --> C[3. 학습 및 테스트 데이터 분할]
        C --> D[4. 학습용 데이터 오버샘플링 적용 여부]
        D --> E[5. 의사결정나무 모델 학습]
        E --> F[6. 분류 임계값 조절 및 예측]
        F --> G[7. 학습 vs 평가 데이터 성능 대조 및 과적합 자가진단]
        G --> H[8. 오차 행렬, 성능 곡선, 피처 중요도 및 구조 시각화]
        style A fill:#f9f,stroke:#333,stroke-width:2px
        style E fill:#bbf,stroke:#333,stroke-width:2px
        style G fill:#bfb,stroke:#333,stroke-width:2px
        style H fill:#fbf,stroke:#333,stroke-width:2px
    ```
    """)

    # --- 사이드바 설정 영역 ---
    st.sidebar.header("⚙️ 2. 머신러닝 모델 설정")
    
    # 예측에 사용할 피처 선택
    num_cols = [
        "Administrative", "Administrative_Duration", 
        "Informational", "Informational_Duration", 
        "ProductRelated", "ProductRelated_Duration", 
        "BounceRates", "ExitRates", "PageValues", "SpecialDay"
    ]
    
    cat_cols = [
        "Month", "OperatingSystems", "Browser", 
        "Region", "TrafficType", "VisitorType", "Weekend"
    ]
    
    all_features = num_cols + cat_cols
    selected_features = st.sidebar.multiselect(
        "예측 모델에 포함할 피처를 선택하세요 (기본값: 전체):",
        options=all_features,
        default=all_features
    )
    
    if not selected_features:
        st.warning("⚠️ 최소 한 개 이상의 피처를 선택해야 모델을 학습할 수 있습니다.")
        return

    # 성능 개선 핵심 설정 (오버샘플링 및 임계값 튜닝)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 모델 성능 최적화 설정")
    
    use_oversampling = st.sidebar.checkbox("학습 데이터 오버샘플링(Oversampling) 적용", value=True)
    if use_oversampling:
        st.sidebar.info("💡 **오버샘플링 적용됨**: 구매 세션(소수 클래스)을 복원 추출하여 클래스 비율을 1:1로 맞춥니다. (재현율 향상 효과)")
    
    threshold = st.sidebar.slider("분류 판단 임계값 (Threshold)", min_value=0.05, max_value=0.95, value=0.50, step=0.05)
    if threshold != 0.50:
        st.sidebar.info(f"💡 **임계값 조정됨 ({threshold})**: 예측 확률이 {threshold} 이상이면 구매(True)로 판정합니다.")

    # 하이퍼파라미터 튜닝
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 하이퍼파라미터 튜닝")
    criterion = st.sidebar.selectbox("분할 기준 (Criterion)", ["gini", "entropy"], index=0)
    max_depth = st.sidebar.slider("트리 최대 깊이 (Max Depth)", min_value=1, max_value=15, value=5)
    min_samples_split = st.sidebar.slider("최소 분할 샘플 수 (Min Samples Split)", min_value=2, max_value=100, value=20)
    min_samples_leaf = st.sidebar.slider("최소 리프 샘플 수 (Min Samples Leaf)", min_value=1, max_value=50, value=10)
    test_size = st.sidebar.slider("테스트 데이터 비율 (Test Size)", min_value=0.1, max_value=0.5, value=0.2, step=0.05)

    # 2. 데이터 전처리 및 인코딩
    X = df[selected_features].copy()
    y = df['Revenue'].astype(int) # True -> 1, False -> 0

    # 범주형 피처 중 선택된 피처 원핫인코딩 적용
    selected_cat = [col for col in cat_cols if col in selected_features]
    if selected_cat:
        X = pd.get_dummies(X, columns=selected_cat, drop_first=True)
    
    # scikit-learn 호환성을 위해 타입 캐스팅
    X = X.astype(int)

    # 학습 및 테스트 셋 분리 (계층화 추출 적용)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    # 오버샘플링 로직 실행 (Pandas 기반 Random Oversampling)
    if use_oversampling:
        df_train = pd.concat([X_train, y_train], axis=1)
        class_0 = df_train[y_train == 0]
        class_1 = df_train[y_train == 1]
        
        # 소수 클래스를 다수 클래스 크기만큼 복원 추출
        if len(class_1) < len(class_0):
            class_1_over = class_1.sample(len(class_0), replace=True, random_state=42)
            df_train_over = pd.concat([class_0, class_1_over], axis=0)
        else:
            class_0_over = class_0.sample(len(class_1), replace=True, random_state=42)
            df_train_over = pd.concat([class_1, class_0_over], axis=0)
            
        df_train_over = df_train_over.sample(frac=1, random_state=42).reset_index(drop=True)
        X_train_model = df_train_over.drop(y_train.name, axis=1)
        y_train_model = df_train_over[y_train.name]
    else:
        X_train_model = X_train
        y_train_model = y_train

    # 3. 모델 학습
    model = DecisionTreeClassifier(
        criterion=criterion,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        random_state=42
    )
    model.fit(X_train_model, y_train_model)

    # 4. 테스트셋 예측 및 평가
    y_test_pred_proba = model.predict_proba(X_test)[:, 1]
    y_test_pred = (y_test_pred_proba >= threshold).astype(int)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_prec = precision_score(y_test, y_test_pred, zero_division=0)
    test_rec = recall_score(y_test, y_test_pred, zero_division=0)
    test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
    test_roc_auc = roc_auc_score(y_test, y_test_pred_proba)

    # 5. 학습셋 예측 및 평가
    y_train_pred_proba = model.predict_proba(X_train_model)[:, 1]
    y_train_pred = (y_train_pred_proba >= threshold).astype(int)

    train_acc = accuracy_score(y_train_model, y_train_pred)
    train_prec = precision_score(y_train_model, y_train_pred, zero_division=0)
    train_rec = recall_score(y_train_model, y_train_pred, zero_division=0)
    train_f1 = f1_score(y_train_model, y_train_pred, zero_division=0)
    train_roc_auc = roc_auc_score(y_train_model, y_train_pred_proba)

    st.write("---")
    st.subheader("📊 2. 예측 모델 성능 대조 (Train vs Test)")
    st.markdown(f"**검증(Test) 세트 크기**: {len(y_test):,} 건 | **학습(Train) 세트 크기**: {len(y_train_model):,} 건" + (" (오버샘플링 적용됨)" if use_oversampling else ""))

    # 5대 평가 지표 표 시각화
    compare_df = pd.DataFrame({
        "평가 지표": ["정확도 (Accuracy)", "정밀도 (Precision)", "재현율 (Recall)", "F1-Score", "ROC-AUC"],
        "학습 데이터셋 (Train)": [train_acc, train_prec, train_rec, train_f1, train_roc_auc],
        "검증 데이터셋 (Test)": [test_acc, test_prec, test_rec, test_f1, test_roc_auc]
    })
    st.dataframe(compare_df.set_index("평가 지표").style.format("{:.4f}"), use_container_width=True)

    # 평가지표 시각화 (두 세트 대조 막대 그래프)
    chart_df = pd.melt(compare_df, id_vars=["평가 지표"], var_name="데이터셋 구분", value_name="점수")
    fig_compare = px.bar(
        chart_df, x="평가 지표", y="점수", color="데이터셋 구분",
        barmode="group", text="점수",
        color_discrete_map={"학습 데이터셋 (Train)": "#3498db", "검증 데이터셋 (Test)": "#e74c3c"},
        title="학습 데이터(Train) vs 검증 데이터(Test) 성능 지표 비교"
    )
    fig_compare.update_layout(yaxis_range=[0, 1.15], paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    fig_compare.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    st.plotly_chart(fig_compare, use_container_width=True)

    # 과적합 & 과소적합 진단 정보
    acc_gap = train_acc - test_acc
    f1_gap = train_f1 - test_f1
    
    st.markdown("#### **🔍 모델 일반화 진단 결과**")
    if train_acc < 0.70 and test_acc < 0.70:
        st.warning("⚠️ **진단 결과: 모델 과소적합 (Underfitting) 상태 의심**")
        st.markdown(f"""
        - **원인**: 학습({train_acc:.2%}) 및 테스트({test_acc:.2%}) 점수가 모두 지나치게 낮습니다. 모델이 데이터의 핵심 구조를 학습하지 못했습니다.
        - **해결 가이드**: 사이드바에서 **'트리 최대 깊이(Max Depth)'**를 늘리거나 **'최소 분할 샘플 수'**를 줄여 모델 복잡도를 높이세요. 더 유의미한 변수들을 학습 피처로 선택하는 것도 좋은 해결책입니다.
        """)
    elif acc_gap > 0.07 or f1_gap > 0.08:
        st.error("🚨 **진단 결과: 모델 과적합 (Overfitting) 상태 감지**")
        st.markdown(f"""
        - **원인**: 학습 데이터 점수({train_acc:.2%})가 테스트 데이터 점수({test_acc:.2%}) 대비 **약 {acc_gap*100:.1f}%p 더 높은 격차**를 보입니다. 학습 셋에만 너무 특화되어 실제 새로운 사용자 행동에 대응하지 못하는 상태입니다.
        - **해결 가이드**: 사이드바에서 **'트리 최대 깊이(Max Depth)'**를 낮추어 모델 구조를 단순화하거나, **'최소 분할 샘플 수(Min Samples Split)'** 및 **'최소 리프 샘플 수(Min Samples Leaf)'**를 높여 트리의 가지치기를 하세요.
        """)
    else:
        st.success("✅ **진단 결과: 적정 일반화 (Good Generalization) 달성**")
        st.markdown(f"""
        - **원인**: 학습 데이터 점수({train_acc:.2%})와 테스트 데이터 점수({test_acc:.2%})의 격차가 **{abs(acc_gap)*100:.1f}%p 이내**로 조화롭게 잘 맞추어져 있습니다.
        - **분석**: 오버피팅과 언더피팅의 위험 없이, 새롭게 방문하는 사용자 데이터 세션에 대해서도 높은 신뢰성을 가지고 구매 여부 예측 결과를 도출해 낼 수 있는 이상적인 훈련 상태입니다.
        """)

    # 5. 오차 행렬, ROC Curve, Precision-Recall Curve 시각화
    st.write("---")
    st.subheader("📈 3. 성능 진단 상세 분석 (검증 데이터 기준)")
    
    tab_cm, tab_curves = st.tabs(["🌪️ 오차 행렬 (Confusion Matrix)", "📉 분류 평가 곡선 (ROC & PR Curve)"])
    
    with tab_cm:
        cm = confusion_matrix(y_test, y_test_pred)
        tn, fp, fn, tp = cm.ravel()
        
        # 오차 행렬 히트맵 시각화
        cm_z = [[tn, fp], [fn, tp]]
        fig_cm = px.imshow(
            cm_z,
            labels=dict(x="예측 결과", y="실제값", color="세션 수"),
            x=["미구매 (Predict False)", "구매완료 (Predict True)"],
            y=["실제 미구매 (Actual False)", "실제 구매완료 (Actual True)"],
            text_auto=True,
            color_continuous_scale="Viridis",
            title="오차 행렬 (Confusion Matrix) 상세 분포"
        )
        fig_cm.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        
        col_cm_left, col_cm_right = st.columns([3, 2])
        with col_cm_left:
            st.plotly_chart(fig_cm, use_container_width=True)
        with col_cm_right:
            st.markdown("#### **오차 행렬 해석 가이드**")
            st.markdown(f"""
            - **진음성 (True Negative - {tn:,}건)**: 실제 미구매 건을 미구매로 올바르게 예측한 비율입니다.
            - **위양성 (False Positive - {fp:,}건)**: 실제 미구매 건이나 구매완료로 잘못 예측한 건입니다 (1종 오류).
            - **위음성 (False Negative - {fn:,}건)**: 실제 구매 완료 건이나 미구매로 잘못 예측한 건입니다 (2종 오류, **쇼핑몰 관점에서 가장 아쉬운 손실** ⚠️).
            - **진양성 (True Positive - {tp:,}건)**: 실제 구매 완료 건을 구매완료로 올바르게 예측한 비율입니다.
            
            **📊 비즈니스 요약**:
            - 예측 모델이 **전체 구매 시도 고객 중 {tp / (tp + fn) * 100:.1f}%(Recall)**를 식별해냈으며,
            - 구매할 것이라 예측한 고객 중 실제 구매에 도달한 고객 비율은 **{tp / (tp + fp) * 100:.1f}%(Precision)**입니다.
            """)

    with tab_curves:
        col_curve_left, col_curve_right = st.columns(2)
        
        # ROC Curve
        fpr, tpr, _ = roc_curve(y_test, y_test_pred_proba)
        fig_roc = go.Figure()
        fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name=f'ROC Curve (AUC = {test_roc_auc:.4f})', line=dict(color='#2980b9', width=3)))
        fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Random Guess', line=dict(dash='dash', color='grey')))
        fig_roc.update_layout(
            title="ROC (Receiver Operating Characteristic) Curve",
            xaxis_title="위양성률 (False Positive Rate)",
            yaxis_title="진양성률 (True Positive Rate)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(x=0.6, y=0.1)
        )
        with col_curve_left:
            st.plotly_chart(fig_roc, use_container_width=True)
            
        # PR Curve
        prec_val, rec_val, _ = precision_recall_curve(y_test, y_test_pred_proba)
        fig_pr = go.Figure()
        fig_pr.add_trace(go.Scatter(x=rec_val, y=prec_val, mode='lines', name='Precision-Recall Curve', line=dict(color='#e74c3c', width=3)))
        fig_pr.update_layout(
            title="Precision-Recall Curve",
            xaxis_title="재현율 (Recall)",
            yaxis_title="정밀도 (Precision)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        with col_curve_right:
            st.plotly_chart(fig_pr, use_container_width=True)

    # 6. 피처 중요도 및 디시전트리 시각화
    st.write("---")
    st.subheader("🌲 4. 디시전트리 구조 및 피처 중요도 분석")
    
    col_tree_left, col_tree_right = st.columns([1, 1])
    
    with col_tree_left:
        st.subheader("📊 피처 중요도 (Feature Importance)")
        importances = model.feature_importances_
        feat_imp_df = pd.DataFrame({
            "피처명": X.columns,
            "중요도": importances
        }).sort_values("중요도", ascending=True)
        
        # 상위 15개 피처만 표시
        feat_imp_df_top = feat_imp_df.tail(15)
        
        fig_imp = px.bar(
            feat_imp_df_top, x="중요도", y="피처명",
            orientation="h",
            title="Revenue 예측에 기여하는 피처 중요도 (상위 15개)",
            color="중요도",
            color_continuous_scale="Plasma"
        )
        fig_imp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_imp, use_container_width=True)
        
    with col_tree_right:
        st.markdown("#### **💡 피처 영향력 비즈니스 해설**")
        # 가장 높은 중요도를 가진 피처를 찾음
        top_feature = feat_imp_df.sort_values("중요도", ascending=False).iloc[0]["피처명"]
        top_importance = feat_imp_df.sort_values("중요도", ascending=False).iloc[0]["중요도"]
        
        st.markdown(f"""
        - 본 의사결정나무 모델에서 고객의 구매 여부(Revenue)를 판별하는데 가장 핵심적으로 기여한 변수는 **'{top_feature}'** 입니다. (중요도 비중: **{top_importance*100:.1f}%**)
        - 일반적으로 **PageValues** (고객이 방문한 페이지의 평균 가치)가 매우 높은 중요도를 차지하게 됩니다. 이 값이 높을수록 최종 장바구니 결제 의지가 확고한 상태를 대변하기 때문입니다.
        - 그 외에 **BounceRates** (이탈률), **ExitRates** (종료율), **ProductRelated_Duration** (제품 탐색 체류 시간) 등이 구매 전환 예측의 주요 벤치마크 지표로 작용하고 있습니다.
        """)

    # 디시전트리 그래픽 시각화 (Matplotlib)
    st.write("---")
    st.subheader("🌳 의사결정나무 학습 규칙 시각화 (Decision Tree 구조)")
    st.markdown("""
    학습된 의사결정나무의 논리적인 분류 조건(Rule)들을 구조화하여 보여줍니다.
    시각적 복잡도를 고려하여 아래 그림은 상위 **3단계(Depth 3)**의 노드들만 요약 시각화하였습니다.
    """)
    
    # matplotlib 한글 폰트 적용 및 트리 시각화
    fig, ax = plt.subplots(figsize=(16, 9))
    plot_tree(
        model,
        max_depth=3, # 시각용으로 깊이를 3으로 고정하여 뭉개짐 방지
        feature_names=list(X.columns),
        class_names=["미구매 (False)", "구매완료 (True)"],
        filled=True,
        rounded=True,
        fontsize=9,
        ax=ax
    )
    # Matplotlib 렌더링
    st.pyplot(fig)

    # 7. 비즈니스 의사결정을 위한 인사이트 및 액션 플랜 (1000자 분량)
    st.write("---")
    st.subheader("🎯 5. 비즈니스 활용 인사이트 및 실행 액션 플랜 (Action Plan)")
    st.markdown("""
    의사결정나무 모델의 분류 규칙과 피처 중요도를 바탕으로, 고객 구매 전환율을 극대화하고 이탈을 최소화하기 위한 비즈니스 인사이트 및 구체적인 마케팅/운영 액션 플랜을 제시합니다.

    #### **💡 1. 핵심 비즈니스 인사이트**
    - **PageValues의 절대적 판별력**: 모델이 구매 여부를 판단하는 가장 결정적인 규칙은 **PageValues**입니다. 페이지 가치가 임계값(일반적으로 약 6.0~8.5) 이상인 고객들은 단순 브라우징 단계를 넘어 구체적인 구매 의도(장바구니 담기, 결제창 진입 등)를 형성한 세션입니다. 이 집단의 최종 구매 성공률은 매우 높지만, 여전히 결제 오류나 프로세스의 피로감으로 인해 미구매 이탈이 발생합니다.
    - **ExitRates & BounceRates의 이탈 시그널**: 종료율과 이탈률이 높은 세션은 사이트 체류 시간이나 페이지 탐색 수와 무관하게 즉각적인 이탈로 연결됩니다. 특히, 특정 제품 페이지에서 종료율이 치솟는다면 이는 정보 부족, 가격 불만족, 혹은 모바일 최적화 미흡 등의 문제를 강력히 반영합니다.
    - **탐색 시간과 실제 구매 의도의 간극**: 제품 페이지 체류 시간이 길다고 해서 항상 구매로 직결되지는 않습니다. 목적 없는 방황(단순 스크롤)과 적극적인 가치 탐색을 구분해야 하며, 탐색 시간을 페이지 가치로 전환시킬 수 있는 동적 유도가 필요합니다.

    #### **📋 2. 구체적인 비즈니스 액션 플랜 (Action Plan)**
    1. **고가치 이탈 우려 세션 대상 실시간 타겟 마케팅 (CRM 연계)**
       - **대상**: PageValues가 0보다 크지만 구매(Revenue = False)에 이르지 못하고 세션을 종료하려는 고객
       - **액션**: 마우스 커서가 브라우저 상단(닫기 버튼)으로 이동하는 등 이탈 조짐을 보일 때, "장바구니 10% 즉시 할인 쿠폰" 또는 "무료 배송 혜택" 팝업을 실시간으로 노출하여 결제 전환을 유인합니다.
       
    2. **ExitRates(종료율) 병목 구간 해소 및 결제 편의성 개선**
       - **대상**: 종료율이 평균 이상으로 높게 나타나는 페이지 및 결제 단계
       - **액션**: 결제 진입 단계에서 간편 결제(네이버페이, 카카오페이, 토스페이 등)를 최상단에 배치하여 터치 1번으로 결제가 가능하게 합니다. 또한, 비회원 구매를 허용하고 복잡한 입력 양식을 대폭 축소하여 구매 피로도를 경감시킵니다.
       
    3. **장바구니 미결제 리타게팅 광고 및 알림 캠페인**
       - **대상**: 고가치 세션을 기록한 후 이탈한 회원 고객
       - **액션**: 이탈 후 1시간 내에 카카오 알림톡이나 푸시 메시지를 통해 "장바구니에 담긴 상품이 품절 임박했습니다"라는 개인화 메시지를 전송하여 사이트 재방문을 유도합니다.
       
    4. **예측 모델 기반 마케팅 예산 및 리소스 효율화 (ROI 극대화)**
       - **대상**: 전체 유입 고객 세션
       - **액션**: 의사결정나무 모델을 통해 예측된 구매 확률이 80% 이상인 유저(자연 구매군)에게는 불필요한 할인 쿠폰 지급을 자제하여 마진율을 방어합니다. 반면, 구매 확률이 40%~60% 사이인 '망설이는 중간군'에게 프로모션 혜택을 집중 투입하여 마케팅 ROI를 최고조로 끌어올립니다.
    """)


# ==================== 앙상블 머신러닝 예측 페이지 렌더링 함수 정의 ====================
def render_ensemble_ml_page(df):
    """
    Revenue(구매 완료 여부)를 예측하는 랜덤 포레스트(Random Forest) 및 그라디언트 부스팅(Gradient Boosting) 모델을 학습하고 평가하는 페이지입니다.
    두 모델의 하이퍼파라미터를 직접 튜닝하여 성능을 비교 분석하고 비즈니스적 활용 방안을 도출합니다.
    """
    st.title("🌲 앙상블 모델 예측 (Random Forest & Gradient Boosting)")
    st.markdown("""
    이 페이지에서는 다수의 의사결정나무를 결합하여 예측 성능을 극대화하는 대표적인 두 가지 앙상블 알고리즘인 **랜덤 포레스트(Random Forest)**와 **그라디언트 부스팅(Gradient Boosting)** 모델을 학습하고 평가합니다.
    사이드바의 하이퍼파라미터를 변경하면서 두 모델의 예측력 비교와 일반화 성능 변화를 실시간으로 관찰할 수 있습니다.
    """)

    # 1. 머신러닝 프로세스 흐름 시각화 (Mermaid)
    st.write("---")
    st.subheader("🔗 1. 앙상블 모델링 및 평가 프로세스")
    st.markdown("""
    본 예측 모델의 전반적인 작업 흐름은 다음과 같습니다.
    """)
    st.markdown("""
    ```mermaid
    graph TD
        A[1. 데이터 로드 및 전처리] --> B[2. 원핫인코딩 & Target 수치화]
        B --> C[3. 학습 및 테스트 데이터 분할]
        C --> D[4. 학습용 데이터 오버샘플링 적용 여부]
        D --> E1[5-1. 랜덤 포레스트 모델 학습]
        D --> E2[5-2. 그라디언트 부스팅 모델 학습]
        E1 --> F[6. 모델별 임계값 기반 예측]
        E2 --> F
        F --> G[7. 모델별 Train vs Test 성능 분석 및 일반화 진단]
        G --> H[8. 두 모델의 성능 곡선, 피처 중요도 시각화 및 비교 분석]
        style A fill:#f9f,stroke:#333,stroke-width:2px
        style E1 fill:#bbf,stroke:#333,stroke-width:2px
        style E2 fill:#bbf,stroke:#333,stroke-width:2px
        style H fill:#fbf,stroke:#333,stroke-width:2px
    ```
    """)

    # --- 사이드바 설정 영역 ---
    st.sidebar.header("⚙️ 앙상블 모델 설정")
    
    # 예측에 사용할 피처 선택
    num_cols = [
        "Administrative", "Administrative_Duration", 
        "Informational", "Informational_Duration", 
        "ProductRelated", "ProductRelated_Duration", 
        "BounceRates", "ExitRates", "PageValues", "SpecialDay"
    ]
    
    cat_cols = [
        "Month", "OperatingSystems", "Browser", 
        "Region", "TrafficType", "VisitorType", "Weekend"
    ]
    
    all_features = num_cols + cat_cols
    selected_features = st.sidebar.multiselect(
        "예측 모델에 포함할 피처를 선택하세요 (기본값: 전체):",
        options=all_features,
        default=all_features,
        key="ensemble_features"
    )
    
    if not selected_features:
        st.warning("⚠️ 최소 한 개 이상의 피처를 선택해야 모델을 학습할 수 있습니다.")
        return

    # 성능 개선 핵심 설정 (오버샘플링 및 임계값 튜닝)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 모델 성능 최적화 설정")
    
    use_oversampling = st.sidebar.checkbox("학습 데이터 오버샘플링(Oversampling) 적용", value=True, key="ensemble_over")
    if use_oversampling:
        st.sidebar.info("💡 **오버샘플링 적용됨**: 구매 세션(소수 클래스)을 복원 추출하여 클래스 비율을 1:1로 맞춥니다. (재현율 향상 효과)")
    
    threshold = st.sidebar.slider("분류 판단 임계값 (Threshold)", min_value=0.05, max_value=0.95, value=0.50, step=0.05, key="ensemble_thresh")
    if threshold != 0.50:
        st.sidebar.info(f"💡 **임계값 조정됨 ({threshold})**: 예측 확률이 {threshold} 이상이면 구매(True)로 판정합니다.")

    test_size = st.sidebar.slider("테스트 데이터 비율 (Test Size)", min_value=0.1, max_value=0.5, value=0.2, step=0.05, key="ensemble_test_size")

    # 하이퍼파라미터 튜닝
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 랜덤 포레스트 파라미터")
    rf_n_estimators = st.sidebar.slider("RF 트리 개수 (n_estimators)", min_value=10, max_value=200, value=100, step=10, key="rf_n_est")
    rf_max_depth = st.sidebar.slider("RF 최대 깊이 (max_depth)", min_value=1, max_value=15, value=5, key="rf_max_dep")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 그라디언트 부스팅 파라미터")
    gb_n_estimators = st.sidebar.slider("GB 트리 개수 (n_estimators)", min_value=10, max_value=200, value=100, step=10, key="gb_n_est")
    gb_learning_rate = st.sidebar.slider("GB 학습률 (learning_rate)", min_value=0.01, max_value=0.50, value=0.10, step=0.01, key="gb_lr")
    gb_max_depth = st.sidebar.slider("GB 최대 깊이 (max_depth)", min_value=1, max_value=10, value=3, key="gb_max_dep")

    # 2. 데이터 전처리 및 인코딩
    X = df[selected_features].copy()
    y = df['Revenue'].astype(int) # True -> 1, False -> 0

    # 범주형 피처 중 선택된 피처 원핫인코딩 적용
    selected_cat = [col for col in cat_cols if col in selected_features]
    if selected_cat:
        X = pd.get_dummies(X, columns=selected_cat, drop_first=True)
    
    # scikit-learn 호환성을 위해 타입 캐스팅
    X = X.astype(int)

    # 학습 및 테스트 셋 분리 (계층화 추출 적용)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    # 오버샘플링 로직 실행 (Pandas 기반 Random Oversampling)
    if use_oversampling:
        df_train = pd.concat([X_train, y_train], axis=1)
        class_0 = df_train[y_train == 0]
        class_1 = df_train[y_train == 1]
        
        # 소수 클래스를 다수 클래스 크기만큼 복원 추출
        if len(class_1) < len(class_0):
            class_1_over = class_1.sample(len(class_0), replace=True, random_state=42)
            df_train_over = pd.concat([class_0, class_1_over], axis=0)
        else:
            class_0_over = class_0.sample(len(class_1), replace=True, random_state=42)
            df_train_over = pd.concat([class_1, class_0_over], axis=0)
            
        df_train_over = df_train_over.sample(frac=1, random_state=42).reset_index(drop=True)
        X_train_model = df_train_over.drop(y_train.name, axis=1)
        y_train_model = df_train_over[y_train.name]
    else:
        X_train_model = X_train
        y_train_model = y_train

    # 3. 모델 학습
    with st.spinner("🌲 앙상블 모델 학습 중입니다... 잠시만 기다려주세요."):
        # Random Forest 학습
        rf_model = RandomForestClassifier(
            n_estimators=rf_n_estimators,
            max_depth=rf_max_depth,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_model, y_train_model)

        # Gradient Boosting 학습
        gb_model = GradientBoostingClassifier(
            n_estimators=gb_n_estimators,
            learning_rate=gb_learning_rate,
            max_depth=gb_max_depth,
            random_state=42
        )
        gb_model.fit(X_train_model, y_train_model)

    # 4. 예측 및 평가 지표 계산
    # Random Forest 평가
    rf_test_pred_proba = rf_model.predict_proba(X_test)[:, 1]
    rf_test_pred = (rf_test_pred_proba >= threshold).astype(int)
    rf_train_pred_proba = rf_model.predict_proba(X_train_model)[:, 1]
    rf_train_pred = (rf_train_pred_proba >= threshold).astype(int)

    rf_metrics = {
        "train_acc": accuracy_score(y_train_model, rf_train_pred),
        "train_prec": precision_score(y_train_model, rf_train_pred, zero_division=0),
        "train_rec": recall_score(y_train_model, rf_train_pred, zero_division=0),
        "train_f1": f1_score(y_train_model, rf_train_pred, zero_division=0),
        "train_roc_auc": roc_auc_score(y_train_model, rf_train_pred_proba),
        "test_acc": accuracy_score(y_test, rf_test_pred),
        "test_prec": precision_score(y_test, rf_test_pred, zero_division=0),
        "test_rec": recall_score(y_test, rf_test_pred, zero_division=0),
        "test_f1": f1_score(y_test, rf_test_pred, zero_division=0),
        "test_roc_auc": roc_auc_score(y_test, rf_test_pred_proba)
    }

    # Gradient Boosting 평가
    gb_test_pred_proba = gb_model.predict_proba(X_test)[:, 1]
    gb_test_pred = (gb_test_pred_proba >= threshold).astype(int)
    gb_train_pred_proba = gb_model.predict_proba(X_train_model)[:, 1]
    gb_train_pred = (gb_train_pred_proba >= threshold).astype(int)

    gb_metrics = {
        "train_acc": accuracy_score(y_train_model, gb_train_pred),
        "train_prec": precision_score(y_train_model, gb_train_pred, zero_division=0),
        "train_rec": recall_score(y_train_model, gb_train_pred, zero_division=0),
        "train_f1": f1_score(y_train_model, gb_train_pred, zero_division=0),
        "train_roc_auc": roc_auc_score(y_train_model, gb_train_pred_proba),
        "test_acc": accuracy_score(y_test, gb_test_pred),
        "test_prec": precision_score(y_test, gb_test_pred, zero_division=0),
        "test_rec": recall_score(y_test, gb_test_pred, zero_division=0),
        "test_f1": f1_score(y_test, gb_test_pred, zero_division=0),
        "test_roc_auc": roc_auc_score(y_test, gb_test_pred_proba)
    }

    st.write("---")
    st.subheader("📊 2. 예측 모델 성능 대조 (Random Forest vs Gradient Boosting)")
    st.markdown(f"**검증(Test) 세트 크기**: {len(y_test):,} 건 | **학습(Train) 세트 크기**: {len(y_train_model):,} 건" + (" (오버샘플링 적용됨)" if use_oversampling else ""))

    # 5대 평가 지표 표 시각화
    metrics_names = ["정확도 (Accuracy)", "정밀도 (Precision)", "재현율 (Recall)", "F1-Score", "ROC-AUC"]
    compare_df = pd.DataFrame({
        "평가 지표": metrics_names,
        "RF 학습 (Train)": [rf_metrics["train_acc"], rf_metrics["train_prec"], rf_metrics["train_rec"], rf_metrics["train_f1"], rf_metrics["train_roc_auc"]],
        "RF 검증 (Test)": [rf_metrics["test_acc"], rf_metrics["test_prec"], rf_metrics["test_rec"], rf_metrics["test_f1"], rf_metrics["test_roc_auc"]],
        "GB 학습 (Train)": [gb_metrics["train_acc"], gb_metrics["train_prec"], gb_metrics["train_rec"], gb_metrics["train_f1"], gb_metrics["train_roc_auc"]],
        "GB 검증 (Test)": [gb_metrics["test_acc"], gb_metrics["test_prec"], gb_metrics["test_rec"], gb_metrics["test_f1"], gb_metrics["test_roc_auc"]]
    })
    st.dataframe(compare_df.set_index("평가 지표").style.format("{:.4f}"), use_container_width=True)

    # 평가지표 시각화 (두 세트 대조 막대 그래프 - 검증 데이터 중심)
    compare_test_df = pd.DataFrame({
        "평가 지표": metrics_names,
        "Random Forest (Test)": [rf_metrics["test_acc"], rf_metrics["test_prec"], rf_metrics["test_rec"], rf_metrics["test_f1"], rf_metrics["test_roc_auc"]],
        "Gradient Boosting (Test)": [gb_metrics["test_acc"], gb_metrics["test_prec"], gb_metrics["test_rec"], gb_metrics["test_f1"], gb_metrics["test_roc_auc"]]
    })
    chart_df = pd.melt(compare_test_df, id_vars=["평가 지표"], var_name="모델 구분", value_name="점수")
    fig_compare = px.bar(
        chart_df, x="평가 지표", y="점수", color="모델 구분",
        barmode="group", text="점수",
        color_discrete_map={"Random Forest (Test)": "#3498db", "Gradient Boosting (Test)": "#e74c3c"},
        title="두 앙상블 모델의 검증 데이터(Test) 성능 지표 비교"
    )
    fig_compare.update_layout(yaxis_range=[0, 1.15], paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    fig_compare.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    st.plotly_chart(fig_compare, use_container_width=True)

    # 두 모델의 일반화 진단 결과
    col_diag_left, col_diag_right = st.columns(2)
    
    with col_diag_left:
        st.markdown("#### **🌲 Random Forest 일반화 진단**")
        rf_acc_gap = rf_metrics["train_acc"] - rf_metrics["test_acc"]
        rf_f1_gap = rf_metrics["train_f1"] - rf_metrics["test_f1"]
        if rf_metrics["train_acc"] < 0.70 and rf_metrics["test_acc"] < 0.70:
            st.warning("⚠️ **진단: 모델 과소적합 (Underfitting)**")
            st.markdown(f"학습({rf_metrics['train_acc']:.2%}) 및 테스트({rf_metrics['test_acc']:.2%}) 성능이 낮습니다. 트리 수나 깊이를 늘려주세요.")
        elif rf_acc_gap > 0.07 or rf_f1_gap > 0.08:
            st.error("🚨 **진단: 모델 과적합 (Overfitting)**")
            st.markdown(f"학습과 검증 격차({rf_acc_gap*100:.1f}%p)가 큽니다. 깊이를 제한하거나 최소 샘플 리프 설정을 적용해 보세요.")
        else:
            st.success("✅ **진단: 적정 일반화 (Good Generalization)**")
            st.markdown(f"두 셋의 점수 차이가 {rf_acc_gap*100:.1f}%p로 작아 새로운 유입 데이터를 안정적으로 분류합니다.")

    with col_diag_right:
        st.markdown("#### **🔥 Gradient Boosting 일반화 진단**")
        gb_acc_gap = gb_metrics["train_acc"] - gb_metrics["test_acc"]
        gb_f1_gap = gb_metrics["train_f1"] - gb_metrics["test_f1"]
        if gb_metrics["train_acc"] < 0.70 and gb_metrics["test_acc"] < 0.70:
            st.warning("⚠️ **진단: 모델 과소적합 (Underfitting)**")
            st.markdown(f"학습({gb_metrics['train_acc']:.2%}) 및 테스트({gb_metrics['test_acc']:.2%}) 성능이 낮습니다. 학습률을 올리거나 트리 개수를 증가시켜 보세요.")
        elif gb_acc_gap > 0.07 or gb_f1_gap > 0.08:
            st.error("🚨 **진단: 모델 과적합 (Overfitting)**")
            st.markdown(f"학습과 검증 격차({gb_acc_gap*100:.1f}%p)가 큽니다. 학습률을 낮추거나 트리 최대 깊이를 제한해 보세요.")
        else:
            st.success("✅ **진단: 적정 일반화 (Good Generalization)**")
            st.markdown(f"두 셋의 점수 차이가 {gb_acc_gap*100:.1f}%p로 안정적이며 강력한 성능을 내고 있습니다.")

    # 5. 분류 평가 곡선 시각화 (ROC & PR Curve)
    st.write("---")
    st.subheader("📈 3. 분류 평가 곡선 상세 비교 (검증 데이터 기준)")
    
    col_curve_left, col_curve_right = st.columns(2)
    
    # ROC Curve 다중 라인 그리기
    rf_fpr, rf_tpr, _ = roc_curve(y_test, rf_test_pred_proba)
    gb_fpr, gb_tpr, _ = roc_curve(y_test, gb_test_pred_proba)
    
    fig_roc = go.Figure()
    fig_roc.add_trace(go.Scatter(x=rf_fpr, y=rf_tpr, mode='lines', name=f'Random Forest (AUC = {rf_metrics["test_roc_auc"]:.4f})', line=dict(color='#3498db', width=3)))
    fig_roc.add_trace(go.Scatter(x=gb_fpr, y=gb_tpr, mode='lines', name=f'Gradient Boosting (AUC = {gb_metrics["test_roc_auc"]:.4f})', line=dict(color='#e74c3c', width=3)))
    fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Random Guess', line=dict(dash='dash', color='grey')))
    fig_roc.update_layout(
        title="ROC (Receiver Operating Characteristic) Curve 비교",
        xaxis_title="위양성률 (False Positive Rate)",
        yaxis_title="진양성률 (True Positive Rate)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0.5, y=0.1)
    )
    with col_curve_left:
        st.plotly_chart(fig_roc, use_container_width=True)
        
    # PR Curve 다중 라인 그리기
    rf_prec_val, rf_rec_val, _ = precision_recall_curve(y_test, rf_test_pred_proba)
    gb_prec_val, gb_rec_val, _ = precision_recall_curve(y_test, gb_test_pred_proba)
    
    fig_pr = go.Figure()
    fig_pr.add_trace(go.Scatter(x=rf_rec_val, y=rf_prec_val, mode='lines', name='Random Forest', line=dict(color='#3498db', width=3)))
    fig_pr.add_trace(go.Scatter(x=gb_rec_val, y=gb_prec_val, mode='lines', name='Gradient Boosting', line=dict(color='#e74c3c', width=3)))
    fig_pr.update_layout(
        title="Precision-Recall Curve 비교",
        xaxis_title="재현율 (Recall)",
        yaxis_title="정밀도 (Precision)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0.1, y=0.1)
    )
    with col_curve_right:
        st.plotly_chart(fig_pr, use_container_width=True)

    # 6. 피처 중요도 비교 시각화
    st.write("---")
    st.subheader("📊 4. 모델별 피처 중요도 (Feature Importance) 비교 분석")
    
    # 중요도 연산 및 데이터프레임 구축
    rf_importances = rf_model.feature_importances_
    gb_importances = gb_model.feature_importances_
    
    feat_imp_df = pd.DataFrame({
        "피처명": X.columns,
        "Random Forest": rf_importances,
        "Gradient Boosting": gb_importances
    })
    
    col_imp_left, col_imp_right = st.columns(2)
    
    with col_imp_left:
        rf_top = feat_imp_df[["피처명", "Random Forest"]].sort_values("Random Forest", ascending=True).tail(15)
        fig_rf_imp = px.bar(
            rf_top, x="Random Forest", y="피처명",
            orientation="h",
            title="Random Forest 피처 중요도 (상위 15개)",
            color="Random Forest",
            color_continuous_scale="Blues"
        )
        fig_rf_imp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_rf_imp, use_container_width=True)
        
    with col_imp_right:
        gb_top = feat_imp_df[["피처명", "Gradient Boosting"]].sort_values("Gradient Boosting", ascending=True).tail(15)
        fig_gb_imp = px.bar(
            gb_top, x="Gradient Boosting", y="피처명",
            orientation="h",
            title="Gradient Boosting 피처 중요도 (상위 15개)",
            color="Gradient Boosting",
            color_continuous_scale="Reds"
        )
        fig_gb_imp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gb_imp, use_container_width=True)

    # 7. 비즈니스 활용 인사이트 및 실행 액션 플랜
    st.write("---")
    st.subheader("🎯 5. 앙상블 예측 모델 기반 비즈니스 인사이트 및 실행 액션 플랜")
    
    # 가장 중요한 변수 추출
    top_rf_feature = feat_imp_df.sort_values("Random Forest", ascending=False).iloc[0]["피처명"]
    top_gb_feature = feat_imp_df.sort_values("Gradient Boosting", ascending=False).iloc[0]["피처명"]
    
    st.markdown(f"""
    단일 의사결정나무 모델의 과적합(Overfitting) 취약성을 극복하고 다수 모델의 의견을 통합하는 앙상블 기법(Random Forest, Gradient Boosting)을 적용함으로써, 실제 비즈니스 환경에서 작동 가능한 고도로 신뢰성 있는 예측 정보를 도출할 수 있습니다.
    
    #### **💡 1. 앙상블 모델 기반 비즈니스 인사이트**
    - **PageValues의 지배력 확인**: 두 모델 모두에서 **{top_rf_feature}** 및 **{top_gb_feature}**(주로 PageValues가 위치함)가 고객 구매 예측에 매우 중대한 기여를 하고 있습니다. 이는 앙상블 모델에서도 구매로 연결되는 세션은 페이지 가치의 흐름이 확연히 다르다는 통계적 안정성을 입증합니다.
    - **세분화된 사용자 행동의 식별력**: 부스팅 계열 모델의 경우 순차적인 오차 보정을 통해 단일 트리나 랜덤 포레스트가 놓치기 쉬운 미세한 변수 간 상호작용(예: 특정 OS나 브라우저를 사용하면서 이탈률이 소폭 높은 집단)까지 포착하여 분류 경계를 정교화합니다.
    - **예측의 안정성 향상**: 단일 디시전 트리는 데이터의 작은 변화에도 나무 구조가 완전히 바뀌어 마케팅 캠페인 타겟팅 대상 목록이 흔들리는 부작용이 있습니다. 반면 랜덤포레스트는 100개 이상의 독립적인 나무들의 평균을 활용하므로 마케팅 타겟 세그먼트의 안정적인 분류 및 모니터링이 가능합니다.

    #### **📋 2. 구체적인 비즈니스 액션 플랜 (Action Plan)**
    1. **망설이는 다수 고객(Probability 40% ~ 60%)을 겨냥한 한정 프로모션 자동화**
       - **원리**: 앙상블 모델이 산출한 예측 확률 값을 기반으로 타겟팅 정교화.
       - **실행**: 예측 확률이 80% 이상인 '확실한 구매군'에게는 불필요한 마케팅 비용 지출(쿠폰 남발)을 차단하여 마진을 보존합니다. 반면, 두 앙상블 모델 모두에서 구매 확률이 **40% ~ 60% 사이로 분류된 애매한 망설임군**에게 실시간으로 "마지막 재고 2개!" 알림이나 쿠폰 팝업을 노출하여 전환 비용(CAC) 대비 ROI를 대폭 개선합니다.
       
    2. **ExitRates(종료율) 감소를 위한 UI/UX 엔지니어링 리소스 효율적 분배**
       - **원리**: 피처 중요도 분석에서 BounceRates 및 ExitRates가 비중 높게 나타남.
       - **실행**: 피처 기여도가 높은 특정 페이지(상품 상세, 결제진입)의 종료 속도를 모니터링하고 최적화합니다. 특히, 모바일/데스크톱 기기별로 앙상블 모델 예측 결과에서 차이가 감지된다면 호환성 오류가 있는지 점검하여 결제 과정 상의 장애물을 즉각 해결합니다.
       
    3. **정밀 타겟 이탈방지 리마케팅 캠페인 운영**
       - **원리**: 재현율(Recall)을 극대화한 임계값 설정.
       - **실행**: 사이드바의 임계값(Threshold)을 하향 조정(예: 0.35)하여 구매 가능성이 조금이라도 있는 고객을 빠짐없이 잡아내도록 설정한 후, 이들에게 유도 광고나 뉴스레터, 카카오톡 알림톡을 발송하여 이탈 후 고객의 재방문을 견인합니다.
    """)


# 데이터 불러오기
try:
    df = load_data()
    data_load_success = True
except Exception as e:
    data_load_success = False
    error_msg = str(e)

# 스타일 정의 (일관된 컬러 팔레트 사용)
COLOR_TRUE = "#2ecc71"   # 구매 완료 (초록색 계열)
COLOR_FALSE = "#e74c3c"  # 미구매 (빨간색 계열)
COLOR_MAP = {"구매 완료 (True)": COLOR_TRUE, "미구매 (False)": COLOR_FALSE}
COLOR_LIST = [COLOR_FALSE, COLOR_TRUE]

# --- 페이지 네비게이션 ---
st.sidebar.title("🧭 페이지 선택")
app_page = st.sidebar.radio(
    "이동할 대시보드 페이지를 선택하세요:",
    ["📊 데이터 분석 대시보드", "🤖 구매 예측 머신러닝 모델", "🌲 앙상블 모델 예측 (RF & Boosting)"]
)

# 1. 머신러닝 예측 모델 페이지 분기
if app_page == "🤖 구매 예측 머신러닝 모델":
    if data_load_success:
        render_machine_learning_page(df)
    else:
        st.error(f"데이터를 불러오는 데 실패하여 머신러닝 분석을 수행할 수 없습니다. 에러: {error_msg}")
    st.stop()

# 2. 앙상블 모델 예측 페이지 분기
elif app_page == "🌲 앙상블 모델 예측 (RF & Boosting)":
    if data_load_success:
        render_ensemble_ml_page(df)
    else:
        st.error(f"데이터를 불러오는 데 실패하여 머신러닝 분석을 수행할 수 없습니다. 에러: {error_msg}")
    st.stop()

# 2. 기존 데이터 분석 대시보드 페이지 타이틀 및 설명
st.title("🛍️ 온라인 쇼핑몰 고객 구매 의도 분석 대시보드")
st.markdown("본 대시보드는 고객 세션 데이터를 바탕으로 **구매 완료 여부(Revenue)**에 따라 고객들의 행동 및 환경 변수들이 어떻게 달라지는지 통계적으로 분석하고 시각화합니다.")

if not data_load_success:
    st.error(f"데이터를 불러오는 데 실패했습니다. 에러 메시지: {error_msg}")
    st.info("인터넷 연결을 확인하거나 데이터 주소 정합성을 점검해 주세요.")
else:
    # 데이터 요약 통계 미리 준비
    total_sessions = len(df)
    purchased_sessions = df['Revenue'].sum()
    non_purchased_sessions = total_sessions - purchased_sessions
    conversion_rate = (purchased_sessions / total_sessions) * 100

    # 변수 목록 구분
    num_cols = [
        "Administrative", "Administrative_Duration", 
        "Informational", "Informational_Duration", 
        "ProductRelated", "ProductRelated_Duration", 
        "BounceRates", "ExitRates", "PageValues", "SpecialDay"
    ]
    
    cat_cols = [
        "Month", "OperatingSystems", "Browser", 
        "Region", "TrafficType", "VisitorType", "Weekend"
    ]

    # --- 사이드바 영역 ---
    st.sidebar.header("📊 데이터 요약 및 진단")
    st.sidebar.markdown(f"**전체 데이터 수**: {total_sessions:,} 행")
    st.sidebar.markdown(f"**변수 개수**: {df.shape[1]} 개")
    
    # 결측치 및 중복 진단
    null_counts = df.isnull().sum().sum()
    duplicate_counts = df.duplicated().sum()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 데이터 무결성 체크")
    if null_counts == 0:
        st.sidebar.success("✅ 결측치 없음")
    else:
        st.sidebar.warning(f"⚠️ 결측치 총 {null_counts}개 발견")
        
    if duplicate_counts == 0:
        st.sidebar.success("✅ 중복 데이터 없음")
    else:
        # 중복 제거 옵션 제공
        st.sidebar.warning(f"⚠️ 중복 데이터 {duplicate_counts}행 발견")
        remove_dup = st.sidebar.checkbox("중복 데이터 제거 후 분석 진행")
        if remove_dup:
            df = df.drop_duplicates().reset_index(drop=True)
            # 수치 다시 연산
            total_sessions = len(df)
            purchased_sessions = df['Revenue'].sum()
            non_purchased_sessions = total_sessions - purchased_sessions
            conversion_rate = (purchased_sessions / total_sessions) * 100

    st.sidebar.markdown("---")
    st.sidebar.markdown("💡 **Tip**: 각 그래프 위로 마우스를 가져가면 툴팁을 통해 상세 통계 수치를 확인하실 수 있습니다.")

    # --- KPI 요약 카드 (최상단) ---
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("총 방문 세션 수", f"{total_sessions:,} 건")
    with kpi_cols[1]:
        st.metric("구매 세션 수 (Revenue = True)", f"{purchased_sessions:,} 건", delta_color="normal")
    with kpi_cols[2]:
        st.metric("미구매 세션 수 (Revenue = False)", f"{non_purchased_sessions:,} 건")
    with kpi_cols[3]:
        st.metric("평균 구매 전환율", f"{conversion_rate:.2f} %", delta=f"{conversion_rate - 15:.2f}% (기준값 15% 대비)", delta_color="normal")

    # 메인 콘텐츠 영역 탭 설계
    tab1, tab2, tab_funnel, tab3 = st.tabs([
        "🔢 수치형 변수 & Revenue 분석", 
        "🔤 범주형 변수 & Revenue 분석", 
        "🌪️ 쇼핑몰 고객 퍼널 분석",
        "🔍 개별 변수 심층 분석 & 통계 검정"
    ])

    # ==================== Tab 1: 수치형 변수 분석 ====================
    with tab1:
        st.header("🔢 수치형 변수 분포 비교 (Revenue 기준)")
        st.markdown("""
        이 탭에서는 쇼핑몰 세션 내 수치형 행동 변수 10가지가 **구매 완료 여부(Revenue)**에 따라 어떻게 다르게 분포하는지 시각화하고 요약 통계를 제공합니다.
        * **시각화**: 각 수치형 변수별로 **상단 박스플롯(Box Plot) + 하단 히스토그램(Histogram) 서브플롯**을 구성하여 두 집단의 분포 차이 및 이상치를 통합적으로 비교합니다.
        * **기술 통계**: 시각화 바로 아래 배치된 표를 통해 평균, 중앙값, 표준편차, 왜도, 첨도 등을 직접 비교할 수 있습니다.
        """)
        
        # 분석할 수치형 변수 선택 (멀티셀렉트)
        selected_num_cols = st.multiselect(
            "시각화 및 기술통계를 확인할 수치형 변수들을 선택하세요 (다중 선택 가능):", 
            num_cols, 
            default=["PageValues", "ProductRelated_Duration", "BounceRates", "ExitRates"],
            key="num_cols_multiselect"
        )
        
        if not selected_num_cols:
            st.warning("분석할 수치형 변수를 최소 하나 이상 선택해 주세요.")
        else:
            for col in selected_num_cols:
                st.write("---")
                st.subheader(f"📊 {col} 분포 및 기술통계")
                
                # Box Plot(위, 수평) & Histogram(아래) 통합 서브플롯 생성
                fig_num = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    row_heights=[0.3, 0.7],
                    vertical_spacing=0.08
                )
                
                # 1. Box Plot 추가 (수평 방향, orientation='h')
                fig_num.add_trace(
                    go.Box(
                        x=df[df['Revenue'] == False][col],
                        name="미구매 (False)",
                        marker_color=COLOR_FALSE,
                        orientation='h',
                        boxpoints="suspectedoutliers",
                        legendgroup="False",
                        showlegend=True
                    ),
                    row=1, col=1
                )
                fig_num.add_trace(
                    go.Box(
                        x=df[df['Revenue'] == True][col],
                        name="구매 완료 (True)",
                        marker_color=COLOR_TRUE,
                        orientation='h',
                        boxpoints="suspectedoutliers",
                        legendgroup="True",
                        showlegend=True
                    ),
                    row=1, col=1
                )
                
                # 2. Histogram 추가 (밀도 분석을 위해 겹침)
                fig_num.add_trace(
                    go.Histogram(
                        x=df[df['Revenue'] == False][col],
                        name="미구매 (False)",
                        marker_color=COLOR_FALSE,
                        opacity=0.6,
                        legendgroup="False",
                        showlegend=False,
                        nbinsx=50
                    ),
                    row=2, col=1
                )
                fig_num.add_trace(
                    go.Histogram(
                        x=df[df['Revenue'] == True][col],
                        name="구매 완료 (True)",
                        marker_color=COLOR_TRUE,
                        opacity=0.6,
                        legendgroup="True",
                        showlegend=False,
                        nbinsx=50
                    ),
                    row=2, col=1
                )
                
                fig_num.update_layout(
                    height=450,
                    barmode="overlay", # 겹치기
                    margin=dict(l=20, r=20, t=10, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig_num.update_yaxes(title_text="집단", row=1, col=1)
                fig_num.update_yaxes(title_text="세션 빈도 (Count)", row=2, col=1)
                fig_num.update_xaxes(title_text=col, row=2, col=1)
                
                st.plotly_chart(fig_num, use_container_width=True)
                
                # 3. 기술통계 요약 테이블 생성 및 출력
                stat_df = df.groupby('Revenue_Str')[col].agg(
                    Count='count',
                    Mean='mean',
                    Median='median',
                    Std='std',
                    Min='min',
                    Max='max',
                    Skewness=lambda x: x.skew(),
                    Kurtosis=lambda x: x.kurtosis()
                ).round(4)
                
                # 컬럼 이름 한국어로 변경
                stat_df.columns = ["샘플 수 (건)", "평균 (Mean)", "중앙값 (Median)", "표준편차 (Std)", "최솟값 (Min)", "최댓값 (Max)", "왜도 (Skewness)", "첨도 (Kurtosis)"]
                
                st.write("**📋 그룹별 기술통계 비교**")
                st.dataframe(stat_df, use_container_width=True)
                
                # 인사이트 해석 텍스트
                mean_false = stat_df.loc["미구매 (False)", "평균 (Mean)"]
                mean_true = stat_df.loc["구매 완료 (True)", "평균 (Mean)"]
                diff_ratio = ((mean_true - mean_false) / mean_false * 100) if mean_false != 0 else 0
                
                st.markdown(f"**📝 {col} 통계 분석 요약**")
                if diff_ratio > 0:
                    st.write(f"- **구매 완료 세션**의 평균({mean_true:.3f})이 미구매 세션({mean_false:.3f})보다 **약 {diff_ratio:.1f}% 더 높게** 분포합니다.")
                elif diff_ratio < 0:
                    st.write(f"- **구매 완료 세션**의 평균({mean_true:.3f})이 미구매 세션({mean_false:.3f})보다 **약 {abs(diff_ratio):.1f}% 더 낮게** 분포합니다.")
                else:
                    st.write(f"- 두 집단의 평균값 차이가 미미합니다.")
                
                # 중앙값 비교 부가 설명
                median_false = stat_df.loc["미구매 (False)", "중앙값 (Median)"]
                median_true = stat_df.loc["구매 완료 (True)", "중앙값 (Median)"]
                st.write(f"- **중앙값 편차**: 구매 완료 세션의 중앙값은 **{median_true:.3f}**이며, 미구매 세션의 중앙값은 **{median_false:.3f}**입니다.")

    # ==================== Tab 2: 범주형 변수 분석 ====================
    with tab2:
        st.header("🔤 범주형 변수 분포 비교 (Revenue 기준)")
        st.markdown("""
        이 탭에서는 방문 고객의 시스템 환경이나 세션 속성을 나타내는 범주형 변수 7가지와 **구매 완료 여부(Revenue)**의 관계를 비교 분석합니다.
        * **서브플롯 1 (빈도 비교)**: 각 범주별 실제 방문 세션의 구매 완료/미구매 빈도(Count)를 비교합니다.
        * **서브플롯 2 (비율 비교)**: 각 막대의 높이를 100%로 통일하여 각 범주별 구매 완료/미구매 비율(Percentage)을 직관적으로 비교합니다.
        * **교차표**: 하단 표를 통해 실제 빈도 수와 세부 비율 값을 상세히 검토할 수 있습니다.
        """)
        
        # 1. 빈도 비교 서브플롯 (4x2 Subplots)
        st.subheader("📊 1. 범주별 방문 빈도 비교 (Count)")
        fig_cat = make_subplots(
            rows=4, cols=2,
            subplot_titles=[f"<b>{col} 빈도</b>" for col in cat_cols],
            horizontal_spacing=0.08,
            vertical_spacing=0.15
        )
        
        for idx, col in enumerate(cat_cols):
            row = (idx // 2) + 1
            col_idx = (idx % 2) + 1
            
            grouped = df.groupby([col, 'Revenue_Str']).size().unstack(fill_value=0)
            
            if len(grouped) > 15:
                top_categories = df[col].value_counts().nlargest(15).index
                grouped = grouped.loc[grouped.index.isin(top_categories)]
            
            fig_cat.add_trace(
                go.Bar(
                    x=grouped.index.astype(str),
                    y=grouped.get("미구매 (False)", pd.Series(0, index=grouped.index)),
                    name="미구매 (False)",
                    marker_color=COLOR_FALSE,
                    showlegend=(idx == 0),
                    legendgroup="FalseCat",
                ),
                row=row, col=col_idx
            )
            
            fig_cat.add_trace(
                go.Bar(
                    x=grouped.index.astype(str),
                    y=grouped.get("구매 완료 (True)", pd.Series(0, index=grouped.index)),
                    name="구매 완료 (True)",
                    marker_color=COLOR_TRUE,
                    showlegend=(idx == 0),
                    legendgroup="TrueCat",
                ),
                row=row, col=col_idx
            )
            
            fig_cat.update_xaxes(type='category', row=row, col=col_idx)

        fig_cat.update_layout(
            height=900,
            margin=dict(l=20, r=20, t=50, b=20),
            barmode="group",
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_cat, use_container_width=True)
        
        st.write("---")
        
        # 2. 비율 비교 서브플롯 (4x2 Subplots, 100% Stacked Bar)
        st.subheader("📈 2. 범주별 구매 전환 비율 비교 (100% Stacked)")
        fig_cat_ratio = make_subplots(
            rows=4, cols=2,
            subplot_titles=[f"<b>{col} 구매율 비중</b>" for col in cat_cols],
            horizontal_spacing=0.08,
            vertical_spacing=0.15
        )
        
        for idx, col in enumerate(cat_cols):
            row = (idx // 2) + 1
            col_idx = (idx % 2) + 1
            
            grouped = df.groupby([col, 'Revenue_Str']).size().unstack(fill_value=0)
            
            if len(grouped) > 15:
                top_categories = df[col].value_counts().nlargest(15).index
                grouped = grouped.loc[grouped.index.isin(top_categories)]
            
            # 비율로 정규화 (100% 기준)
            grouped_ratio = grouped.div(grouped.sum(axis=1), axis=0) * 100
            
            fig_cat_ratio.add_trace(
                go.Bar(
                    x=grouped_ratio.index.astype(str),
                    y=grouped_ratio.get("미구매 (False)", pd.Series(0, index=grouped_ratio.index)),
                    name="미구매 (False)",
                    marker_color=COLOR_FALSE,
                    showlegend=(idx == 0),
                    legendgroup="FalseRatio",
                ),
                row=row, col=col_idx
            )
            
            fig_cat_ratio.add_trace(
                go.Bar(
                    x=grouped_ratio.index.astype(str),
                    y=grouped_ratio.get("구매 완료 (True)", pd.Series(0, index=grouped_ratio.index)),
                    name="구매 완료 (True)",
                    marker_color=COLOR_TRUE,
                    showlegend=(idx == 0),
                    legendgroup="TrueRatio",
                ),
                row=row, col=col_idx
            )
            
            fig_cat_ratio.update_xaxes(type='category', row=row, col=col_idx)
            fig_cat_ratio.update_yaxes(range=[0, 100], row=row, col=col_idx)

        fig_cat_ratio.update_layout(
            height=900,
            margin=dict(l=20, r=20, t=50, b=20),
            barmode="stack", # 누적 막대 그래프
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_cat_ratio, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 범주형 변수별 Revenue 교차표 및 구매율 비교")
        
        selected_cat_col = st.selectbox("교차 요약표를 확인하고 비교할 변수를 선택하세요:", cat_cols, key="cat_stat_select")
        
        # 교차표 생성 (빈도)
        crosstab_count = pd.crosstab(df[selected_cat_col], df['Revenue_Str'])
        
        # 교차표 생성 (비율 - 행 기준 백분율)
        crosstab_ratio = pd.crosstab(df[selected_cat_col], df['Revenue_Str'], normalize='index') * 100
        
        # 두 표를 합치기 위해 준비
        crosstab_combined = pd.DataFrame(index=crosstab_count.index)
        crosstab_combined['미구매 (빈도)'] = crosstab_count.get("미구매 (False)", 0)
        crosstab_combined['구매 완료 (빈도)'] = crosstab_count.get("구매 완료 (True)", 0)
        crosstab_combined['합계 (빈도)'] = crosstab_combined['미구매 (빈도)'] + crosstab_combined['구매 완료 (빈도)']
        crosstab_combined['미구매 비율 (%)'] = crosstab_ratio.get("미구매 (False)", 0).round(2)
        crosstab_combined['구매 완료 비율 (%)'] = crosstab_ratio.get("구매 완료 (True)", 0).round(2)
        
        # 총계 행 추가
        total_row = pd.Series({
            '미구매 (빈도)': non_purchased_sessions,
            '구매 완료 (빈도)': purchased_sessions,
            '합계 (빈도)': total_sessions,
            '미구매 비율 (%)': round((non_purchased_sessions / total_sessions) * 100, 2),
            '구매 완료 비율 (%)': round((purchased_sessions / total_sessions) * 100, 2)
        }, name='전체 (Total)')
        
        crosstab_combined = pd.concat([crosstab_combined, total_row.to_frame().T])
        
        st.dataframe(crosstab_combined, use_container_width=True)
        
        # 인사이트 해석 텍스트
        st.markdown(f"#### 💡 **{selected_cat_col}** 변수 교차분석 해석")
        # 가장 구매율이 높은 카테고리 찾아보기 (전체 행 제외)
        temp_df = crosstab_combined.drop('전체 (Total)', errors='ignore')
        # 데이터가 일정 수 이상 되는 신뢰성 있는 범주만 필터 (총 빈도가 전체 평균의 10% 이상인 경우만)
        min_sample = total_sessions * 0.02
        reliable_df = temp_df[temp_df['합계 (빈도)'] >= min_sample]
        
        if not reliable_df.empty:
            max_purch_cat = reliable_df['구매 완료 비율 (%)'].idxmax()
            max_purch_val = reliable_df.loc[max_purch_cat, '구매 완료 비율 (%)']
            st.write(f"- 세션 수가 일정 수준(전체의 2%인 {int(min_sample)}건 이상) 보장되는 범주 중, 가장 높은 구매 전환율을 기록한 그룹은 **'{max_purch_cat}'** 이며, 전환율은 **{max_purch_val:.2f}%** 입니다.")
            st.write(f"- 이는 전체 평균 구매 전환율인 **{conversion_rate:.2f}%** 대비 통계적/비즈니스적으로 주목할 만한 차이입니다.")
        else:
            st.write(f"- 범주 내 데이터 분포가 너무 작게 쪼개져 있어 개별 특징 해석 시 샘플 크기에 유의해야 합니다.")

    # ==================== Tab: 퍼널 분석 (Funnel Analysis) ====================
    with tab_funnel:
        st.header("🌪️ 쇼핑몰 고객 행동 퍼널 분석")
        st.markdown("""
        웹 쇼핑몰 고객의 유입부터 최종 구매 완료(Revenue = True)까지의 단계를 퍼널로 정의하고,
        각 단계별 전환율(Conversion Rate)과 이탈률(Drop-out Rate)을 분석합니다.
        
        **쇼핑몰 고객 여정 퍼널(Funnel) 단계 정의**:
        1. **1단계: 전체 방문 (All Sessions)** - 쇼핑몰에 유입된 전체 세션
        2. **2단계: 제품 탐색 (Product Detail View)** - 제품 상세 페이지를 1회 이상 방문한 세션 (`ProductRelated > 0`)
        3. **3단계: 가치 탐색 (High PageValue View)** - 장바구니 추가 등 구매 의도가 높은 페이지 가치가 발생한 세션 (`PageValues > 0`)
        4. **4단계: 구매 완료 (Purchase Completion)** - 최종 결제 및 구매가 완료된 세션 (`Revenue == True`)
        """)
        
        # 1. 전체 퍼널 데이터 계산
        step1_all = len(df)
        step2_prod = len(df[df['ProductRelated'] > 0])
        step3_val = len(df[(df['ProductRelated'] > 0) & (df['PageValues'] > 0)])
        step4_rev = len(df[(df['ProductRelated'] > 0) & (df['PageValues'] > 0) & (df['Revenue'] == True)])
        
        funnel_data = pd.DataFrame({
            "단계": ["1. 전체 방문", "2. 제품 탐색", "3. 가치 탐색", "4. 구매 완료"],
            "세션 수": [step1_all, step2_prod, step3_val, step4_rev]
        })
        
        # 2. 세그먼트별 비교 (VisitorType: New vs Returning)
        # New Visitor 데이터
        df_new = df[df['VisitorType'] == 'New_Visitor']
        step1_new = len(df_new)
        step2_new = len(df_new[df_new['ProductRelated'] > 0])
        step3_new = len(df_new[(df_new['ProductRelated'] > 0) & (df_new['PageValues'] > 0)])
        step4_new = len(df_new[(df_new['ProductRelated'] > 0) & (df_new['PageValues'] > 0) & (df_new['Revenue'] == True)])
        
        # Returning Visitor 데이터
        df_ret = df[df['VisitorType'] == 'Returning_Visitor']
        step1_ret = len(df_ret)
        step2_ret = len(df_ret[df_ret['ProductRelated'] > 0])
        step3_ret = len(df_ret[(df_ret['ProductRelated'] > 0) & (df_ret['PageValues'] > 0)])
        step4_ret = len(df_ret[(df_ret['ProductRelated'] > 0) & (df_ret['PageValues'] > 0) & (df_ret['Revenue'] == True)])
        
        # 시각화 레이아웃 선택
        funnel_view = st.radio("퍼널 분석 보기를 선택하세요:", ["전체 고객 퍼널", "신규 vs 재방문자 퍼널 비교"], horizontal=True, key="funnel_view_select")
        
        if funnel_view == "전체 고객 퍼널":
            fig_funnel = go.Figure(go.Funnel(
                y=funnel_data["단계"],
                x=funnel_data["세션 수"],
                textinfo="value+percent initial+percent previous",
                marker={"color": ["#34495e", "#3498db", "#f1c40f", "#2ecc71"]},
                connector={"line": {"color": "#bdc3c7", "width": 2}}
            ))
            fig_funnel.update_layout(
                title_text="전체 유입 고객 여정 퍼널",
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_funnel, use_container_width=True)
        else:
            fig_funnel_comp = go.Figure()
            
            fig_funnel_comp.add_trace(go.Funnel(
                name="신규 방문자 (New Visitor)",
                y=["1. 전체 방문", "2. 제품 탐색", "3. 가치 탐색", "4. 구매 완료"],
                x=[step1_new, step2_new, step3_new, step4_new],
                textinfo="value+percent initial+percent previous",
                marker={"color": ["#2c3e50", "#2980b9", "#d35400", "#27ae60"]},
                connector={"line": {"color": "#bdc3c7", "width": 1.5}}
            ))
            
            fig_funnel_comp.add_trace(go.Funnel(
                name="재방문자 (Returning Visitor)",
                y=["1. 전체 방문", "2. 제품 탐색", "3. 가치 탐색", "4. 구매 완료"],
                x=[step1_ret, step2_ret, step3_ret, step4_ret],
                textinfo="value+percent initial+percent previous",
                marker={"color": ["#7f8c8d", "#95a5a6", "#f39c12", "#2ecc71"]},
                connector={"line": {"color": "#bdc3c7", "width": 1.5}}
            ))
            
            fig_funnel_comp.update_layout(
                title_text="방문자 세그먼트별 퍼널 비교",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
              )
            st.plotly_chart(fig_funnel_comp, use_container_width=True)
        
        st.subheader("📋 퍼널 단계별 전환 및 이탈 요약 표")
        
        summary_df = pd.DataFrame(index=["1. 전체 방문", "2. 제품 탐색", "3. 가치 탐색", "4. 구매 완료"])
        summary_df["전체 세션 수"] = [step1_all, step2_prod, step3_val, step4_rev]
        summary_df["신규 방문자"] = [step1_new, step2_new, step3_new, step4_new]
        summary_df["재방문자"] = [step1_ret, step2_ret, step3_ret, step4_ret]
        
        summary_df["전체 대비 최종 전환율 (%)"] = (summary_df["전체 세션 수"] / step1_all * 100).round(2)
        summary_df["이전 단계 대비 전환율 (%)"] = [
            100.0,
            round(step2_prod / step1_all * 100, 2),
            round(step3_val / step2_prod * 100, 2),
            round(step4_rev / step3_val * 100, 2)
        ]
        
        st.dataframe(summary_df, use_container_width=True)
        
        st.subheader("💡 퍼널 단계별 비즈니스 해석 및 개선 전략 가이드")
        st.markdown("""
        #### **Step 1 ➔ Step 2: 제품 탐색 단계 (유입 후 이탈 분석)**
        - **현황**: 전체 방문자 중 대부분(99% 이상)이 제품 상세 페이지(`ProductRelated > 0`)를 조회합니다. 이는 웹사이트에 유입된 사용자의 탐색 목적이 뚜렷함을 의미합니다.
        - **개선안**: 유입 후 첫 페이지에서 제품 목록으로의 매끄러운 유도가 이미 잘 구축되어 있습니다. 메인 랜딩 페이지 최적화보다는 다음 단계(장바구니)로 유도하는 것이 시급합니다.
        
        #### **Step 2 ➔ Step 3: 가치 탐색 단계 (핵심 이탈 병목 구간 ⚠️)**
        - **현황**: 제품 상세를 조회한 고객 중 **상당수(약 80% 이상)가 구매 의도가 높은 가치 페이지(`PageValues > 0`) 도달 전에 이탈**합니다. 이 단계는 전체 쇼핑몰 여정 중 가장 큰 병목 구간입니다.
        - **개선안**:
          - 제품 상세 페이지 내 **장바구니 담기(CTA) 버튼의 시각적 강조** 및 위치 최적화가 필요합니다.
          - 상세 페이지 로딩 속도를 점검하고, 리뷰 및 신뢰성 정보를 상단에 배치하여 구매 의사결정을 가속화해야 합니다.
          - 이탈을 고민하는 고객에게 실시간 할인 쿠폰이나 한정 수량 알림 등의 트리거(Trigger) 마케팅 팝업 제공을 고려하십시오.
        
        #### **Step 3 ➔ Step 4: 최종 구매 완료 단계 (결제 전환 분석)**
        - **현황**: 장바구니/고가치 페이지에 도달한 고객 중 **약 50% 내외가 실제 최종 구매 완료(`Revenue == True`)에 성공**합니다.
        - **개선안**:
          - 일단 페이지 가치를 확보한 세션은 구매로 이어질 확률이 매우 높습니다.
          - 이 단계에서 절반 가량이 이탈하는 주된 원인은 **복잡한 결제 프로세스, 예상치 못한 추가 비용(배송비 등), 회원가입 요구** 등입니다.
          - 간편결제 시스템(네이버페이, 카카오페이 등) 도입, 비회원 결제 허용, 결제 페이지 정보 단순화를 통해 결제 완료율을 끌어올려야 합니다.
          - 결제 페이지를 이탈한 고객들을 대상으로 장바구니 미결제 상품 리타게팅 광고(이메일, 카카오톡 알림톡 등)를 수행하는 것이 극도로 효과적입니다.
          
        #### **👥 신규 vs 재방문자 세그먼트 비교 분석**
        - **신규 방문자(New Visitor)**는 재방문자보다 평균 구매 전환율이 높은 경향을 보일 수 있으나, 탐색 세션 비중이 작을 수 있습니다.
        - **재방문자(Returning Visitor)**는 대량의 유입 수를 차지하나, 목적 없는 브라우징(단순 탐색 후 이탈) 비중 또한 높을 수 있습니다. 두 그룹에 대한 개인화 마케팅(신규 고객 웰컴 쿠폰 vs 재방문 고객 적립금 혜택 등)을 다르게 집행하여 각 병목을 완화해야 합니다.
        """)

    # ==================== Tab 3: 개별 변수 심층 분석 ====================
    with tab3:
        st.header("🔍 개별 변수 심층 분석 및 통계적 가설 검정")
        st.markdown("""
        분석하고자 하는 특정 변수를 1개 선택하여 상세 분포를 뜯어보고, 
        두 집단(구매 완료 vs 미구매) 간 통계적으로 유의미한 차이가 실제로 존재하는지 가설 검정을 통해 증명합니다.
        """)
        
        # 단일 변수 선택 셀렉트박스
        all_variables = num_cols + cat_cols
        selected_var = st.selectbox("심층 분석 및 통계 검정을 수행할 변수를 선택하세요:", all_variables, index=8) # 기본 PageValues
        
        col_left, col_right = st.columns([3, 2])
        
        if selected_var in num_cols:
            # --- 수치형 변수 심층 분석 ---
            with col_left:
                st.subheader(f"📊 {selected_var} 분포 상세 시각화 (Violin Plot)")
                fig_detail = px.violin(
                    df, y=selected_var, x="Revenue_Str", color="Revenue_Str",
                    box=True, points="outliers",
                    color_discrete_map=COLOR_MAP,
                    title=f"Revenue 여부에 따른 {selected_var} 바이올린 플롯"
                )
                fig_detail.update_layout(
                    xaxis_title="구매 여부",
                    yaxis_title=selected_var,
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_detail, use_container_width=True)
                
            with col_right:
                st.subheader("🔬 독립표본 T-검정 (Two-sample T-test) 결과")
                st.markdown(f"**{selected_var}**의 평균이 구매 집단과 미구매 집단 간에 진짜 다른지 검정합니다.")
                
                group_false = df[df['Revenue'] == False][selected_var]
                group_true = df[df['Revenue'] == True][selected_var]
                
                mean_f = group_false.mean()
                mean_t = group_true.mean()
                
                st.write(f"- **미구매 세션 평균**: {mean_f:.4f}")
                st.write(f"- **구매 세션 평균**: {mean_t:.4f}")
                st.write(f"- **두 집단 간 평균 차이**: {abs(mean_t - mean_f):.4f}")
                
                if scipy_available:
                    # t-test 수행 (등분산성 비가정인 Welch's t-test 수행하여 안정성 확보)
                    t_stat, p_val = stats.ttest_ind(group_true, group_false, equal_var=False)
                    p_val_str = f"{p_val:.4e}" if p_val < 0.0001 else f"{p_val:.4f}"
                    
                    st.info(f"**Welch's T-통계량**: {t_stat:.4f}")
                    st.info(f"**P-value (유의확률)**: {p_val_str}")
                    
                    st.markdown("**🔍 검정 결과 해석:**")
                    if p_val < 0.05:
                        st.success(f"**유의수준 5%에서 귀무가설을 기각합니다.**")
                        st.markdown(f"통계적으로 구매 완료 집단과 미구매 집단의 **{selected_var}** 평균에는 **유의미한 차이가 존재합니다**.")
                    else:
                        st.warning(f"**유의수준 5%에서 귀무가설을 기각하지 못합니다.**")
                        st.markdown(f"통계적으로 구매 완료 집단과 미구매 집단의 **{selected_var}** 평균에는 **유의미한 차이가 없다고 볼 수 있습니다**.")
                else:
                    st.warning("`scipy` 라이브러리가 설치되지 않아 통계 검정 값을 자동 계산할 수 없습니다. 수동으로 환경에 scipy를 추가 설치하면 사용이 가능합니다.")
                    
        else:
            # --- 범주형 변수 심층 분석 ---
            with col_left:
                st.subheader(f"📊 {selected_var} 누적 백분율 시각화 (100% Stacked Bar)")
                # 백분율 계산을 위한 피벗 테이블
                temp_ct = pd.crosstab(df[selected_var], df['Revenue_Str'], normalize='index') * 100
                temp_ct = temp_ct.reset_index()
                
                fig_detail = px.bar(
                    temp_ct, x=selected_var, y=['미구매 (False)', '구매 완료 (True)'],
                    title=f"{selected_var} 카테고리별 구매 전환율 비중",
                    color_discrete_sequence=[COLOR_FALSE, COLOR_TRUE],
                    labels={"value": "비율 (%)", "variable": "구매 여부"}
                )
                fig_detail.update_layout(
                    xaxis_title=selected_var,
                    yaxis_title="비중 (%)",
                    barmode="stack",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_detail, use_container_width=True)
                
            with col_right:
                st.subheader("🔬 카이제곱 독립성 검정 (Chi-square Test) 결과")
                st.markdown(f"**{selected_var}**의 카테고리 분포와 **Revenue** 변수 간에 유의미한 연관성이 있는지 검정합니다.")
                
                # 교차표 생성
                ct = pd.crosstab(df[selected_var], df['Revenue'])
                
                st.write("**교차표 데이터 (구매 여부 빈도):**")
                st.write(ct)
                
                if scipy_available:
                    # 카이제곱 검정 수행
                    chi2, p_val, dof, expected = stats.chi2_contingency(ct)
                    p_val_str = f"{p_val:.4e}" if p_val < 0.0001 else f"{p_val:.4f}"
                    
                    st.info(f"**카이제곱(χ²) 통계량**: {chi2:.4f}")
                    st.info(f"**P-value (유의확률)**: {p_val_str}")
                    st.info(f"**자유도 (df)**: {dof}")
                    
                    st.markdown("**🔍 검정 결과 해석:**")
                    if p_val < 0.05:
                        st.success(f"**유의수준 5%에서 귀무가설을 기각합니다.**")
                        st.markdown(f"통계적으로 **{selected_var}** 변수와 구매 완료(Revenue) 변수 간에는 **밀접한 상관관계(연관성)가 존재합니다**.")
                    else:
                        st.warning(f"**유의수준 5%에서 귀무가설을 기각하지 못합니다.**")
                        st.markdown(f"통계적으로 **{selected_var}** 변수와 구매 완료(Revenue) 변수 간에는 **유의미한 연관성이 발견되지 않았습니다**.")
                else:
                    st.warning("`scipy` 라이브러리가 설치되지 않아 통계 검정 값을 자동 계산할 수 없습니다. 수동으로 환경에 scipy를 추가 설치하면 사용이 가능합니다.")
