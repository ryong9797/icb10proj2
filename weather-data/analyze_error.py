"""
2021년~2025년 학습 데이터 기반 2026년 가격 예측 오차 분석 스크립트
작성자: AI Assistant
"""

import pandas as pd
import datetime
import math
import random
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from src.collectors import generate_mock_weather_data, merge_and_preprocess_data
from src.models import CropPricePredictor

def run_analysis():
    print("데이터를 수집하고 생성하는 중입니다...")
    
    # 1. 2021년 1월 1일 ~ 2026년 7월 1일 데이터 생성 (충분한 윈도우 확보 위해)
    start_date = datetime.date(2021, 1, 1)
    end_date = datetime.date(2026, 7, 1)
    
    # 기상 데이터 (mock)
    weather_df = generate_mock_weather_data(start_date, end_date)
    
    # 5대 핵심 품목 설정
    base_prices = {
        "배추": 3500, 
        "무": 1800, 
        "양파": 2200, 
        "대파": 2500, 
        "마늘": 6500
    }
    
    random.seed(42)
    price_records = []
    current_prices = base_prices.copy()
    current_date = start_date
    delta = datetime.timedelta(days=1)
    
    while current_date <= end_date:
        # 주말 제외 (시장 휴무 반영)
        if current_date.weekday() < 5:
            day_of_year = current_date.timetuple().tm_yday
            
            for item, base in base_prices.items():
                # 품목별 노이즈 (매일 기준가의 5% 내외 변동) - 누적되는 랜덤 워크 방지
                noise = random.uniform(-base * 0.05, base * 0.05)
                current_prices[item] = base + noise
                
                # 상/하한선 규제
                current_prices[item] = max(base * 0.5, min(base * 2.5, current_prices[item]))
                
                # 품목별 약간 다른 계절성 위상 부여
                phase_shift = {"배추": 150, "무": 180, "양파": 90, "대파": 120, "마늘": 210}[item]
                seasonal_factor = 1.0 + 0.25 * math.sin(2 * math.pi * (day_of_year - phase_shift) / 365.0)
                
                final_price = current_prices[item] * seasonal_factor
                
                price_records.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "item_name": item,
                    "price": int(final_price),
                    "volume": int(random.uniform(200, 1000))
                })
                
        current_date += delta
        
    price_df = pd.DataFrame(price_records)
    price_df["date"] = pd.to_datetime(price_df["date"])
    
    # 병합
    merged_df = merge_and_preprocess_data(weather_df, [price_df])
    
    # 2. 파생 변수(rolling 기상 지표) 일괄 생성 후 훈련/테스트 세트 분할
    dummy = CropPricePredictor(merged_df, [])  # 빈 리스트로 넘겨 학습은 생략, 변수만 생성
    full_df = dummy.df
    
    # 학습 데이터: 2021-01 ~ 2025-12
    # 예측 테스트 데이터: 2026-03 ~ 2026-06 (4개월)
    train_df = full_df[full_df['date'].dt.year <= 2025].copy()
    test_df = full_df[(full_df['date'].dt.year == 2026) & (full_df['date'].dt.month.isin([3, 4, 5, 6]))].copy()
    
    print(f"학습 데이터 크기: {len(train_df)}일")
    print(f"테스트 데이터 크기: {len(test_df)}일")
    
    # 3. 모델 학습 (5개 품목 동시 학습)
    print("Random Forest 모델을 모든 품목에 대해 학습합니다...")
    item_list = list(base_prices.keys())
    predictor = CropPricePredictor(train_df, item_list)
    
    # 4. 예측 및 오차 분석
    print("\n" + "="*50)
    print("🎯 [분석 결과] 2026년 3월~6월 주요 품목별 예측 오차")
    print("="*50)
    
    for item in item_list:
        model = predictor.models.get(item)
        if model is None:
            print(f"[{item}] 데이터 부족으로 모델 학습이 실패했습니다.")
            continue
            
        base_features = predictor.base_features
        X_test = test_df[base_features]
        y_test = test_df[f"{item}_가격"]
        
        predictions = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, predictions)
        mape = mean_absolute_percentage_error(y_test, predictions) * 100
        r2 = predictor.metrics[item]['r2']
        
        # 품목별 이모지
        emoji = {"배추": "🥬", "무": "🥕", "양파": "🧅", "대파": "🌿", "마늘": "🧄"}[item]
        
        print(f"{emoji} [{item}] MAE: {mae:5,.0f}원 | MAPE: {mape:5.2f}% | R²: {r2:.3f}")
        
    print("="*50)
    print("※ MAPE 기준: 10% 미만(매우 우수), 10~20%(양호)")

if __name__ == "__main__":
    run_analysis()
