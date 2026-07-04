"""
기상 데이터 기반 농산물 가격 예측 모델 및 시뮬레이터 모듈

이 모듈은 Scikit-learn의 Random Forest 알고리즘을 활용하여,
이상 기후 변수(폭염 일수, 강수량 등)에 따른 농산물 품목별 가격 예측 모델을 구축하고 학습합니다.
데이터가 부족한 경우에는 규칙 기반(Rule-based)의 물리 모델로 자동 폴백하여 시뮬레이션을 원활히 제공합니다.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


class CropPricePredictor:
    """농산물 가격 예측 및 시뮬레이션을 담당하는 머신러닝 예측 클래스입니다."""

    def __init__(self, df: pd.DataFrame, item_names: list):
        self.df = df.copy()
        self.item_names = item_names
        self.models = {}
        self.features_list = {}
        self.metrics = {}
        self.feature_importances = {}
        
        # 기상 특성 엔지니어링 수행
        self._prepare_features()
        # 품목별 모델 학습 진행
        self._train_models()

    def _prepare_features(self):
        """기상 조건으로부터 파생 변수(폭염 일수, 폭우 일수, 누적 강수량 등)를 생성합니다."""
        # 1. 폭염 여부 정의 (최고 기온 33도 이상)
        self.df["is_heatwave"] = (self.df["max_temp"] >= 33.0).astype(int)
        # 2. 폭우 여부 정의 (일 강수량 50mm 이상)
        self.df["is_heavy_rain"] = (self.df["precipitation"] >= 50.0).astype(int)

        # 3. 최근 30일 기준 이동 합계/평균 지표 생성
        self.df["rolling_heatwave_days"] = self.df["is_heatwave"].rolling(window=30, min_periods=1).sum()
        self.df["rolling_heavyrain_days"] = self.df["is_heavy_rain"].rolling(window=30, min_periods=1).sum()
        self.df["rolling_avg_temp"] = self.df["avg_temp"].rolling(window=30, min_periods=1).mean()
        self.df["rolling_sum_rain"] = self.df["precipitation"].rolling(window=30, min_periods=1).sum()
        self.df["rolling_humidity"] = self.df["humidity"].rolling(window=30, min_periods=1).mean()
        
        # 4. 계절성 지표 추가 (월별, 일별 기온/가격 패턴 학습용)
        if "date" in self.df.columns:
            self.df["month"] = self.df["date"].dt.month
            day_of_year = self.df["date"].dt.dayofyear
            self.df["sin_day"] = np.sin(2 * np.pi * day_of_year / 365.25)
            self.df["cos_day"] = np.cos(2 * np.pi * day_of_year / 365.25)
        else:
            self.df["month"] = 1
            self.df["sin_day"] = 0.0
            self.df["cos_day"] = 1.0

        # 기상 예측 기본 독립 변수 정의
        self.base_features = [
            "rolling_avg_temp",
            "rolling_sum_rain",
            "rolling_heatwave_days",
            "rolling_heavyrain_days",
            "rolling_humidity",
            "month",
            "sin_day",
            "cos_day"
        ]

    def _train_models(self):
        """지정된 농산물 품목별로 Random Forest 예측 모델을 개별 학습합니다."""
        for item in self.item_names:
            target_col = f"{item}_가격"
            if target_col not in self.df.columns:
                continue

            # 결측치 제거 후 유효한 데이터 확보
            valid_df = self.df.dropna(subset=[target_col] + self.base_features)

            # 데이터 행 수가 머신러닝 학습에 적절한 수준(최소 20개 이상)인지 확인
            if len(valid_df) < 20:
                self.models[item] = None  # 규칙 기반 시뮬레이션 모드로 플래그 처리
                self.metrics[item] = {"r2": 0.0, "status": "데이터 부족 (규칙 기반 폴백 모드)"}
                continue

            X = valid_df[self.base_features]
            y = valid_df[target_col]

            # 학습 및 테스트 데이터 분할
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Random Forest Regressor 선언 및 학습 (더 깊고 많은 트리로 비선형 계절성 완벽 학습)
            model = RandomForestRegressor(n_estimators=300, max_depth=15, random_state=42)
            model.fit(X_train, y_train)

            # 모델 평가 스코어 기록
            r2_score = model.score(X_test, y_test)
            # 음수 스코어 방지
            r2_score = max(0.0, round(r2_score, 3))

            self.models[item] = model
            self.features_list[item] = self.base_features
            self.metrics[item] = {
                "r2": r2_score,
                "status": f"Random Forest 학습 완료 (R²: {r2_score})"
            }

            # 피처 중요도(Feature Importance) 추출 및 저장
            importances = model.feature_importances_
            feat_imp = {feat: float(imp) for feat, imp in zip(self.base_features, importances)}
            self.feature_importances[item] = feat_imp

    def simulate_price(
        self,
        item_name: str,
        input_avg_temp: float,
        input_sum_rain: float,
        input_heatwave_days: float,
        input_heavyrain_days: float,
        input_humidity: float
    ) -> dict:
        """가상의 이상 기후 조건 입력에 따른 가격 변동 및 예측 가격을 시뮬레이션합니다."""
        target_col = f"{item_name}_가격"
        
        # 기본 현재(또는 데이터셋 마지막 시점)의 품목 가격 조회
        if target_col in self.df.columns:
            last_price = self.df[target_col].iloc[-1]
            base_mean_price = self.df[target_col].mean()
        else:
            last_price = 3000.0
            base_mean_price = 3000.0

        model = self.models.get(item_name)

        # 1. 머신러닝 예측 모드 (정상 학습된 모델이 있는 경우)
        if model is not None:
            if "date" in self.df.columns:
                current_month = self.df["date"].dt.month.iloc[-1]
                current_doy = self.df["date"].dt.dayofyear.iloc[-1]
            else:
                current_month = 1
                current_doy = 1
                
            input_df = pd.DataFrame([{
                "rolling_avg_temp": input_avg_temp,
                "rolling_sum_rain": input_sum_rain,
                "rolling_heatwave_days": input_heatwave_days,
                "rolling_heavyrain_days": input_heavyrain_days,
                "rolling_humidity": input_humidity,
                "month": current_month,
                "sin_day": float(np.sin(2 * np.pi * current_doy / 365.25)),
                "cos_day": float(np.cos(2 * np.pi * current_doy / 365.25))
            }])
            predicted_price = float(model.predict(input_df)[0])
        
        # 2. 규칙 기반 물리 모델 폴백 모드 (데이터가 부족한 경우)
        else:
            # 품목별 이상 기후 민감도 (collectors.py의 설정과 일치)
            sensitivity = {
                "배추": {"temp": 1.5, "rain": 1.2, "base": 3500.0},
                "무": {"temp": 1.0, "rain": 1.5, "base": 1800.0},
                "양파": {"temp": 0.8, "rain": 0.8, "base": 2200.0},
                "대파": {"temp": 1.2, "rain": 1.4, "base": 2500.0},
                "마늘": {"temp": 0.5, "rain": 0.6, "base": 6500.0}
            }
            coeff = sensitivity.get(item_name, {"temp": 1.0, "rain": 1.0, "base": 2500.0})
            
            # 기준가에서 폭염 일수와 강수량 증가에 따른 변동폭 수식화
            temp_shock = input_heatwave_days * coeff["temp"] * 0.04  # 폭염 1일당 약 4% 상승
            rain_shock = (input_sum_rain / 100.0) * coeff["rain"] * 0.08  # 누적 강수량 100mm당 8% 상승
            heavy_rain_shock = input_heavyrain_days * coeff["rain"] * 0.06 # 폭우 1일당 6% 상승

            total_shock_ratio = temp_shock + rain_shock + heavy_rain_shock
            
            # 가상 기온 편차 추가 보정 (기준 평년 기온 18도 대비 편차)
            temp_dev = max(0.0, input_avg_temp - 18.0) * 0.02
            total_shock_ratio += temp_dev

            predicted_price = last_price * (1.0 + total_shock_ratio)
            # 가격 하한 및 상한 규제 적용
            predicted_price = max(coeff["base"] * 0.4, min(coeff["base"] * 3.5, predicted_price))

        # 정수형으로 반환 처리
        predicted_price = int(round(predicted_price))
        price_change = predicted_price - last_price
        change_rate = (price_change / last_price) * 100.0

        return {
            "predicted_price": predicted_price,
            "base_price": int(last_price),
            "price_change": int(price_change),
            "change_rate": round(change_rate, 2),
            "is_ml_mode": model is not None
        }
