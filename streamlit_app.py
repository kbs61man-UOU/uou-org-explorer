import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 데이터 로드
st.set_page_config(page_title="UOU 조직도 Explorer", layout="wide")

@st.cache_data
def load_data():
    try:
        return pd.read_csv("org_sample.csv", encoding="utf-8-sig")
    except:
        return pd.read_csv("org_sample.csv", encoding="cp949")

df = load_data().fillna("")

# 2. 직급 및 근무기간 유틸리티
def get_rank_display(row):
    title = str(row.get('보직명', '')).strip()
    rank = str(row.get('직급', '')).strip()
    rank_map = {'5급':'부장', '6급':'차장', '7급':'과장', '8급':'대리', '9급':'사원'}
    for k, v in rank_map.items():
        if k in rank: return title if title else v
    return title if title else rank

def get_duration(date_str):
    try:
        start = pd.to_datetime(str(date_str).replace('.','-').strip())
        diff = (datetime.now() - start).days
        return f"{diff // 365}년 {(diff % 365) // 30}개월"
    except: return "-"

# 3. 사이드바 - 조직 탐색 (Drill-down)
st.sidebar.header("🏢 조직 탐색")

# [1단계] 처 선택
selected_chu = st.sidebar.selectbox("1. '처'를 선택하세요", ["선택하세요"] + sorted(df['처'].unique().tolist()))

if selected_chu != "선택하세요":
    dept_df = df[df['처'] == selected_chu]
    
    # [2단계] 처장/보직자 선택
    heads = dept_df[(dept_df['부'] == selected_chu) | (dept_df['부'] == "")]
    head_names = heads['성명'].tolist()
    selected_head = st.sidebar.selectbox(f"2. {selected_chu}장 선택", ["선택하세요"] + head_names)

    if selected_head != "선택하세요":
        # 처장 정보 표시
        head_row = heads[heads['성명'] == selected_head].iloc[0]
        
        # [3단계] 팀 선택
        teams = sorted([t for t in dept_df['부'].unique() if t and t != selected_chu])
        selected_team = st.sidebar.selectbox("3. 부/팀을 선택하세요", ["선택하세요"] + teams)
        
        # 메인 화면 구성
        col1, col2 = st.columns([1, 2])
        
        # 만약 팀이 선택되지 않았다면 처장 정보만 크게 표시
        target_person = head_row
        if selected_team != "선택하세요":
            team_members = dept_df[dept_df['부'] == selected_team].copy()
            # 직급순 정렬 (5급~9급)
            team_members['rank_val'] = team_members['직급'].str.extract('(\d+)').astype(float)
            team_members = team_members.sort_values('rank_val')
            
            st.subheader(f"👥 {selected_team} 구성원")
            member_names = team_members['성명'].tolist()
            selected_member = st.selectbox("조회할 팀원을 선택하세요", member_names)
            target_person = team_members[team_members['성명'] == selected_member].iloc[0]

        # 4. 상세 프로필 렌더링 (오른쪽 패널)
        with st.container():
            st.divider()
            c1, c2 = st.columns([1, 3])
            with c1:
                # 사진 연동 (사번.jpg)
                st.image(f"assets/{target_person['사번']}.jpg", width=150, caption=f"사번: {target_person['사번']}")
            with c2:
                st.header(f"{target_person['성명']} ({get_rank_display(target_person)})")
                st.write(f"**현재 업무:** {target_person.get('주요업무', '-')}")
            
            st.markdown("---")
            tab1, tab2, tab3 = st.tabs(["📋 기본정보", "⏳ 상세이력", "🎖️ 인사정보"])
            
            with tab1:
                st.write(f"**소속:** {target_person['본부']} / {target_person['처']} {target_person['부']}")
                st.write(f"**최종학력:** {target_person.get('최종학력', '-')}")
            
            with tab2:
                st.write(f"**법인임용일:** {target_person['법인임용일']}")
                st.write(f"**총 근무기간:** {get_duration(target_person['법인임용일'])}")
                st.write(f"**퇴직예정일:** {target_person['퇴직예정일']}")
                
            with tab3:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info("**발령 정보**")
                    st.text(target_person.get('발령정보', '내역 없음'))
                with col_b:
                    st.info("**포상 및 자격**")
                    st.text(target_person.get('포상이력', '내역 없음'))
else:
    st.title("🏢 울산대학교 조직도 Explorer")
    st.info("왼쪽 사이드바에서 '처'를 선택하여 조직 탐색을 시작하세요.")