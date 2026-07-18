"""
이 스크립트는 서울 생활인구 데이터를 읽어와서 성별 및 연령대 컬럼을 Tidy Data 형태로 변환하고,
데이터를 downcast하여 Parquet 포맷으로 압축 저장한 후, 변환 전후의 데이터를 비교하는 리포트를 생성합니다.
"""
import pandas as pd
import io
import sys

def main():
    zip_path = r"../data/LOCAL_PEOPLE_DONG_202606.zip"
    parquet_path = r"../data/LOCAL_PEOPLE_DONG_202606.parquet"
    report_path = r"../report/data_comparison.md"
    
    print("데이터를 불러오는 중입니다...")
    # csv 파일이 zip 안에 하나 있을 것으로 가정합니다.
    try:
        df = pd.read_csv(zip_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(zip_path, encoding='cp949')
        
    print("=== 상위 5개 행 ===")
    print(df.head())
    
    # 원본 데이터 info 기록
    buf_orig = io.StringIO()
    df.info(buf=buf_orig)
    orig_info = buf_orig.getvalue()
    
    print("\nTidy data 형태로 변환 중...")
    # 총생활인구수는 생활인구수의 합으로 구할 수 있으므로 제거하여 중복 저장과 용량을 방지합니다.
    if '총생활인구수' in df.columns:
        df = df.drop('총생활인구수', axis=1)

    # 컬럼명에 '남자' 또는 '여자'가 포함된 컬럼을 성별/연령대로 추정합니다.
    # 예: 남자0세부터9세생활인구수, 여자70세이상생활인구수
    id_vars = [c for c in df.columns if not ('남자' in c or '여자' in c)]
    value_vars = [c for c in df.columns if '남자' in c or '여자' in c]
    
    df_melt = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name='성별_연령대', value_name='생활인구수')
    
    # 성별과 연령대 컬럼 분리
    df_melt['성별'] = df_melt['성별_연령대'].str[:2] # '남자' 또는 '여자'
    df_melt['연령대'] = df_melt['성별_연령대'].str[2:].str.replace('생활인구수', '', regex=False)
    df_melt = df_melt.drop('성별_연령대', axis=1)
    
    print("기준일ID, 행정동코드 및 범주형 변수를 category로 변환 중...")
    if '기준일ID' in df_melt.columns:
        df_melt['기준일ID'] = df_melt['기준일ID'].astype('category')
    if '행정동코드' in df_melt.columns:
        df_melt['행정동코드'] = df_melt['행정동코드'].astype('category')
    df_melt['성별'] = df_melt['성별'].astype('category')
    df_melt['연령대'] = df_melt['연령대'].astype('category')
    
    print("\n=== 범주형 데이터 기술 통계 ===")
    cat_desc = df_melt.describe(include=['category']).to_string()
    print(cat_desc)
    
    print("\n=== 수치형 데이터 기술 통계 ===")
    num_desc = df_melt.describe(include=['number']).to_string()
    print(num_desc)

    print("\n데이터 형식을 downcast 하여 수치형 메모리 추가 최적화 중...")
    for col in df_melt.select_dtypes(include=['float']).columns:
        df_melt[col] = pd.to_numeric(df_melt[col], downcast='float')
    for col in df_melt.select_dtypes(include=['int']).columns:
        df_melt[col] = pd.to_numeric(df_melt[col], downcast='integer')
        
    print(f"Parquet 형식으로 저장 중... ({parquet_path})")
    try:
        df_melt.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    except ImportError:
        print("pyarrow 또는 fastparquet 라이브러리가 필요합니다. 'uv pip install pyarrow'를 실행해 주세요.")
        sys.exit(1)
        
    # 저장된 parquet 파일 다시 불러와서 info 확인
    df_pq = pd.read_parquet(parquet_path)
    buf_pq = io.StringIO()
    df_pq.info(buf=buf_pq)
    pq_info = buf_pq.getvalue()
    
    print("\n=== 최종 다운캐스트 완료 후 Info ===")
    print(pq_info)
    
    # Parquet 메타데이터 추출
    import pyarrow.parquet as pq
    pq_meta = pq.read_metadata(parquet_path)
    meta_info = f"- **행 수 (num_rows)**: {pq_meta.num_rows:,} 개\n"
    meta_info += f"- **컬럼 수 (num_columns)**: {pq_meta.num_columns} 개\n"
    meta_info += f"- **로우 그룹 수 (num_row_groups)**: {pq_meta.num_row_groups} 개\n"
    meta_info += f"- **포맷 버전 (format_version)**: {pq_meta.format_version}\n"
    meta_info += f"- **직렬화 용량 (serialized_size)**: {pq_meta.serialized_size:,} Bytes\n"
    
    # 마크다운 리포트 생성
    report_content = f"""# 서울 생활인구 데이터 변환 리포트

## 1. 개요
원본 `.zip` 내부의 데이터를 Pandas로 직접 읽어와서 성별과 연령대 컬럼을 Tidy-data 형태(Long form)로 변환하였습니다. 이후 데이터 자료형(Data type)을 downcast하여 메모리 사용량을 줄이고 최적화된 `.parquet` 포맷으로 저장하였습니다.

## 2. 원본 데이터 (ZIP 파일 내부 CSV) Info
```text
{orig_info}
```

## 3. 기술 통계 요약
### 범주형 데이터 통계
```text
{cat_desc}
```

### 수치형 데이터 통계
```text
{num_desc}
```

## 4. 변환 및 저장된 데이터 (Parquet) Info
```text
{pq_info}
```

## 5. Parquet 메타 정보 (Metadata)
{meta_info}

### 메타 정보 설명:
- **행 수 (num_rows)**: Parquet 파일에 저장된 전체 데이터 행(Row)의 개수입니다.
- **컬럼 수 (num_columns)**: Parquet 파일에 저장된 전체 컬럼(열)의 개수입니다.
- **로우 그룹 수 (num_row_groups)**: Parquet는 데이터를 '로우 그룹(Row Group)'이라는 수평적 청크 단위로 분할하여 저장합니다. 각 로우 그룹별로 메타데이터(최솟값, 최댓값 등)를 가지며, 조건 검색 시 필요한 로우 그룹만 읽어올 수 있어(Predicate Pushdown) 쿼리 속도와 메모리 효율이 대폭 향상됩니다.
- **포맷 버전 (format_version)**: Parquet 파일 구조의 규격 버전입니다. (예: 1.0, 2.0 등)
- **직렬화 용량 (serialized_size)**: 메타데이터 자체의 직렬화된 크기 또는 구조적 크기 정보입니다.

## 6. 데이터 최적화 비교 결과
- **구조 변환 (Tidy Data)**: 기존 넓은 형태(Wide)의 데이터를 성별과 연령대로 분리하여 새로운 컬럼으로 생성함으로써, 차원별 분석(예: 성별 집계, 연령대별 패턴 분석)이 용이해졌습니다.
- **메모리 최적화**: 64비트 실수형/정수형 데이터를 `downcast` 옵션으로 각각 최소 단위 자료형으로 압축 변환했으며, 범주형(Category) 변환을 통해 메모리를 훨씬 효율적으로 사용하게 되었습니다.
- **파일 포맷 변경**: 텍스트 기반의 CSV 포맷(ZIP 내장)을 Parquet 포맷으로 변경하였습니다. Parquet는 열 기반(columnar) 압축 포맷이므로 디스크 용량 절감은 물론 데이터 로드 속도가 대폭 향상되었습니다.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"\n작업이 완료되었습니다. 결과 리포트는 {report_path} 에 저장되었습니다.")

if __name__ == "__main__":
    main()
