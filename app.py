import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import glob
import os

# ---------------------------------------------------------
# 1. 기본 설정 및 한글 폰트
# ---------------------------------------------------------
st.set_page_config(page_title="학과별 생기부 트렌드 매칭 분석", layout="wide")

# 한글 폰트 설정 (Mac/Windows 호환)
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
except:
    plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# 2. 데이터 로드 함수
# ---------------------------------------------------------

@st.cache_data
def load_keyword_data():
    """
    폴더 내의 '*년 키워드.csv' 파일들을 모두 읽어 통합합니다.
    """
    # 현재 폴더 및 하위 데이터 폴더 검색
    files = glob.glob("*년 키워드.csv") + glob.glob("data/keyword/*년 키워드.csv")
    
    all_dfs = []
    for filename in files:
        try:
            df = pd.read_csv(filename)
            # 날짜 파싱 (다양한 포맷 대응)
            def parse_date(date_str):
                for fmt in ['%y-%b', '%b-%y', '%Y-%m', '%Y.%m']:
                    try: return pd.to_datetime(date_str, format=fmt)
                    except: continue
                return pd.NaT

            df['Date_Parsed'] = df['Date'].apply(parse_date)
            df = df.dropna(subset=['Date_Parsed'])
            all_dfs.append(df)
        except Exception as e:
            st.error(f"키워드 파일 로드 중 오류 발생 ({filename}): {e}")
            
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

@st.cache_data
def load_student_summary():
    """
    '생기부 정리.csv' 파일을 로드합니다.
    """
    # 파일 경로 (필요시 경로 수정)
    file_path = "생기부 정리.csv"
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"생기부 데이터 로드 실패: {e}")
        return pd.DataFrame()

# 데이터 로드
keyword_df = load_keyword_data()
student_df = load_student_summary()

# ---------------------------------------------------------
# 3. 메인 앱 로직
# ---------------------------------------------------------
st.title("📈 학과별 뉴스 키워드 트렌드 & 생기부 매칭 분석")
st.markdown("---")

if keyword_df.empty:
    st.error("❌ 키워드 데이터 파일(*년 키워드.csv)을 찾을 수 없습니다.")
elif student_df.empty:
    st.error("❌ '생기부 정리.csv' 파일을 찾을 수 없습니다.")
