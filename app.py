import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import glob
import os
import seaborn as sns # 처음 실행 시 pip install seaborn

# ---------------------------------------------------------
# 1. 기본 설정 및 폰트
# ---------------------------------------------------------
st.set_page_config(page_title="학과별 생기부 트렌드 매칭 분석", layout="wide")

# 한글 폰트 설정
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
except:
    plt.rcParams['font.family'] = 'AppleGothic'    # Mac
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# 2. 데이터 로드 함수
# ---------------------------------------------------------

@st.cache_data
def load_keyword_data():
    """
    과거 트렌드 데이터 로드
    """
    files = glob.glob("*년 키워드.csv") + glob.glob("data/keyword/*년 키워드.csv")
    all_dfs = []
    for filename in files:
        if "25년도 트랜드" in filename:
            continue
            
        try:
            df = pd.read_csv(filename)
            def parse_date(date_str):
                for fmt in ['%y-%b', '%b-%y', '%Y-%m', '%Y.%m']:
                    try: return pd.to_datetime(date_str, format=fmt)
                    except: continue
                return pd.NaT
            df['Date_Parsed'] = df['Date'].apply(parse_date)
            df = df.dropna(subset=['Date_Parsed'])
            all_dfs.append(df)
        except Exception:
            continue
            
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

@st.cache_data
def load_student_summary():
    """
    생기부 요약 데이터 로드
    """
    file_path = "data/shcool_record/생기부 정리.csv"
    try:
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"생기부 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def load_2025_trend():
    """
    2025년도 트렌드 데이터 로드
    """
    file_path = "data/keyword/25년도 트랜드.csv"
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            def parse_date(date_str):
                for fmt in ['%b-%y', '%y-%b', '%Y-%m', '%Y.%m']: 
                    try: return pd.to_datetime(date_str, format=fmt)
                    except: continue
                return pd.NaT
            
            df['Date_Parsed'] = df['Date'].apply(parse_date)
            df = df.dropna(subset=['Date_Parsed'])
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"2025 트렌드 데이터 로드 실패: {e}")
        return pd.DataFrame()

# 데이터 로드 실행
keyword_df = load_keyword_data()
student_df = load_student_summary()
trend_2025_df = load_2025_trend()

# ---------------------------------------------------------
# 3. 메인 앱 로직
# ---------------------------------------------------------
st.title("📈 학과별 뉴스 키워드 트렌드 & 생기부 매칭 분석")
st.markdown("---")

if keyword_df.empty and trend_2025_df.empty:
    st.error("❌ 키워드 데이터 파일들을 찾을 수 없습니다.")
elif student_df.empty:
    st.error("❌ '생기부 정리.csv' 파일을 찾을 수 없습니다.")
