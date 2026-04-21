import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. 초기 설정 및 데이터 로드
st.set_page_config(page_title="UOU 조직도 Explorer", layout="wide")

# 클릭한 직원을 기억하는 메모리
if 'selected_emp' not in st.session_state:
    st.session_state.selected_emp = None

@st.cache_data
def load_data():
    try: return pd.read_csv("org_sample.csv", encoding="utf-8-sig")
    except: return pd.read_csv("org_sample.csv", encoding="cp949")

df = load_data().fillna("")

# 직급 정렬 및 명칭 매핑 (팀장 0순위)
def get_rank_info(row):
    title = str(row.get('보직명', '')).strip()
    rank_str = str(row.get('직급', '')).strip()
    
    if '팀장' in title: return 0, title
    
    rank_map = {'5급':(1,'부장'), '6급':(2,'차장'), '7급':(3,'과장'), '8급':(4,'대리'), '9급':(5,'사원')}
    order, name = 99, rank_str
    for k, v in rank_map.items():
        if k in rank_str: order, name = v; break
    return order, (title if title else name)

def get_duration(date_str):
    try:
        start = pd.to_datetime(str(date_str).replace('.','-').strip())
        diff = (datetime.now() - start).days
        return f"{diff // 365}년 {(diff % 365) // 30}개월"
    except: return "-"

# 2. 사이드바 - 조직 탐색
st.sidebar.header("🏢 조직 탐색")
chu_list = [d for d in df['처'].unique() if d]
selected_chu = st.sidebar.selectbox("1. '처'를 선택하세요", ["선택하세요"] + sorted(chu_list))

if selected_chu != "선택하세요":
    dept_df = df[df['처'] == selected_chu]
    teams = sorted([t for t in dept_df['부'].unique() if t and t != selected_chu])
    selected_team = st.sidebar.selectbox("2. 부/팀을 선택하세요", ["처장 직속"] + teams)

    st.divider()
    col_tree, col_profile = st.columns([1, 2.5])
    
    # 3. 왼쪽 화면: 수직 체인 조직도
    with col_tree:
        st.subheader("📌 조직 체인")
        
        # [Step 1] 처장 먼저 그리기
        heads = dept_df[(dept_df['부'] == selected_chu) | (dept_df['부'] == "")]
        for _, head in heads.iterrows():
            _, head_rank = get_rank_info(head)
            if st.button(f"👑 {head['성명']} ({head_rank})", key=f"btn_{head['사번']}", use_container_width=True):
                st.session_state.selected_emp = head['사번']
        
        # [Step 2] 팀이 선택되었다면 팀원들 직급순(팀장 최우선 -> 사원) 그리기
        if selected_team != "처장 직속":
            st.markdown("<div style='text-align:center; font-size:20px; color:#1a365d;'>⬇</div>", unsafe_allow_html=True)
            
            tm_df = dept_df[dept_df['부'] == selected_team].copy()
            
            # [에러 해결 구간] KeyError 방지를 위해 리스트 컴프리헨션 사용
            orders = []
            for _, row in tm_df.iterrows():
                orders.append(get_rank_info(row)[0])
            
            tm_df['so'] = orders
            tm_df = tm_df.sort_values('so', ascending=True)
            
            for i, (_, tm) in enumerate(tm_df.iterrows()):
                _, tm_rank = get_rank_info(tm)
                icon = "🔥" if tm_rank == '팀장' else ("💼" if tm_rank in ['부장', '차장'] else "👤")
                
                if st.button(f"{icon} {tm['성명']} ({tm_rank})", key=f"btn_{tm['사번']}", use_container_width=True):
                    st.session_state.selected_emp = tm['사번']
                
                if i < len(tm_df) - 1:
                    st.markdown("<div style='text-align:center; font-size:16px; color:#ccc;'>⬇</div>", unsafe_allow_html=True)

    # 4. 오른쪽 화면: 상세 프로필 (사진 예외처리 적용)
    with col_profile:
        if st.session_state.selected_emp:
            try:
                target = df[df['사번'].astype(str) == str(st.session_state.selected_emp)].iloc[0]
                _, t_rank = get_rank_info(target)
                
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        # [핵심] 사진 존재 여부 확인
                        img_path = f"assets/{target['사번']}.jpg"
                        if os.path.exists(img_path):
                            st.image(img_path, use_column_width=True)
                        else:
                            st.info("📷 사진 미등록")
                    with c2:
                        st.header(f"{target['성명']} {t_rank}")
                        st.caption(f"사번: {target['사번']}")
                        st.write(f"**수행업무:** {target.get('주요업무', '-')}")
                
                tab1, tab2, tab3 = st.tabs(["📋 기본정보", "⏳ 상세이력", "🎖️ 인사정보"])
                with tab1:
                    st.write(f"**소속:** {target['본부']} / {target['처']} {target['부']}")
                    st.write(f"**직종/직급:** {target.get('직종명', '-')} / {target.get('직급', '-')}")
                with tab2:
                    st.write(f"**법인임용일:** {target['법인임용일']}")
                    st.write(f"**총 근무기간:** {get_duration(target['법인임용일'])}")
                with tab3:
                    st.markdown("**발령/포상 정보**")
                    st.info(str(target.get('발령정보', '내역 없음')).replace('\n', '\n\n'))
            except IndexError:
                st.error("해당 사번의 정보를 찾을 수 없습니다.")
        else:
            st.info("👈 왼쪽 조직 체인에서 직원을 클릭하면 상세 이력이 표시됩니다.")
else:
    st.title("🏢 울산대학교 조직도 Explorer")
    st.info("왼쪽 사이드바에서 '처'를 선택하여 탐색을 시작하세요.")
