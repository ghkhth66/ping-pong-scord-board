import streamlit as st
import os
import numpy as np
import random
import pandas as pd
import re
from datetime import datetime
import math
import io, time
import hashlib

from streamlit_autorefresh import st_autorefresh

# 스마트폰에서 이전 방을 기억하기 위한 쿠키 매니저 라이브러리 임포트
try:
    from streamlit_cookies_manager import EncryptedCookieManager
except ImportError:
    st.error("⚠️ 'streamlit-cookies-manager' 라이브러리가 설치되지 않았습니다. 터미널에서 설치해주세요.")

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("⚠️ 'st-gsheets-connection' 라이브러리가 설치되지 않았습니다."
             " 터미널에서 'pip install st-gsheets-connection'을 실행해주세요.")

from Program_User_Guide import show_help_section

# ==========================================
# 1. 환경 설정 및 전처리 (Config & CSS)
# ==========================================
DEV_MODE = False

# 관리자 마스터 비밀번호 설정 (secrets 설정에서만 가져옴)
MASTER_PASSWORD = st.secrets["master_password"]

def hash_password(password):
    """비밀번호를 안전하게 보관하기 위해 SHA-256 방식으로 암호화하는 함수"""
    return hashlib.sha256(password.encode()).hexdigest()

# 마스터 비밀번호 암호화 저장
HASHED_MASTER_PW = hash_password(MASTER_PASSWORD)

CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')  # 오늘 날짜

# 마스터 DB 시트 URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1x26ijdrwI9BKPXYM7IJAkTUVYZBgSqST6X9sVgwvhcE/edit"

# 시스템 관리자가 미리 만들어둔 빈 구글 시트 URL 리스트 (Pool)
PRE_MADE_URLS = [
    "https://docs.google.com/spreadsheets/d/10wiPeAlcfVFG1Ea74T8tQmuOre4FtIULdFXt6h5DTfk/edit"
    "https://docs.google.com/spreadsheets/d/1-FmAJWOb8I0l14wJOWgX98PFzR0MYKOB5rio455tXo0/edit"
    "https://docs.google.com/spreadsheets/d/1AKfdQOo3EsodIJpgcuMd-A42xvaKhyIM-k-i93Eu_Lg/edit"
    "https://docs.google.com/spreadsheets/d/1LJl3cBkVLhbNCzYhDqYcz84lKDqe76lY14hXUFkHC3c/edit"
    "https://docs.google.com/spreadsheets/d/1ORJhzSxelwB2_uKlVa5rFOagTqgSdI6R3S400VC0-dA/edit"
    "https://docs.google.com/spreadsheets/d/1R1BDavQ9Gi44Jl-QnNqvAQQb35qChWv608sSlUh-IZU/edit"
    "https://docs.google.com/spreadsheets/d/1U9vKw_FFc55Ft-hdUkbY5mQwKDlzc6AsJWrXRNIxY8c/edit"
    "https://docs.google.com/spreadsheets/d/1_5hVAmDeUG_PCJKx9-pPkWBmCBzNwnZz-KZoXSOJo44/edit"
    "https://docs.google.com/spreadsheets/d/1n5iz4ZOlv6OUcNGQcojTZaCeGf5JdAEyeu-WoeIO1YA/edit"
    "https://docs.google.com/spreadsheets/d/1Gwk0L-MY4s7Uwnv9K73oqdEzqNAjnXsTNjhHVKQcqJE/edit"
    "https://docs.google.com/spreadsheets/d/1J6Pe71i1SHVg6t4vqv3k_FIaZkWPQeGwjmFZxk6lHWw/edit"
    "https://docs.google.com/spreadsheets/d/1TO7Ny1Jy845N2OyJTceVmio8-DkfLKu25HbXvHJyBd8/edit"
    "https://docs.google.com/spreadsheets/d/1VwQcD7CHkwt_J4F_PLMMaDkoZOV5x4uXTfyvgvvnD8c/edit"
    "https://docs.google.com/spreadsheets/d/1WXwxbKzO4jNdv9eKM3cS9CrU8Vsm6bgwYWj-E3NyCTI/edit"
    "https://docs.google.com/spreadsheets/d/1d6sQcSX-AWIGCv9zoMEO-Cui-z_2Ch3RbsDGAkbt50A/edit"
    "https://docs.google.com/spreadsheets/d/1fU78i-onZOOYGdAdaamsANAuxPnAYoic-P2fHB4ojWk/edit"
    "https://docs.google.com/spreadsheets/d/1gsj1vb5NUeDhVn26-0Jk9vYmpJmUmeHVZHXUMJYnfjg/edit"
    "https://docs.google.com/spreadsheets/d/1bHpoOGeG9yfXeShVmrXASylSchrfzOddQhE2krfL8DA/edit"
    "https://docs.google.com/spreadsheets/d/1mlvNNNHjCQRm5yGE4JtJseNUtDgWbkvlbJxxy4hYcDA/edit"
    "https://docs.google.com/spreadsheets/d/1o3t1OhfeZuhdtx23bs2kGRGxjpXZcJeYqf1J3QYjrE4/edit"
]

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="리그 운영 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 쿠키 매니저 초기화
cookies = EncryptedCookieManager(password="my_super_secret_cookie_password")
if not cookies.ready():
    st.stop()

