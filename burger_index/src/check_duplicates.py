"""
이 스크립트는 burger.csv 파일 내 중복된 데이터를 확인하고,
어떤 데이터가 어떻게 겹치는지(완전 중복인지 등) 그 내역을 상세히 출력합니다.
"""
import pandas as pd

def main():
    file_path = r"c:\Users\admin\Desktop\icb10proj2\burger_index\data\burger.csv"
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return
        
    # 모든 컬럼 값이 완전히 동일한 중복 확인 (keep=False로 모든 중복 행 선택)
    dup_all = df[df.duplicated(keep=False)].sort_values(by=['상가업소번호'])
    
    # 상가업소번호(고유 식별자) 기준으로만 중복인지 확인
    dup_by_id = df[df.duplicated(subset=['상가업소번호'], keep=False)].sort_values(by=['상가업소번호'])
    
    print("\n[중복 데이터 확인 결과 요약]")
    print("=" * 60)
    print(f"전체 데이터 수: {len(df)}건")
    print(f"1) 상가업소번호 기준 중복 행 수: {len(dup_by_id)}건")
    print(f"2) 모든 내용이 완전히 동일한 중복 행 수: {len(dup_all)}건")
    print("=" * 60)
    
    if len(dup_all) > 0:
        print("\n[모든 내용이 완전히 겹치는 중복 데이터 상세 내역]")
        # 식별 번호로 그룹화하여 어떻게 겹치는지 보여줌
        grouped = dup_all.groupby('상가업소번호')
        count = 0
        for name, group in grouped:
            count += 1
            if count > 10:  # 내역이 너무 많을 경우 10개만 출력
                print(f"\n... 그 외 {len(grouped) - 10}개의 동일한 중복 그룹이 더 있습니다.")
                break
            print(f"\n▶ 상가업소번호 [{name}] ({len(group)}번 중복 발생)")
            print(f"   상호명: {group.iloc[0]['상호명']} (지점: {group.iloc[0]['지점명']})")
            print(f"   도로명주소: {group.iloc[0]['도로명주소']}")
            print(f"   업종: {group.iloc[0]['상권업종소분류명']}")
            
    elif len(dup_by_id) > 0:
        print("\n[상가업소번호는 같지만 일부 다른 내용이 있는 중복 데이터]")
        grouped = dup_by_id.groupby('상가업소번호')
        for name, group in grouped:
            print(f"\n▶ 상가업소번호: {name}")
            for i, (_, row) in enumerate(group.iterrows(), 1):
                print(f"   ({i}) 상호명: {row['상호명']} | 도로명주소: {row['도로명주소']} | 업종: {row['상권업종소분류명']}")
    else:
        print("\n중복된 데이터가 전혀 없습니다! 아주 깔끔합니다.")
        
if __name__ == "__main__":
    main()
