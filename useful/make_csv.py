import pandas as pd

# -------------------------------------------------------
# 1. 설정: 키워드별 [카테고리, 관련학과] 매핑 정의
# -------------------------------------------------------
# 형식: "키워드": ("대분류", "학과")
keyword_map = {
    # [2016년 예시]
    "AlphaGo": ("IT/과학", "컴퓨터공학과"),
    "이세돌": ("IT/과학", "컴퓨터공학과"),
    "경주 지진": ("사회/안전", "지구환경과학과"),
    "가습기 살균제": ("사회/보건", "화학공학과"), # 혹은 환경공학과
    "포켓몬 GO": ("IT/문화", "게임콘텐츠학과"), # 혹은 소프트웨어학과
    "지카 바이러스": ("의료/보건", "간호학과"),  # 혹은 의예과
    
    # [2024년 예시]
    "생성형 AI": ("IT/과학", "인공지능학과"),
    "의대 증원": ("사회/정책", "의예과"),
    "저출산": ("사회/경제", "사회학과"),
    
    # ... 나머지 키워드들도 이렇게 작성 ...
}

# -------------------------------------------------------
# 2. 데이터 로드
# -------------------------------------------------------
# 빅카인즈에서 다운로드 받은 엑셀 파일명 입력
file_path = 'BigKinds_Raw_Data.xlsx' 
# csv라면: df = pd.read_csv('filename.csv')
df = pd.read_excel(file_path)

print(f"원본 데이터 로드 완료: {len(df)}건")

# -------------------------------------------------------
# 3. 전처리 및 데이터 추출 로직
# -------------------------------------------------------

# (1) 날짜 변환 (YYYYMMDD -> YYYY-MM)
df['일자'] = df['일자'].astype(str)
df['Date'] = pd.to_datetime(df['일자'], format='%Y%m%d').dt.to_period('M')

results = []

# (2) 키워드별 루프
for keyword, (category, dept) in keyword_map.items():
    # 해당 키워드가 포함된 기사 필터링 (키워드 컬럼 or 제목)
    mask = (
        df['키워드'].str.contains(keyword, na=False) | 
        df['제목'].str.contains(keyword, na=False)
    )
    filtered_df = df[mask]
    
    # 월별 빈도수 계산
    monthly_counts = filtered_df.groupby('Date').size()
    
    # 결과 리스트에 추가
    for date, count in monthly_counts.items():
        results.append({
            'Date': str(date),       # 예: 2016-03
            'Keyword': keyword,      # 예: AlphaGo
            'Category': category,    # 예: IT/과학
            'Department': dept,      # [NEW] 예: 컴퓨터공학과
            'Count': count           # 예: 521
        })

# -------------------------------------------------------
# 4. 저장
# -------------------------------------------------------
final_df = pd.DataFrame(results)

# 컬럼 순서 정렬 (보기 좋게)
final_df = final_df[['Date', 'Keyword', 'Category', 'Department', 'Count']]

# CSV 저장
output_filename = 'processed_news_trend_with_dept.csv'
final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"\n[완료] 총 {len(final_df)}개의 월별 데이터가 생성되었습니다.")
print(f"파일 저장됨: {output_filename}")
print("\n--- 데이터 미리보기 ---")
print(final_df.head())