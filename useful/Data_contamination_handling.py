import pandas as pd

class TextCleaner:
    # 2. Oxy Humidifier Disinfectant (Target: Scandal / Noise: Generic Ads, unrelated chemical cleaning)
    NOISE_KEYWORDS = [
      "테마주", "수혜주", "관련주", "급등", "상한가", 
        "주식", "종목", "매수", "매도", "목표가", 
        "체결", "투자 설명회", "분양", "모델하우스"
    ]

    def filter_noise(self, df: pd.DataFrame, text_column: str) -> pd.DataFrame:
        """특정 컬럼(제목 또는 본문)에서 노이즈 기사 제거"""
        
        if df is None or df.empty:
            print("[Warning] DataFrame is empty. Skipping filtration.")
            return df

        if text_column not in df.columns:
            raise KeyError(f"'{text_column}' 컬럼이 DataFrame에 존재하지 않습니다. 실제 컬럼명을 확인하세요: {df.columns.tolist()}")

        initial_size = len(df)
        pattern = '|'.join(self.NOISE_KEYWORDS)

        mask_noise = df[text_column].astype(str).str.contains(pattern, case=False, na=False)
        df_clean = df[~mask_noise]

        removed = initial_size - len(df_clean)
        print(f"[Filter Report] '{text_column}' 기준으로 {removed}개 기사 제거됨.")
        print(f"[Filter Report] 남은 기사 수: {len(df_clean)}")

        return df_clean


# 엑셀 파일 불러오기
df = pd.read_excel("2017년 4차산업혁명 메타데이터.xlsx")   # 파일 이름은 원하는 것으로 변경

cleaner = TextCleaner()

# 1차: 제목 기준 필터링
df_filtered = cleaner.filter_noise(df, text_column='제목')

# 2차: 본문 기준 필터링
df_filtered = cleaner.filter_noise(df_filtered, text_column='본문')

# 결과 저장
df_filtered.to_excel("2017년 4차산업혁명 메타데이터_수정.xlsx", index=False)

print("필터링 완료!")




