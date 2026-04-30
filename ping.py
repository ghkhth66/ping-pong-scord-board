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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1x26ijdrwI9BKPXYM7IJAkTUVYZBgSqST6X9sVgwvhcE/edit"  # 구글 시트 주소

# Streamlit 페이지 기본 설정 (브라우저 탭 이름, 넓은 화면 모드 등)
st.set_page_config(
    page_title="리그 운영 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 쿠키 매니저 초기화
cookies = EncryptedCookieManager(password="my_super_secret_cookie_password")
if not cookies.ready():
    st.stop()

# UX/UI 개선을 위한 커스텀 CSS (버튼 색상, 테이블 너비, 정렬 등 디자인 요소 변경)
st.markdown("""
<style>
    /* 1. 특정 배너(알림창, 설정창 등)의 디자인을 꾸미는 클래스 */
    .setting-banner { 
        background-color: #f8f9fa; /* 배경색을 아주 연한 회색으로 설정 */
        border: 2px solid #28a745; /* 테두리를 2px 두께의 초록색 실선으로 설정 */
        border-radius: 12px;       /* 모서리를 둥글게 처리 (숫자가 클수록 더 둥글어짐) */
        padding: 20px;             /* 테두리 안쪽 여백을 20px로 설정하여 내용물이 답답해 보이지 않게 함 */
        margin-bottom: 20px;       /* 배너 아래쪽 바깥 여백을 20px 주어 다른 요소와 간격을 띄움 */
    }

    /* 2. Streamlit의 'Primary(주요)' 버튼 스타일 변경 */
    div.stButton > button[kind="primary"] { 
        background-color: #28a745 !important; /* 버튼 배경색을 초록색으로 강제 적용 (!important) */
        color: white !important;              /* 버튼 글자색을 흰색으로 강제 적용 */
    }

    /* 3. Streamlit의 'Secondary(보조)' 버튼 스타일 변경 */
    div.stButton > button[kind="secondary"] { 
        background-color: #dc3545 !important; /* 버튼 배경색을 빨간색으로 강제 적용 */
        color: white !important;              /* 버튼 글자색을 흰색으로 강제 적용 */
    }

    /* 4. 커스텀 테이블을 감싸는 영역의 너비 설정 */
    .custom-table-wrapper { 
        width: 100%; /* 테이블이 화면(또는 부모 컨테이너)의 가로 너비를 100% 꽉 채우도록 설정 */
    }

    /* 5. 라디오 버튼 가로 정렬 및 간격 축소 */
    div.row-widget.stRadio > div { 
        flex-direction: row; /* 기본적으로 세로로 나열되는 라디오 버튼을 가로(row)로 나열되게 변경 */
        gap: 10px;           /* 라디오 버튼 항목 사이의 간격을 10px로 좁게 설정 */
        align-items: center; /* 라디오 버튼과 텍스트가 수직 기준으로 중앙에 오도록 정렬 */
    }

    /* 6. 컬럼 내 수직 중앙 정렬을 위한 트릭 */
    [data-testid="column"] { 
        display: flex;             /* 컬럼 내부 요소를 Flexbox 레이아웃으로 설정 */
        flex-direction: column;    /* 내부 요소들이 위에서 아래로(세로로) 배치되도록 설정 */
        justify-content: center;   /* 내부 요소들을 컬럼의 세로 기준 '중앙'에 배치 (수직 중앙 정렬) */
    }

    /* 7. 화면 맨 위쪽 여백 줄이기 (새로 추가된 부분) */
    .block-container {
        padding-top: 2.5rem; /* 숫자를 줄일수록 위로 올라갑니다 (기본값 약 6rem) */
    }
    
    /* 사이드바(왼쪽)의 맨 위쪽 여백 조절 */
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True) # HTML과 CSS 태그가 문자열 그대로 출력되지 않고 실제 웹페이지에 적용되도록 허용하는 옵션

# 1. 반응형 텍스트를 출력하는 함수 정의
def responsive_text(text, pc_size="28px", mobile_size="18px", font_weight="bold", color="inherit"):
    """
    PC와 모바일에서 글자 크기가 자동으로 변하는 텍스트를 출력하는 함수
    """
    # 설정한 크기에 따라 고유한 CSS 클래스 이름 생성 (충돌 방지)
    class_name = f"resp-text-{pc_size}-{mobile_size}".replace("px", "").replace(" ", "")

    # CSS 스타일 정의
    css = f"""
    <style>
        /* PC 등 큰 화면 기본 설정 */
        .{class_name} {{
            font-size: {pc_size};
            font-weight: {font_weight};
            color: {color};
            margin-bottom: 10px;
            line-height: 1.4;
        }}

        /* 스마트폰 등 작은 화면 (768px 이하) 설정 */
        @media (max-width: 768px) {{
            .{class_name} {{
                font-size: {mobile_size};
            }}
        }}
    </style>
    """
    # CSS 주입 및 HTML 텍스트 렌더링
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(f'<div class="{class_name}">{text}</div>', unsafe_allow_html=True)


def reset_config_state():
    """설정을 초기화할 때 기존에 만들어진 조 편성, 대진표 등의 데이터를 삭제하는 함수"""
    st.session_state.config_confirmed = False

    keys_to_delete = ['matrix', 'ind_matrix', 'teams', 'draw_results']

    for k in keys_to_delete:
        if k in st.session_state: del st.session_state[k]


def update_cumulative_record(p_a, p_b, s_a, s_b):
    """경기가 끝날 때마다 선수들의 누적 전적(승, 패, 득점, 실점)과 상대 전적을 업데이트하는 함수
       - p_a, p_b: 선수 A와 선수 B의 이름
       - s_a, s_b: 선수 A와 선수 B의 점수(Score)
    """
    # 세션 상태에 누적 전적 데이터프레임(cum_df)이 없으면 빈 표를 새로 만듭니다.
    if 'cum_df' not in st.session_state:
        st.session_state.cum_df = pd.DataFrame(columns=['방이름', '이름', '총경기수', '승', '패', '득점', '실점'])

    df_cum = st.session_state.cum_df
    room = st.session_state.room_name

    # 내부 함수: 명단에 없는 새로운 선수면 데이터프레임에 0전 0승 0패로 새로 추가하는 역할
    def ensure_player(df, name):
        if name not in df['이름'].values:
            new_row = pd.DataFrame([{'이름': name, '총경기수': 0, '승': 0, '패': 0, '득점': 0, '실점': 0}])
            # 기존 표(df) 아래에 새로운 행(new_row)을 이어 붙임 (ignore_index=True로 인덱스 번호 재배열)
            df = pd.concat([df, new_row], ignore_index=True)
        return df

    # "선택안함"(부전승 등 빈 자리)이 아닌 실제 선수일 경우에만 명단에 추가/확인
    if p_a != "선택안함": df_cum = ensure_player(df_cum, p_a)
    if p_b != "선택안함": df_cum = ensure_player(df_cum, p_b)

    for p, win, lose, score, opp_score in [(p_a, s_a > s_b, s_a < s_b, s_a, s_b),
                                           (p_b, s_b > s_a, s_b < s_a, s_b, s_a)]:
        if p != "선택안함":  # 실제 선수인 경우에만 기록 업데이트
            # 해당 선수가 있는 행의 위치(인덱스 번호)를 찾음
            idx = df_cum[df_cum['이름'] == p].index[0]

            # .at[행, 열]을 사용하여 해당 선수의 기록에 값을 더해줌 (+=)
            df_cum.at[idx, '총경기수'] += 1
            df_cum.at[idx, '승'] += 1 if win else 0      # 이겼으면 1을 더하고, 아니면 0을 더함
            df_cum.at[idx, '패'] += 1 if lose else 0     # 졌으면 1을 더하고, 아니면 0을 더함
            df_cum.at[idx, '득점'] += score               # 내가 낸 점수를 득점에 누적
            df_cum.at[idx, '실점'] += opp_score           # 상대가 낸 점수를 실점에 누적

    # 업데이트된 표를 다시 세션 상태에 저장하여 화면에 반영되게 함
    st.session_state.cum_df = df_cum

    if p_a != "선택안함" and p_b != "선택안함":

        # 상대 전적 표(h2h_df)가 없으면 새로 만듦
        if 'h2h_df' not in st.session_state:
            st.session_state.h2h_df = pd.DataFrame(
                columns=['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

        h2h = st.session_state.h2h_df

        # ★ 핵심: A vs B 와 B vs A 가 따로 기록되는 것을 막기 위해 이름을 가나다(알파벳) 순으로 정렬
        p1, p2 = sorted([p_a, p_b])

        # 표에서 Player1이 p1이고, Player2가 p2인 행을 찾는 조건(마스크) 생성
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)

        # 만약 두 사람의 맞대결 기록이 아예 없다면 새로 0승 0패로 만들어줌
        if not mask.any():
            new_row = pd.DataFrame(
                [{'방이름': room, 'Player1': p1, 'Player2': p2, 'P1_Win': 0, 'P2_Win': 0, 'P1_Score': 0, 'P2_Score': 0}])
            h2h = pd.concat([h2h, new_row], ignore_index=True)
            mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)

        # 해당 맞대결 기록이 있는 행의 위치(인덱스)를 찾음
        idx = h2h[mask].index[0]

        # p1이 원래 p_a 였는지, p_b 였는지에 따라 점수와 승패를 알맞게 배분하여 더해줌
        if p1 == p_a:
            h2h.at[idx, 'P1_Win'] += 1 if s_a > s_b else 0
            h2h.at[idx, 'P2_Win'] += 1 if s_b > s_a else 0
            h2h.at[idx, 'P1_Score'] += s_a
            h2h.at[idx, 'P2_Score'] += s_b
        else:  # p1이 원래 p_b 였던 경우 (이름 순 정렬 때문에 자리가 바뀐 경우)
            h2h.at[idx, 'P1_Win'] += 1 if s_b > s_a else 0
            h2h.at[idx, 'P2_Win'] += 1 if s_a > s_b else 0
            h2h.at[idx, 'P1_Score'] += s_b
            h2h.at[idx, 'P2_Score'] += s_a

        # 업데이트된 상대 전적 표를 세션 상태에 저장
        st.session_state.h2h_df = h2h


# ==========================================
# 1. 시트 종류별 기준 템플릿(샘플) 정의 함수
# ==========================================
# ==========================================
# 🌟 [새로 추가된 부분 1] 데이터 템플릿 및 보정 함수
# ==========================================
# def get_sheet_template(sheet_type):
#     """선택한 시트 종류에 맞는 빈 컬럼 구조를 반환합니다."""
#     if sheet_type == "선수명단":
#         return pd.DataFrame({"선수ID": [], "이름": [], "부서": [], "탁구등급": [], "가입일자": []})
#     elif sheet_type == "누적전적":
#         return pd.DataFrame({"경기일자": [], "선수1": [], "선수2": [], "세트스코어": [], "승자": [], "비고": []})
#     # 🌟 [상대전적 추가된 부분 1] 상대전적 템플릿 추가 (기존 코드의 컬럼명 반영)
#     elif sheet_type == "상대전적":
#         return pd.DataFrame({"방이름": [], "Player1": [], "Player2": [], "P1_Win": [], "P2_Win": [], "P1_Score": [], "P2_Score": []})
#     return pd.DataFrame()

def get_sheet_template(sheet_type):
    """선택한 시트 종류에 맞는 빈 컬럼 구조를 반환합니다."""
    if sheet_type == "선수명단":
        # 🌟 [수정된 부분] 말씀하신 필수 컬럼들을 모두 추가했습니다.
        # (기존에 있던 부서, 탁구등급 등과 함께 필요에 맞게 순서를 조정하셔도 됩니다)
        return pd.DataFrame({
            # "선수ID": [],
            "이름": [],
            "부수": [],  # 👈 추가됨
            "참석예정": [],  # 👈 추가됨
            "참석": [],  # 👈 추가됨
            "조편성_신청": []  # 👈 추가됨
        })

    elif sheet_type == "누적전적":
        return pd.DataFrame({
            "경기일자": [], "선수1": [], "선수2": [], "세트스코어": [], "승자": [], "비고": []
        })

    elif sheet_type == "상대전적":
        return pd.DataFrame({
            "방이름": [], "Player1": [], "Player2": [], "P1_Win": [], "P2_Win": [], "P1_Score": [], "P2_Score": []
        })

    return pd.DataFrame()
# ==========================================
# 2. 업로드된 데이터의 컬럼을 템플릿에 맞게 보정하는 함수
# ==========================================
def align_columns_to_template(uploaded_df, template_df):
    expected_columns = template_df.columns.tolist()
    for col in expected_columns:
        if col not in uploaded_df.columns:
            uploaded_df[col] = None
    # return uploaded_df[expected_columns]
    # ✅ 날짜처럼 추가된 컬럼도 유지하도록 수정
    return uploaded_df
    
def extract_busu(busu_str):
    """'3부', '4부' 같은 문자열에서 숫자(3, 4)만 추출하여 계산에 사용할 수 있게 변환"""
    try:
        nums = re.findall(r'\d+', str(busu_str))
        return float(nums[0]) if nums else 9.0
    except:
        return 9.0


@st.dialog("📊 역대 누적 상대 전적")
def show_h2h_dialog(player_a, player_b):
    """두 선수를 선택했을 때 팝업창으로 역대 전적을 보여주는 함수"""
    # 1. 데이터 검색을 위한 이름 정렬 _ 이전 코드에서 저장할 때 가나다순으로 정렬했으므로, 불러올 때도 똑같이 정렬해야 데이터를 찾을 수 있습니다.
    p1, p2 = sorted([player_a, player_b])

    # 2. 세션 상태에서 상대 전적 표(h2h_df) 불러오기 _ 만약 데이터가 아예 없다면 에러가 나지 않도록 빈 표(pd.DataFrame())를 기본값으로 가져옵니다.
    h2h = st.session_state.get('h2h_df', pd.DataFrame())

    # 3. 표가 비어있지 않은지 확인
    if not h2h.empty:

        # p1과 p2가 맞붙은 기록이 있는지 찾는 조건(마스크) 생성
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)

        # 해당 조건에 맞는 데이터가 하나라도 존재한다면
        if mask.any():
            # .iloc[0]을 사용해 검색된 결과 중 첫 번째 줄(행)의 데이터를 통째로 가져옵니다.
            record = h2h[mask].iloc[0]

            # 표에 적힌 승수와 득점 데이터를 각각의 변수에 나누어 담습니다.
            p1_w, p2_w = record['P1_Win'], record['P2_Win']
            p1_s, p2_s = record['P1_Score'], record['P2_Score']

            # 4. 팝업창 상단 제목 및 총 경기 수 출력 (HTML/CSS 활용)
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

            st.write("")  # 약간의 빈 줄(여백) 추가

            # 6. 닫기 버튼 _ use_container_width=True를 주어 버튼이 팝업창 가로 길이에 꽉 차게 만듦
            if st.button("닫기", use_container_width=True):
                st.rerun()  # 버튼을 누르면 화면을 새로고침하여 팝업창을 닫음

            return  # 전적을 성공적으로 보여줬으므로 여기서 함수를 종료함

    # 7. 만약 표가 비어있거나, 두 사람의 맞대결 기록이 없을 경우 실행되는 부분
    st.warning("아직 두 선수의 누적 맞대결 기록이 없습니다.")  # 노란색 경고창 출력
    if st.button("닫기", use_container_width=True):
        st.rerun()

    st.warning("아직 두 선수의 누적 맞대결 기록이 없습니다.")
    if st.button("닫기", use_container_width=True): st.rerun()


def load_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            return pd.read_csv(uploaded_file, encoding='cp949')
    data = [{"순서": i, "이름": f"회원{i}", "성별": random.choice(["남", "여"]),
             "부수": f"{random.randint(1, 13)}부", "조편성_신청": random.choice(["토끼", "여우", "곰", "호랑이"]),
             "참석예정": random.choice(["Y", "N"])} for i in range(1, 51)]
    return pd.DataFrame(data)


# 💡 [적용 포인트 1: st.session_state]
# 화면이 재실행되어도 유지되어야 하는 핵심 데이터(권한, 방이름, 명단 등)를 세션에 저장합니다.
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'room_name' not in st.session_state: st.session_state.room_name = "생활_탁구장"
if 'main_df' not in st.session_state: st.session_state.main_df = load_data()
if 'attendance_confirmed' not in st.session_state: st.session_state.attendance_confirmed = False
if 'config_confirmed' not in st.session_state: st.session_state.config_confirmed = False

# ==========================================
# 🌐 구글 시트 연결 및 데이터 로드
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)


# 💡 [적용 포인트 2: @st.cache_data]
# 구글 시트에서 방 목록을 가져오는 작업은 무거우므로 캐싱 처리합니다. (10분 유지)
# 화면이 재실행될 때마다 API를 호출하는 것을 방지하여 속도를 크게 높입니다.
@st.cache_data(ttl=600)
def load_room_list():
    try:
        db_df = conn.read(spreadsheet=SHEET_URL, worksheet="시트1", ttl=0)
        room_list = db_df['방이름'].tolist() if not db_df.empty else ["생활_탁구장"]
        return db_df, room_list
    except Exception as e:
        st.error(f"⚠️ DB(구글시트) 연결 실패. secrets.toml 설정을 확인하세요 \n {e}")
        return pd.DataFrame(columns=["방이름", "관리자이름", "이메일", "비밀번호", "생성일자"]), ["생활_탁구장"]


db_df, room_list = load_room_list()

is_admin = st.session_state.is_admin
room_name = st.session_state.room_name

# ==========================================
# 🔴 [로그인 전] 관리자가 아닐 때 보여지는 사이드바 화면
# ==========================================
if not is_admin:
    st.sidebar.markdown("### 🏟️ 구장 접속 및 생성")
    tab_login, tab_create = st.sidebar.tabs(["🔑 기존 구장 접속", "➕ 새 구장 만들기"])

    with tab_login:
        with st.form(key="login_form"):
            last_room = cookies.get("last_room", "")
            default_index = room_list.index(last_room) if last_room in room_list else 0

            login_room_name = st.selectbox("구장명 (방 이름) 선택", options=room_list, index=default_index)
            admin_password = st.text_input("관리자 비밀번호 (조회 시 생략 가능)", type="password")

            submit_login = st.form_submit_button("로그인", use_container_width=True)

        if submit_login:
            st.session_state.room_name = login_room_name

            if admin_password:
                hashed_pw = hash_password(admin_password)
                is_valid_admin = False

                if hashed_pw == HASHED_MASTER_PW:
                    is_valid_admin = True
                    st.sidebar.success("👑 마스터 권한으로 접속했습니다.")
                elif login_room_name in db_df['방이름'].values:
                    saved_pw = db_df.loc[db_df['방이름'] == login_room_name, '비밀번호'].values[0]
                    if hashed_pw == saved_pw:
                        is_valid_admin = True
                        st.sidebar.success(f"✅ '{login_room_name}' 관리자 모드 활성화")
                    else:
                        st.sidebar.error("❌ 비밀번호가 틀렸습니다.")

                if is_valid_admin:
                    st.session_state.is_admin = True
                    cookies["last_room"] = login_room_name
                    cookies.save()

                    try:
                        all_cum = conn.read(spreadsheet=SHEET_URL, worksheet="누적전적", ttl=0)
                        all_h2h = conn.read(spreadsheet=SHEET_URL, worksheet="상대전적", ttl=0)

                        st.session_state.cum_df = all_cum[
                            all_cum['방이름'] == login_room_name] if not all_cum.empty else pd.DataFrame(
                            columns=['방이름', '이름', '총경기수', '승', '패', '득점', '실점'])
                        st.session_state.h2h_df = all_h2h[
                            all_h2h['방이름'] == login_room_name] if not all_h2h.empty else pd.DataFrame(
                            columns=['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])
                    except:
                        st.session_state.cum_df = pd.DataFrame(columns=['방이름', '이름', '총경기수', '승', '패', '득점', '실점'])
                        st.session_state.h2h_df = pd.DataFrame(
                            columns=['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

                    time.sleep(1)
                    st.rerun()
            else:
                st.sidebar.info("👀 현재 조회 전용(Read-only) 모드입니다.")

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
                hashed_pw = hash_password(new_room_pw)
                new_data = pd.DataFrame(
                    [{"방이름": new_room_name, "관리자이름": admin_name, "이메일": admin_email, "비밀번호": hashed_pw,
                      "생성일자": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                updated_df = pd.concat([db_df, new_data], ignore_index=True)

                try:
                    conn.update(spreadsheet=SHEET_URL, worksheet="시트1", data=updated_df)
                    load_room_list.clear()

                    st.session_state.room_name = new_room_name
                    st.session_state.is_admin = True
                    cookies["last_room"] = new_room_name
                    cookies.save()

                    st.session_state.cum_df = pd.DataFrame(columns=['방이름', '이름', '총경기수', '승', '패', '득점', '실점'])
                    st.session_state.h2h_df = pd.DataFrame(
                        columns=['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

                    st.success(f"✅ '{new_room_name}' 구장이 생성되었습니다!")
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

    # 🛠️ [수정된 부분 1] 기존 코드에 '클라우드 동기화' 부분이 똑같이 2번 중복되어 있어서 하나를 삭제했습니다.
    st.sidebar.markdown("#### ☁️ 클라우드 동기화")
    if st.sidebar.button("💾 오늘의 최종 결과 구글시트 저장", type="primary", use_container_width=True):
        with st.spinner("구글 시트에 데이터를 안전하게 저장 중입니다..."):
            try:
                try:
                    all_cum = conn.read(spreadsheet=SHEET_URL, worksheet="누적전적", ttl=0)
                    all_h2h = conn.read(spreadsheet=SHEET_URL, worksheet="상대전적", ttl=0)
                except:
                    all_cum = pd.DataFrame(columns=['방이름', '이름', '총경기수', '승', '패', '득점', '실점'])
                    all_h2h = pd.DataFrame(
                        columns=['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

                if not all_cum.empty and '방이름' in all_cum.columns:
                    all_cum = all_cum[all_cum['방이름'] != room_name]
                if not all_h2h.empty and '방이름' in all_h2h.columns:
                    all_h2h = all_h2h[all_h2h['방이름'] != room_name]

                new_cum = pd.concat([all_cum, st.session_state.cum_df], ignore_index=True)
                new_h2h = pd.concat([all_h2h, st.session_state.h2h_df], ignore_index=True)

                conn.update(spreadsheet=SHEET_URL, worksheet="누적전적", data=new_cum)
                conn.update(spreadsheet=SHEET_URL, worksheet="상대전적", data=new_h2h)

                st.sidebar.success("✅ 클라우드 최종 저장 완료!")
            except Exception as e:
                st.sidebar.error(f"저장 실패: {e}")

    st.sidebar.divider()

    auto_refresh = st.sidebar.checkbox("자동 새로고침 켜기 (PC 전광판용)")
    if auto_refresh:
        st_autorefresh(interval=5 * 60 * 1000, limit=None, key="dashboard_refresh")
        st.sidebar.info("🟢 현재 5분마다 화면이 자동 갱신 중입니다. \n\n⚠️ 데이터 입력/수정 중에는 이 기능을 꺼주세요!")

    st.sidebar.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

    # ==========================================
    # 🌟 [수정된 부분 2] 기존의 단순한 '데이터 파일 업로드' Expander를 지우고,
    # 직접 생성 + 템플릿 다운로드 + 규격 보정 기능이 모두 포함된 새로운 Expander로 교체했습니다.
    # ==========================================
    with st.sidebar.expander("⚙️ 데이터 관리 (생성 및 업로드)", expanded=False):

        # 1. 어떤 데이터를 다룰지 선택 (선수명단 or 누적전적)
        sheet_type = st.selectbox("작업할 시트 종류", ["선수명단", "누적전적", "상대전적"], key="sheet_select")
        template_df = get_sheet_template(sheet_type)

        # 2. 직접 타이핑할지, 엑셀(CSV)을 올릴지 선택
        input_mode = st.radio("작업 방식", ["✍️ 직접 데이터 생성", "📁 CSV 파일 업로드"], key="mode_select")

        st.divider()

        # --- [모드 A] 직접 데이터 생성 ---
        if input_mode == "✍️ 직접 데이터 생성":
            with st.form(key=f"create_form_{sheet_type}"):
                input_data = {}
                # 템플릿 컬럼명에 맞춰서 입력칸을 자동으로 만들어줍니다.
                for col in template_df.columns:
                    # 🌟 [수정된 부분] '방이름' 컬럼일 경우 현재 구장 이름을 기본값으로 자동 세팅합니다.
                    if col == "방이름":
                        input_data[col] = st.text_input(f"{col} 입력", value=room_name)
                    else:
                        input_data[col] = st.text_input(f"{col} 입력")

                submit_btn = st.form_submit_button("데이터 생성 및 적용", use_container_width=True)

            if submit_btn:
                new_row_df = pd.DataFrame([input_data])
                # 메인 화면에 미리보기를 띄우기 위해 session_state에 임시 저장합니다.
                st.session_state.preview_df = new_row_df
                st.session_state.preview_msg = f"✅ 새로운 '{sheet_type}' 데이터가 생성되었습니다!"
                st.success("생성 완료! 우측 메인 화면을 확인하세요.")

        # --- [모드 B] CSV 파일 업로드 ---
        elif input_mode == "📁 CSV 파일 업로드":
            # 사용자가 헷갈리지 않게 빈 템플릿을 다운받을 수 있는 버튼
            empty_template_csv = template_df.head(0).to_csv(index=False).encode('cp949')
            st.download_button(
                label=f"📥 '{sheet_type}' 빈 템플릿 다운로드",
                data=empty_template_csv,
                file_name=f"{sheet_type}_template.csv",
                mime="text/csv",
                use_container_width=True
            )

            # 파일 업로더
            uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])

            if uploaded_file:
                try:
                    uploaded_file.seek(0)  # 에러 방지용 커서 초기화
                    raw_df = pd.read_csv(uploaded_file, encoding='cp949')

                    # 핵심: 업로드한 파일의 컬럼이 안 맞아도 강제로 규격을 맞춰줍니다.
                    final_df = align_columns_to_template(raw_df, template_df)

                    # 메인 화면에 미리보기를 띄우기 위해 임시 저장
                    st.session_state.preview_df = final_df
                    st.session_state.preview_msg = f"✅ 규격에 맞게 보정된 '{sheet_type}' 데이터입니다."

                    # 기존 코드에 있던 '명단 적용하기' 버튼의 업그레이드 버전
                    if st.button(f"'{sheet_type}' 적용하기", type="primary", use_container_width=True):
                        # 선택한 시트 종류에 따라 알맞은 변수에 덮어씌웁니다.
                        if sheet_type == "선수명단":
                            st.session_state.main_df = final_df
                        elif sheet_type == "누적전적":
                            st.session_state.cum_df = final_df
                        # 👇 이 부분이 추가되어야 상대전적 데이터가 실제 시스템에 반영됩니다.
                        elif sheet_type == "상대전적":
                            st.session_state.h2h_df = final_df

                        st.success("새로운 데이터가 적용되었습니다.")
                        time.sleep(1)
                        st.rerun()

                except pd.errors.EmptyDataError:
                    st.error("업로드한 CSV 파일이 비어있습니다.")
                except Exception as e:
                    st.error(f"파일 처리 중 에러 발생: {e}")

# ==========================================
# 🌟 [새로 추가된 부분 2] 메인 화면 데이터 미리보기
# 사이드바는 좁아서 표가 잘리므로, 사이드바 바깥(메인 화면)에 표를 그려줍니다.
# (이 코드는 사이드바 들여쓰기(if/else)가 모두 끝난 맨 아래에 위치해야 합니다)
# ==========================================
if 'preview_df' in st.session_state:
    st.subheader("👀 데이터 미리보기")
    st.info(st.session_state.preview_msg)
    st.dataframe(st.session_state.preview_df, use_container_width=True)

# ---------------------------------------------------------
# 3. 메인 화면 데이터 처리 (날짜 및 출석/조편성)
# ---------------------------------------------------------
selected_date = st.date_input("일자 선택", datetime.now(), disabled=not is_admin)

# 선택된 날짜를 '2023-10-25' 같은 문자열 형태로 변환합니다.
CURRENT_DATE = selected_date.strftime('%Y-%m-%d')

# 표(데이터프레임)에 출석을 기록할 새로운 열(컬럼) 이름을 만듭니다. (예: "출석_2023-10-25")
col_date = f"출석_{CURRENT_DATE}"

# ------------------------------------------
# 출석 기본값 세팅 (오늘 날짜 컬럼이 없으면 새로 생성)
# ------------------------------------------
if col_date not in st.session_state.main_df.columns:
    # 만약 원본 엑셀 파일에 '참석예정'이라는 열이 있다면, 그 데이터를 바탕으로 출석을 미리 체크해 줍니다.
    if '참석예정' in st.session_state.main_df.columns:
        # apply와 lambda를 사용해 데이터 정제:
        # 사람들이 엑셀에 'Y', 'O', '1', 'TRUE', '참석' 등 제각각으로 적어놔도 모두 'Y'로 통일해서 인식하게 만듭니다.
        st.session_state.main_df[col_date] = st.session_state.main_df['참석예정'].apply(
            lambda x: 'Y' if str(x).strip().upper() in ['Y', 'O', '1', 'TRUE', '참석'] else 'N'
        )
    else:
        # '참석예정' 열이 아예 없다면, 일단 모든 사람을 기본적으로 참석('Y')한다고 세팅합니다.
        st.session_state.main_df[col_date] = 'Y'

# 👇 [수정 부분 1] 여기에 "조편성_신청" 컬럼 확인 및 자동 생성 코드를 추가합니다. 👇
if '조편성_신청' not in st.session_state.main_df.columns:
    # 💡 개선 5: 함수 정의 대신 lambda를 사용하여 코드를 간결하게 만들고 속도 향상
    st.session_state.main_df['조편성_신청'] = st.session_state.main_df[col_date].apply(
        lambda x: str(random.randint(1, 4)) if x == 'Y' else ""
    )

tab_home, tab_config, tab_team, tab_match, tab_score, tab_help = st.tabs(
    [" 출석체크", " 운영 설정", " 조 편성 결과", " 경기 배정", " 스코어보드", "사용설명서"])

# 오늘 날짜 열(col_date)에서 값이 'Y'인 사람의 수를 세어 현재 참석 인원을 계산합니다.
attendees_count = (
            st.session_state.main_df[col_date] == 'Y').sum() if col_date in st.session_state.main_df.columns else 0

# ==========================================
# 탭 1: 출석체크 화면 구성
# ==========================================
with tab_home:
    responsive_text(f"📋 {CURRENT_DATE}", pc_size="20px", mobile_size="16px")

    # 원본 데이터를 건드리지 않기 위해 복사본(copy)을 만듭니다.
    df = st.session_state.main_df.copy()

    # 화면에 체크박스(☑️)로 보여주기 위해 'Y'/'N' 문자를 파이썬의 True/False(참/거짓)로 바꿉니다.
    df['참석'] = df[col_date].apply(lambda x: True if x == 'Y' else False)

    mid_idx = len(df) // 2 + (len(df) % 2)

    # 화면을 정확히 5:5 비율의 두 칸(col1, col2)으로 나눕니다.
    col1, col2 = st.columns(2)

    # st.data_editor: 엑셀처럼 화면에서 직접 데이터를 수정할 수 있게 해주는 강력한 기능입니다.
    with col1:
        edited_left = st.data_editor(df.iloc[:mid_idx][['순서', '이름', '참석', '부수']], hide_index=True,
                                     disabled=not is_admin)
    with col2:
        edited_right = st.data_editor(df.iloc[mid_idx:][['순서', '이름', '참석', '부수']], hide_index=True,
                                      disabled=not is_admin)

    # 사용자가 화면에서 체크박스를 껐다 켰다 수정한 좌/우 데이터를 다시 하나의 표로 합칩니다.
    edited_df = pd.concat([edited_left, edited_right], ignore_index=True)

    # 참석(True)으로 체크된 사람만 골라냅니다.
    current_checked = edited_df[edited_df['참석'] == True]

    # 참석자들의 이름을 가나다순으로 정렬한 뒤, 쉼표(,)로 연결하여 한 줄의 문장으로 만듭니다.
    live_names = ", ".join(sorted(current_checked['이름'].tolist()))

    st.info(f"<strong>현재 참석 ({len(current_checked)}명):</strong> \n\n {live_names}")

    if is_admin:
        # 이미 확정 버튼을 눌렀다면 버튼 이름과 색상(primary/secondary)을 바꿉니다.
        btn_label = "확정 완료 (참석자 저장됨)" if st.session_state.attendance_confirmed else "참석자 확정하기"
        btn_type = "primary" if st.session_state.attendance_confirmed else "secondary"

        # 확정 버튼을 눌렀을 때 실행되는 부분
        if st.button(btn_label, type=btn_type, use_container_width=True):
            # 화면에서 수정한 True/False 값을 다시 원본 데이터용 'Y'/'N'으로 되돌려 저장합니다.
            st.session_state.main_df[col_date] = edited_df['참석'].apply(lambda x: 'Y' if x else 'N')
            st.session_state.attendance_confirmed = True
            st.rerun()

        st.divider()
        responsive_text(f"💾 최신 명단 다운로드", pc_size="20px", mobile_size="16px")
        # 현재까지의 모든 데이터(출석 기록 포함)를 CSV 파일 형태로 변환합니다. (한글 깨짐 방지 utf-8-sig)
        csv_main = st.session_state.main_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(label="📥 최신 명단(CSV) 다운로드", data=csv_main, file_name=f"{room_name}_최신명단_{CURRENT_DATE}.csv",
                           mime="text/csv", type="primary", use_container_width=True)

# ==========================================
# 탭 2: 운영 설정
# ==========================================
with tab_config:
    # 출석체크 탭에서 계산된 총 참석 인원을 파란색 정보창으로 띄워줍니다.
    st.info(f"👥 현재 확정된 참석 인원: **{attendees_count}명** \n\n {live_names}")

    # CSS 스타일을 적용하기 위해 HTML div 태그를 엽니다.
    st.markdown('<div class="setting-banner">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5])

    with c1:
        # st.markdown(f"#### 👥 조 구성")
        responsive_text(f"👥 조 구성", pc_size="20px", mobile_size="16px")
        # 숫자 입력 위젯 (기본값 4조, 1\~20조까지 설정 가능)
        g_val = st.number_input("편성 조 수", 1, 20, 4, disabled=not is_admin)

        if g_val > 0:
            avg = attendees_count // g_val  # 몫: 한 조에 들어갈 기본 인원
            rem = attendees_count % g_val   # 나머지: 남는 인원

            # 나머지가 있으면 어떤 조는 1명이 더 많아지므로 범위를 보여주고, 딱 떨어지면 고정 인원을 보여줍니다.
            if rem > 0:
                st.info(f"👉 조당 {avg}~{avg + 1}명 배정")
            else:
                st.info(f"👉 조당 {avg}명 배정")

    with c2:
        # st.markdown("#### 🎾 경기 규칙")
        responsive_text(f"🎾 경기 규칙", pc_size="20px", mobile_size="16px")
        s_g = st.number_input("단식 게임", 0, 10, 2, disabled=not is_admin)
        d_g = st.number_input("복식 게임", 0, 5, 1, disabled=not is_admin)
        set_c = st.selectbox("개인전 선승 세트", [2, 3, 4, 5], index=1, disabled=not is_admin)

    with c3:
        # st.markdown("#### ⚙️ 환경 설정")
        responsive_text(f"⚙️ 환경 설정", pc_size="20px", mobile_size="16px")
        t_val = st.number_input("Table_No.", 1, 20, 3, disabled=not is_admin)

    with c4:
        # st.markdown("#### 🎲 방식")
        responsive_text(f"🎲 방식", pc_size="20px", mobile_size="16px")
        # 라디오 버튼으로 둘 중 하나를 선택하게 합니다.
        draw_method = st.radio("방식", ["AI 선정", "제비뽑기", "조편성_신청"], label_visibility="collapsed", disabled=not is_admin)

    with c5:
        # st.markdown("#### ✅ 실행")
        responsive_text(f"✅ 실행", pc_size="20px", mobile_size="16px")
        if is_admin:
            btn_label = "설정 확정 완료" if st.session_state.config_confirmed else "설정 확정 및 편성 시작"
            btn_type = "primary" if st.session_state.config_confirmed else "secondary"

            if st.button(btn_label, type=btn_type, use_container_width=True):
                # 위에서 설정한 모든 값들을 'config'라는 하나의 딕셔너리(보따리)에 담아 세션에 저장합니다.
                st.session_state.config = {
                    "g": g_val, "t": t_val, "s_games": s_g, "d_games": d_g, "set_count": set_c,
                    # "total_g": s_g + d_g, "draw_method": draw_method, "selected_adj": selected_adj,
                    "total_g": s_g + d_g, "draw_method": draw_method,
                    # 동점자 처리를 위해 모든 사람에게 0\~1 사이의 랜덤 숫자를 미리 부여해 둡니다.
                    "tie_breakers": {name: random.random() for name in st.session_state.main_df['이름']}
                }
                st.session_state.config_confirmed = True
                st.rerun()
        else:
            st.info("관리자 전용")

    st.markdown('</div>', unsafe_allow_html=True)  # CSS div 태그 닫기

    if "config" in st.session_state and st.session_state.config.get('draw_method') == '제비뽑기':

        # 아직 제비뽑기가 완전히 끝나지 않았다면
        if not st.session_state.get('draw_completed', False):
            st.divider()
            cfg = st.session_state.config
            # adj_col = cfg['selected_adj']
            df = st.session_state.main_df

            # 참석자 명단만 추려냅니다.
            attendees = df[df[col_date] == 'Y'].copy()
            # '1부', '2부' 같은 글자에서 숫자만 뽑아냅니다. (정렬을 위해)
            attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
            # 아까 만들어둔 랜덤 숫자를 매칭합니다.
            attendees['Random'] = attendees['이름'].map(cfg['tie_breakers'])

            # 💡 핵심: 실력이 비슷한 사람끼리 묶기 위해 부수 -> 조정부수 -> 랜덤 순으로 줄을 세웁니다.
            # sorted_members = attendees.sort_values(['부수_숫자', adj_col, 'Random'], ascending=True).reset_index(drop=True)
            sorted_members = attendees.sort_values(['부수_숫자', 'Random'], ascending=True).reset_index(drop=True)

            # 총 몇 개의 실력 그룹(레벨)이 나오는지 계산합니다. (예: 16명이고 4조면 4개의 그룹)
            total_levels = math.ceil(len(sorted_members) / cfg['g'])

            # 현재 몇 번째 그룹(레벨)의 제비뽑기를 진행 중인지 추적합니다. (처음엔 0)
            draw_level = st.session_state.get('draw_level', 0)

            # st.markdown("### 제비뽑기 진행 현황")
            responsive_text(f"📋 제비뽑기 진행 현황", pc_size="20px", mobile_size="16px")

            # 각 실력 그룹(레벨)별로 반복문을 돌며 화면을 그립니다.
            for level in range(total_levels):
                # 현재 그룹에 속할 사람들의 시작 번호와 끝 번호를 계산하여 잘라냅니다.
                start_idx = level * cfg['g']
                end_idx = min((level + 1) * cfg['g'], len(sorted_members))
                current_group = sorted_members.iloc[start_idx:end_idx]
                group_members = current_group['이름'].tolist()

                # st.markdown(f"#### 그룹 {level + 1}")
                responsive_text(f"📋 그룹 {level + 1}", pc_size="20px", mobile_size="16px")
                cols = st.columns(cfg['g'])  # 조 개수만큼 화면을 가로로 나눕니다.

                # [상태 1] 이미 제비뽑기가 끝난 과거의 그룹들
                if level < draw_level:
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        with cols[i % cfg['g']]:
                            # 배정된 조를 가져와서 초록색 성공 창으로 보여줍니다.
                            assigned_team = st.session_state.draw_results.get(row['이름'], "-")
                            st.success(f" <strong>{row['이름']}</strong> ➔ **{assigned_team}조**")

                # [상태 2] 현재 제비뽑기를 진행 중인 그룹 (가장 중요!)
                elif level == draw_level:
                    available_options = list(range(1, cfg['g'] + 1))
                    state_key = f"group_selections_{level}"

                    # 처음 화면이 열렸을 때, 1번 사람에게 1조, 2번 사람에게 2조를 임시로 쥐여줍니다.
                    if state_key not in st.session_state:
                        st.session_state[state_key] = {name: available_options[i] for i, name in
                                                       enumerate(group_members)}
                        st.session_state[f"{state_key}_prev"] = st.session_state[state_key].copy()

                    # 💡 중복 선택 방지 콜백 함수 (누군가 조를 바꾸면, 원래 그 조를 갖고 있던 사람과 맞바꿈)
                    def on_selection_change(changed_member, lvl):
                        s_key = f"group_selections_{lvl}"
                        prev_selections = st.session_state[f"{s_key}_prev"]
                        current_selections = st.session_state[s_key]
                        new_val = st.session_state[f"select_{lvl}_{changed_member}"]
                        old_val = prev_selections[changed_member]

                        if new_val != old_val:
                            # 다른 사람 중에 내가 방금 선택한 조를 가지고 있는 사람을 찾아서
                            for other_member, val in prev_selections.items():
                                if other_member != changed_member and val == new_val:
                                    # 그 사람에게 내 옛날 조를 줘버립니다. (서로 맞교환)
                                    st.session_state[f"select_{lvl}_{other_member}"] = old_val
                                    current_selections[other_member] = old_val
                                    break
                            current_selections[changed_member] = new_val
                            st.session_state[f"{s_key}_prev"] = current_selections.copy()

                    # 현재 그룹 사람들의 드롭다운(선택창)을 그립니다.
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        name = row['이름']
                        with cols[i % cfg['g']]:
                            st.markdown(f" **{name}**")
                            current_val = st.session_state[state_key][name]
                            # on_change 옵션을 통해 값을 바꿀 때마다 위의 맞교환 함수가 실행되게 합니다.
                            st.selectbox("조 선택", options=available_options, index=available_options.index(current_val),
                                         key=f"select_{level}_{name}", on_change=on_selection_change,
                                         args=(name, level), label_visibility="collapsed", disabled=not is_admin)
                    st.write("")

                    # 관리자용 진행 버튼
                    if is_admin:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            # 버튼 1: 컴퓨터가 알아서 현재 그룹을 랜덤으로 섞어버림
                            if st.button(f" 그룹 {level + 1} 랜덤 배정"):
                                shuffled_options = available_options[:len(group_members)]
                                random.shuffle(shuffled_options)
                                for i, name in enumerate(group_members):
                                    st.session_state.draw_results[name] = shuffled_options[i]
                                st.session_state.draw_level += 1
                                st.rerun()
                        with btn_col2:
                            # 버튼 2: 화면에 선택된 그대로 확정하고 넘어감
                            if st.button(f" 그룹 {level + 1} 제비뽑기 완료 및 다음 진행", type="primary", width="stretch"):
                                for name in group_members:
                                    st.session_state.draw_results[name] = st.session_state[f"select_{level}_{name}"]
                                st.session_state.draw_level += 1  # 다음 그룹으로 넘어감
                                st.rerun()

                # [상태 3] 아직 차례가 오지 않은 미래의 대기 그룹들
                else:
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        with cols[i % cfg['g']]:
                            # 회색 점선 박스로 대기 중임을 표시합니다.
                            st.markdown(
                                f"<div style='color:#999; padding:10px; border:1px dashed #ccc; border-radius:5px;'> {row['이름']} ({row['부수']}) - 대기중</div>",
                                unsafe_allow_html=True)
                st.divider()

            # 모든 그룹의 뽑기가 끝났다면 완료 플래그를 켭니다.
            if draw_level >= total_levels:
                st.session_state.draw_completed = True
                st.rerun()

        # 제비뽑기가 모두 완료된 후 보여지는 화면
        else:
            st.divider()
            st.success(" 제비뽑기가 모두 완료되었습니다! 상단의 **'조 편성 결과'** 탭으로 이동하여 결과를 확인해주세요.")

            # 다시 하기 버튼 (모든 제비뽑기 관련 세션 데이터를 초기화함)
            if is_admin and st.button(" 제비뽑기 다시 하기", type="secondary"):
                st.session_state.draw_level = 0
                st.session_state.draw_results = {}
                st.session_state.draw_completed = False
                for key in list(st.session_state.keys()):
                    if key.startswith("group_selections_") or key.startswith("select_"):
                        del st.session_state[key]
                st.rerun()

# ==========================================
# 탭 3: 조 편성 결과
# ==========================================
with tab_team:
    if "config" not in st.session_state:
        st.warning("먼저 '운영 설정'을 완료해주세요.")
    else:
        st.info(f"👥 현재 확정된 참석 인원: **{attendees_count}명**")
        cfg = st.session_state.config
        df = st.session_state.main_df
        attendees = df[df[col_date] == 'Y'].copy()
        attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
        sorted_members = attendees.sort_values(['부수_숫자'], ascending=True).reset_index(drop=True)

        teams = {i: [] for i in range(1, cfg['g'] + 1)}
        team_stats = {i: {"sum": 0.0, "count": 0} for i in range(1, cfg['g'] + 1)}
        all_member_names = []

        # AI 선정 방식: ㄹ자(스네이크) 방식으로 실력 분배
        if cfg.get('draw_method', 'AI 선정') == 'AI 선정':
            for idx, row in sorted_members.iterrows():
                r_idx = idx // cfg['g']
                pos_idx = idx % cfg['g']
                # 짝수 줄은 정방향(1->2->3), 홀수 줄은 역방향(3->2->1) 배정
                t_idx = (pos_idx + 1) if r_idx % 2 == 0 else (cfg['g'] - pos_idx)
                teams[t_idx].append(f"{row['이름']}({row['부수']})")
                all_member_names.append(row['이름'])
                team_stats[t_idx]["sum"] += row['부수_숫자']
                team_stats[t_idx]["count"] += 1

        # 👇 [수정 부분 2] "조편성_신청" 방식 로직 추가 👇
        elif cfg.get('draw_method') == '조편성_신청':
            # 1. 빈칸이나 결측치(NaN)를 '미지정'으로 처리하고, 양옆 공백을 제거하여 대소문자 무관하게 통일
            attendees['조편성_신청'] = attendees['조편성_신청'].fillna('미지정').astype(str).str.strip().str.upper()

            # 2. 입력된 고유한 팀/조 이름들을 추출
            unique_groups = attendees['조편성_신청'].unique()
            group_to_team_map = {g_name: (i % cfg['g']) + 1 for i, g_name in enumerate(unique_groups)}

            for idx, row in attendees.iterrows():
                t_idx = group_to_team_map[row['조편성_신청']]
                teams[t_idx].append(f"{row['이름']}({row['부수']})")
                all_member_names.append(row['이름'])
                team_stats[t_idx]["sum"] += row['부수_숫자']
                team_stats[t_idx]["count"] += 1
        # 👆 -------------------------------------------------------- 👆

        # 제비뽑기 방식: 저장된 결과대로 배정
        else:
            for idx, row in sorted_members.iterrows():
                t_idx = st.session_state.draw_results.get(row['이름'], 1)
                teams[t_idx].append(f"{row['이름']}({row['부수']})")
                all_member_names.append(row['이름'])
                team_stats[t_idx]["sum"] += row['부수_숫자']
                team_stats[t_idx]["count"] += 1

        # 조당 평균 인원이 1.5명 이하이면 '개인전'으로 간주
        avg_p = sum(t["count"] for t in team_stats.values()) / cfg['g'] if cfg['g'] > 0 else 0
        st.session_state.config['is_individual'] = True if avg_p <= 1.5 else False
        st.session_state.labels = [f"{i}조({teams[i][0].split('(')[0]})" for i in range(1, cfg['g'] + 1) if teams[i]]
        st.session_state.teams = teams

        # st.markdown("### 조별 최종 구성 및 부수 합계")
        responsive_text(f"📋 조별 최종 구성 및 부수 합계", pc_size="20px", mobile_size="16px")
        valid_teams = [t_num for t_num in range(1, cfg['g'] + 1) if teams[t_num]]
        num_cols = min(len(valid_teams), 5)

        # 편성된 조를 카드 형태로 화면에 출력
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

        # 점수 기록을 위한 매트릭스(표) 초기화
        if st.session_state.get('matrix') is None:
            st.session_state.matrix = pd.DataFrame(0.0, index=st.session_state.labels, columns=st.session_state.labels)
            for l in st.session_state.labels: st.session_state.matrix.loc[l, l] = np.nan

        if st.session_state.get('ind_matrix') is None:
            all_member_names = sorted(list(set(all_member_names)))
            st.session_state.ind_matrix = pd.DataFrame(0.0, index=all_member_names, columns=all_member_names)
            for m in all_member_names: st.session_state.ind_matrix.loc[m, m] = np.nan

# ==========================================
# 탭 4: 경기 배정 및 점수 입력
# ==========================================
with tab_match:
    # 조 편성이 완료되어 세션에 'labels'(조 이름 목록)와 'matrix'(점수판)가 존재할 때만 실행
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:

        def get_matches(teams):
            t_list = list(teams)
            # 팀이 홀수면 짝을 맞추기 위해 가상의 '부전승(None)' 팀을 추가합니다.
            if len(t_list) % 2: t_list.append(None)
            res = []
            # 총 라운드 수는 (팀 수 - 1) 입니다.
            for _ in range(len(t_list) - 1):
                # 리스트의 양 끝에서부터 안쪽으로 짝을 지어줍니다. (예: 1번-6번, 2번-5번, 3번-4번)
                for j in range(len(t_list) // 2):
                    if t_list[j] and t_list[-1 - j]:  # 부전승(None)이 포함된 경기는 제외
                        res.append((t_list[j], t_list[-1 - j]))
                # 💡 핵심: 첫 번째 팀은 가만히 두고, 나머지 팀들만 시계 방향으로 한 칸씩 회전시킵니다.
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            return res


        all_matches = get_matches(st.session_state.labels)

        # 설정값(config) 불러오기
        cfg = st.session_state.config
        t_count = cfg['t']  # 탁구대 개수
        s_games = cfg.get('s_games', 0)  # 단식 경기 수
        d_games = cfg.get('d_games', 0)  # 복식 경기 수
        is_ind = cfg.get('is_individual', False)  # 개인전 여부
        # 개인전이면 세트 수(예: 3판 2선승), 단체전이면 총 경기 수(단식+복식)를 최대 점수로 설정
        limit = cfg.get('set_count', 3) if is_ind else cfg.get('total_g', 5)
        match_info = "개인전" if is_ind else f"단식 {s_games} / 복식 {d_games}"

        m_data = []
        for i, (a, b) in enumerate(all_matches):
            s1, s2 = 0, 0
            # 점수판(matrix)에 이미 입력된 점수가 있는지 확인
            if a in st.session_state.matrix.index and b in st.session_state.matrix.columns:
                s1, s2 = st.session_state.matrix.loc[a, b], st.session_state.matrix.loc[b, a]

            # 점수가 1점이라도 입력되어 있으면 '종료', 아니면 '대기' 상태로 표시
            status = " 종료" if (not np.isnan(s1) and (s1 + s2 > 0)) else " 대기"

            m_data.append({
                "순서": i + 1,
                "Table_No": f"{(i % t_count) + 1}번 대",  # 탁구대 번호를 순서대로 배정 (1번->2번->3번->1번...)
                "상태": status,
                "대진": f"{a} VS {b}",
                "경기 구성": match_info,
                "결과": f"{int(s1)} : {int(s2)}" if status == " 종료" else "-"
            })

        df_match = pd.DataFrame(m_data)

        # 종료된 경기는 표에서 회색으로 흐리게 보이도록 만드는 스타일 함수
        def highlight_finished(row):
            if row['상태'] == ' 종료': return ['background-color: rgba(128, 128, 128, 0.15); color: gray;'] * len(row)
            return [''] * len(row)

        # 대진표가 길어질 수 있으므로 좌/우 두 개의 표로 나눕니다.
        mid_idx = (len(df_match) + 1) // 2
        df_left = df_match.iloc[:mid_idx].reset_index(drop=True)
        df_right = df_match.iloc[mid_idx:].reset_index(drop=True)

        col_title, col_info = st.columns([3, 7])
        with col_title:
            # st.markdown("### 경기 배정표")
            responsive_text(f"📋 경기 배정표", pc_size="20px", mobile_size="16px")
        with col_info:
            st.info(" **아래 표에서 결과를 입력할 경기의 행(Row)을 클릭**하면 상세 입력창이 나타납니다.")

        col1, col2 = st.columns(2)
        with col1:
            # on_select="rerun": 표의 특정 줄을 클릭하면 화면이 새로고침되면서 클릭한 정보를 가져옵니다.
            event_left = st.dataframe(df_left.style.apply(highlight_finished, axis=1), width="stretch", hide_index=True,
                                      on_select="rerun", selection_mode="single-row")
        with col2:
            event_right = st.dataframe(df_right.style.apply(highlight_finished, axis=1), width="stretch",
                                       hide_index=True, on_select="rerun",
                                       selection_mode="single-row") if not df_right.empty else None

        # 사용자가 왼쪽 표를 클릭했는지, 오른쪽 표를 클릭했는지 파악하여 해당 경기의 인덱스(번호)를 찾습니다.
        selected_match_idx = None
        if event_left and event_left.selection.rows:
            selected_match_idx = event_left.selection.rows[0]
        elif event_right and event_right.selection.rows:
            selected_match_idx = event_right.selection.rows[0] + mid_idx

        if selected_match_idx is not None:
            team_a, team_b = all_matches[selected_match_idx]
            st.divider()
            # st.markdown(f"### 🎯 {team_a} VS {team_b} 상세 결과 입력")
            responsive_text(f"🎯 {team_a} VS {team_b} 상세 결과 입력", pc_size="20px", mobile_size="16px")

            if not is_admin:
                st.warning("🔒 점수 입력은 관리자만 가능합니다. 사이드바에서 관리자 비밀번호를 입력해주세요.")
            else:
                # [A] 개인전일 경우의 점수 입력 UI (간단함)
                if is_ind:
                    m_idx = selected_match_idx
                    c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 2.5, 1.5, 1.5])
                    with c1:
                        st.markdown(
                            f"<div style='font-size:1.2rem; font-weight:bold; text-align:center;'>{team_a}</div>",
                            unsafe_allow_html=True)
                    with c2:
                        # 승/패 선택 라디오 버튼
                        res_type = st.radio(f"{team_a} 결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_ind_res",
                                            label_visibility="collapsed")
                    with c3:
                        # 승리 시(3:0, 3:1, 3:2) / 패배 시(0:3, 1:3, 2:3) 선택지를 다르게 보여줌
                        win_scores = [f"{limit}:{i}" for i in range(limit)]
                        lose_scores = [f"{i}:{limit}" for i in range(limit)]
                        display_scores = win_scores if res_type == "승" else lose_scores
                        selected_score = st.radio("스코어 선택", display_scores, horizontal=True, key=f"m{m_idx}_ind_score",
                                                  label_visibility="collapsed")
                    with c4:
                        st.markdown(
                            f"<div style='font-size:1.2rem; font-weight:bold; text-align:center;'>{team_b}</div>",
                            unsafe_allow_html=True)

                    with c5:
                        if st.button("결과 저장", type="primary", key=f"btn_save_ind_match_{m_idx}",
                                     use_container_width=True):
                            s_a, s_b = map(int, selected_score.split(':'))
                            # 점수판(matrix)에 점수 기록
                            st.session_state.matrix.loc[team_a, team_b] = s_a
                            st.session_state.matrix.loc[team_b, team_a] = s_b

                            # 누적 전적 업데이트를 위해 이름만 추출 (예: "1조(홍길동)" -> "홍길동")
                            p_a_name = team_a.split('(')[0].split('조')[-1].strip() if '조' in team_a else team_a
                            p_b_name = team_b.split('(')[0].split('조')[-1].strip() if '조' in team_b else team_b
                            update_cumulative_record(p_a_name, p_b_name, s_a, s_b)
                            st.success("저장 완료! 스코어보드에 반영되었습니다.")
                            st.rerun()

                # [B] 단체전(조별 리그)일 경우의 점수 입력 UI (단식/복식 각각 입력)
                else:
                    # 해당 조에 속한 선수 명단을 가져오는 함수
                    def get_team_players(team_str):
                        match = re.search(r'(\d+)조', str(team_str))
                        if match and 'teams' in st.session_state:
                            t_idx = int(match.group(1))
                            if t_idx in st.session_state.teams:
                                return [p.split('(')[0] for p in st.session_state.teams[t_idx]]
                        return list(st.session_state.ind_matrix.index)


                    team_a_players = get_team_players(team_a)
                    team_b_players = get_team_players(team_b)
                    m_idx = selected_match_idx

                    a_keys = [f"m{m_idx}_s_pa_{s}" for s in range(s_games)] + [f"m{m_idx}_d_pa1_{d}" for d in
                                                                               range(d_games)] + [f"m{m_idx}_d_pa2_{d}"
                                                                                                  for d in
                                                                                                  range(d_games)]
                    b_keys = [f"m{m_idx}_s_pb_{s}" for s in range(s_games)] + [f"m{m_idx}_d_pb1_{d}" for d in
                                                                               range(d_games)] + [f"m{m_idx}_d_pb2_{d}"
                                                                                                  for d in
                                                                                                  range(d_games)]

                    # 💡 이미 다른 경기(단식/복식)에 선택된 선수는 드롭다운 목록에서 빼버리는 함수
                    def get_avail(players, current_key, all_keys):
                        selected = [st.session_state[k] for k in all_keys if
                                    k in st.session_state and k != current_key and st.session_state[k] != "선택안함"]
                        return ["선택안함"] + [p for p in players if p not in selected]


                    match_results = []
                    set_limit = 3  # 단체전 내의 개별 경기는 보통 3판 2선승
                    set_win_scores = [f"{set_limit}:{i}" for i in range(set_limit)]
                    set_lose_scores = [f"{i}:{set_limit}" for i in range(set_limit)]

                    # 단식 입력창 생성
                    if s_games > 0:
                        # st.markdown("##### 👤 단식 경기")
                        responsive_text(f"👤 단식 경기", pc_size="20px", mobile_size="16px")
                        for s in range(s_games):
                            c1, c2, c3, c4, c5 = st.columns([1, 2, 1.5, 2.5, 2])
                            with c1: st.markdown(f"<div style='font-weight:bold; color:#1f77b4;'>단식 {s + 1}</div>",
                                                 unsafe_allow_html=True)
                            with c2:
                                k_a = f"m{m_idx}_s_pa_{s}"
                                # get_avail 함수를 써서 남은 선수만 선택할 수 있게 함
                                p_a = st.selectbox(f"{team_a} 선수", get_avail(team_a_players, k_a, a_keys), key=k_a,
                                                   label_visibility="collapsed")
                            with c3:
                                res_type = st.radio("결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_s_res_{s}",
                                                    label_visibility="collapsed")
                            with c4:
                                display_scores = set_win_scores if res_type == "승" else set_lose_scores
                                selected_score = st.radio("스코어", display_scores, horizontal=True,
                                                          key=f"m{m_idx}_s_score_{s}", label_visibility="collapsed")
                            with c5:
                                k_b = f"m{m_idx}_s_pb_{s}"
                                p_b = st.selectbox(f"{team_b} 선수", get_avail(team_b_players, k_b, b_keys), key=k_b,
                                                   label_visibility="collapsed")

                            s_a, s_b = map(int, selected_score.split(':'))
                            match_results.append(("S", p_a, s_a, s_b, p_b))

                    # 복식 입력창 생성 (단식과 원리는 같으나 선수를 2명씩 고름)
                    if d_games > 0:
                        # st.markdown("##### 👥 복식 경기")
                        responsive_text(f"👥 복식 경기", pc_size="20px", mobile_size="16px")
                        for d in range(d_games):
                            c1, c2, c3, c4, c5 = st.columns([1, 2.5, 1.5, 2.5, 2.5])
                            with c1: st.markdown(f"<div style='font-weight:bold; color:#ff7f0e;'>복식 {d + 1}</div>",
                                                 unsafe_allow_html=True)
                            with c2:
                                k_a1, k_a2 = f"m{m_idx}_d_pa1_{d}", f"m{m_idx}_d_pa2_{d}"
                                p_a1 = st.selectbox(f"{team_a} 선수1", get_avail(team_a_players, k_a1, a_keys), key=k_a1,
                                                    label_visibility="collapsed")
                                p_a2 = st.selectbox(f"{team_a} 선수2", get_avail(team_a_players, k_a2, a_keys), key=k_a2,
                                                    label_visibility="collapsed")
                            with c3:
                                res_type = st.radio("결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_d_res_{d}",
                                                    label_visibility="collapsed")
                            with c4:
                                display_scores = set_win_scores if res_type == "승" else set_lose_scores
                                selected_score = st.radio("스코어", display_scores, horizontal=True,
                                                          key=f"m{m_idx}_d_score_{d}", label_visibility="collapsed")
                            with c5:
                                k_b1, k_b2 = f"m{m_idx}_d_pb1_{d}", f"m{m_idx}_d_pb2_{d}"
                                p_b1 = st.selectbox(f"{team_b} 선수1", get_avail(team_b_players, k_b1, b_keys), key=k_b1,
                                                    label_visibility="collapsed")
                                p_b2 = st.selectbox(f"{team_b} 선수2", get_avail(team_b_players, k_b2, b_keys), key=k_b2,
                                                    label_visibility="collapsed")
                            s_a, s_b = map(int, selected_score.split(':'))
                            match_results.append(("D", (p_a1, p_a2), s_a, s_b, (p_b1, p_b2)))

                    st.write("")

                    # 단체전 결과 종합 저장 버튼
                    if st.button("💾 상세 결과 저장 및 스코어보드 반영", type="primary", use_container_width=True,
                                 key=f"btn_save_match_{m_idx}"):
                        team_a_wins = 0
                        team_b_wins = 0

                        # 위에서 임시 저장한 단식/복식 결과들을 하나씩 꺼내서 처리
                        for res in match_results:
                            m_type = res[0]
                            if m_type == "S":  # 단식일 때
                                _, p_a, s_a, s_b, p_b = res
                                if p_a != "선택안함" and p_b != "선택안함" and p_a != p_b:
                                    # 개인 간의 전적(ind_matrix)에 점수 기록
                                    st.session_state.ind_matrix.loc[p_a, p_b] = s_a
                                    st.session_state.ind_matrix.loc[p_b, p_a] = s_b
                                    update_cumulative_record(p_a, p_b, s_a, s_b)
                                if s_a > s_b:
                                    team_a_wins += 1
                                elif s_b > s_a:
                                    team_b_wins += 1

                            elif m_type == "D":  # 복식일 때
                                _, (p_a1, p_a2), s_a, s_b, (p_b1, p_b2) = res
                                # 복식은 개인 전적에는 넣지 않고 팀 승수만 올림
                                if s_a > s_b:
                                    team_a_wins += 1
                                elif s_b > s_a:
                                    team_b_wins += 1

                        # 조별 매트릭스(matrix)에 최종 팀 승수(예: 3승 2패) 기록
                        st.session_state.matrix.loc[team_a, team_b] = team_a_wins
                        st.session_state.matrix.loc[team_b, team_a] = team_b_wins
                        st.success(f"저장 완료! {team_a} ({team_a_wins}) : ({team_b_wins}) {team_b} 결과가 스코어보드에 반영되었습니다.")
                        st.rerun()
    else:
        st.info("조 편성이 완료되면 경기 배정표가 나타납니다.")

# ==========================================
# 탭 5: 스코어보드
# ==========================================
with tab_score:
    # 조 편성이 완료되어 세션에 'labels'(조 이름)와 'matrix'(점수판)가 있을 때만 실행
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:
        cfg = st.session_state.config
        is_ind = cfg.get('is_individual', False)  # 개인전인지 단체전인지 확인

        if 'table_font_size' not in st.session_state:
            num_rows = len(st.session_state.labels)
            st.session_state.table_font_size = 20 if num_rows <= 4 else (
                16 if num_rows <= 6 else (13 if num_rows <= 8 else 11))

        # 전체 화면 모드 여부를 기억하는 변수 (기본값: False)
        if 'fullscreen_table' not in st.session_state:
            st.session_state.fullscreen_table = False


        def draw_summary_table():
            m = st.session_state.matrix  # 현재 점수판 가져오기
            rank = pd.DataFrame(index=st.session_state.labels)  # 순위를 기록할 새로운 표 생성

            # 💡 판다스 행렬 계산의 마법: m(내 점수)과 m.T(상대 점수, 전치행렬)를 비교하여 승/패를 한 번에 계산합니다.
            rank['승'] = (m > m.T).sum(axis=1)
            rank['패'] = (m < m.T).sum(axis=1)
            # 가로줄(axis=1)을 더하면 내가 얻은 총 득점, 세로줄(axis=0)을 더하면 내가 잃은 총 실점입니다.
            rank['득점'] = m.sum(axis=1, skipna=True).astype(int)
            rank['실점'] = m.sum(axis=0, skipna=True).astype(int)
            rank['득실차'] = rank['득점'] - rank['실점']

            # 원래 점수판(m) 옆에 방금 계산한 승, 패, 득점, 실점, 득실차 열을 이어 붙입니다.
            combined_df = pd.concat([m, rank[['승', '패', '득점', '실점', '득실차']]], axis=1)

            # 1순위: 승수가 많은 순, 2순위: 득실차가 높은 순으로 표를 정렬(순위 매기기)합니다.
            combined_df = combined_df.sort_values(['승', '득실차'], ascending=False)

            # 현재 설정된 글자 크기에 맞춰 표의 행 높이(ROW_HEIGHT)를 계산합니다.
            current_fs = st.session_state.table_font_size
            ROW_HEIGHT = f"{current_fs + 25}px"

            # Pandas Styler를 이용해 표의 디자인(가운데 정렬, 높이 등)을 세밀하게 설정합니다.
            styled_df = combined_df.style.format(precision=0, na_rep='-').set_properties(**{
                'text-align': 'center', 'vertical-align': 'middle', 'height': ROW_HEIGHT,
            }).set_table_styles([{'selector': 'th', 'props': [('text-align', 'center'), ('vertical-align', 'middle'),
                                                              ('height', ROW_HEIGHT)]}])

            # 💡 Streamlit 기본 표 대신, HTML과 CSS를 직접 주입하여 '진짜 전광판'처럼 꽉 차게 만듭니다.
            raw_html = styled_df.to_html().replace('\n', '')
            css = f"""
            <style>
            .custom-table-wrapper table {{ width: 100% !important; table-layout: fixed !important; font-size: {current_fs}px !important; }}
            .custom-table-wrapper th, .custom-table-wrapper td {{ white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; padding: 2px 4px !important; }}
            .custom-table-wrapper th:nth-last-child(-n+5), .custom-table-wrapper td:nth-last-child(-n+5) {{ width: 70px !important; }}
            .custom-table-wrapper th:first-child {{ width: {current_fs * 6}px !important; }}
            </style>
            """
            st.markdown(css + '<div class="custom-table-wrapper">' + raw_html + '</div>', unsafe_allow_html=True)


        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([4, 2, 2, 2])

        with col_ctrl1:  # 전체 화면 전환 버튼
            if not st.session_state.get('fullscreen_table', False):
                if st.button("📺 전체 화면 모드", type="primary"):
                    st.session_state.fullscreen_table = True
                    st.rerun()
            else:
                if st.button("🔙 이전 화면으로", type="primary"):
                    st.session_state.fullscreen_table = False
                    st.rerun()

        with col_ctrl2:  # 글자 크기 조절 버튼 (+ / -)
            f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1])
            with f_col1:
                if st.button("➖", help="글자 축소"):
                    st.session_state.table_font_size = max(8, st.session_state.table_font_size - 1);
                    st.rerun()
            with f_col2:
                st.markdown(
                    f"<div style='text-align:center; padding-top:5px;'><b>크기: {st.session_state.table_font_size}</b></div>",
                    unsafe_allow_html=True)
            with f_col3:
                if st.button("➕", help="글자 확대"):
                    st.session_state.table_font_size = min(30, st.session_state.table_font_size + 1);
                    st.rerun()

        with col_ctrl3:  # 누적 결과 다운로드
            if 'cum_df' in st.session_state and not st.session_state.cum_df.empty:
                csv_bytes = st.session_state.cum_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 누적 결과 다운로드", data=csv_bytes, file_name=f"{room_name}_누적결과.csv",
                                   mime="text/csv", type="primary", use_container_width=True)

        with col_ctrl4:  # 상대 전적 다운로드
            if 'h2h_df' in st.session_state and not st.session_state.h2h_df.empty:
                h2h_bytes = st.session_state.h2h_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 상대전적 다운로드", data=h2h_bytes, file_name=f"{room_name}_상대전적.csv",
                                   mime="text/csv", type="secondary", use_container_width=True)

        is_fullscreen = st.session_state.get('fullscreen_table', False)

        if is_fullscreen:
            responsive_text(f"📋 종합 결과표 (전체 화면 모드)", pc_size="20px", mobile_size="16px")
            draw_summary_table()
        else:
            responsive_text(f"📋 {'조별' if not is_ind else '개인전'} 경기 결과 수동 입력", pc_size="20px", mobile_size="16px")

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
                        # 💡 이미 경기가 끝난 상대방 이름 옆에는 '(완료)'라는 글자를 붙여주는 함수
                        def format_team_b(team_b_name):
                            s_a_val = st.session_state.matrix.loc[team_a, team_b_name]
                            s_b_val = st.session_state.matrix.loc[team_b_name, team_a]
                            if not np.isnan(s_a_val) and (s_a_val + s_b_val > 0): return f"{team_b_name} (완료)"
                            return team_b_name


                        team_b = st.selectbox("상대 조/선수 (B)", [l for l in labels if l != team_a],
                                              format_func=format_team_b, key="sb_team_b")

                    if team_a and team_b:
                        # 선택한 두 팀의 점수를 확인하여 경기가 끝났는지(is_completed) 판별
                        s_a_val = st.session_state.matrix.loc[team_a, team_b]
                        s_b_val = st.session_state.matrix.loc[team_b, team_a]
                        is_completed = not np.isnan(s_a_val) and (s_a_val + s_b_val > 0)

                        if is_completed: st.warning(f"⚠️ {team_a} vs {team_b} 경기는 이미 결과가 입력되었습니다.")

                        with c3:
                            # disabled=is_completed: 이미 끝난 경기면 라디오 버튼을 회색으로 비활성화하여 수정을 막음
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
                            if st.button(" 저장", type="primary", use_container_width=True, key="btn_save_team",
                                         disabled=is_completed):
                                s_a, s_b = map(int, selected_score.split(':'))
                                st.session_state.matrix.loc[team_a, team_b] = s_a
                                st.session_state.matrix.loc[team_b, team_a] = s_b
                                p_a_name = team_a.split('(')[0].split('조')[-1].strip() if '조' in team_a else team_a
                                p_b_name = team_b.split('(')[0].split('조')[-1].strip() if '조' in team_b else team_b
                                update_cumulative_record(p_a_name, p_b_name, s_a, s_b)
                                st.success(f"저장 완료! {team_a} {s_a} : {s_b} {team_b} 결과가 스코어보드에 반영되었습니다.")
                                st.rerun()

            st.divider()
            # st.markdown(f"### {'조별 리그' if not is_ind else '개인전'} 종합 결과표")
            responsive_text(f"📋 {'조별 리그' if not is_ind else '개인전'} 종합 결과표", pc_size="20px", mobile_size="16px")
            draw_summary_table()  # 위에서 만든 표 그리기 함수 호출

            if not is_ind:
                st.divider()
                # st.markdown("### 개인 성적 관리 및 단식 결과 수동 입력")
                responsive_text(f"📋 개인 성적 관리 및 단식 결과 수동 입력", pc_size="20px", mobile_size="16px")
                responsive_text(f"📋 개인 성적표 (매트릭스)", pc_size="20px", mobile_size="16px")
                st.info(" **아래 표에서 특정 선수의 행(Row)을 클릭**하면 오늘 진행된 상세 세트 전적을 확인할 수 있습니다.")

                # 💡 관리자와 일반 유저의 권한 분리 (핵심 UX)
                if is_admin:
                    # 관리자는 st.data_editor를 통해 엑셀처럼 표의 숫자를 직접 더블클릭해서 수정할 수 있습니다.
                    edited_ind_matrix = st.data_editor(st.session_state.ind_matrix, width="stretch", height=400,
                                                       hide_index=False, key="ind_matrix_editor")
                    if not edited_ind_matrix.equals(st.session_state.ind_matrix):
                        st.session_state.ind_matrix = edited_ind_matrix
                        st.rerun()
                else:
                    # 일반 유저는 수정은 불가능하고(st.dataframe), 대신 표의 특정 줄을 클릭(on_select)할 수 있습니다.
                    event_matrix = st.dataframe(st.session_state.ind_matrix.style.format(precision=0, na_rep='-'),
                                                width="stretch", height=400, on_select="rerun",
                                                selection_mode="single-row", key="ind_matrix_select")

                    # 유저가 특정 선수를 클릭했다면, 그 선수의 오늘 모든 경기 결과를 문장으로 풀어서 보여줍니다.
                    if event_matrix and event_matrix.selection.rows:
                        selected_idx = event_matrix.selection.rows[0]
                        selected_player = st.session_state.ind_matrix.index[selected_idx]
                        # st.markdown(f"##### [{selected_player}] 오늘 상세 세트 전적")
                        responsive_text(f"📋 [{selected_player}] 오늘 상세 세트 전적", pc_size="20px", mobile_size="16px")
                        history = []
                        for opp in st.session_state.ind_matrix.columns:
                            if selected_player == opp: continue
                            s_a = st.session_state.ind_matrix.loc[selected_player, opp]
                            s_b = st.session_state.ind_matrix.loc[opp, selected_player]
                            if not np.isnan(s_a) and not np.isnan(s_b) and (s_a + s_b > 0):
                                res_str = "승리 " if s_a > s_b else ("패배 " if s_a < s_b else "무승부 ")
                                history.append(f"- vs **{opp}** : {int(s_a)} 대 {int(s_b)} ({res_str})")
                        if history:
                            for h in history: st.markdown(h)
                        else:
                            st.info("아직 진행된 경기가 없습니다.")

                st.divider()

                # 💡 [적용 포인트 4: @st.fragment]
                # 선수 1, 선수 2를 선택할 때마다 전체 화면이 재실행되는 것을 막기 위해
                # 해당 검색 영역만 독립적으로 동작하는 fragment 함수로 분리했습니다.
                @st.fragment
                def head_to_head_search_ui():
                    responsive_text(f"🔍 역대 누적 상대 전적 검색", pc_size="20px", mobile_size="16px")
                    players_list = list(st.session_state.ind_matrix.index)
                    if len(players_list) >= 2:
                        col_s1, col_s2, col_btn = st.columns([3, 3, 2])
                        with col_s1:
                            search_p1 = st.selectbox("선수 1 선택", players_list, key="search_p1")
                        with col_s2:
                            search_p2 = st.selectbox("선수 2 선택", [p for p in players_list if p != search_p1],
                                                     key="search_p2")
                        with col_btn:
                            if st.button("📊 전적 창 열기", type="primary", use_container_width=True):
                                show_h2h_dialog(search_p1, search_p2)


                # 분리한 fragment 함수 실행
                head_to_head_search_ui()

                st.divider()

                im = st.session_state.ind_matrix
                ind_rank = pd.DataFrame(index=im.index)
                ind_rank['개인승'] = (im > im.T).sum(axis=1)  # 승수 계산
                ind_rank['개인패'] = (im < im.T).sum(axis=1)  # 패수 계산
                ind_rank['세트득실'] = im.sum(axis=1, skipna=True) - im.sum(axis=0, skipna=True)  # 득실차 계산
                # st.markdown("#### 개인별 순위 (세트 기준)")
                responsive_text(f"📋 개인별 순위 (세트 기준)", pc_size="20px", mobile_size="16px")
                # 승수 -> 세트득실 순으로 정렬하여 표로 보여줍니다.
                st.table(ind_rank.sort_values(['개인승', '세트득실'], ascending=False))
    else:
        st.info("조 편성이 완료되면 스코어보드가 나타납니다.")

with tab_help:
    lang = st.radio("언어 선택 / Select Language", ["한국어", "English"], horizontal=True)
    show_help_section(lang)
