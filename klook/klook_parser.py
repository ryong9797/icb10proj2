"""
Klook 원본 데이터베이스의 raw_data JSON을 파싱하여
개별 컬럼으로 분리된 새로운 데이터베이스(klook/data/klook_data.db)를 생성하는 스크립트입니다.
"""

import sqlite3
import json
import os

def parse_and_rebuild_db(source_db_path, target_db_path):
    # 타겟 디렉토리 생성
    os.makedirs(os.path.dirname(target_db_path), exist_ok=True)
    
    # 소스 DB 연결
    src_conn = sqlite3.connect(source_db_path)
    src_cursor = src_conn.cursor()
    
    # 원본 데이터 읽기
    src_cursor.execute("SELECT page, item_index, raw_data FROM klook_search_results")
    rows = src_cursor.fetchall()
    
    if not rows:
        print("원본 데이터가 없습니다.")
        return
        
    parsed_records = []
    all_keys = set()
    
    for page, item_index, raw_data_str in rows:
        try:
            card = json.loads(raw_data_str)
            # Klook 카드는 보통 "data" 키 안에 주요 정보가 있습니다.
            data = card.get("data", card) 
            
            record = {
                "source_page": page,
                "source_item_index": item_index
            }
            
            # Primitive 타입(int, float, str, bool)만 컬럼으로 추출
            for k, v in data.items():
                if isinstance(v, (int, float, str, bool)):
                    record[k] = v
                    all_keys.add(k)
                elif isinstance(v, dict) and "amount" in v: 
                    # 가격 정보처럼 딕셔너리 안에 amount가 있는 경우 추출
                    record[f"{k}_amount"] = v.get("amount")
                    all_keys.add(f"{k}_amount")
                elif isinstance(v, dict) and "display_amount" in v:
                    record[f"{k}_display"] = v.get("display_amount")
                    all_keys.add(f"{k}_display")
                    
            parsed_records.append(record)
        except json.JSONDecodeError:
            continue

    if not parsed_records:
        print("파싱할 수 있는 데이터가 없습니다.")
        return

    # 타겟 DB 연결 및 테이블 생성
    tgt_conn = sqlite3.connect(target_db_path)
    tgt_cursor = tgt_conn.cursor()
    
    # 테이블 스키마 동적 생성
    columns = ["source_page INTEGER", "source_item_index INTEGER"]
    sorted_keys = sorted(list(all_keys))
    
    for key in sorted_keys:
        # 간단한 타입 추론 (첫 번째 유효한 값을 기준)
        col_type = "TEXT"
        for rec in parsed_records:
            if key in rec and rec[key] is not None:
                if isinstance(rec[key], int):
                    col_type = "INTEGER"
                elif isinstance(rec[key], float):
                    col_type = "REAL"
                break
        columns.append(f'"{key}" {col_type}')
        
    create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS parsed_klook_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {", ".join(columns)}
        )
    '''
    
    tgt_cursor.execute("DROP TABLE IF EXISTS parsed_klook_data")
    tgt_cursor.execute(create_table_sql)
    
    # 데이터 삽입
    insert_cols = ["source_page", "source_item_index"] + [f'"{k}"' for k in sorted_keys]
    placeholders = ", ".join(["?"] * len(insert_cols))
    insert_sql = f'INSERT INTO parsed_klook_data ({", ".join(insert_cols)}) VALUES ({placeholders})'
    
    for rec in parsed_records:
        values = [rec.get("source_page"), rec.get("source_item_index")] + [rec.get(k) for k in sorted_keys]
        tgt_cursor.execute(insert_sql, values)
        
    tgt_conn.commit()
    
    print(f"총 {len(parsed_records)}개의 데이터를 파싱하여 '{target_db_path}'에 저장했습니다.")
    print(f"추출된 컬럼 수: {len(sorted_keys)}개")
    print(f"주요 컬럼 예시: {', '.join(sorted_keys[:10])} ...")
    
    src_conn.close()
    tgt_conn.close()

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    src_db = os.path.join(base_dir, "klook_data.db")
    tgt_db = os.path.join(base_dir, "data", "klook_data.db")
    
    print(f"원본 DB: {src_db}")
    print(f"타겟 DB: {tgt_db}")
    parse_and_rebuild_db(src_db, tgt_db)