# UX/UI 개선을 위한 커스텀 CSS
st.markdown("""
<style>
    .setting-banner { background-color: #f8f9fa; border: 2px solid #28a745; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #dc3545 !important; color: white !important; }
    .custom-table-wrapper { width: 100%; }
    div.row-widget.stRadio > div { flex-direction: row; gap: 10px; align-items: center; }
    [data-testid="column"] { display: flex; flex-direction: column; justify-content: center; }
    .block-container { padding-top: 2.5rem; }
    [data-testid="stSidebar"] .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

def responsive_text(text, pc_size="28px", mobile_size="18px", font_weight="bold", color="inherit"):
    class_name = f"resp-text-{pc_size}-{mobile_size}".replace("px", "").replace(" ", "")
    css = f"""
    <style>
        .{class_name} {{ font-size: {pc_size}; font-weight: {font_weight}; color: {color}; margin-bottom: 10px; line-height: 1.4; }}
        @media (max-width: 768px) {{ .{class_name} {{ font-size: {mobile_size}; }} }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(f'<div class="{class_name}">{text}</div>', unsafe_allow_html=True)

def reset_config_state():
    st.session_state.config_confirmed = False
    keys_to_delete = ['matrix', 'ind_matrix', 'teams', 'draw_results']
    for k in keys_to_delete:
        if k in st.session_state: del st.session_state[k]

def update_cumulative_record(p_a, p_b, s_a, s_b):
    if 'cum_df' not in st.session_state:
        st.session_state.cum_df = pd.DataFrame(columns=['방이름', '이름', '총경기수', '승', '패', '득점', '실점'])

    df_cum = st.session_state.cum_df
    room = st.session_state.room_name

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
            st.session_state.h2h_df = pd.DataFrame(columns=['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

        h2h = st.session_state.h2h_df
        p1, p2 = sorted([p_a, p_b])
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)

        if not mask.any():
            new_row = pd.DataFrame([{'방이름': room, 'Player1': p1, 'Player2': p2, 'P1_Win': 0, 'P2_Win': 0, 'P1_Score': 0, 'P2_Score': 0}])
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

def get_sheet_template(sheet_type):
    if sheet_type == "선수명단":
        return pd.DataFrame({"이름": [], "부수": [], "참석예정": [], "참석": [], "조편성_신청": []})
    elif sheet_type == "누적전적":
        return pd.DataFrame({"경기일자": [], "선수1": [], "선수2": [], "세트스코어": [], "승자": [], "비고": []})
    elif sheet_type == "상대전적":
        return pd.DataFrame({"방이름": [], "Player1": [], "Player2": [], "P1_Win": [], "P2_Win": [], "P1_Score": [], "P2_Score": []})
    return pd.DataFrame()

def generate_excel_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        get_sheet_template("선수명단").to_excel(writer, sheet_name="선수명단", index=False)
        get_sheet_template("누적전적").to_excel(writer, sheet_name="누적전적", index=False)
        get_sheet_template("상대전적").to_excel(writer, sheet_name="상대전적", index=False)
    processed_data = output.getvalue()
    return processed_data

def align_columns_to_template(uploaded_df, template_df):
    expected_columns = template_df.columns.tolist()
    for col in expected_columns:
        if col not in uploaded_df.columns:
            uploaded_df[col] = None
    return uploaded_df

def extract_busu(busu_str):
    try:
        nums = re.findall(r'\d+', str(busu_str))
        return float(nums[0]) if nums else 9.0
    except:
        return 9.0

@st.dialog("📊 역대 누적 상대 전적")
def show_h2h_dialog(player_a, player_b):
    p1, p2 = sorted([player_a, player_b])
    h2h = st.session_state.get('h2h_df', pd.DataFrame())

    if not h2h.empty:
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)
        if mask.any():
            record = h2h[mask].iloc[0]
            p1_w, p2_w = record['P1_Win'], record['P2_Win']
            p1_s, p2_s = record['P1_Score'], record['P2_Score']

            st.markdown(f"<h3 style='text-align: center; color: #28a745;'>{p1} <span style='color:gray;'>vs</span> {p2}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size:1.1rem;'>총 <b>{p1_w + p2_w}</b>전 맞대결</p>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.info(f"<div style='text-align:center; font-size:1.2rem;'><b>{p1}</b><br><br>🏆 <b>{p1_w}</b> 승<br>🎯 {p1_s} 득점</div>", unsafe_allow_html=True)
            with c2:
                st.error(f"<div style='text-align:center; font-size:1.2rem;'><b>{p2}</b><br><br>🏆 <b>{p2_w}</b> 승<br>🎯 {p2_s} 득점</div>", unsafe_allow_html=True)
            st.write("")
            if st.button("닫기", use_container_width=True): st.rerun()
            return

    st.warning("아직 두 선수의 누적 맞대결 기록이 없습니다.")
    if st.button("닫기", use_container_width=True): st.rerun()

# ==========================================
# 🌐 세션 초기화 및 구글 시트 연결
# ==========================================
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'room_name' not in st.session_state: st.session_state.room_name = "생활_탁구장"
if 'main_df' not in st.session_state: st.session_state.main_df = get_sheet_template("선수명단")
if 'cum_df' not in st.session_state: st.session_state.cum_df = get_sheet_template("누적전적")
if 'h2h_df' not in st.session_state: st.session_state.h2h_df = get_sheet_template("상대전적")
if 'attendance_confirmed' not in st.session_state: st.session_state.attendance_confirmed = False
if 'config_confirmed' not in st.session_state: st.session_state.config_confirmed = False

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_room_list():
    try:
        db_df = conn.read(spreadsheet=SHEET_URL, worksheet="시트1", ttl=0)
        room_list = db_df['방이름'].tolist() if not db_df.empty else []
        return db_df, room_list
    except Exception as e:
        st.error(f"마스터 DB 연결 실패: {e}")
        return pd.DataFrame(), []

def get_current_room_sheet_url(target_room):
    try:
        url = db_df.loc[db_df['방이름'] == target_room, '시트URL'].values[0]
        return url
    except:
        return None

def get_available_url(db_df):
    used_urls = db_df['시트URL'].dropna().tolist() if not db_df.empty else []
    for url in PRE_MADE_URLS:
        if url not in used_urls:
            return url
    return None

# ==========================================
# 🟢 메인 로직 시작
# ==========================================
db_df, room_list = load_room_list()

is_admin = st.session_state.is_admin
room_name = st.session_state.room_name

if not is_admin:
    st.sidebar.markdown("### 🏟️ 구장 접속 및 생성")
    tab_login, tab_create = st.sidebar.tabs(["🔑 기존 구장 접속", "➕ 새 구장 만들기"])

    # ------------------------------------------
    # 🔑 1. 기존 구장 접속 (로그인)
    # ------------------------------------------
    with tab_login:
        with st.form(key="login_form"):
            last_room = cookies.get("last_room", "")
            default_index = room_list.index(last_room) if last_room in room_list else 0

            login_room_name = st.selectbox("구장명 (방 이름) 선택", options=room_list, index=default_index)
            admin_password = st.text_input("관리자 비밀번호 (조회 시 생략 가능)", type="password")

            submit_login = st.form_submit_button("로그인", use_container_width=True)

        if submit_login:
            st.session_state.room_name = login_room_name
            is_valid_admin = False

            if admin_password:
                hashed_pw = hash_password(admin_password)
                if hashed_pw == HASHED_MASTER_PW:
                    is_valid_admin = True
                    st.sidebar.success("👑 마스터 권한 접속")
                elif login_room_name in db_df['방이름'].values:
                    saved_pw = db_df.loc[db_df['방이름'] == login_room_name, '비밀번호'].values[0]
                    if hashed_pw == saved_pw:
                        is_valid_admin = True
                        st.sidebar.success(f"✅ '{login_room_name}' 관리자 모드 활성화")
                    else:
                        st.sidebar.error("❌ 비밀번호가 틀렸습니다.")

            if is_valid_admin or not admin_password:
                if is_valid_admin:
                    st.session_state.is_admin = True

                cookies["last_room"] = login_room_name
                cookies.save()

                target_url = get_current_room_sheet_url(login_room_name)
                if target_url:
                    try:
                        st.session_state.main_df = conn.read(spreadsheet=target_url, worksheet="선수명단", ttl=0)
                        st.session_state.cum_df = conn.read(spreadsheet=target_url, worksheet="누적전적", ttl=0)
                        st.session_state.h2h_df = conn.read(spreadsheet=target_url, worksheet="상대전적", ttl=0)
                    except Exception as e:
                        st.sidebar.warning("⚠️ 전용 시트 연결 실패. 기본 시트 구조를 생성합니다.")
                        st.session_state.main_df = get_sheet_template("선수명단")
                        st.session_state.cum_df = get_sheet_template("누적전적")
                        st.session_state.h2h_df = get_sheet_template("상대전적")
                time.sleep(1)
                st.rerun()

    # ------------------------------------------
    # ➕ 2. 새 구장 만들기
    # ------------------------------------------
    with tab_create:
        st.markdown("#### ✨ 새로운 구장 등록")
        with st.form(key="create_room_form"):
            new_room_name = st.text_input("새로 만들 구장명 (중복 불가)")
            admin_name = st.text_input("관리자 이름 (대표자명)")
            admin_email = st.text_input("관리자 이메일 (비밀번호 분실 시 필요)")
            new_room_pw = st.text_input("새 구장 비밀번호 설정", type="password")

            submit_create = st.form_submit_button("새 구장 생성하기", type="primary", use_container_width=True)

        if submit_create:
            if not new_room_name or not admin_name or not admin_email or not new_room_pw:
                st.warning("모든 정보를 빠짐없이 입력해주세요.")
            elif new_room_name in db_df['방이름'].values:
                st.error(f"⚠️ '{new_room_name}'(은)는 이미 존재하는 구장입니다.")
            else:
                assigned_url = get_available_url(db_df)
                if not assigned_url:
                    st.error("❌ 시스템에 할당 가능한 빈 시트가 없습니다. 시스템 관리자에게 문의하세요.")
                    st.stop()

                hashed_pw = hash_password(new_room_pw)
                new_data = pd.DataFrame([{
                    "방이름": new_room_name,
                    "관리자이름": admin_name,
                    "이메일": admin_email,
                    "비밀번호": hashed_pw,
                    "시트URL": assigned_url,
                    "생성일자": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])

                try:
                    updated_df = pd.concat([db_df, new_data], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="시트1", data=updated_df)
                    load_room_list.clear()

                    st.session_state.room_name = new_room_name
                    st.session_state.is_admin = True
                    cookies["last_room"] = new_room_name
                    cookies.save()

                    with st.spinner("구장 전용 데이터베이스를 초기화 중입니다... (약 5\~10초 소요)"):
                        empty_main = get_sheet_template("선수명단")
                        empty_cum = get_sheet_template("누적전적")
                        empty_h2h = get_sheet_template("상대전적")

                        conn.update(spreadsheet=assigned_url, worksheet="선수명단", data=empty_main)
                        conn.update(spreadsheet=assigned_url, worksheet="누적전적", data=empty_cum)
                        conn.update(spreadsheet=assigned_url, worksheet="상대전적", data=empty_h2h)

                        st.session_state.main_df = empty_main
                        st.session_state.cum_df = empty_cum
                        st.session_state.h2h_df = empty_h2h

                    st.success(f"✅ '{new_room_name}' 구장이 생성되었습니다! 바로 접속합니다.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"DB 저장 중 오류가 발생했습니다: {e}")
else:
    # ==========================================
    # 🟢 [로그인 후] 관리자 모드 사이드바
    # ==========================================
    st.sidebar.markdown(f"### 🏟️ {room_name} 구장")
    st.sidebar.success("👑 관리자 모드로 접속 중입니다.")

    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state.is_admin = False
        st.rerun()

    st.sidebar.divider()

    st.sidebar.markdown("#### ☁️ 클라우드 동기화")
    if st.sidebar.button("💾 오늘의 최종 결과 구글시트 저장", type="primary", use_container_width=True):
        if "room_name" in st.session_state and st.session_state.room_name:
            with st.spinner("해당 구장 전용 시트에 저장 중..."):
                try:
                    target_sheet_url = get_current_room_sheet_url(st.session_state.room_name)
                    if target_sheet_url:
                        conn.update(spreadsheet=target_sheet_url, worksheet="선수명단", data=st.session_state.main_df)
                        conn.update(spreadsheet=target_sheet_url, worksheet="누적전적", data=st.session_state.cum_df)
                        conn.update(spreadsheet=target_sheet_url, worksheet="상대전적", data=st.session_state.h2h_df)
                        st.sidebar.success(f"✅ {st.session_state.room_name} 전용 시트 저장 완료!")
                    else:
                        st.sidebar.error("❌ 이 구장의 전용 시트 URL을 찾을 수 없습니다. (마스터 DB 확인 필요)")
                except Exception as e:
                    st.sidebar.error(f"❌ 저장 실패: {e}")
        else:
            st.sidebar.warning("⚠️ 접속된 구장 정보가 없습니다. 다시 로그인해 주세요.")

    st.sidebar.divider()

    auto_refresh = st.sidebar.checkbox("자동 새로고침 켜기 (PC 전광판용)")
    if auto_refresh:
        st_autorefresh(interval=5 * 60 * 1000, limit=None, key="dashboard_refresh")
        st.sidebar.info("🟢 현재 5분마다 화면이 자동 갱신 중입니다. \n\n⚠️ 데이터 입력/수정 중에는 이 기능을 꺼주세요!")

    st.sidebar.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

    # ==========================================
    # 🌟 데이터 관리 (명단/전적 업로드) - 인코딩 에러 완벽 방어
    # ==========================================
    with st.sidebar.expander("⚙️ 데이터 관리 (명단/전적 업로드)", expanded=False):

        data_source = st.radio("데이터 가져오기 방식", ["☁️ 구글 시트에서 불러오기", "📁 내 기기에서 파일 업로드"])

        if data_source == "☁️ 구글 시트에서 불러오기":
            st.info("클라우드에 저장된 최신 데이터를 화면으로 불러옵니다.")
            if st.button("구글 시트 데이터 최신화", use_container_width=True):
                with st.spinner("클라우드에서 데이터를 가져오는 중..."):
                    target_url = get_current_room_sheet_url(st.session_state.room_name)
                    if target_url:
                        st.session_state.main_df = conn.read(spreadsheet=target_url, worksheet="선수명단", ttl=0)
                        st.session_state.cum_df = conn.read(spreadsheet=target_url, worksheet="누적전적", ttl=0)
                        st.session_state.h2h_df = conn.read(spreadsheet=target_url, worksheet="상대전적", ttl=0)
                        st.success("동기화 완료!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("URL을 찾을 수 없습니다.")

        else:  # 📁 내 기기에서 파일 업로드
            st.markdown("---")
            st.markdown("**1. 양식 다운로드 및 작성**")
            st.caption("아래 버튼을 눌러 3개의 탭이 포함된 빈 엑셀 양식을 다운로드하고, PC나 스마트폰에서 내용을 채워주세요.")

            excel_data = generate_excel_template()
            st.download_button(
                label="📥 표준 엑셀 템플릿 다운로드",
                data=excel_data,
                file_name=f"{st.session_state.room_name}_데이터양식.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            st.markdown("<strong>2. 작성된 파일 업로드 (Excel 또는 CSV)</strong>")
            # 🌟 [수정됨] xlsx 뿐만 아니라 csv 파일도 업로드 가능하도록 허용
            uploaded_file = st.file_uploader("파일 선택 (.xlsx, .csv)", type=['xlsx', 'xls', 'csv'])

            if uploaded_file:
                if st.button("파일 데이터 적용 및 클라우드 저장", type="primary", use_container_width=True):
                    try:
                        with st.spinner("파일을 읽고 클라우드에 저장하는 중..."):
                            file_ext = uploaded_file.name.split('.')[-1].lower()
                            xls_data = {}

                            # 🌟 [수정됨] CSV 파일일 경우 여러 인코딩을 순회하며 에러 없이 읽어들임
                            if file_ext == 'csv':
                                encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin1']
                                df_loaded = None
                                for enc in encodings:
                                    try:
                                        uploaded_file.seek(0)
                                        df_loaded = pd.read_csv(uploaded_file, encoding=enc)
                                        break  # 성공하면 루프 탈출
                                    except (UnicodeDecodeError, UnicodeError):
                                        continue
                                
                                if df_loaded is not None:
                                    # CSV는 시트가 1개이므로, 컬럼명을 분석하여 어떤 데이터인지 유추
                                    cols = set(df_loaded.columns)
                                    if 'P1_Win' in cols or 'P2_Score' in cols:
                                        xls_data["상대전적"] = df_loaded
                                    elif '세트스코어' in cols or '승자' in cols:
                                        xls_data["누적전적"] = df_loaded
                                    else:
                                        xls_data["선수명단"] = df_loaded
                                else:
                                    st.error("CSV 파일의 인코딩을 인식할 수 없습니다. 파일을 확인해주세요.")
                                    st.stop()
                            
                            # 🌟 [수정됨] 엑셀 파일일 경우
                            else:
                                try:
                                    uploaded_file.seek(0)
                                    xls_data = pd.read_excel(uploaded_file, sheet_name=None)
                                except Exception as e:
                                    # 혹시 확장자만 .xlsx 이고 실제로는 CSV인 가짜 엑셀 파일일 경우를 대비한 방어 로직
                                    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
                                    df_loaded = None
                                    for enc in encodings:
                                        try:
                                            uploaded_file.seek(0)
                                            df_loaded = pd.read_csv(uploaded_file, encoding=enc)
                                            break
                                        except:
                                            continue
                                    if df_loaded is not None:
                                        xls_data["선수명단"] = df_loaded
                                    else:
                                        st.error(f"엑셀 파일 읽기 오류: {e}")
                                        st.stop()

                            # 각 시트가 존재하면 규격을 맞춘 후 세션에 저장
                            if "선수명단" in xls_data:
                                st.session_state.main_df = align_columns_to_template(xls_data["선수명단"], get_sheet_template("선수명단"))
                            if "누적전적" in xls_data:
                                st.session_state.cum_df = align_columns_to_template(xls_data["누적전적"], get_sheet_template("누적전적"))
                            if "상대전적" in xls_data:
                                st.session_state.h2h_df = align_columns_to_template(xls_data["상대전적"], get_sheet_template("상대전적"))

                            # 클라우드에 즉시 저장
                            target_url = get_current_room_sheet_url(st.session_state.room_name)
                            if target_url:
                                conn.update(spreadsheet=target_url, worksheet="선수명단", data=st.session_state.main_df)
                                conn.update(spreadsheet=target_url, worksheet="누적전적", data=st.session_state.cum_df)
                                conn.update(spreadsheet=target_url, worksheet="상대전적", data=st.session_state.h2h_df)

                        st.success("✅ 데이터가 성공적으로 적용되고 클라우드에 저장되었습니다!")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"파일 처리 중 오류 발생: {e}")

# ---------------------------------------------------------
# 3. 메인 화면 데이터 처리 (날짜 및 출석/조편성)
# ---------------------------------------------------------
selected_date = st.date_input("일자 선택", datetime.now(), disabled=not is_admin)
CURRENT_DATE = selected_date.strftime('%Y-%m-%d')
col_date = f"출석_{CURRENT_DATE}"

if col_date not in st.session_state.main_df.columns:
    if '참석예정' in st.session_state.main_df.columns:
        st.session_state.main_df[col_date] = st.session_state.main_df['참석예정'].apply(
            lambda x: 'Y' if str(x).strip().upper() in ['Y', 'O', '1', 'TRUE', '참석'] else 'N'
        )
    else:
        st.session_state.main_df[col_date] = 'Y'

if '조편성_신청' not in st.session_state.main_df.columns:
    st.session_state.main_df['조편성_신청'] = st.session_state.main_df[col_date].apply(
        lambda x: str(random.randint(1, 4)) if x == 'Y' else ""
    )

tab_home, tab_config, tab_team, tab_match, tab_score, tab_help = st.tabs(
    [" 출석체크", " 운영 설정", " 조 편성 결과", " 경기 배정", " 스코어보드", "사용설명서"])

attendees_count = (st.session_state.main_df[col_date] == 'Y').sum() if col_date in st.session_state.main_df.columns else 0
