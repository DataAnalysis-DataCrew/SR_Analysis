import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import glob # 파일 목록을 찾기 위해 사용

# ---------------------------------------------------------
# 1. 기본 설정 및 한글 폰트
# ---------------------------------------------------------
st.set_page_config(page_title="연도별 통합 트렌드 분석", layout="wide")

try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
except:
    plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# 2. 데이터 로드 (여러 CSV 파일 통합 기능 추가)
# ---------------------------------------------------------
@st.cache_data
def load_all_data(file_list):
    all_dfs = []
    
    for file_path in file_list:
        try:
            df = pd.read_csv(file_path)
            
            # 결측치 제거 (빈 줄 삭제)
            df = df.dropna(subset=['Date', 'Keyword', 'Count'])
            
            # 날짜 변환 함수 (두 가지 형식 모두 지원)
            def parse_date(date_str):
                try:
                    # 1. '16-Mar' (년-월) 형식
                    return pd.to_datetime(date_str, format='%y-%b')
                except:
                    try:
                        # 2. 'Sep-16' (월-년) 형식
                        return pd.to_datetime(date_str, format='%b-%y')
                    except:
                        return pd.NaT

            df['Date_Parsed'] = df['Date'].apply(parse_date)
            df = df.dropna(subset=['Date_Parsed']) # 날짜 변환 실패 행 제거
            
            all_dfs.append(df)
            
        except Exception as e:
            st.error(f"'{file_path}' 로드 중 오류: {e}")
            
    if all_dfs:
        # 모든 연도의 데이터를 하나로 합치기
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

# ---------------------------------------------------------
# 3. 학생 생기부 매핑 데이터 (필요 시 수정/추가)
# ---------------------------------------------------------
STUDENT_RECORDS = {
    # 2016년
    "알파고": "2016-09-15",
    "포켓몬GO": "2016-10-20", 
    "경주 지진": "2016-11-01",
    "가습기 살균제": "2016-05-20",
    # 2017년
    "4차산업혁명": "2017-09-10",
    "미세먼지": "2017-05-15",
    "비트코인": "2018-01-20", # 시차가 해를 넘길 수도 있음
    "포항 지진": "2017-11-20",
    # 2018년
    "남북회담": "2018-05-01",
    "평창 올림픽": "2018-03-10",
    "BMW 화재": "2018-09-01"
}

# ---------------------------------------------------------
# 4. 메인 앱 로직
# ---------------------------------------------------------
st.title("📊 연도별 CSV 통합 분석 시스템")

# (1) 데이터 로드: 파일 리스트를 직접 지정하거나, glob으로 찾을 수 있음
target_files = ['data/keyword/2016년 키워드.csv', 'data/keyword/2017년 키워드.csv', 'data/keyword/2018년 키워드.csv', 'data/keyword/2021년 키워드.csv'
                ,'data/keyword/2022년 키워드.csv', 'data/keyword/2023년 키워드.csv', 'data/keyword/2024년 키워드.csv']
# 만약 파일이 더 많다면 아래 주석을 풀어서 자동으로 찾게 할 수도 있습니다.
# target_files = glob.glob("*년 키워드.csv") 

df = load_all_data(target_files)

if not df.empty:
    # (2) 사이드바: 카테고리 선택
    st.sidebar.header("🔍 분석 옵션")
    
    categories = df['Category'].unique()
    selected_category = st.sidebar.selectbox("분석할 카테고리 선택", categories)
    
    # 해당 카테고리 데이터만 추출
    category_df = df[df['Category'] == selected_category]
    keywords_in_category = category_df['Keyword'].unique()
    
    st.header(f"📂 [{selected_category}] 분야 키워드별 상세 분석")
    st.caption(f"총 {len(keywords_in_category)}개의 이슈가 발견되었습니다.")

    # (3) 키워드별로 그래프 따로 그리기 (반복문)
    for kw in keywords_in_category:
        st.markdown("---") # 구분선
        
        # 특정 키워드 데이터 추출 및 정렬
        subset = category_df[category_df['Keyword'] == kw].sort_values('Date_Parsed')
        
        # 데이터가 비어있지 않은지 확인
        if subset.empty:
            continue
            
        # 레이아웃: 왼쪽(그래프) / 오른쪽(설명)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            fig, ax1 = plt.subplots(figsize=(10, 4))
            
            # 뉴스 트렌드 선 그래프
            ax1.plot(subset['Date_Parsed'], subset['Count'], 
                     marker='o', markersize=4, color='#1f77b4', label='뉴스 빈도')
            
            # 생기부 기록 시점 (빨간선) 표시
            if kw in STUDENT_RECORDS:
                record_date = pd.to_datetime(STUDENT_RECORDS[kw])
                
                # 그래프 X축 범위 자동 조정 (생기부 날짜가 그래프 범위를 벗어날 경우 대비)
                min_date = min(subset['Date_Parsed'].min(), record_date)
                max_date = max(subset['Date_Parsed'].max(), record_date)
                # 여유 공간 추가 (7일 정도)
                ax1.set_xlim(min_date - pd.Timedelta(days=15), max_date + pd.Timedelta(days=15))

                # 수직선
                ax1.axvline(x=record_date, color='red', linestyle='--', linewidth=1.5, label='생기부 기록')
                # 별 마커
                ax1.scatter([record_date], [subset['Count'].max() * 0.5], color='red', s=150, marker='*', zorder=5)
                # 텍스트
                ax1.text(record_date, subset['Count'].max() * 0.55, " 생기부", color='red', fontweight='bold')

            # 그래프 스타일링
            ax1.set_title(f"'{kw}' 뉴스 트렌드", fontsize=14, fontweight='bold')
            ax1.set_ylabel('기사 건수')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax1.grid(True, linestyle='--', alpha=0.3)
            ax1.legend()
            
            st.pyplot(fig)
            
        with col2:
            # 통계 요약 카드
            max_val = subset['Count'].max()
            peak_date = subset.loc[subset['Count'].idxmax(), 'Date_Parsed']
            dept_name = subset.iloc[0]['Department']
            
            st.subheader(f"📌 {kw}")
            st.write(f"**관련 학과:** {dept_name}")
            st.write(f"**최고 화제:** {peak_date.strftime('%Y년 %m월')}")
            st.write(f"**최대 기사:** {int(max_val)}건")
            
            if kw in STUDENT_RECORDS:
                rec_date = pd.to_datetime(STUDENT_RECORDS[kw])
                diff_days = (rec_date - peak_date).days
                lag_months = round(diff_days / 30, 1)
                
                if diff_days > 0:
                    st.success(f"⏱️ **시차: +{lag_months}개월**\n(뉴스 후 반영됨)")
                else:
                    st.warning(f"⏱️ **시차: {lag_months}개월**\n(동시/사전 반영)")
            else:
                st.info("생기부 데이터 없음")

    # (4) 하단에 전체 통합 데이터 테이블 (접기)
    with st.expander("💾 통합 데이터 원본 보기"):
        st.dataframe(category_df.sort_values(['Keyword', 'Date_Parsed']))

else:
    st.error("불러올 데이터 파일이 없습니다. 폴더에 csv 파일들이 있는지 확인해주세요.")