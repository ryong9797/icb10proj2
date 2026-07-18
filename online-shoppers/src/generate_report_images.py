"""
online_shoppers_intention.csv 데이터를 바탕으로 EDA 분석 차트와 머신러닝(의사결정나무, 랜덤포레스트, 그라디언트 부스팅)
모델의 학습/평가 성능 그래프를 Matplotlib 및 koreanize-matplotlib을 사용하여 PNG 이미지로 자동 추출하는 스크립트입니다.
추출된 이미지들은 online-shoppers/images/ 디렉토리에 저장되어 마크다운 분석 리포트에 임베드됩니다.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve
)

# 경로 설정
DATA_PATH = os.path.join("online-shoppers", "data", "online_shoppers_intention.csv")
IMAGE_DIR = os.path.join("online-shoppers", "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# 1. 데이터 로드 및 가공
print("1. 데이터를 로드하고 있습니다...")
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"데이터 파일이 존재하지 않습니다: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)
df['Revenue_Str'] = df['Revenue'].map({True: '구매 완료 (True)', False: '미구매 (False)'})
df['Weekend_Str'] = df['Weekend'].map({True: '주말 (True)', False: '평일 (False)'})

# 그래프 스타일 전역 설정
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'NanumGothic' if 'NanumGothic' in plt.rcParams['font.sans-serif'] else plt.rcParams['font.family']
plt.rcParams['axes.unicode_minus'] = False

# ----------------------------------------------------
# 2. EDA 이미지 생성
# ----------------------------------------------------
print("2. EDA 시각화 이미지를 생성하고 있습니다...")

# 2-1. 수치형 주요 피처 분포 (Boxplot & Histogram)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
numeric_cols = ["PageValues", "ProductRelated_Duration", "BounceRates", "ExitRates"]
titles = ["페이지 가치 (PageValues) 분포", "제품 페이지 체류 시간 분포", "이탈률 (BounceRates) 분포", "종료율 (ExitRates) 분포"]

for idx, col in enumerate(numeric_cols):
    ax = axes[idx // 2, idx % 2]
    # Revenue 여부에 따른 Boxplot
    data_to_plot = [df[df['Revenue'] == False][col], df[df['Revenue'] == True][col]]
    ax.boxplot(data_to_plot, labels=['미구매 (False)', '구매완료 (True)'], patch_artist=True,
               boxprops=dict(facecolor='#f8d7da', color='#dc3545'),
               medianprops=dict(color='black'),
               whiskerprops=dict(color='#dc3545'),
               capprops=dict(color='#dc3545'))
    ax.set_title(f"{titles[idx]} (구매 기준 비교)")
    ax.set_ylabel(col)

plt.tight_layout()
fig.savefig(os.path.join(IMAGE_DIR, "eda_numeric_distribution.png"), dpi=200)
plt.close(fig)

# 2-2. 범주형 피처 누적 비율 (VisitorType, Weekend)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# VisitorType 비교
ct_visitor = pd.crosstab(df['VisitorType'], df['Revenue_Str'], normalize='index') * 100
ct_visitor.plot(kind='bar', stacked=True, color=['#e74c3c', '#2ecc71'], ax=axes[0])
axes[0].set_title("방문자 유형(VisitorType)별 구매 여부 비율")
axes[0].set_ylabel("비율 (%)")
axes[0].set_xlabel("방문자 유형")
axes[0].legend(title="구매 여부")

# Weekend 비교
ct_weekend = pd.crosstab(df['Weekend_Str'], df['Revenue_Str'], normalize='index') * 100
ct_weekend.plot(kind='bar', stacked=True, color=['#e74c3c', '#2ecc71'], ax=axes[1])
axes[1].set_title("주말 여부(Weekend)별 구매 여부 비율")
axes[1].set_ylabel("비율 (%)")
axes[1].set_xlabel("주말 여부")
axes[1].legend(title="구매 여부")

plt.tight_layout()
fig.savefig(os.path.join(IMAGE_DIR, "eda_categorical_crosstab.png"), dpi=200)
plt.close(fig)

# 2-3. 퍼널 분석 (Matplotlib 가로 막대 그래프형 퍼널)
fig, ax = plt.subplots(figsize=(10, 6))
step1_all = len(df)
step2_prod = len(df[df['ProductRelated'] > 0])
step3_val = len(df[(df['ProductRelated'] > 0) & (df['PageValues'] > 0)])
step4_rev = len(df[(df['ProductRelated'] > 0) & (df['PageValues'] > 0) & (df['Revenue'] == True)])

funnel_y = ["1. 전체 방문\n(100.0%)", "2. 제품 탐색\n(99.1%)", "3. 가치 탐색\n(17.9%)", "4. 구매 완료\n(7.8%)"]
funnel_x = [step1_all, step2_prod, step3_val, step4_rev]
ratios = [100.0, (step2_prod/step1_all)*100, (step3_val/step1_all)*100, (step4_rev/step1_all)*100]

bars = ax.barh(funnel_y[::-1], funnel_x[::-1], color=['#2ecc71', '#f1c40f', '#3498db', '#34495e'])
ax.set_title("고객 구매 의정 퍼널 단계별 전환 현황 (세션 수 기준)")
ax.set_xlabel("방문 세션 수")

# 수치 텍스트 표시
for bar in bars:
    width = bar.get_width()
    ax.text(width + 100, bar.get_y() + bar.get_height()/2, f"{int(width):,} 건",
            va='center', ha='left', fontsize=10, fontweight='bold')

plt.tight_layout()
fig.savefig(os.path.join(IMAGE_DIR, "funnel_analysis.png"), dpi=200)
plt.close(fig)

# 2-4. T-test 검정 시각화 (PageValues 분포 비교)
fig, ax = plt.subplots(figsize=(8, 6))
group_false = df[df['Revenue'] == False]['PageValues']
group_true = df[df['Revenue'] == True]['PageValues']
ax.boxplot([group_false, group_true], labels=['미구매 (False)', '구매완료 (True)'], patch_artist=True,
           boxprops=dict(facecolor='#d1ecf1', color='#17a2b8'))
ax.set_title("구매완료 여부에 따른 페이지 가치(PageValues) 분포 상세")
ax.set_ylabel("PageValues")
fig.savefig(os.path.join(IMAGE_DIR, "statistical_test_detail.png"), dpi=200)
plt.close(fig)

# ----------------------------------------------------
# 3. 머신러닝 모델 학습 및 평가 이미지 생성
# ----------------------------------------------------
print("3. 머신러닝 모델을 학습하고 있습니다...")

# 변수 리스트 정의
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

# 데이터 전처리
X = df[all_features].copy()
y = df['Revenue'].astype(int)
X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
X = X.astype(int)

# 데이터셋 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 오버샘플링 적용 (Random Oversampling)
df_train = pd.concat([X_train, y_train], axis=1)
class_0 = df_train[y_train == 0]
class_1 = df_train[y_train == 1]
class_1_over = class_1.sample(len(class_0), replace=True, random_state=42)
df_train_over = pd.concat([class_0, class_1_over], axis=0).sample(frac=1, random_state=42).reset_index(drop=True)
X_train_model = df_train_over.drop('Revenue', axis=1)
y_train_model = df_train_over['Revenue']

# 모델 학습
dt_model = DecisionTreeClassifier(max_depth=5, random_state=42)
rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
gb_model = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)

dt_model.fit(X_train_model, y_train_model)
rf_model.fit(X_train_model, y_train_model)
gb_model.fit(X_train_model, y_train_model)

# 평가 지표 도출 함수
def evaluate_model(model, X_t, y_t):
    pred_proba = model.predict_proba(X_t)[:, 1]
    pred = (pred_proba >= 0.50).astype(int)
    return {
        "acc": accuracy_score(y_t, pred),
        "prec": precision_score(y_t, pred, zero_division=0),
        "rec": recall_score(y_t, pred, zero_division=0),
        "f1": f1_score(y_t, pred, zero_division=0),
        "auc": roc_auc_score(y_t, pred_proba)
    }

dt_results = evaluate_model(dt_model, X_test, y_test)
rf_results = evaluate_model(rf_model, X_test, y_test)
gb_results = evaluate_model(gb_model, X_test, y_test)

# 3-1. 모델 성능 지표 대조 그래프
print("4. 모델 성능 평가 그래프를 그리고 있습니다...")
fig, ax = plt.subplots(figsize=(10, 6))
metrics = ["정확도", "정밀도", "재현율", "F1-Score", "ROC-AUC"]
x = np.arange(len(metrics))
width = 0.25

rects1 = ax.bar(x - width, [dt_results["acc"], dt_results["prec"], dt_results["rec"], dt_results["f1"], dt_results["auc"]], width, label='의사결정나무 (DT)', color='#bdc3c7')
rects2 = ax.bar(x, [rf_results["acc"], rf_results["prec"], rf_results["rec"], rf_results["f1"], rf_results["auc"]], width, label='랜덤 포레스트 (RF)', color='#3498db')
rects3 = ax.bar(x + width, [gb_results["acc"], gb_results["prec"], gb_results["rec"], gb_results["f1"], gb_results["auc"]], width, label='그라디언트 부스팅 (GB)', color='#e74c3c')

ax.set_ylabel('스코어')
ax.set_title('3대 머신러닝 모델의 5대 평가지표 비교 (검증 데이터)')
ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.set_ylim(0, 1.15)
ax.legend(loc='lower right')

# 막대 높이 텍스트 추가
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

plt.tight_layout()
fig.savefig(os.path.join(IMAGE_DIR, "model_performance_comparison.png"), dpi=200)
plt.close(fig)

# 3-2. ROC 및 PR Curve 비교 그래프
print("5. ROC 및 PR 곡선을 생성하고 있습니다...")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# ROC Curve
dt_proba = dt_model.predict_proba(X_test)[:, 1]
rf_proba = rf_model.predict_proba(X_test)[:, 1]
gb_proba = gb_model.predict_proba(X_test)[:, 1]

dt_fpr, dt_tpr, _ = roc_curve(y_test, dt_proba)
rf_fpr, rf_tpr, _ = roc_curve(y_test, rf_proba)
gb_fpr, gb_tpr, _ = roc_curve(y_test, gb_proba)

axes[0].plot(dt_fpr, dt_tpr, label=f"DT (AUC = {dt_results['auc']:.4f})", color='#bdc3c7', lw=2)
axes[0].plot(rf_fpr, rf_tpr, label=f"RF (AUC = {rf_results['auc']:.4f})", color='#3498db', lw=2)
axes[0].plot(gb_fpr, gb_tpr, label=f"GB (AUC = {gb_results['auc']:.4f})", color='#e74c3c', lw=2)
axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.5)
axes[0].set_title("ROC (Receiver Operating Characteristic) Curve 비교")
axes[0].set_xlabel("위양성률 (False Positive Rate)")
axes[0].set_ylabel("진양성률 (True Positive Rate)")
axes[0].legend(loc='lower right')

# Precision-Recall Curve
dt_prec, dt_rec, _ = precision_recall_curve(y_test, dt_proba)
rf_prec, rf_rec, _ = precision_recall_curve(y_test, rf_proba)
gb_prec, gb_rec, _ = precision_recall_curve(y_test, gb_proba)

axes[1].plot(dt_rec, dt_prec, label="의사결정나무 (DT)", color='#bdc3c7', lw=2)
axes[1].plot(rf_rec, rf_prec, label="랜덤 포레스트 (RF)", color='#3498db', lw=2)
axes[1].plot(gb_rec, gb_prec, label="그라디언트 부스팅 (GB)", color='#e74c3c', lw=2)
axes[1].set_title("Precision-Recall Curve 비교")
axes[1].set_xlabel("재현율 (Recall)")
axes[1].set_ylabel("정밀도 (Precision)")
axes[1].legend(loc='lower left')

plt.tight_layout()
fig.savefig(os.path.join(IMAGE_DIR, "model_curves.png"), dpi=200)
plt.close(fig)

# 3-3. 피처 중요도 분석 (상위 10개 피처)
print("6. 피처 중요도 비교 차트를 생성하고 있습니다...")
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

feat_names = X.columns
rf_importances = rf_model.feature_importances_
gb_importances = gb_model.feature_importances_
# Decision Tree의 피처 중요도
dt_importances = dt_model.feature_importances_

def plot_importance(ax, importances, title, color):
    df_imp = pd.DataFrame({"Feature": feat_names, "Importance": importances}).sort_values("Importance", ascending=True).tail(10)
    ax.barh(df_imp["Feature"], df_imp["Importance"], color=color)
    ax.set_title(title)
    ax.set_xlabel("중요도")

plot_importance(axes[0], dt_importances, "의사결정나무 (DT) 피처 중요도", '#bdc3c7')
plot_importance(axes[1], rf_importances, "랜덤 포레스트 (RF) 피처 중요도", '#3498db')
plot_importance(axes[2], gb_importances, "그라디언트 부스팅 (GB) 피처 중요도", '#e74c3c')

plt.tight_layout()
fig.savefig(os.path.join(IMAGE_DIR, "feature_importance_comparison.png"), dpi=200)
plt.close(fig)

print("🎉 모든 시각화 이미지 추출이 완료되었습니다!")
print(f"이미지 저장 경로: {IMAGE_DIR}")
