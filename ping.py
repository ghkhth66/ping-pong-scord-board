import streamlit as st
import pandas as pd
import os
import numpy as np
import random
import re
from datetime import datetime
import math
import io
import pickle  # 다중 기기/구장 간 상태 공유를 위한 모듈
import hashlib  # 🔒 비밀번호 암호화를 위한 모듈 추가

# ==========================================
# 🛠️ 개발자 모드 설정
# ==========================================
# True로 설정 시: 비밀번호 없이 관리자 권한 획득, 더미 데이터로 즉시 테스트 가능
# False로 설정 시: 실제 운영 모드 (비밀번호 필요)
DEV_MODE = False

CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')

st.set_page_config(
    page_title="동호회 운영 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .setting-banner { background-color: #f8f9fa; border: 2px solid #28a745; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #dc3545 !important; color: white !important; }
    .custom-table-wrapper { width: 100%; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# [보안] 비밀번호 암호화 함수
# ==========================================
def hash_password(password):
    """입력받은 비밀번호를 SHA-256 방식으로 암호화하여 반환"""
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# [핵심] 구장별 데이터 저장 및 불러오기 (다중 기기 공유)
# ==========================================
def save_room_state(room_name):
    """현재 세션의 데이터를 구장 이름의 파일로 저장하여 다른 기기에서 볼 수 있게 함"""
    state_to_save = {
        'main_df': st.session_state.get('main_df'),
        'config': st.session_state.get('config'),
        'teams': st.session_state.get('teams'),
        'matrix': st.session_state.get('matrix'),
        'ind_matrix': st.session_state.get('ind_matrix'),
        'cum_df': st.session_state.get('cum_df'),
        'h2h_df': st.session_state.get('h2h_df'),
        'labels': st.session_state.get('labels'),
        'attendance_confirmed': st.session_state.get('attendance_confirmed'),
        'config_confirmed': st.session_state.get('config_confirmed'),
        'draw_results': st.session_state.get('draw_results'),
        'draw_completed': st.session_state.get('draw_completed')
    }
    try:
        with open(f"{room_name}_state.pkl", "wb") as f:
            pickle.dump(state_to_save, f)
    except Exception as e:
        st.sidebar.error(f"상태 저장 오류: {e}")

def load_room_state(room_name):
    """구장 이름의 파일을 읽어와 현재 화면에 반영 (조회용)"""
    file_name = f"{room_name}_state.pkl"
    if os.path.exists(file_name):
        try:
            with open(file_name, "rb") as f:
                state = pickle.load(f)
                for k, v in state.items():
                    if v is not None:
                        st.session_state[k] = v
            return True
        except Exception as e:
            st.sidebar.error(f"데이터 불러오기 실패: {e}")
    return False

def reset_config_state():
    st.session_state.config_confirmed = False
    keys_to_delete = ['matrix', 'ind_matrix', 'teams', 'draw_results']
    for k in keys_to_delete:
        if k in st.session_state: del st.session_state[k]

def extract_busu(busu_str):
    try:
        nums = re.findall(r'\d+', str(busu_str))
        return float(nums[0]) if nums else 9.0
    except:
        return 9.0

def load_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            return pd.read_csv(uploaded_file, encoding='cp949')

    # 파일이 없을 경우 더미 데이터 생성 (개발/테스트용)
    data = [{"순서": i, "이름": f"회원{i}", "성별": random.choice(["남", "여"]),
             "나이": random.randint(20, 75), "부수": f"{random.randint(1, 13)}부",
             "부수_조정1": 0.0, "부수_조정2": 0.0, "부수_조정3": 0.0,
             "참석예정": random.choice(["Y", "N"])} for i in range(1, 11)]
    return pd.DataFrame(data)

# ==========================================
# [핵심] 누적 데이터 업데이트 로직 (메모리 기반)
# ==========================================
def update_cumulative_record(p_a, p_b, s_a, s_b):
    if 'cum_df' not in st.session_state:
        st.session_state.cum_df = pd.DataFrame(columns=['이름', '총경기수', '승', '패', '득점', '실점'])

    df_cum = st.session_state.cum_df

    def ensure_player(df, name):
        if name not in df['이름'].values:
            new_row = pd.DataFrame([{'이름': name, '총경기수': 0, '승': 0, '패': 0, '득점': 0, '실점': 0}])
            df = pd.concat([df, new_row], ignore_index=True)
        return df

    if p_a != "선택안함": df_cum = ensure_player(df_cum, p_a)
    if p_b != "선택안함": df_cum = ensure_player(df_cum, p_b)

    for p, win, lose, score, opp_score in [(p_a, s_a > s_b, s_a < s_b, s_a, s_b),
                                           (p_b, s_b > s_a, s_b < s_a, s_b, s_a)]:
        if p != "선택안함":
            idx = df_cum[df_cum['이름'] == p].index[0]
            df_cum.at[idx, '총경기수'] += 1
            df_cum.at[idx, '승'] += 1 if win else 0
            df_cum.at[idx, '패'] += 1 if lose else 0
            df_cum.at[idx, '득점'] += score
            df_cum.at[idx, '실점'] += opp_score

    st.session_state.cum_df = df_cum

    if p_a != "선택안함" and p_b != "선택안함":
        if 'h2h_df' not in st.session_state:
            st.session_state.h2h_df = pd.DataFrame(
                columns=['Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

        h2h = st.session_state.h2h_df
        p1, p2 = sorted([p_a, p_b])

        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)
        if not mask.any():
            new_row = pd.DataFrame(
                [{'Player1': p1, 'Player2': p2, 'P1_Win': 0, 'P2_Win': 0, 'P1_Score': 0, 'P2_Score': 0}])
            h2h = pd.concat([h2h, new_row], ignore_index=True)
            mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)

        idx = h2h[mask].index[0]

        if p1 == p_a:
            h2h.at[idx, 'P1_Win'] += 1 if s_a > s_b else 0
            h2h.at[idx, 'P2_Win'] += 1 if s_b > s_a else 0
            h2h.at[idx, 'P1_Score'] += s_a
            h2h.at[idx, 'P2_Score'] += s_b
        else:
            h2h.at[idx, 'P1_Win'] += 1 if s_b > s_a else 0
            h2h.at[idx, 'P2_Win'] += 1 if s_a > s_b else 0
            h2h.at[idx, 'P1_Score'] += s_b
            h2h.at[idx, 'P2_Score'] += s_a

        st.session_state.h2h_df = h2h

# ==========================================
# [핵심] 누적 상대 전적 팝업 창 (Dialog)
# ==========================================
@st.dialog("📊 역대 누적 상대 전적")
def show_h2h_dialog(player_a, player_b):
    p1, p2 = sorted([player_a, player_b])
    h2h = st.session_state.get('h2h_df', pd.DataFrame())

    if not h2h.empty:
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)
        if mask.any():
            record = h2h[mask].iloc[0]
            p1_w = record['P1_Win']
            p2_w = record['P2_Win']
            p1_s = record['P1_Score']
            p2_s = record['P2_Score']

            st.markdown(
                f"<h3 style='text-align: center; color: #28a745;'>{p1} <span style='color:gray;'>vs</span> {p2}</h3>",
                unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size:1.1rem;'>총 <b>{p1_w + p2_w}</b>전 맞대결</p>",
                        unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.info(
                    f"<div style='text-align:center; font-size:1.2rem;'><b>{p1}</b><br><br>🏆 <b>{p1_w}</b> 승<br>🎯 {p1_s} 득점</div>",
                    unsafe_allow_html=True)
            with c2:
                st.error(
                    f"<div style='text-align:center; font-size:1.2rem;'><b>{p2}</b><br><br>🏆 <b>{p2_w}</b> 승<br>🎯 {p2_s} 득점</div>",
                    unsafe_allow_html=True)

            st.write("")
            if st.button("닫기", use_container_width=True):
                st.rerun()
            return

    st.warning("아직 두 선수의 누적 맞대결 기록이 없습니다.")
    if st.button("닫기", use_container_width=True):
        st.rerun()

# ----------------- 초기화 -----------------
if 'main_df' not in st.session_state: st.session_state.main_df = load_data()
if 'attendance_confirmed' not in st.session_state: st.session_state.attendance_confirmed = False
if 'config_confirmed' not in st.session_state: st.session_state.config_confirmed = False
if 'cum_df' not in st.session_state: st.session_state.cum_df = pd.DataFrame(
    columns=['이름', '총경기수', '승', '패', '득점', '실점'])
if 'h2h_df' not in st.session_state: st.session_state.h2h_df = pd.DataFrame(
    columns=['Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

# ==========================================
# 사이드바: 구장 관리 및 권한 설정
# ==========================================
st.sidebar.markdown("### 🏟️ 구장 및 권한 설정")
room_name = st.sidebar.text_input("구장명 (방 이름)", value="생활탁구장", help="구장 이름을 입력하면 해당 구장의 데이터를 불러옵니다.")

if st.sidebar.button("🔄 최신 경기결과 불러오기", type="primary"):
    if load_room_state(room_name):
        st.sidebar.success(f"'{room_name}' 구장의 데이터를 불러왔습니다.")
    else:
        st.sidebar.warning("저장된 구장 데이터가 없습니다.")

st.sidebar.divider()

# 🛠️ 권한 처리 및 비밀번호 암호화 로직
is_admin = False

if DEV_MODE:
    is_admin = True
    st.sidebar.warning("🛠️ **[개발자 모드]** 관리자 권한이 자동 부여되었습니다.")
else:
    admin_password = st.sidebar.text_input("관리자 비밀번호 (입력 시 관리자 모드)", type="password")
    pw_file = f"{room_name}_pw.txt"

    if admin_password:
        hashed_pw = hash_password(admin_password)  # 🔒 입력한 비밀번호를 암호화

        if os.path.exists(pw_file):
            with open(pw_file, "r") as f:
                saved_pw = f.read().strip()

            # 🔒 암호화된 값끼리 비교
            if hashed_pw == saved_pw:
                is_admin = True
                st.sidebar.success("✅ 관리자 모드 활성화")
            else:
                st.sidebar.error("❌ 비밀번호가 틀렸습니다.")
        else:
            # 🔒 최초 설정 시 암호화된 값을 파일에 저장
            with open(pw_file, "w") as f:
                f.write(hashed_pw)
            is_admin = True
            st.sidebar.success(f"✅ '{room_name}' 구장 관리자 설정 완료")
    else:
        st.sidebar.info("👀 현재 조회 전용(Read-only) 모드입니다.")

st.sidebar.divider()

if is_admin:
    st.sidebar.markdown("### 📁 데이터 파일 업로드")
    uploaded_file = st.sidebar.file_uploader("1. 명단 파일(CSV) 업로드")
    if uploaded_file and uploaded_file.name.lower().endswith('.csv'):
        if st.sidebar.button("명단 적용하기"):
            st.session_state.main_df = load_data(uploaded_file)
            st.sidebar.success("새로운 명부가 적용되었습니다.")
            st.rerun()

    cum_file = st.sidebar.file_uploader("2. 기존 누적 결과(CSV) 업로드")
    if cum_file and cum_file.name.lower().endswith('.csv'):
        if st.sidebar.button("누적 데이터 적용"):
            st.session_state.cum_df = pd.read_csv(cum_file, encoding='utf-8-sig')
            st.sidebar.success("누적 데이터가 연동되었습니다.")
            st.rerun()

    h2h_file = st.sidebar.file_uploader("3. 누적 상대전적(CSV) 업로드")
    if h2h_file and h2h_file.name.lower().endswith('.csv'):
        if st.sidebar.button("상대전적 데이터 적용"):
            st.session_state.h2h_df = pd.read_csv(h2h_file, encoding='utf-8-sig')
            st.sidebar.success("상대전적 데이터가 연동되었습니다.")
            st.rerun()

selected_date = st.date_input("시합 일자 선택", datetime.now(), disabled=not is_admin)
CURRENT_DATE = selected_date.strftime('%Y-%m-%d')
SAVE_FILE_NAME = f"{room_name}_{CURRENT_DATE}_경기결과.csv"
col_date = f"출석_{CURRENT_DATE}"

# ==========================================
# [핵심] '참석예정' 컬럼을 확인하여 출석 기본값 자동 세팅
# ==========================================
if col_date not in st.session_state.main_df.columns:
    if '참석예정' in st.session_state.main_df.columns:
        st.session_state.main_df[col_date] = st.session_state.main_df['참석예정'].apply(
            lambda x: 'Y' if str(x).strip().upper() in ['Y', 'O', '1', 'TRUE', '참석'] else 'N'
        )
    else:
        st.session_state.main_df[col_date] = 'Y'

selected_adj = st.sidebar.selectbox("부수 조정 기준", ["부수_조정1", "부수_조정2", "부수_조정3"], disabled=not is_admin)

tab_home, tab_config, tab_team, tab_match, tab_score = st.tabs([" 출석체크", " 운영 설정", " 조 편성 결과", " 경기 배정", " 스코어보드"])

# ==========================================
# 탭 1: 출석체크
# ==========================================
@st.fragment
def attendance_check_fragment():
    st.markdown(f"### 📋 {CURRENT_DATE} 참석 현황")
    df = st.session_state.main_df.copy()
    df['참석'] = df[col_date].apply(lambda x: True if x == 'Y' else False)

    mid_idx = len(df) // 2 + (len(df) % 2)
    col1, col2 = st.columns(2)

    with col1:
        edited_left = st.data_editor(df.iloc[:mid_idx][['순서', '이름', '참석', '부수', selected_adj]], hide_index=True,
                                     disabled=not is_admin)
    with col2:
        edited_right = st.data_editor(df.iloc[mid_idx:][['순서', '이름', '참석', '부수', selected_adj]], hide_index=True,
                                      disabled=not is_admin)

    edited_df = pd.concat([edited_left, edited_right], ignore_index=True)
    current_checked = edited_df[edited_df['참석'] == True]
    live_names = ", ".join(sorted(current_checked['이름'].tolist()))

    st.info(f"**현재 참석 ({len(current_checked)}명):** {live_names}")

    if is_admin:
        btn_label = "확정 완료 (참석자 저장됨)" if st.session_state.attendance_confirmed else "참석자 확정하기"
        btn_type = "primary" if st.session_state.attendance_confirmed else "secondary"
        if st.button(btn_label, type=btn_type, use_container_width=True):
            st.session_state.main_df[col_date] = edited_df['참석'].apply(lambda x: 'Y' if x else 'N')
            st.session_state.attendance_confirmed = True
            save_room_state(room_name)
            st.rerun()

        st.divider()
        st.markdown("#### 💾 최신 명단 다운로드")
        st.info("오늘 수정한 참석 현황이 반영된 명단을 다음 모임에서도 사용하려면 아래 버튼을 눌러 다운로드하세요.")

        csv_main = st.session_state.main_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 최신 명단(CSV) 다운로드",
            data=csv_main,
            file_name=f"{room_name}_최신명단_{CURRENT_DATE}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )


with tab_home:
    attendance_check_fragment()

# ==========================================
# 탭 2: 운영 설정
# ==========================================
@st.fragment
def config_setup_fragment():
    st.markdown('<div class="setting-banner">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5])
    attendees_count = (
            st.session_state.main_df[col_date] == 'Y').sum() if col_date in st.session_state.main_df.columns else 0

    with c1:
        st.markdown(f"#### 👥 조 구성")
        g_val = st.number_input("편성 조 수", 1, 20, 4, disabled=not is_admin)
        if g_val > 0:
            avg = attendees_count // g_val
            rem = attendees_count % g_val
            st.info(f"👉 조당 {avg}~{avg + 1 if rem > 0 else avg}명 배정")

    with c2:
        st.markdown("#### 🎾 경기 규칙")
        s_g = st.number_input("단식 게임", 0, 10, 2, disabled=not is_admin)
        d_g = st.number_input("복식 게임", 0, 5, 1, disabled=not is_admin)
        set_c = st.selectbox("개인전 선승 세트", [2, 3, 4, 5], index=1, disabled=not is_admin)

    with c3:
        st.markdown("#### ⚙️ 환경 설정")
        t_val = st.number_input("Table_No.", 1, 20, 3, disabled=not is_admin)

    with c4:
        st.markdown("#### 🎲 방식")
        draw_method = st.radio("방식", ["AI 선정", "제비뽑기"], label_visibility="collapsed", disabled=not is_admin)

    with c5:
        st.markdown("#### ✅ 실행")
        if is_admin:
            btn_label = "설정 확정 완료" if st.session_state.config_confirmed else "설정 확정 및 편성 시작"
            btn_type = "primary" if st.session_state.config_confirmed else "secondary"
            if st.button(btn_label, type=btn_type, use_container_width=True):
                st.session_state.config = {
                    "g": g_val, "t": t_val, "s_games": s_g, "d_games": d_g, "set_count": set_c,
                    "total_g": s_g + d_g, "draw_method": draw_method, "selected_adj": selected_adj,
                    "tie_breakers": {name: random.random() for name in st.session_state.main_df['이름']}
                }
                st.session_state.config_confirmed = True
                save_room_state(room_name)
                st.rerun()
        else:
            st.info("관리자 전용")
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def draw_process_fragment():
    if "config" in st.session_state and st.session_state.config.get('draw_method') == '제비뽑기':
        if not st.session_state.get('draw_completed', False):
            st.divider()
            cfg = st.session_state.config

            adj_col = cfg['selected_adj']
            df = st.session_state.main_df

            attendees = df[df[col_date] == 'Y'].copy()
            attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)

            attendees['Random'] = attendees['이름'].map(cfg['tie_breakers'])

            sorted_members = attendees.sort_values(['부수_숫자', adj_col, 'Random'], ascending=True).reset_index(drop=True)

            total_levels = math.ceil(len(sorted_members) / cfg['g'])
            draw_level = st.session_state.get('draw_level', 0)

            st.markdown("### 제비뽑기 진행 현황")
            st.info("실력(부수) 순으로 그룹을 나누어 제비뽑기를 진행합니다. 조 번호를 선택하면 다른 인원의 번호가 자동으로 바뀝니다(중복 방지).")

            for level in range(total_levels):
                start_idx = level * cfg['g']
                end_idx = min((level + 1) * cfg['g'], len(sorted_members))
                current_group = sorted_members.iloc[start_idx:end_idx]
                group_members = current_group['이름'].tolist()

                st.markdown(f"#### 그룹 {level + 1}")
                cols = st.columns(cfg['g'])

                if level < draw_level:
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        with cols[i % cfg['g']]:
                            assigned_team = st.session_state.draw_results.get(row['이름'], "-")
                            st.success(f" **{row['이름']}** ➔ **{assigned_team}조**")

                elif level == draw_level:
                    available_options = list(range(1, cfg['g'] + 1))
                    state_key = f"group_selections_{level}"

                    if state_key not in st.session_state:
                        st.session_state[state_key] = {name: available_options[i] for i, name in
                                                       enumerate(group_members)}
                        st.session_state[f"{state_key}_prev"] = st.session_state[state_key].copy()

                    def on_selection_change(changed_member, lvl):
                        s_key = f"group_selections_{lvl}"
                        prev_selections = st.session_state[f"{s_key}_prev"]
                        current_selections = st.session_state[s_key]

                        new_val = st.session_state[f"select_{lvl}_{changed_member}"]
                        old_val = prev_selections[changed_member]

                        if new_val != old_val:
                            for other_member, val in prev_selections.items():
                                if other_member != changed_member and val == new_val:
                                    st.session_state[f"select_{lvl}_{other_member}"] = old_val
                                    current_selections[other_member] = old_val
                                    break

                            current_selections[changed_member] = new_val
                            st.session_state[f"{s_key}_prev"] = current_selections.copy()

                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        name = row['이름']
                        with cols[i % cfg['g']]:
                            st.markdown(f" **{name}**")
                            current_val = st.session_state[state_key][name]
                            st.selectbox(
                                "조 선택",
                                options=available_options,
                                index=available_options.index(current_val),
                                key=f"select_{level}_{name}",
                                on_change=on_selection_change,
                                args=(name, level),
                                label_visibility="collapsed",
                                disabled=not is_admin
                            )

                    st.write("")
                    if is_admin:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button(f" 그룹 {level + 1} 랜덤 배정"):
                                shuffled_options = available_options[:len(group_members)]
                                random.shuffle(shuffled_options)
                                for i, name in enumerate(group_members):
                                    st.session_state.draw_results[name] = shuffled_options[i]
                                st.session_state.draw_level += 1
                                st.rerun()

                        with btn_col2:
                            if st.button(f" 그룹 {level + 1} 제비뽑기 완료 및 다음 진행", type="primary", width="stretch"):
                                for name in group_members:
                                    st.session_state.draw_results[name] = st.session_state[f"select_{level}_{name}"]
                                st.session_state.draw_level += 1
                                st.rerun()

                else:
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        with cols[i % cfg['g']]:
                            st.markdown(
                                f"<div style='color:#999; padding:10px; border:1px dashed #ccc; border-radius:5px;'>"
                                f" {row['이름']} ({row['부수']}) - 대기중</div>", unsafe_allow_html=True)

                st.divider()

            if draw_level >= total_levels:
                st.session_state.draw_completed = True
                st.rerun()
        else:
            st.divider()
            st.success(" 제비뽑기가 모두 완료되었습니다! 상단의 **'조 편성 결과'** 탭으로 이동하여 결과를 확인해주세요.")
            if is_admin:
                if st.button(" 제비뽑기 다시 하기", type="secondary"):
                    st.session_state.draw_level = 0
                    st.session_state.draw_results = {}
                    st.session_state.draw_completed = False
                    for key in list(st.session_state.keys()):
                        if key.startswith("group_selections_") or key.startswith("select_"):
                            del st.session_state[key]
                    st.rerun()

with tab_config:
    config_setup_fragment()
    draw_process_fragment()

# ==========================================
# 탭 3: 조 편성 결과
# ==========================================
with tab_team:
    if "config" not in st.session_state:
        st.warning("먼저 '운영 설정'을 완료해주세요.")
    else:
        cfg = st.session_state.config
        df = st.session_state.main_df
        attendees = df[df[col_date] == 'Y'].copy()
        attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
        sorted_members = attendees.sort_values(['부수_숫자', '부수_조정1'], ascending=True).reset_index(drop=True)

        teams = {i: [] for i in range(1, cfg['g'] + 1)}
        team_stats = {i: {"sum": 0.0, "count": 0} for i in range(1, cfg['g'] + 1)}
        all_member_names = []

        if cfg.get('draw_method', 'AI 선정') == 'AI 선정':
            for idx, row in sorted_members.iterrows():
                r_idx = idx // cfg['g']
                pos_idx = idx % cfg['g']
                t_idx = (pos_idx + 1) if r_idx % 2 == 0 else (cfg['g'] - pos_idx)
                teams[t_idx].append(f"{row['이름']}({row['부수']})")
                all_member_names.append(row['이름'])
                team_stats[t_idx]["sum"] += row['부수_숫자']
                team_stats[t_idx]["count"] += 1
        else:
            for idx, row in sorted_members.iterrows():
                name = row['이름']
                t_idx = st.session_state.draw_results.get(name, 1)
                teams[t_idx].append(f"{row['이름']}({row['부수']})")
                all_member_names.append(row['이름'])
                team_stats[t_idx]["sum"] += row['부수_숫자']
                team_stats[t_idx]["count"] += 1

        avg_p = sum(t["count"] for t in team_stats.values()) / cfg['g'] if cfg['g'] > 0 else 0
        st.session_state.config['is_individual'] = True if avg_p <= 1.5 else False
        st.session_state.labels = [f"{i}조({teams[i][0].split('(')[0]})" for i in range(1, cfg['g'] + 1) if teams[i]]
        st.session_state.teams = teams

        st.markdown("### 조별 최종 구성 및 부수 합계")
        valid_teams = [t_num for t_num in range(1, cfg['g'] + 1) if teams[t_num]]
        num_cols = min(len(valid_teams), 5)

        if num_cols > 0:
            for i in range(0, len(valid_teams), num_cols):
                chunk = valid_teams[i:i + num_cols]
                cols = st.columns(num_cols)
                for j, t_num in enumerate(chunk):
                    with cols[j]:
                        members_html = "<br>".join(teams[t_num])
                        st.markdown(f"""
                            <div class="team-card" style="font-size: 1rem;">
                                <div style="background-color:#f8f9fa; padding:8px; margin-bottom:10px; border-radius:5px; border:1px solid #eee;">
                                    <b>{t_num}조 _ {len(teams[t_num])}명 : {int(team_stats[t_num]['sum'])}부</b>
                                </div>
                                <div style="line-height: 1.6;">{members_html}</div>
                            </div>""", unsafe_allow_html=True)

        if st.session_state.get('matrix') is None:
            st.session_state.matrix = pd.DataFrame(0.0, index=st.session_state.labels, columns=st.session_state.labels)
            for l in st.session_state.labels: st.session_state.matrix.loc[l, l] = np.nan

        if st.session_state.get('ind_matrix') is None:
            all_member_names = sorted(list(set(all_member_names)))
            st.session_state.ind_matrix = pd.DataFrame(0.0, index=all_member_names, columns=all_member_names)
            for m in all_member_names: st.session_state.ind_matrix.loc[m, m] = np.nan

# ==========================================
# 탭 4: 경기 배정 및 결과 입력
# ==========================================
with tab_match:
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:
        def get_matches(teams):
            t_list = list(teams)
            if len(t_list) % 2: t_list.append(None)
            res = []
            for _ in range(len(t_list) - 1):
                for j in range(len(t_list) // 2):
                    if t_list[j] and t_list[-1 - j]:
                        res.append((t_list[j], t_list[-1 - j]))
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            return res


        all_matches = get_matches(st.session_state.labels)
        cfg = st.session_state.config
        t_count = cfg['t']
        s_games = cfg.get('s_games', 0)
        d_games = cfg.get('d_games', 0)
        is_ind = cfg.get('is_individual', False)
        limit = cfg.get('set_count', 3) if is_ind else cfg.get('total_g', 5)
        match_info = "개인전" if is_ind else f"단식 {s_games} / 복식 {d_games}"

        m_data = []
        for i, (a, b) in enumerate(all_matches):
            s1, s2 = 0, 0
            if a in st.session_state.matrix.index and b in st.session_state.matrix.columns:
                s1, s2 = st.session_state.matrix.loc[a, b], st.session_state.matrix.loc[b, a]
            status = " 종료" if (not np.isnan(s1) and (s1 + s2 > 0)) else " 대기"
            m_data.append({
                "순서": i + 1, "Table_No": f"{(i % t_count) + 1}번 대", "상태": status,
                "대진": f"{a} VS {b}", "경기 구성": match_info,
                "결과": f"{int(s1)} : {int(s2)}" if status == " 종료" else "-"
            })

        df_match = pd.DataFrame(m_data)


        def highlight_finished(row):
            if row['상태'] == ' 종료': return ['background-color: rgba(128, 128, 128, 0.15); color: gray;'] * len(row)
            return [''] * len(row)


        mid_idx = (len(df_match) + 1) // 2
        df_left = df_match.iloc[:mid_idx].reset_index(drop=True)
        df_right = df_match.iloc[mid_idx:].reset_index(drop=True)

        col_title, col_info = st.columns([3, 7])
        with col_title:
            st.markdown("### 경기 배정표")
        with col_info:
            st.info(" **아래 표에서 결과를 입력할 경기의 행(Row)을 클릭**하면 상세 입력창이 나타납니다.")

        col1, col2 = st.columns(2)
        with col1:
            event_left = st.dataframe(df_left.style.apply(highlight_finished, axis=1), width="stretch", hide_index=True,
                                      on_select="rerun", selection_mode="single-row")
        with col2:
            event_right = st.dataframe(df_right.style.apply(highlight_finished, axis=1), width="stretch",
                                       hide_index=True, on_select="rerun",
                                       selection_mode="single-row") if not df_right.empty else None

        selected_match_idx = None
        if event_left and event_left.selection.rows:
            selected_match_idx = event_left.selection.rows[0]
        elif event_right and event_right.selection.rows:
            selected_match_idx = event_right.selection.rows[0] + mid_idx

        if selected_match_idx is not None:
            team_a, team_b = all_matches[selected_match_idx]
            st.divider()
            st.markdown(f"### {team_a} VS {team_b} 상세 결과 입력")

            if not is_admin:
                st.warning("🔒 점수 입력은 관리자만 가능합니다. 사이드바에서 관리자 비밀번호를 입력해주세요.")
            else:
                col_form, col_empty = st.columns([1, 1])

                with col_form:
                    if is_ind:
                        m_idx = selected_match_idx
                        c1, c2, c3, c4 = st.columns([1.5, 1.5, 2.5, 1.5])
                        with c1:
                            st.markdown(
                                f"<div style='margin-top:8px; font-weight:bold; text-align:center;'>{team_a}</div>",
                                unsafe_allow_html=True)
                        with c2:
                            res_type = st.radio(f"{team_a} 결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_ind_res",
                                                label_visibility="collapsed")
                        with c3:
                            win_scores = [f"{limit}:{i}" for i in range(limit)]
                            lose_scores = [f"{i}:{limit}" for i in range(limit)]
                            display_scores = win_scores if res_type == "승" else lose_scores
                            selected_score = st.radio("스코어 선택", display_scores, horizontal=True,
                                                      key=f"m{m_idx}_ind_score", label_visibility="collapsed")
                        with c4:
                            st.markdown(
                                f"<div style='margin-top:8px; font-weight:bold; text-align:center;'>{team_b}</div>",
                                unsafe_allow_html=True)

                        if st.button("결과 저장", type="primary", key=f"btn_save_ind_match_{m_idx}"):
                            s_a, s_b = map(int, selected_score.split(':'))
                            st.session_state.matrix.loc[team_a, team_b] = s_a
                            st.session_state.matrix.loc[team_b, team_a] = s_b

                            p_a_name = team_a.split('(')[0].split('조')[-1].strip() if '조' in team_a else team_a
                            p_b_name = team_b.split('(')[0].split('조')[-1].strip() if '조' in team_b else team_b

                            update_cumulative_record(p_a_name, p_b_name, s_a, s_b)
                            save_room_state(room_name)

                            st.success("저장 완료! 스코어보드에 반영되었습니다.")
                            st.rerun()
                    else:
                        def get_team_players(team_str):
                            import re
                            match = re.search(r'(\d+)조', str(team_str))
                            if match and 'teams' in st.session_state:
                                t_idx = int(match.group(1))
                                if t_idx in st.session_state.teams:
                                    return [p.split('(')[0] for p in st.session_state.teams[t_idx]]
                            return list(st.session_state.ind_matrix.index)


                        team_a_players = get_team_players(team_a)
                        team_b_players = get_team_players(team_b)

                        m_idx = selected_match_idx

                        a_keys = [f"m{m_idx}_s_pa_{s}" for s in range(s_games)] + \
                                 [f"m{m_idx}_d_pa1_{d}" for d in range(d_games)] + \
                                 [f"m{m_idx}_d_pa2_{d}" for d in range(d_games)]

                        b_keys = [f"m{m_idx}_s_pb_{s}" for s in range(s_games)] + \
                                 [f"m{m_idx}_d_pb1_{d}" for d in range(d_games)] + \
                                 [f"m{m_idx}_d_pb2_{d}" for d in range(d_games)]


                        def get_avail(players, current_key, all_keys):
                            selected = [st.session_state[k] for k in all_keys
                                        if k in st.session_state and k != current_key and st.session_state[k] != "선택안함"]
                            return ["선택안함"] + [p for p in players if p not in selected]


                        match_results = []
                        set_limit = 3
                        set_win_scores = [f"{set_limit}:{i}" for i in range(set_limit)]
                        set_lose_scores = [f"{i}:{set_limit}" for i in range(set_limit)]

                        if s_games > 0:
                            st.markdown("##### 단식 경기")
                            for s in range(s_games):
                                c1, c2, c3, c4, c5 = st.columns([1.2, 2.5, 2, 3, 2.5])
                                with c1:
                                    st.markdown(
                                        f"<div style='margin-top:8px; font-weight:bold; color:#1f77b4;'>단식 {s + 1}</div>",
                                        unsafe_allow_html=True)
                                with c2:
                                    k_a = f"m{m_idx}_s_pa_{s}"
                                    avail_a = get_avail(team_a_players, k_a, a_keys)
                                    p_a = st.selectbox(f"{team_a} 선수", avail_a, key=k_a, label_visibility="collapsed")
                                with c3:
                                    res_type = st.radio("결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_s_res_{s}",
                                                        label_visibility="collapsed")
                                with c4:
                                    display_scores = set_win_scores if res_type == "승" else set_lose_scores
                                    selected_score = st.radio("스코어", display_scores, horizontal=True,
                                                              key=f"m{m_idx}_s_score_{s}", label_visibility="collapsed")
                                with c5:
                                    k_b = f"m{m_idx}_s_pb_{s}"
                                    avail_b = get_avail(team_b_players, k_b, b_keys)
                                    p_b = st.selectbox(f"{team_b} 선수", avail_b, key=k_b, label_visibility="collapsed")

                                s_a, s_b = map(int, selected_score.split(':'))
                                match_results.append(("S", p_a, s_a, s_b, p_b))

                        if d_games > 0:
                            st.markdown("##### 복식 경기")
                            for d in range(d_games):
                                c1, c2, c3, c4, c5 = st.columns([1.2, 2.5, 2, 3, 2.5])
                                with c1:
                                    st.markdown(
                                        f"<div style='margin-top:32px; font-weight:bold; color:#ff7f0e;'>복식 {d + 1}</div>",
                                        unsafe_allow_html=True)
                                with c2:
                                    k_a1 = f"m{m_idx}_d_pa1_{d}"
                                    avail_a1 = get_avail(team_a_players, k_a1, a_keys)
                                    p_a1 = st.selectbox(f"{team_a} 선수1", avail_a1, key=k_a1,
                                                        label_visibility="collapsed")

                                    k_a2 = f"m{m_idx}_d_pa2_{d}"
                                    avail_a2 = get_avail(team_a_players, k_a2, a_keys)
                                    p_a2 = st.selectbox(f"{team_a} 선수2", avail_a2, key=k_a2,
                                                        label_visibility="collapsed")
                                with c3:
                                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                                    res_type = st.radio("결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_d_res_{d}",
                                                        label_visibility="collapsed")
                                with c4:
                                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                                    display_scores = set_win_scores if res_type == "승" else set_lose_scores
                                    selected_score = st.radio("스코어", display_scores, horizontal=True,
                                                              key=f"m{m_idx}_d_score_{d}", label_visibility="collapsed")
                                with c5:
                                    k_b1 = f"m{m_idx}_d_pb1_{d}"
                                    avail_b1 = get_avail(team_b_players, k_b1, b_keys)
                                    p_b1 = st.selectbox(f"{team_b} 선수1", avail_b1, key=k_b1,
                                                        label_visibility="collapsed")

                                    k_b2 = f"m{m_idx}_d_pb2_{d}"
                                    avail_b2 = get_avail(team_b_players, k_b2, b_keys)
                                    p_b2 = st.selectbox(f"{team_b} 선수2", avail_b2, key=k_b2,
                                                        label_visibility="collapsed")

                                s_a, s_b = map(int, selected_score.split(':'))
                                match_results.append(("D", (p_a1, p_a2), s_a, s_b, (p_b1, p_b2)))

                        st.write("")
                        if st.button(" 상세 결과 저장 및 스코어보드 반영", type="primary", width="stretch",
                                     key=f"btn_save_match_{m_idx}"):
                            team_a_wins = 0
                            team_b_wins = 0

                            for res in match_results:
                                m_type = res[0]
                                if m_type == "S":
                                    _, p_a, s_a, s_b, p_b = res
                                    if p_a != "선택안함" and p_b != "선택안함" and p_a != p_b:
                                        st.session_state.ind_matrix.loc[p_a, p_b] = s_a
                                        st.session_state.ind_matrix.loc[p_b, p_a] = s_b
                                        update_cumulative_record(p_a, p_b, s_a, s_b)

                                    if s_a > s_b:
                                        team_a_wins += 1
                                    elif s_b > s_a:
                                        team_b_wins += 1

                                elif m_type == "D":
                                    _, (p_a1, p_a2), s_a, s_b, (p_b1, p_b2) = res
                                    if s_a > s_b:
                                        team_a_wins += 1
                                    elif s_b > s_a:
                                        team_b_wins += 1

                            st.session_state.matrix.loc[team_a, team_b] = team_a_wins
                            st.session_state.matrix.loc[team_b, team_a] = team_b_wins

                            save_room_state(room_name)

                            st.success(
                                f"저장 완료! {team_a} ({team_a_wins}) : ({team_b_wins}) {team_b} 결과가 스코어보드에 반영되었습니다.")
                            st.rerun()
    else:
        st.info("조 편성이 완료되면 경기 배정표가 나타납니다.")

# ==========================================
# 탭 5: 스코어보드 및 누적 결과 다운로드
# ==========================================
with tab_score:
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:
        cfg = st.session_state.config
        is_ind = cfg.get('is_individual', False)

        if 'table_font_size' not in st.session_state:
            num_rows = len(st.session_state.labels)
            if num_rows <= 4:
                st.session_state.table_font_size = 20
            elif num_rows <= 6:
                st.session_state.table_font_size = 16
            elif num_rows <= 8:
                st.session_state.table_font_size = 13
            else:
                st.session_state.table_font_size = 11

        if 'fullscreen_table' not in st.session_state:
            st.session_state.fullscreen_table = False

        def draw_summary_table():
            m = st.session_state.matrix
            rank = pd.DataFrame(index=st.session_state.labels)
            rank['승'] = (m > m.T).sum(axis=1)
            rank['패'] = (m < m.T).sum(axis=1)
            rank['득점'] = m.sum(axis=1, skipna=True).astype(int)
            rank['실점'] = m.sum(axis=0, skipna=True).astype(int)
            rank['득실차'] = rank['득점'] - rank['실점']

            combined_df = pd.concat([m, rank[['승', '패', '득점', '실점', '득실차']]], axis=1)
            combined_df = combined_df.sort_values(['승', '득실차'], ascending=False)

            current_fs = st.session_state.table_font_size
            ROW_HEIGHT = f"{current_fs + 25}px"

            styled_df = combined_df.style.format(precision=0, na_rep='-').set_properties(**{
                'text-align': 'center',
                'vertical-align': 'middle',
                'height': ROW_HEIGHT,
            }).set_table_styles([
                {'selector': 'th',
                 'props': [('text-align', 'center'),
                           ('vertical-align', 'middle'),
                           ('height', ROW_HEIGHT)
                           ]},
            ])

            raw_html = styled_df.to_html().replace('\n', '')

            css = f"""
            <style>
            .custom-table-wrapper table {{
                 width: 100% !important;
                 table-layout: fixed !important;
                 font-size: {current_fs}px !important;
            }}
            .custom-table-wrapper th, .custom-table-wrapper td {{
                 white-space: nowrap !important;
                 overflow: hidden !important;
                 text-overflow: ellipsis !important;
                 padding: 2px 4px !important; 
            }}
            .custom-table-wrapper th:nth-last-child(-n+5),
            .custom-table-wrapper td:nth-last-child(-n+5) {{
                 width: 70px !important; 
            }}
            .custom-table-wrapper th:first-child {{
                 width: {current_fs * 6}px !important;
            }}
            </style>
            """
            full_width_html = css + '<div class="custom-table-wrapper">' + raw_html + '</div>'
            st.markdown(full_width_html, unsafe_allow_html=True)

        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([4, 2, 2, 2])

        with col_ctrl1:
            if not st.session_state.get('fullscreen_table', False):
                if st.button("📺 전체 화면 모드", type="primary"):
                    st.session_state.fullscreen_table = True
                    st.rerun()
            else:
                if st.button("🔙 이전 화면으로", type="primary"):
                    st.session_state.fullscreen_table = False
                    st.rerun()

        with col_ctrl2:
            f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1])
            with f_col1:
                if st.button("➖", help="글자 축소"):
                    st.session_state.table_font_size = max(8, st.session_state.table_font_size - 1)
                    st.rerun()
            with f_col2:
                st.markdown(
                    f"<div style='text-align:center; padding-top:5px;'><b>크기: {st.session_state.table_font_size}</b></div>",
                    unsafe_allow_html=True)
            with f_col3:
                if st.button("➕", help="글자 확대"):
                    st.session_state.table_font_size = min(30, st.session_state.table_font_size + 1)
                    st.rerun()

        with col_ctrl3:
            if 'cum_df' in st.session_state and not st.session_state.cum_df.empty:
                csv_bytes = st.session_state.cum_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 누적 결과 다운로드",
                    data=csv_bytes,
                    file_name=f"{room_name}_누적결과.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )

        with col_ctrl4:
            if 'h2h_df' in st.session_state and not st.session_state.h2h_df.empty:
                h2h_bytes = st.session_state.h2h_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 상대전적 다운로드",
                    data=h2h_bytes,
                    file_name=f"{room_name}_상대전적.csv",
                    mime="text/csv",
                    type="secondary",
                    use_container_width=True
                )

        is_fullscreen = st.session_state.get('fullscreen_table', False)

        if is_fullscreen:
            st.markdown("### 종합 결과표 (전체 화면 모드)")
            draw_summary_table()
        else:
            col_btn1, col_btn2 = st.columns([8, 2])
            with col_btn1:
                if st.button(" 종합 결과표만 전체 화면으로 보기", type="primary"):
                    st.session_state.fullscreen_table = True
                    st.rerun()

            st.markdown(f"### {'조별' if not is_ind else '개인전'} 경기 결과 수동 입력")

            if not is_admin:
                st.warning("🔒 점수 입력은 관리자만 가능합니다. 사이드바에서 관리자 비밀번호를 입력해주세요.")
            else:
                st.info(" 기준이 되는 조(선수)를 선택하고 승/패 및 스코어를 입력하세요. (이미 완료된 경기는 비활성화됩니다.)")
                labels = st.session_state.labels
                limit = cfg.get('set_count', 3) if is_ind else cfg.get('total_g', 5)

                if len(labels) > 0:
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2.5, 1.5])

                    with c1:
                        team_a = st.selectbox("기준 조/선수 (A)", labels, key="sb_team_a")

                    with c2:
                        def format_team_b(team_b_name):
                            s_a_val = st.session_state.matrix.loc[team_a, team_b_name]
                            s_b_val = st.session_state.matrix.loc[team_b_name, team_a]
                            if not np.isnan(s_a_val) and (s_a_val + s_b_val > 0):
                                return f"{team_b_name} (완료)"
                            return team_b_name

                        team_b = st.selectbox("상대 조/선수 (B)", [l for l in labels if l != team_a],
                                              format_func=format_team_b, key="sb_team_b")

                    if team_a and team_b:
                        s_a_val = st.session_state.matrix.loc[team_a, team_b]
                        s_b_val = st.session_state.matrix.loc[team_b, team_a]
                        is_completed = not np.isnan(s_a_val) and (s_a_val + s_b_val > 0)

                        if is_completed:
                            st.warning(f"⚠️ {team_a} vs {team_b} 경기는 이미 결과가 입력되었습니다. 다른 팀을 선택해주세요.")

                        with c3:
                            res_type = st.radio(f"{team_a} 결과", ["승", "패"], horizontal=True, key="sb_res",
                                                disabled=is_completed)

                        with c4:
                            win_scores = [f"{s_a}:{limit - s_a}" for s_a in range(limit, -1, -1) if
                                          s_a >= (limit - s_a)]
                            lose_scores = [f"{s.split(':')[1]}:{s.split(':')[0]}" for s in win_scores]
                            display_scores = win_scores if res_type == "승" else lose_scores
                            selected_score = st.radio("스코어 선택", display_scores, horizontal=True, key="sb_score",
                                                      disabled=is_completed)

                        with c5:
                            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                            if st.button(" 저장", type="primary", width="stretch", key="btn_save_team",
                                         disabled=is_completed):
                                s_a, s_b = map(int, selected_score.split(':'))
                                st.session_state.matrix.loc[team_a, team_b] = s_a
                                st.session_state.matrix.loc[team_b, team_a] = s_b

                                p_a_name = team_a.split('(')[0].split('조')[-1].strip() if '조' in team_a else team_a
                                p_b_name = team_b.split('(')[0].split('조')[-1].strip() if '조' in team_b else team_b
                                update_cumulative_record(p_a_name, p_b_name, s_a, s_b)
                                save_room_state(room_name)

                                st.success(f"저장 완료! {team_a} {s_a} : {s_b} {team_b} 결과가 스코어보드에 반영되었습니다.")
                                st.rerun()

            st.divider()
            st.markdown(f"### {'조별 리그' if not is_ind else '개인전'} 종합 결과표")
            draw_summary_table()

            if not is_ind:
                st.divider()
                col_title, col_status = st.columns([3.5, 6.5])
                with col_title:
                    st.markdown("### 개인 성적 관리 및 단식 결과 수동 입력")

                with col_status:
                    if not is_admin:
                        st.error("🚫 **권한 없음:** 성적 입력 및 수정은 관리자만 가능합니다.", icon="⚠️")
                    else:
                        st.success("✅ **관리자 모드:** 입력된 단식 결과가 아래 표에 자동 반영됩니다.", icon="💡")

                        players = list(st.session_state.ind_matrix.index)
                        if len(players) > 0:
                            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2.5, 1.5])

                            with c1:
                                p_a = st.selectbox("기준 선수 (A)", players, key="ind_p_a")
                            with c2:
                                def format_player_b(p_b_name):
                                    s_a_val = st.session_state.ind_matrix.loc[p_a, p_b_name]
                                    s_b_val = st.session_state.ind_matrix.loc[p_b_name, p_a]
                                    if not np.isnan(s_a_val) and (s_a_val + s_b_val > 0):
                                        return f"{p_b_name} (완료)"
                                    return p_b_name

                                p_b = st.selectbox("상대 선수 (B)", [p for p in players if p != p_a],
                                                   format_func=format_player_b, key="ind_p_b")

                            if p_a and p_b:
                                s_a_val = st.session_state.ind_matrix.loc[p_a, p_b]
                                s_b_val = st.session_state.ind_matrix.loc[p_b, p_a]
                                is_completed_ind = not np.isnan(s_a_val) and (s_a_val + s_b_val > 0)

                                if is_completed_ind:
                                    st.warning(f"⚠️ {p_a} vs {p_b} 경기는 이미 결과가 입력되었습니다.")

                                with c3:
                                    res_type_ind = st.radio(f"{p_a} 결과", ["승", "패"], horizontal=True,
                                                            key="ind_res_radio", disabled=is_completed_ind)

                                with c4:
                                    ind_limit = 3
                                    win_scores_ind = [f"{ind_limit}:{i}" for i in range(ind_limit)]
                                    lose_scores_ind = [f"{i}:{ind_limit}" for i in range(ind_limit)]
                                    display_scores_ind = win_scores_ind if res_type_ind == "승" else lose_scores_ind
                                    selected_score_ind = st.radio("스코어 선택", display_scores_ind, horizontal=True,
                                                                  key="ind_score_radio", disabled=is_completed_ind)

                                with c5:
                                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                                    if st.button(" 저장", type="primary", width="stretch", key="btn_save_ind",
                                                 disabled=is_completed_ind):
                                        s_a, s_b = map(int, selected_score_ind.split(':'))
                                        st.session_state.ind_matrix.loc[p_a, p_b] = s_a
                                        st.session_state.ind_matrix.loc[p_b, p_a] = s_b
                                        update_cumulative_record(p_a, p_b, s_a, s_b)
                                        save_room_state(room_name)
                                        st.success(f"저장 완료! {p_a} {s_a} : {s_b} {p_b} 결과가 반영되었습니다.")
                                        st.rerun()

                col_title, col_info = st.columns([3, 7])
                with col_title:
                    st.markdown("#### 개인 성적표 (매트릭스)")
                with col_info:
                    st.info(" **아래 표에서 특정 선수의 행(Row)을 클릭**하면 오늘 진행된 상세 세트 전적을 확인할 수 있습니다.")

                if is_admin:
                    st.success("마스터 권한 활성화: 표를 더블클릭하여 직접 수정할 수 있습니다.")
                    edited_ind_matrix = st.data_editor(
                        st.session_state.ind_matrix,
                        width="stretch",
                        height=400,
                        hide_index=False,
                        key="ind_matrix_editor"
                    )
                    if not edited_ind_matrix.equals(st.session_state.ind_matrix):
                        st.session_state.ind_matrix = edited_ind_matrix
                        save_room_state(room_name)
                        st.rerun()
                else:
                    event_matrix = st.dataframe(
                        st.session_state.ind_matrix.style.format(precision=0, na_rep='-'),
                        width="stretch",
                        height=400,
                        on_select="rerun",
                        selection_mode="single-row",
                        key="ind_matrix_select"
                    )

                    if event_matrix and event_matrix.selection.rows:
                        selected_idx = event_matrix.selection.rows[0]
                        selected_player = st.session_state.ind_matrix.index[selected_idx]

                        st.markdown(f"##### [{selected_player}] 오늘 상세 세트 전적")

                        history = []
                        for opp in st.session_state.ind_matrix.columns:
                            if selected_player == opp: continue
                            s_a = st.session_state.ind_matrix.loc[selected_player, opp]
                            s_b = st.session_state.ind_matrix.loc[opp, selected_player]

                            if not np.isnan(s_a) and not np.isnan(s_b) and (s_a + s_b > 0):
                                res_str = "승리 " if s_a > s_b else ("패배 " if s_a < s_b else "무승부 ")
                                history.append(f"- vs **{opp}** : {int(s_a)} 대 {int(s_b)} ({res_str})")

                        if history:
                            for h in history:
                                st.markdown(h)
                        else:
                            st.info("아직 진행된 경기가 없습니다.")

                st.divider()
                st.markdown("#### 🔍 역대 누적 상대 전적 검색")
                st.info("두 선수를 선택하고 버튼을 누르면 지금까지의 누적 맞대결 전적을 팝업 창으로 확인할 수 있습니다.")

                players_list = list(st.session_state.ind_matrix.index)
                if len(players_list) >= 2:
                    col_s1, col_s2, col_btn = st.columns([3, 3, 2])
                    with col_s1:
                        search_p1 = st.selectbox("선수 1 선택", players_list, key="search_p1")
                    with col_s2:
                        search_p2 = st.selectbox("선수 2 선택", [p for p in players_list if p != search_p1],
                                                 key="search_p2")
                    with col_btn:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("📊 전적 창 열기", type="primary", use_container_width=True):
                            show_h2h_dialog(search_p1, search_p2)

                st.divider()

                im = st.session_state.ind_matrix
                ind_rank = pd.DataFrame(index=im.index)
                ind_rank['개인승'] = (im > im.T).sum(axis=1)
                ind_rank['개인패'] = (im < im.T).sum(axis=1)
                ind_rank['세트득실'] = im.sum(axis=1, skipna=True) - im.sum(axis=0, skipna=True)

                st.markdown("#### 개인별 순위 (세트 기준)")
                st.table(ind_rank.sort_values(['개인승', '세트득실'], ascending=False))
    else:
        st.info("조 편성이 완료되면 스코어보드가 나타납니다.")

