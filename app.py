import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import glob
import os

# ---------------------------------------------------------
# 1. 기본 설정 및 한글 폰트
# ---------------------------------------------------------
st.set_page_config(page_title="통합 생기부 트렌드 매칭 시스템", layout="wide")

try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
except:
    plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# 2. 키워드 데이터 로드 (모든 연도 통합)
# ---------------------------------------------------------
@st.cache_data
def load_keyword_data():
    # 1. 파일 찾기 (현재 폴더 및 data/keyword 폴더)
    files_in_root = glob.glob("*년 키워드.csv")
    files_in_data = glob.glob("data/keyword/*년 키워드.csv")
    all_files = files_in_root + files_in_data
    
    all_dfs = []
    
    for filename in all_files:
        try:
            df = pd.read_csv(filename)
            
            # 날짜 파싱 (키워드 파일용: 년-월 or 월-년)
            def parse_date(date_str):
                try: return pd.to_datetime(date_str, format='%y-%b') # 16-Mar
                except: 
                    try: return pd.to_datetime(date_str, format='%b-%y') # Sep-16
                    except: return pd.NaT

            df['Date_Parsed'] = df['Date'].apply(parse_date)
            df = df.dropna(subset=['Date_Parsed'])
            
            # 태그 컬럼 정제
            if 'tag' in df.columns:
                df['tag'] = df['tag'].fillna('').astype(str).str.strip()
                df.loc[df['tag'] == '', 'tag'] = None
                df.loc[df['tag'] == 'nan', 'tag'] = None
            else:
                df['tag'] = None
            
            all_dfs.append(df)
        except Exception as e:
            st.error(f"키워드 파일 로드 오류 ({filename}): {e}")
            
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

# ---------------------------------------------------------
# 3. 생기부 데이터 로드 (모든 학생 통합) - [수정됨]
# ---------------------------------------------------------
@st.cache_data
def load_all_student_data():
    # 현재 폴더 및 하위 폴더 탐색
    student_files = glob.glob("*생기부*.csv") + glob.glob("data/shcool_record/*생기부*.csv")
    
    all_students = []
    
    for filepath in student_files:
        try:
            df = pd.read_csv(filepath)
            
            filename = os.path.basename(filepath)
            student_name = filename.split('_')[0] 
            
            col_rename_map = {
                'ketworad': 'Keyword', 'Activiy': 'Activity',
                'category': 'Category', 'content': 'Content'
            }
            df = df.rename(columns=col_rename_map)
            
            required_cols = ['Date', 'Keyword', 'Category', 'Activity', 'Content']
            for col in required_cols:
                if col not in df.columns: df[col] = ''

            # [수정] 날짜 파싱 로직 업데이트 (일-월-년 우선 적용)
            def parse_student_date(date_str):
                # 1. 일-월-년 (예: 20-Dec-20 -> 2020-12-20)
                try: return pd.to_datetime(date_str, format='%d-%b-%y')
                except:
                    # 2. 기존 포맷 폴백 (혹시 다른 파일이 예전 형식일 경우 대비)
                    try: return pd.to_datetime(date_str, format='%y-%b')
                    except: 
                        try: return pd.to_datetime(date_str, format='%b-%y')
                        except: return pd.NaT
            
            df['Date_Parsed'] = df['Date'].apply(parse_student_date)
            
            # 날짜 변환 실패한 행 확인 (디버깅용)
            if df['Date_Parsed'].isna().any():
                failed_rows = df[df['Date_Parsed'].isna()]['Date'].unique()
                print(f"Warning: {filename}에서 날짜 변환 실패: {failed_rows}")

            df['Year'] = df['Date_Parsed'].dt.year
            df['StudentName'] = student_name 
            
            # 태그 컬럼 정제
            if 'tag' in df.columns:
                df['tag'] = df['tag'].fillna('').astype(str).str.strip()
                df.loc[df['tag'] == '', 'tag'] = None
                df.loc[df['tag'] == 'nan', 'tag'] = None
            else:
                df['tag'] = None

            all_students.append(df)
            
        except Exception as e:
            st.error(f"학생 파일 로드 오류 ({filepath}): {e}")
            
    if all_students:
        return pd.concat(all_students, ignore_index=True)
    else:
        return pd.DataFrame()

# ---------------------------------------------------------
# 4. 메인 앱 로직
# ---------------------------------------------------------
st.title("📊 통합 키워드 트렌드 & 생기부 매칭 분석")
st.markdown("---")

