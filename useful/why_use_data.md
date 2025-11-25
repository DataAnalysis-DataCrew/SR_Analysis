데이터 오염에 대한 처리
검색 시 예상치 못한 데이터가 추가적으로 검색되는 경우가 발생했다. 그래서 빅카인즈에서 데이터 수집 시 퀴리문을 사용해 데이터 오염을 막고자 했다.
그리고 다운로드한 메타데이터 중에서도 분류하지 못한 추가 오염이 있을 수 있기 때문에 밑 코드를 이용한 추가적인 필터링을 수행했다.
import pandas as pd

class TextCleaner:
    
    NOISE_KEYWORDS = [
        # 제거할 키워드
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
df = pd.read_excel("2017년 포항지진 메타데이터.xlsx")   # 파일 이름은 원하는 것으로 변경

cleaner = TextCleaner()

# 1차: 제목 기준 필터링
df_filtered = cleaner.filter_noise(df, text_column='제목')

# 2차: 본문 기준 필터링
df_filtered = cleaner.filter_noise(df_filtered, text_column='본문')

# 결과 저장
df_filtered.to_excel("2017년 포항지진 메타데이터_수정.xlsx", index=False)

print("필터링 완료!")


제거할 때 사용한 키워드
알파고
빅카인드 검색: 인공지능 OR 알파고 OR 딥러닝 OR 머신러닝 OR (AI AND NOT (조류 OR 독감))
NOISE_KEYWORDS = [
        "조류", "독감", "virus", "바이러스", "살처분", "방역",
        "고병원성", "농가", "닭", "오리", "가금류", "확진",
        "양계", "축산", "폐사", "AI", "인플루엔자"
        
    ]
경주지진
빅카인드 검색: (경주 AND 지진) OR (규모 5.8) OR (내진설계) OR (여진 AND 경주) OR (한반도 AND 지진)
NOISE_KEYWORDS = [
        "마라톤", "경마", "레이스", "달리기", "대회", "선수", 
        "우승", "코스", "F1", "자동차 경주", "체육대회"
    ]
가습기살균제
빅카인드 검색: (가습기 살균제) OR (옥시싹싹) OR (PHMG) OR (PGH) OR (폐손상 AND 가습기)
NOISE_KEYWORDS = [
        "주식", "주가", "투자", "종목", "상한가", "광고", "이벤트", "할인", "항산화"
    ]
포켓몬 고
빅카인드 검색: (포켓몬GO) OR (포켓몬 고) OR (포켓몬 AND (증강현실 OR AR OR 속초))
NOISE_KEYWORDS = [
        "빵", "스티커", "띠부띠부씰", "애니메이션", "만화", "극장판", "카드 게임", "색칠공부", "인형"
    ]
지가 바이러스
빅카인드 검색: (지카바이러스) OR (지카 AND 모기) OR (소두증) OR (이집트숲모기)
NOISE_KEYWORDS = [
        "컴퓨터", "해킹", "랜섬웨어", "지코", "뮤직비디오", "악성코드", "PC방", "백신 프로그램"
    ]
비트코인
빅카인드 검색: `(비트코인) OR (가상화폐) OR (암호화폐) OR (블록체인) OR (이더리움) OR (빗썸)
NOISE_KEYWORDS = [
        "토토", "홀짝", "바카라", "카지노", "도박", "성인", "출장", "대출", "조건만남", "스팸"
    ]
탈원전
빅카인드 검색: ((탈원전) OR (신고리 AND 공론화) OR (에너지전환) OR (원자력발전소 AND 폐쇄)) AND NOT (북한 OR 핵실험 OR 미사일 OR 김정은 OR 핵무기)
``` python
NOISE_KEYWORDS = [
        "토토", "홀짝", "바카라", "카지노", "도박", "성인", "출장", "대출", "조건만남", "스팸"
    ]
미세먼지
빅카인드 검색: (미세먼지) OR (초미세먼지) OR (대기질 AND (경보 OR 주의보)) OR (중국발 AND 먼지)
NOISE_KEYWORDS = [
        "특가", "할인", "쿠팡", "위메프", "티몬", "구매", "공동구매", "사은품", "렌탈", "필터 판매"
    ]
4차 산업 혁명
빅카인드 검색: ("4차 산업혁명") OR ("제4차 산업혁명") OR (4차산업혁명)
NOISE_KEYWORDS = [
        "테마주", "수혜주", "관련주", "급등", "상한가", 
        "주식", "종목", "매수", "매도", "목표가", 
        "체결", "투자 설명회", "분양", "모델하우스"
    ]
포항지진
빅카인드 검색: (포항 AND 지진) OR (수능 연기 AND 지진) OR (필로티 AND 지진) OR (액상화 현상)
NOISE_KEYWORDS = [
        "축구", "스틸러스", "프로축구", "K리그", "경기", 
        "득점", "결승골", "감독", "훈련", "전지훈련"
    ]