'''
🏓 동호회 운영 시스템 사용 설명서
환영합니다!
본 시스템은 동호회(탁구, 배드민턴 등)의 출석 체크, 자동 조 편성, 경기 진행, 스코어 기록 및 누적 전적 
관리를 한 번에 해결해 주는 스마트 운영 플랫폼입니다.

🔐 1. 시작하기 (접속 및 권한)
본 시스템은 '관리자(운영진)'와 '일반 회원(조회용)' 모드로 나뉘어 작동합니다.

구장명(방 이름) 입력: 좌측 사이드바에서 사용할 구장명(예: 우리동호회_일요모임)을 입력합니다. 
같은 구장명을 입력한 기기끼리는 실시간으로 화면이 공유됩니다.
일반 회원 (조회 전용): 비밀번호를 입력하지 않으면 조회 전용 모드로 접속되며, 점수 조작이나 설정 변경이 불가능합니다.
관리자 모드 (운영진 전용):
최초 접속 시: 원하는 비밀번호를 입력하면 해당 구장의 공식 비밀번호로 암호화되어 영구 저장됩니다.
이후 접속 시: 처음에 설정했던 비밀번호를 입력해야 관리자 권한(점수 입력, 명단 업로드 등)이 활성화됩니다.
📁 2. 사전 준비 (데이터 업로드)
※ 관리자만 가능합니다.

좌측 사이드바에서 모임 운영에 필요한 데이터를 업로드합니다.

명단 파일(CSV) 업로드: 회원의 이름, 부수, 참석예정 여부가 적힌 최신 명단을 업로드합니다.
누적 결과 / 상대전적 업로드 (선택): 이전 모임까지의 누적 데이터가 있다면 업로드하여 역대 전적을 이어갈 수 있습니다.
시합 일자 및 부수 조정 기준 선택: 오늘 날짜를 확인하고, 대회에 적용할 부수 조정 기준을 선택합니다.
🚀 3. 단계별 진행 가이드 (상단 탭 순서대로 진행)
탭 1️⃣ : 출석체크
오늘 모임에 참석한 인원을 확정하는 단계입니다.

명단에 있는 회원들의 '참석' 체크박스를 클릭하여 출석을 확인합니다. (명단의 '참석예정' 데이터가 자동으로 기본 반영되어 있습니다.)
체크가 끝나면 [참석자 확정하기] 버튼을 누릅니다.
💡 Tip: 모임이 끝난 후 [📥 최신 명단(CSV) 다운로드] 버튼을 누르면, 오늘 출석이 반영된 명단을 받을 수 있어 다음 모임 때 편리합니다.
탭 2️⃣ : 운영 설정
오늘 진행할 시합의 룰과 조 편성 방식을 결정합니다.

조 구성 & 경기 규칙: 몇 개의 조로 나눌지, 단식/복식은 몇 게임씩 할지, 탁구대(코트)는 몇 개를 사용할지 설정합니다.
방식 선택:
AI 선정: 실력(부수)이 균등하게 분배되도록 시스템이 1초 만에 자동으로 조를 짭니다.
**제비뽑기: 부수별로 그룹을 나눈 뒤, 화면에서 직접 조 번호를 선택하는 '디지털 제비뽑기'를 진행합니다.
설정이 완료되면 [설정 확정 및 편성 시작] 버튼을 누릅니다.
탭 3️⃣ : 조 편성 결과
완성된 조별 명단과 각 조의 총합 부수(실력 지표)를 한눈에 확인할 수 있습니다.
이 화면을 띄워두고 회원들에게 본인의 조를 확인하도록 안내해 주세요.
탭 4️⃣ : 경기 배정 (스코어 입력)
본격적인 시합이 시작되면 사용하는 탭입니다.

경기 배정표: 몇 번 테이블에서 어느 조가 맞붙는지 대진표가 표시됩니다.
상세 결과 입력: 배정표에서 진행할 경기의 행(Row)을 클릭하면 아래에 점수 입력창이 열립니다.
출전할 선수(단식/복식)를 선택하고, 세트 스코어를 입력한 뒤 **[상세 결과 저장]**을 누르면 스코어보드에 즉시 반영됩니다.
탭 5️⃣ : 스코어보드 (종합 상황판)
현재까지의 대회 진행 상황과 개인별 성적을 확인하는 탭입니다.

📺 전체 화면 모드: 버튼을 누르면 스코어보드가 화면에 꽉 차게 표시됩니다. (구장의 대형 TV나 모니터에 띄워두기 좋습니다.)
개인 성적표 (매트릭스): 특정 선수의 행을 클릭하면 오늘 누구와 붙어서 몇 대 몇으로 이기고 졌는지 상세 히스토리가 나옵니다.
📊 역대 누적 상대 전적 검색: 두 명의 선수를 선택하고 버튼을 누르면, 지금까지 두 사람의 역대 맞대결 전적(승률, 득점 등)이 팝업창으로 화려하게 나타납니다.
💾 4. 모임 종료 후 마무리 (데이터 백업)
모든 시합이 종료되면 다음 모임을 위해 데이터를 백업해야 합니다. [스코어보드] 탭 상단에 있는 두 개의 다운로드 버튼을 클릭하세요.

[📥 누적 결과 다운로드] : 회원들의 총 경기수, 승/패, 득실점 데이터가 저장됩니다.
[📥 상대전적 다운로드] : 회원들 간의 1:1 맞대결 기록이 저장됩니다.
다운로드한 CSV 파일들은 잘 보관해 두었다가, 다음 모임 시작 시 사이드바에 업로드하면 역대 전적이 계속해서 누적됩니다!

❓ 자주 묻는 질문 (FAQ)
Q. 다른 사람 핸드폰에서도 점수를 볼 수 있나요? A. 네! 사이드바에서 **같은 '구장명'을 입력하고 [🔄 최신 경기결과 불러오기] 버튼을 누르면, 관리자가 입력한 점수와 조 편성 결과가 실시간으로 동기화되어 보입니다.

Q. 점수를 잘못 입력했어요. 수정할 수 있나요? A. 네, 관리자 모드라면 [스코어보드] 탭 하단의 '개인 성적표(매트릭스)' 표를 더블 클릭하여 점수를 직접 수정할 수 있습니다.

Q. 비밀번호를 잊어버렸어요. A. 시스템 관리자(서버 운영자)에게 문의하여 해당 구장의 _pw.txt 파일을 삭제해 달라고 요청하세요. 삭제 후 다시 접속하여 새로운 비밀번호를 설정할 수 있습니다.

'''
