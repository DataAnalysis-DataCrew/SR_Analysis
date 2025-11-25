import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. 기본 설정 및 폰트 처리
# ---------------------------------------------------------
st.set_page_config(page_title="사회적 이슈와 생기부 동조화 분석", layout="wide")

# 한글 폰트 설정 (시스템에 따라 다를 수 있음, 깨지면 영어로 테스트)
plt.rcParams['font.family'] = 'Malgun Gothic' # Windows 기준
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# 2. Mock Data (가짜 데이터) 생성기 - 데이터 파일 없을 때 사용
# ---------------------------------------------------------
def get_mock_database():
    """
    실제 CSV가 없을 때, 로직 시연을 위해 가상의 데이터를 생성하여 반환합니다.
    구조: 연도 | 키워드 | 카테고리 | 뉴스_트렌드(월별) | 생기부_등장_월
    """
    
    # [Case 1: 과거 데이터 - AlphaGo (2016)]
    # 뉴스 피크: 3월 / 생기부 등장: 9월 (약 6개월 시차)
    dates_2016 = pd.date_range(start="2016-01-01", periods=12, freq='M')
    trend_alphago = [20, 100, 500, 300, 100, 50, 40, 30, 80, 60, 40, 20] # 3월 피크
    
    # [Case 2: 최신 데이터 - 생성형 AI (2024)]
    # 뉴스 피크: 10월 / 생기부 예측: 내년 4월
    dates_2024 = pd.date_range(start="2024-01-01", periods=12, freq='M')
    trend_gen_ai = [50, 60, 80, 100, 120, 150, 200, 300, 400, 600, 500, 450] # 10월 피크

    data = [
        {
            "year": 2016,
            "keyword": "AlphaGo (알파고)",
            "category": "SW/AI",
            "dates": dates_2016,
            "news_volume": trend_alphago,
            "student_record_date": datetime(2016, 9, 15), # 실제 생기부 등장 시점
            "lag_month": 6
        },
        {
            "year": 2024,
            "keyword": "Generative AI (생성형 AI)",
            "category": "SW/AI",
            "dates": dates_2024,
            "news_volume": trend_gen_ai,
            "student_record_date": None, # 미래라 아직 없음 (예측 대상)
            "lag_month": None
        },
        # 다른 카테고리 예시
        {
            "year": 2016,
            "keyword": "경주 지진",
            "category": "지구과학/안전",
            "dates": dates_2016,
            "news_volume": [10, 10, 10, 10, 10, 20, 30, 50, 600, 400, 100, 50], # 9월 피크
            "student_record_date": datetime(2017, 3, 10), # 다음 학기 등장
            "lag_month": 6
        }
    ]
    return data

# ---------------------------------------------------------
# 3. 메인 화면 로직
# ---------------------------------------------------------
st.title("📊 뉴스 트렌드 기반 생기부 주제 추천 시스템")
st.markdown("""
이 프로그램은 **'사회적 이슈가 약 6개월 뒤 학교 생기부에 반영된다'**는 통계적 가설을 바탕으로,
현재의 뉴스 트렌드를 분석하여 **다음 학기 탐구 주제**를 예측 및 추천합니다.
""")

# 사이드바: 사용자 입력
st.sidebar.header("검색 조건 설정")
selected_category = st.sidebar.selectbox("관심 분야 선택", ["SW/AI", "지구과학/안전", "사회/경제"])
st.sidebar.info("현재 프로토타입 모드입니다.\n(Mock Data 사용 중)")

# 데이터 로드
db = get_mock_database()

# 해당 카테고리의 데이터 필터링
filtered_data = [d for d in db if d['category'] == selected_category]

if not filtered_data:
    st.warning("해당 분야의 샘플 데이터가 아직 없습니다.")
else:
    # -----------------------------------------------------
    # [Part 1] 모델 검증 (과거 데이터)
    # -----------------------------------------------------
    st.header(f"1. [Model Verification] {selected_category} 분야의 시차 분석")
    
    # 과거 데이터(2024년 이전)만 가져오기
    past_cases = [d for d in filtered_data if d['year'] < 2024]
    
    if past_cases:
        case = past_cases[0] # 첫 번째 예시 사용
        st.subheader(f"📋 분석 사례: {case['year']}년 '{case['keyword']}'")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 그래프 그리기
            fig, ax1 = plt.subplots(figsize=(10, 4))
            
            # 뉴스 트렌드 (Line)
            ax1.plot(case['dates'], case['news_volume'], color='blue', label='뉴스 언급량', linewidth=2)
            ax1.set_ylabel('뉴스 빈도', color='blue')
            ax1.tick_params(axis='y', labelcolor='blue')
            ax1.grid(True, linestyle='--', alpha=0.5)
            
            # 생기부 등장 시점 (Vertical Line & Scatter)
            ax2 = ax1.twinx()
            ax2.set_ylim(0, 10) # 스케일 임의 조정
            ax2.set_yticks([]) # y축 눈금 제거
            
            # 생기부 기록 시점 표시
            record_date = case['student_record_date']
            ax2.axvline(x=record_date, color='red', linestyle=':', linewidth=2, label='생기부 기록 시점')
            ax2.scatter([record_date], [5], color='red', s=150, zorder=10, marker='*')
            ax2.text(record_date, 5.5, " 생기부 등장", color='red', fontweight='bold')

            ax1.set_title(f"뉴스 트렌드와 생기부 기록 시점 비교 ({case['keyword']})")
            st.pyplot(fig)
            
        with col2:
            st.metric(label="뉴스 피크 시점", value="3월")
            st.metric(label="생기부 기록 시점", value="9월")
            st.success(f"⏱️ 분석된 시차\n\n**+{case['lag_month']}개월**")
            
        st.info(f"💡 **통계적 결론:** {selected_category} 분야의 사회적 이슈는 평균적으로 **{case['lag_month']}개월의 지연(Lag)**을 두고 학교 현장에 반영되는 경향이 있습니다.")

    else:
        st.write("과거 분석 데이터가 없습니다.")

    st.markdown("---")

    # -----------------------------------------------------
    # [Part 2] 미래 예측 (2024년 -> 2025년)
    # -----------------------------------------------------
    st.header("2. [Prediction] 2025년 1학기 추천 주제")
    
    # 최신 데이터(2024년) 가져오기
    future_cases = [d for d in filtered_data if d['year'] == 2024]
    
    if future_cases:
        target = future_cases[0]
        
        # 예측 시점 계산 (뉴스 피크 + 6개월)
        # 간단히 데이터에서 max값 찾기
        peak_idx = np.argmax(target['news_volume'])
        peak_date = target['dates'][peak_idx]
        predicted_date = peak_date + timedelta(days=30*6) # +6개월
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.write(f"### 🔥 급상승 키워드: {target['keyword']}")
            st.line_chart(pd.DataFrame({'News Trend': target['news_volume']}, index=target['dates']))
            
        with col_p2:
            st.write("### 🎯 AI 예측 결과")
            st.markdown(f"""
            * **현재 트렌드 상태:** <span style='color:red'>급상승세 (Peak: {peak_date.strftime('%Y-%m')})</span>
            * **과거 데이터 기반 시차:** +6개월 적용
            * **예상되는 생기부 반영 최적기:**
            # 📅 {predicted_date.strftime('%Y년 %m월')} (내년 1학기)
            """, unsafe_allow_html=True)
            
            st.success("✅ **추천 활동:** 생성형 AI의 저작권 면책 조항에 관한 모의 법정")
            
    else:
        st.write("추천할 최신 트렌드 데이터가 없습니다.")