import pandas as pd
import os

# 1. 키워드 파일 리스트 (2016~2025)
keyword_files = [
    "2016년 키워드.csv", "2017년 키워드.csv", "2018년 키워드.csv", 
    "2019년 키워드.csv", "2020년 키워드.csv", "2021년 키워드.csv", 
    "2022년 키워드.csv", "2023년 키워드.csv", "2024년 키워드.csv", 
    "2025년 키워드.csv"
]

# 2. 키워드-학과 매핑 딕셔너리 생성
keyword_dept_map = {}

for file in keyword_files:
    try:
        # 파일 읽기
        df = pd.read_csv(file)
        # 키워드와 학과 컬럼이 있는지 확인 (대소문자 무시 및 공백 제거 처리)
        df.columns = [c.strip() for c in df.columns]
        
        if 'Keyword' in df.columns and 'Department' in df.columns:
            # {키워드: 학과} 형태로 저장. 
            # 여러 파일에 같은 키워드가 있을 경우, 나중에 읽은 파일(최신 연도) 정보로 덮어씌워질 수 있으나,
            # 통상 학과 매핑은 연도별로 변하지 않는다고 가정하고 진행합니다.
            for idx, row in df.iterrows():
                kw = str(row['Keyword']).strip()
                dept = str(row['Department']).strip()
                keyword_dept_map[kw] = dept
    except Exception as e:
        print(f"Error reading {file}: {e}")

# 3. 생기부 정리 파일 불러오기 및 수정
target_file = "생기부 정리.csv"
target_df = pd.read_csv(target_file)

# 매핑 적용 함수
def update_dept_name(row):
    # 생기부 파일의 매칭 키워드 가져오기
    matched_kw = str(row['matched_keyword']).strip()
    
    # 매핑 딕셔너리에 해당 키워드가 있으면 학과명 반환, 없으면 원래 학과명 유지
    if matched_kw in keyword_dept_map:
        return keyword_dept_map[matched_kw]
    else:
        return row['dept_name']

# dept_name 업데이트
target_df['dept_name'] = target_df.apply(update_dept_name, axis=1)

# 4. 결과 확인 및 저장
# 변경된 내용 일부 출력 (예: 코로나가 포함된 행 확인)
print("Mapping Sample (Keyword -> Dept):")
sample_keys = ['코로나', '알파고', '미세먼지']
for k in sample_keys:
    if k in keyword_dept_map:
        print(f"{k} -> {keyword_dept_map[k]}")

print("\nUpdated DataFrame Head:")
print(target_df[['matched_keyword', 'dept_name']].head())

# 파일 저장
output_filename = "생기부_정리_학과수정완료.csv"
target_df.to_csv(output_filename, index=False, encoding='utf-8-sig')