else:
    # -----------------------------------------------------
    # 3.1. 사이드바 옵션 (학과 선택만 남김)
    # -----------------------------------------------------
    st.sidebar.header("🔍 분석 옵션")
    
    # 학과 목록 추출 및 선택
    if 'dept_name' in student_df.columns:
        dept_list = sorted(student_df['dept_name'].unique().astype(str))
        selected_dept = st.sidebar.selectbox("학과 선택 (Department)", dept_list)
    else:
        st.error("'생기부 정리.csv'에 'dept_name' 컬럼이 없습니다.")
        st.stop()

    # -----------------------------------------------------
    # 3.2. 데이터 필터링 및 통계 계산
    # -----------------------------------------------------
    # 선택한 학과의 생기부 데이터 필터링
    target_student_df = student_df[student_df['dept_name'] == selected_dept].copy()
    
    # 평균 시차 계산 (선택된 학과 전체 기준, 유효 데이터만)
    valid_lags = target_student_df[(target_student_df['time_lag'] >= 0) & (target_student_df['time_lag'] <= 2)]
    if not valid_lags.empty:
        avg_lag = valid_lags['time_lag'].mean()
        avg_lag_text = f"{avg_lag:.2f}년"
    else:
        avg_lag_text = "데이터 없음"

    # 상단 요약 정보 표시
    col1, col2 = st.columns(2)
    col1.metric("선택된 학과", selected_dept)
    col2.metric("평균 반응 시차 (Lag)", avg_lag_text, help="뉴스가 발생한 후 생기부에 기록되기까지 걸린 평균 시간 (0~2년 데이터 기준)")

    st.markdown("---")

    # -----------------------------------------------------
    # 3.3. 키워드별 그래프 그리기 (매칭된 키워드만 표시)
    # -----------------------------------------------------
    
    # 이 학과 학생들이 활동한 키워드 목록 추출 (중복 제거)
    matched_keywords = target_student_df['matched_keyword'].unique()
    
    if len(matched_keywords) == 0:
        st.warning(f"'{selected_dept}' 학과 데이터에서 매칭된 키워드를 찾을 수 없습니다.")
    else:
        st.subheader(f"📊 {selected_dept} 관련 주요 이슈 트렌드")
        
        # 키워드 순회 (매칭된 것만)
        for kw in matched_keywords:
            # 해당 키워드의 뉴스 트렌드 데이터 조회
            kw_trend = keyword_df[keyword_df['Keyword'] == kw].sort_values('Date_Parsed')
            
            # 뉴스 데이터가 없는 경우 스킵
            if kw_trend.empty:
                continue
                
            # 해당 키워드와 매칭되는 학생 활동 데이터
            matched_activities = target_student_df[target_student_df['matched_keyword'] == kw]
            
            # 활동 데이터가 없으면 스킵
            if matched_activities.empty:
                continue
            
            # 레이아웃: 그래프(3) + 설명(1)
            g_col1, g_col2 = st.columns([3, 1])
            
            with g_col1:
                fig, ax = plt.subplots(figsize=(10, 4))
                
                # 1) 뉴스 트렌드 선 그래프
                ax.plot(kw_trend['Date_Parsed'], kw_trend['Count'], 
                        color='#1f77b4', marker='o', markersize=3, label='뉴스 언급량')
                
                # 2) 생기부 활동 시점 평균 점 표시 (Average Point)
                # 활동 연도의 평균 계산 (예: 2020, 2021 -> 평균 2020.5년)
                avg_activity_year = matched_activities['activity_year'].mean()
                avg_time_lag = matched_activities['time_lag'].mean()
                
                # 평균 연도를 날짜 형식으로 변환 (해당 연도 1월 1일 + 오차일수)
                base_year = int(avg_activity_year)
                days_offset = int((avg_activity_year - base_year) * 365)
                # 시각적으로 보기 좋게 해당 연도의 중간쯤에 찍히도록 7월 1일 기준 보정 가능하나, 
                # 여기서는 수학적 평균 날짜로 변환합니다.
                avg_plot_date = pd.to_datetime(f"{base_year}-01-01") + pd.Timedelta(days=days_offset)
                
                # 뉴스 빈도 최대값의 50% 높이에 점 표시
                y_max = kw_trend['Count'].max()
                if pd.isna(y_max) or y_max == 0: y_max = 10
                
                # 평균 지점(별표) 표시
                ax.scatter([avg_plot_date], [y_max * 0.5],
                           color='red', s=200, marker='*', zorder=5, label='평균 활동 시점')
                
                # 텍스트 라벨 (평균 시차 정보)
                label_text = f"평균 시차: {avg_time_lag:.1f}년\n(활동수: {len(matched_activities)}건)"
                ax.text(avg_plot_date, y_max * 0.58, 
                        label_text, 
                        color='red', fontsize=10, ha='center', fontweight='bold', 
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.3'))
            
                ax.set_title(f"Keyword: {kw}", fontweight='bold')
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                ax.grid(True, linestyle='--', alpha=0.3)
                ax.legend()
                st.pyplot(fig)
                
            with g_col2:
                st.markdown(f"**📌 {kw}**")
                st.success(f"✅ **{len(matched_activities)}건**의 활동 평균")
                st.write(f"**평균 활동 연도:** {avg_activity_year:.1f}년")
                st.write(f"**평균 반응 시차:** {avg_time_lag:.2f}년 후")
                
                # 개별 활동 내역은 확장해서 볼 수 있도록 숨김 처리
                with st.expander("세부 활동 내역 보기"):
                    for _, row in matched_activities.iterrows():
                        st.caption(f"[{row['student_id']}] {row['activity_year']}년 (Lag {row['time_lag']}년)")
                        context_text = str(row['context'])
                        # 내용이 너무 길면 자름
                        if len(context_text) > 80: context_text = context_text[:80] + "..."
                        st.write(f"- {context_text}")
            
            st.divider()