else:
    # -----------------------------------------------------
    # 3.1. 사이드바 옵션
    # -----------------------------------------------------
    st.sidebar.header("🔍 분석 옵션")
    
    if 'dept_name' in student_df.columns:
        dept_list = sorted(student_df['dept_name'].unique().astype(str))
        selected_dept = st.sidebar.selectbox("학과 선택 (Department)", dept_list)
    else:
        st.error("'생기부 정리.csv'에 'dept_name' 컬럼이 없습니다.")
        st.stop()

    # -----------------------------------------------------
    # 3.2. 데이터 필터링 및 통계 계산
    # -----------------------------------------------------
    target_student_df = student_df[student_df['dept_name'] == selected_dept].copy()
    
    # 이상치 제외 (0~2년)
    valid_lags = target_student_df[(target_student_df['time_lag'] >= 0) & (target_student_df['time_lag'] <= 2)]
    if not valid_lags.empty:
        avg_lag = valid_lags['time_lag'].mean()
        avg_lag_text = f"{avg_lag:.2f}년"
    else:
        avg_lag_text = "데이터 없음"

    col1, col2 = st.columns(2)
    col1.metric("선택된 학과", selected_dept)
    col2.metric("평균 반응 시차 (Lag)", avg_lag_text, help="뉴스가 발생한 후 생기부에 기록되기까지 걸린 평균 시간")

    st.markdown("---")

    # -----------------------------------------------------
    # 3.3. 과거 키워드별 그래프 (매칭된 키워드)
    # -----------------------------------------------------
    matched_keywords = target_student_df['matched_keyword'].unique()
    
    if len(matched_keywords) == 0:
        st.warning(f"'{selected_dept}' 학과 데이터에서 매칭된 과거 키워드 기록을 찾을 수 없습니다.")
    else:
        st.subheader(f"📊 {selected_dept} 관련 주요 이슈 트렌드 (과거 분석)")
        
        for kw in matched_keywords:
            kw_trend = keyword_df[keyword_df['Keyword'] == kw].sort_values('Date_Parsed')
            
            if kw_trend.empty:
                continue
                
            matched_activities = target_student_df[target_student_df['matched_keyword'] == kw]
            
            if matched_activities.empty:
                continue
            
            g_col1, g_col2 = st.columns([3, 1])
            
            with g_col1:
                fig, ax = plt.subplots(figsize=(10, 4))
                
                # 1) 뉴스 트렌드 라인
                ax.plot(kw_trend['Date_Parsed'], kw_trend['Count'], 
                        color='#1f77b4', marker='o', markersize=3, label='뉴스 언급량')
                
                # 2) 평균 활동 시점 계산
                avg_activity_year = matched_activities['activity_year'].mean()
                avg_time_lag = matched_activities['time_lag'].mean()
                
                base_year = int(avg_activity_year)
                days_offset = int((avg_activity_year - base_year) * 365)
                avg_plot_date = pd.to_datetime(f"{base_year}-11-01") + pd.Timedelta(days=days_offset)
                
                y_max = kw_trend['Count'].max()
                if pd.isna(y_max) or y_max == 0: y_max = 10
                
                # 평균 지점(별표) 표시
                ax.scatter([avg_plot_date], [y_max * 0.5],
                           color='red', s=200, marker='*', zorder=5, label='평균 활동 시점')
                
                # 텍스트 라벨
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
                
                with st.expander("세부 활동 내역 보기"):
                    for _, row in matched_activities.iterrows():
                        st.caption(f"[{row['student_id']}] {row['activity_year']}년 (Lag {row['time_lag']}년)")
                        context_text = str(row['context'])
                        if len(context_text) > 80: context_text = context_text[:80] + "..."
                        st.write(f"- {context_text}")
            
            st.divider()

    # -----------------------------------------------------
    # 4. 2025년도 학과별 트렌드 및 활동 예측
    # -----------------------------------------------------
    st.markdown("---")
    st.header(f"📅 2025년도 {selected_dept} 키워드 트렌드 및 예상 활동 시점")
    
    if trend_2025_df.empty:
        st.info("2025년도 트렌드 데이터가 없습니다.")
    else:
        # 데이터 필터링
        trend_2025_df['Department'] = trend_2025_df['Department'].astype(str).str.strip()
        dept_trend = trend_2025_df[trend_2025_df['Department'] == selected_dept].copy()
        
        if dept_trend.empty:
            st.warning(f"'{selected_dept}' 학과에 해당하는 2025년 데이터가 없습니다.")
        else:
            dept_trend = dept_trend.sort_values('Date_Parsed')
            
            # 그래프 생성
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            
            keywords_2025 = dept_trend['Keyword'].unique()
            colors = sns.color_palette("husl", len(keywords_2025))
            
            for i, kw in enumerate(keywords_2025):
                subset = dept_trend[dept_trend['Keyword'] == kw]
                ax2.plot(subset['Date_Parsed'], subset['Count'], 
                         marker='o', linestyle='-', linewidth=2, markersize=6,
                         color=colors[i], label=kw)
            
            # 전략 가이드 생성을 위한 변수 초기화
            predicted_date = None
            avg_lag_years = 0
            
            # -------------------------------------------------
            # 트렌드 중심 및 예상 활동 시점 계산
            if not target_student_df.empty and not dept_trend.empty:
                
                # A. 과거 데이터 기반 평균 반응 시차 계산
                valid_lags = target_student_df[
                    (target_student_df['time_lag'] >= 0) & 
                    (target_student_df['time_lag'] <= 5)
                ]
                
                if not valid_lags.empty:
                    avg_lag_years = valid_lags['time_lag'].mean()
                    
                    # 1. 예상 활동 연도 계산 (2025년 + 평균 시차)
                    target_year_float = 2025 + avg_lag_years
                    
                    # 2. 연도 정수 부분과 소수 부분 분리
                    base_year_int = int(target_year_float)      # 예: 2025
                    fractional_diff = target_year_float - base_year_int # 예: 0.0 or 0.5
                    
                    # 3. 해당 연도의 11월 1일 기준 설정
                    base_date_nov1 = pd.to_datetime(f"{base_year_int}-11-01")
                    
                    # 4. 소수점 연도 보정 (시차가 1.5년이면 0.5년치 날짜를 더함)
                    days_offset = int(fractional_diff * 365)
                    predicted_date = base_date_nov1 + pd.Timedelta(days=days_offset)
                    
                    # -----------------------------------------------------------
                    # D. 시각화 (별표 표시)
                    # -----------------------------------------------------------
                    y_max_2025 = dept_trend['Count'].max()
                    if pd.isna(y_max_2025) or y_max_2025 == 0: y_max_2025 = 10
                    
                    ax2.scatter([predicted_date], [y_max_2025 * 0.5], 
                                color='red', s=250, marker='*', zorder=10, 
                                label=f'예상 활동 (Lag {avg_lag_years:.1f}년)', 
                                edgecolors='white', linewidth=1.5)
                    
                    date_str = predicted_date.strftime('%Y년 %m월')
                    # 텍스트 라벨 내용도 변경
                    label_text = f"기준점 + 시차 보정\n예상: {date_str}"
                    
                    ax2.text(predicted_date, y_max_2025 * 0.60, 
                             label_text, 
                             color='red', fontsize=10, ha='center', fontweight='bold',
                             bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', boxstyle='round,pad=0.3'))
            # 그래프 데코레이션
            ax2.set_title(f"2025년 {selected_dept} 트렌드 기반 예상 활동 시점", fontsize=16, fontweight='bold')
            ax2.set_xlabel("날짜 (2025년 ~)", fontsize=12)
            ax2.set_ylabel("검색량 / 언급량", fontsize=12)
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.grid(True, linestyle='--', alpha=0.5)
            
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m'))
            ax2.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=45)
            
            st.pyplot(fig2)

            # -------------------------------------------------
            # 맞춤형 전략 가이드 출력
            # -------------------------------------------------
            if predicted_date is not None:
                top_keyword = dept_trend.groupby('Keyword')['Count'].sum().idxmax()
                rec_date_str = predicted_date.strftime('%Y년 %m월')
                
                st.success(f"""
                ### 🚀 **{selected_dept} 맞춤 전략 가이드**
                
                **{top_keyword}**에 대한 심화 탐구(세특) 내용을  
                👉 **{rec_date_str}** 쯤에 작성하여 제출하는 것을 추천합니다.
                
                ---
                * **이유:** {selected_dept} 선배들의 과거 데이터를 분석했을 때, 사회적 이슈가 발생한 후 평균 **약 {avg_lag_years:.1f}년** 뒤에 생기부에 기록되는 패턴이 있습니다.  
                * 남들보다 빠르거나 늦지 않게, 학과 특성에 맞는 **최적의 타이밍**을 선점하세요!
                """)
                
            with st.expander("데이터 상세 보기"):
                st.dataframe(dept_trend[['Date', 'Keyword', 'Category', 'Count']])