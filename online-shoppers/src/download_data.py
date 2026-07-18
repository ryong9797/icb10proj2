"""
Online Shoppers Purchasing Intention Dataset을 UCI 저장소에서 다운로드하는 스크립트입니다.
이 스크립트는 네트워크를 통해 데이터를 가져와 프로젝트의 'data' 폴더에 CSV 파일로 저장합니다.
"""
import os
import pandas as pd
import urllib.request

def download_dataset():
    # 데이터 소스 URL (UCI Online Shoppers Purchasing Intention Dataset)
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00468/online_shoppers_intention.csv"
    
    # 저장할 디렉토리 및 파일 경로 설정
    # 워크스페이스 기준 상대 경로 사용
    data_dir = os.path.join("online-shoppers", "data")
    file_path = os.path.join(data_dir, "online_shoppers_intention.csv")
    
    # 디렉토리가 없으면 생성
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"디렉토리 생성됨: {data_dir}")
        
    print(f"데이터 다운로드 중... URL: {url}")
    try:
        # urllib를 사용하여 파일 다운로드
        urllib.request.urlretrieve(url, file_path)
        print(f"다운로드 완료! 파일 저장 경로: {file_path}")
        
        # 정상적으로 로드되는지 확인
        df = pd.read_csv(file_path)
        print(f"데이터 로드 성공. 행 수: {df.shape[0]}, 열 수: {df.shape[1]}")
    except Exception as e:
        print(f"데이터 다운로드 또는 로드 실패: {e}")
        # 예외 처리: 만약 네트워크 문제 등으로 실패 시 pandas에서 직접 시도
        try:
            print("pandas.read_csv로 직접 시도합니다...")
            df = pd.read_csv(url)
            df.to_csv(file_path, index=False)
            print(f"직접 다운로드 및 저장 성공: {file_path}")
        except Exception as ex:
            print(f"대체 다운로드도 실패했습니다: {ex}")

if __name__ == "__main__":
    download_dataset()