keyword_df = load_keyword_data()
student_df = load_all_student_data()

if keyword_df.empty:
    st.error("키워드 데이터 파일(*년 키워드.csv)을 찾을 수 없습니다.")
elif student_df.empty:
    st.error("생기부 데이터 파일(*생기부*.csv)을 찾을 수 없습니다.")
else:
    # 사이드바
    st.sidebar.header("🔍 분석 옵션")
    categories = keyword_df['Category'].unique()
    selected_category = st.sidebar.selectbox("분석할 카테고리", categories)
    
    student_names = ["전체 학생 보기"] + list(student_df['StudentName'].unique())
    selected_student = st.sidebar.selectbox("학생 필터", student_names)
    
    if selected_student != "전체 학생 보기":
        target_student_df = student_df[student_df['StudentName'] == selected_student]
    else:
        target_student_df = student_df
    
    # 메인 화면
    category_df = keyword_df[keyword_df['Category'] == selected_category]
    keywords_in_category = category_df['Keyword'].unique()
    
    st.header(f"📂 [{selected_category}] 분야 트렌드 분석")
    st.caption(f"선택된 학생: **{selected_student}** | 키워드 수: {len(keywords_in_category)}개")

    for kw in keywords_in_category:
        st.markdown("###") 
        
        subset = category_df[category_df['Keyword'] == kw].sort_values('Date_Parsed')
        if subset.empty: continue
            
        peak_date = subset.loc[subset['Count'].idxmax(), 'Date_Parsed']
        keyword_year = peak_date.year
        
        valid_tags = subset['tag'].dropna().unique()
        current_kw_tag = valid_tags[0] if len(valid_tags) > 0 else None
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            fig, ax1 = plt.subplots(figsize=(10, 4))
            
            ax1.plot(subset['Date_Parsed'], subset['Count'], 
                     marker='o', markersize=4, color='#1f77b4', label='뉴스 빈도')
            
            matched_records = []
            
            if current_kw_tag is not None:
                tag_matches = target_student_df[target_student_df['tag'] == current_kw_tag]
                
                for _, record in tag_matches.iterrows():
                    student_year = record['Year']
                    
                    if student_year == keyword_year or student_year == keyword_year + 1:
                        record_date = record['Date_Parsed']
                        s_name = record['StudentName']
                        
                        curr_xlim = ax1.get_xlim()
                        rec_date_num = mdates.date2num(record_date)
                        if rec_date_num < curr_xlim[0]: ax1.set_xlim(left=record_date - pd.Timedelta(days=30))
                        if rec_date_num > curr_xlim[1]: ax1.set_xlim(right=record_date + pd.Timedelta(days=30))

                        ax1.axvline(x=record_date, color='red', linestyle='--', alpha=0.5)
                        ax1.scatter([record_date], [subset['Count'].max() * 0.5], 
                                    color='red', s=100, marker='*', zorder=5)
                        
                        label_text = f"[{s_name}] {record['Activity']}"
                        ax1.text(record_date, subset['Count'].max() * 0.6, 
                                 label_text, color='red', fontsize=9, rotation=45)
                        
                        matched_records.append(record)

            ax1.set_title(f"'{kw}' 트렌드 (Peak: {keyword_year})", fontsize=14, fontweight='bold')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax1.grid(True, linestyle='--', alpha=0.3)
            ax1.legend(loc='upper left')
            st.pyplot(fig)
            
        with col2:
            st.subheader(f"📌 {kw}")
            tag_display = current_kw_tag if current_kw_tag else "(태그 없음)"
            st.write(f"**태그:** {tag_display}")
            
            if matched_records:
                st.success(f"✅ {len(matched_records)}건 매칭됨")
                for rec in matched_records:
                    with st.expander(f"[{rec['StudentName']}] {rec['Activity']}", expanded=True):
                        # 날짜 표시 포맷도 보기 좋게 변경
                        date_display = rec['Date_Parsed'].strftime('%Y-%m-%d') if pd.notnull(rec['Date_Parsed']) else rec['Date']
                        st.caption(f"{date_display}")
                        st.write(f"{rec['Content']}")
            else:
                if current_kw_tag is None:
                    st.caption("키워드에 설정된 태그가 없어 매칭하지 않습니다.")
                else:
                    st.info("조건(태그+연도)에 맞는 활동이 없습니다.")

    with st.expander("📂 로드된 전체 생기부 데이터 확인"):
        st.dataframe(student_df)