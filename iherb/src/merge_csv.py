"""
수집된 CSV 파일 병합 스크립트
작성자: Antigravity
"""

import os
import csv

def merge_files():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    csv_files = [os.path.join(data_dir, f"sports_products_page{i}.csv") for i in range(1, 11)]
    merged_file = os.path.join(data_dir, "sports_products_merged.csv")

    headers_written = False
    total_rows = 0

    with open(merged_file, 'w', encoding='utf-8-sig', newline='') as fout:
        writer = csv.writer(fout)
        for file in csv_files:
            if not os.path.exists(file):
                print(f"파일 없음: {os.path.basename(file)}")
                continue
            
            with open(file, 'r', encoding='utf-8-sig', newline='') as fin:
                reader = csv.reader(fin)
                try:
                    headers = next(reader)
                except StopIteration:
                    continue
                
                if not headers_written:
                    writer.writerow(headers)
                    headers_written = True
                
                rows_in_file = 0
                for row in reader:
                    writer.writerow(row)
                    rows_in_file += 1
                    total_rows += 1
                
                print(f"{os.path.basename(file)} 에서 {rows_in_file}개 행 병합됨.")

    print(f"\n모든 파일 병합 완료! 총 {total_rows}개 행이 {merged_file}에 저장되었습니다.")

if __name__ == '__main__':
    merge_files()
