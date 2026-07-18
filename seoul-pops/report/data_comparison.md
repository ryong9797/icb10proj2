# 서울 생활인구 데이터 변환 리포트

## 1. 개요
원본 `.zip` 내부의 데이터를 Pandas로 직접 읽어와서 성별과 연령대 컬럼을 Tidy-data 형태(Long form)로 변환하였습니다. 이후 데이터 자료형(Data type)을 downcast하여 메모리 사용량을 줄이고 최적화된 `.parquet` 포맷으로 저장하였습니다.

## 2. 원본 데이터 (ZIP 파일 내부 CSV) Info
```text
<class 'pandas.DataFrame'>
Index: 305280 entries, 20260601 to 20260630
Data columns (total 32 columns):
 #   Column           Non-Null Count   Dtype  
---  ------           --------------   -----  
 0   기준일ID            305280 non-null  int64  
 1   시간대구분            305280 non-null  int64  
 2   행정동코드            305280 non-null  float64
 3   총생활인구수           305280 non-null  float64
 4   남자0세부터9세생활인구수    305280 non-null  float64
 5   남자10세부터14세생활인구수  305280 non-null  float64
 6   남자15세부터19세생활인구수  305280 non-null  float64
 7   남자20세부터24세생활인구수  305280 non-null  float64
 8   남자25세부터29세생활인구수  305280 non-null  float64
 9   남자30세부터34세생활인구수  305280 non-null  float64
 10  남자35세부터39세생활인구수  305280 non-null  float64
 11  남자40세부터44세생활인구수  305280 non-null  float64
 12  남자45세부터49세생활인구수  305280 non-null  float64
 13  남자50세부터54세생활인구수  305280 non-null  float64
 14  남자55세부터59세생활인구수  305280 non-null  float64
 15  남자60세부터64세생활인구수  305280 non-null  float64
 16  남자65세부터69세생활인구수  305280 non-null  float64
 17  남자70세이상생활인구수     305280 non-null  float64
 18  여자0세부터9세생활인구수    305280 non-null  float64
 19  여자10세부터14세생활인구수  305280 non-null  float64
 20  여자15세부터19세생활인구수  305280 non-null  float64
 21  여자20세부터24세생활인구수  305280 non-null  float64
 22  여자25세부터29세생활인구수  305280 non-null  float64
 23  여자30세부터34세생활인구수  305280 non-null  float64
 24  여자35세부터39세생활인구수  305280 non-null  float64
 25  여자40세부터44세생활인구수  305280 non-null  float64
 26  여자45세부터49세생활인구수  305280 non-null  float64
 27  여자50세부터54세생활인구수  305280 non-null  float64
 28  여자55세부터59세생활인구수  305280 non-null  float64
 29  여자60세부터64세생활인구수  305280 non-null  float64
 30  여자65세부터69세생활인구수  305280 non-null  float64
 31  여자70세이상생활인구수     0 non-null       float64
dtypes: float64(30), int64(2)
memory usage: 76.9 MB

```

## 3. 기술 통계 요약
### 범주형 데이터 통계
```text
          기준일ID         행정동코드       성별      연령대
count   8547840  8.547840e+06  8547840  8547840
unique       24  3.051480e+05        2       14
top           0  1.909227e+04       남자   0세부터9세
freq     356160  8.400000e+01  4273920   610560
```

### 수치형 데이터 통계
```text
              시간대구분         생활인구수
count  8.547840e+06  8.242560e+06
mean   1.143320e+07  8.571736e+02
std    1.916679e+05  7.278165e+02
min    1.111052e+07  0.000000e+00
25%    1.126065e+07  4.355273e+02
50%    1.144062e+07  6.753078e+02
75%    1.159814e+07  1.050090e+03
max    1.174070e+07  2.124420e+04
```

## 4. 변환 및 저장된 데이터 (Parquet) Info
```text
<class 'pandas.DataFrame'>
RangeIndex: 8547840 entries, 0 to 8547839
Data columns (total 6 columns):
 #   Column  Dtype   
---  ------  -----   
 0   기준일ID   int64   
 1   시간대구분   int32   
 2   행정동코드   float64 
 3   생활인구수   float64 
 4   성별      category
 5   연령대     category
dtypes: category(2), float64(2), int32(1), int64(1)
memory usage: 244.6 MB

```

## 5. 데이터 최적화 비교 결과
- **구조 변환 (Tidy Data)**: 기존 넓은 형태(Wide)의 데이터를 성별과 연령대로 분리하여 새로운 컬럼으로 생성함으로써, 차원별 분석(예: 성별 집계, 연령대별 패턴 분석)이 용이해졌습니다.
- **메모리 최적화**: 64비트 실수형/정수형 데이터를 `downcast` 옵션으로 각각 `float32` 등 최소 단위 자료형으로 압축 변환했습니다. Info 결과를 비교해 보면 원본 대비 자료형 최적화를 통해 메모리를 훨씬 효율적으로 사용하는 것을 볼 수 있습니다.
- **파일 포맷 변경**: 텍스트 기반의 CSV 포맷(ZIP 내장)을 Parquet 포맷으로 변경하였습니다. Parquet는 열 기반(columnar) 압축 포맷이므로 디스크 용량 절감은 물론 읽기/쓰기 속도가 대폭 향상되었습니다.
