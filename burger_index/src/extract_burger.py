"""
이 스크립트는 전국 상가(상권)정보 CSV 파일에서 버거킹, 맥도날드, KFC, 롯데리아(영문 포함)
데이터를 추출하여 하나의 파일(burger.csv)로 병합하는 역할을 수행합니다.
"""
import os
import pandas as pd
import glob
import re

def main():
    data_dir = r"c:\Users\admin\Desktop\icb10proj2\burger_index\data"
    out_file = os.path.join(data_dir, "burger.csv")

    files = glob.glob(os.path.join(data_dir, "*.csv"))
    files = [f for f in files if 'burger.csv' not in f]
    
    # 롯데리아, 맥도날드, 버거킹, kfc 및 영문명 포함
    keywords = ['버거킹', 'burger king', 'burgerking', 
                '맥도날드', 'mcdonald', 
                'kfc', '케이에프씨', 
                '롯데리아', 'lotteria']
    
    # 정규식 패턴 생성
    pattern = '|'.join(keywords)

    df_list = []
    total_files = len(files)
    print(f"Total {total_files} files found. Starting extraction...")

    for i, file in enumerate(files, 1):
        print(f"[{i}/{total_files}] Processing {os.path.basename(file)}...")
        try:
            df = pd.read_csv(file, low_memory=False)
            
            if '상호명' in df.columns:
                mask = df['상호명'].fillna('').str.lower().str.contains(pattern, flags=re.IGNORECASE, regex=True)
                filtered_df = df[mask]
                df_list.append(filtered_df)
                print(f"  -> Found {len(filtered_df)} matching rows.")
            else:
                print("  -> No '상호명' column found.")
        except Exception as e:
            print(f"  -> Error processing {file}: {e}")

    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        final_df.to_csv(out_file, index=False, encoding='utf-8-sig')
        print(f"\nExtraction completed! Saved {len(final_df)} rows to {out_file}")
    else:
        print("\nNo matching data found.")

if __name__ == "__main__":
    main()
