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
import gspread  # 🔥 [수정 포인트] 구글 시트 탭(워크시트)을 직접 생성하기 위해 추가

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

# st.secrets에서 URL 정보 불러오기
SHEET_URL = st.secrets["sheet_url"]
SHEET_informal_URL = st.secrets["sheet_informal_url"]
PRE_MADE_URLS = st.secrets["pre_made_urls"]

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="리그 운영 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# st.secrets를 통해 toml 파일에 저장된 비밀번호를 불러옵니다.
cookies = EncryptedCookieManager(password=st.secrets.get("cookie_password", "default_fallback_password"))

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
""", unsafe_allow_html=True)  # HTML과 CSS 태그가 문자열 그대로 출력되지 않고 실제 웹페이지에 적용되도록 허용하는 옵션

def save_room_state(room_name):
    """
    현재 구장의 모든 진행 상황(세션 상태)을 pkl 파일로 저장하여 새로고침해도 날아가지 않게 함
    """
    pass

def load_room_state(room_name):
    """
    저장된 pkl 파일에서 구장 데이터를 불러와 세션 상태를 복구하는 함수
    """
    pass


# 1. 반응형 텍스트를 출력하는 함수 정의
def responsive_text(text, pc_size="28px", mobile_size="18px", font_weight="bold", color="inherit"):
    """
    PC와 모바일에서 글자 크기가 자동으로 변하는 텍스트를 출력하는 함수, 설정한 크기에 따라 고유한 CSS 클래스 이름 생성 (충돌 방지)
    """
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


def extract_busu(busu_str):
    """'3부', '4부' 같은 문자열에서 숫자(3, 4)만 추출하여 계산에 사용할 수 있게 변환"""
    try:
        nums = re.findall(r'\d+', str(busu_str))
        return float(nums[0]) if nums else 9.0
    except:
        return 9.0

def load_data(uploaded_file=None):
    #사용하지 않음
    """회원 명단 CSV 파일을 불러오는 함수. 파일이 없으면 테스트용 더미 데이터를 생성함"""
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            return pd.read_csv(uploaded_file, encoding='cp949')
    # 더미 데이터 생성
    data = [{"순서": i, "이름": f"회원{i}", "성별": random.choice(["남", "여"]),
             "부수": f"{random.randint(1, 13)}부",
             "부수_조정": 0.0,
             "조편성_신청":f"{random.randint(1, 6)}조",
             "참석예정": random.choice(["Y", "N"])} for i in range(1, 11)]
    return pd.DataFrame(data)


def update_cumulative_record(p_a, p_b, s_a, s_b):
    """경기가 끝날 때마다 선수들의 누적 전적(승, 패, 득점, 실점)과 상대 전적을 업데이트하는 함수
       - p_a, p_b: 선수 A와 선수 B의 이름
       - s_a, s_b: 선수 A와 선수 B의 점수(Score)
    """
    # 세션 상태에 누적 전적 데이터프레임(cum_df)이 없으면 빈 표를 새로 만듭니다.
    if 'cum_df' not in st.session_state:
        st.session_state.cum_df = pd.DataFrame(columns=['방이름', '이름', '총경기수', '승', '패', '득점', '실점'])

    df_cum = st.session_state.cum_df
    # 방이름이 없을 경우를 대비한 기본값 설정
    room = st.session_state.get('room_name', '기본방')

    # 내부 함수: 명단에 없는 새로운 선수면 데이터프레임에 0전 0승 0패로 새로 추가하는 역할
    def ensure_player(df, name):
        # [추가] 만약 df에 필요한 컬럼이 없다면 즉시 생성 (에러 방지)
        required_columns = ['방이름', '이름', '총경기수', '승', '패', '득점', '실점']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0 if col in ['총경기수', '승', '패', '득점', '실점'] else None

        # 이제 '이름' 컬럼이 확실히 존재하므로 mask 생성이 안전합니다.
        mask = (df['이름'] == name) & (df['방이름'] == room)

        if not df[mask].any().any():
            new_row = pd.DataFrame([{
                '방이름': room,
                '이름': name,
                '총경기수': 0, '승': 0, '패': 0, '득점': 0, '실점': 0
            }])
            df = pd.concat([df, new_row], ignore_index=True)
        return df

    # "선택안함"(부전승 등 빈 자리)이 아닌 실제 선수일 경우에만 명단에 추가/확인
    if p_a != "선택안함": df_cum = ensure_player(df_cum, p_a)
    if p_b != "선택안함": df_cum = ensure_player(df_cum, p_b)

    for p, win, lose, score, opp_score in [(p_a, s_a > s_b, s_a < s_b, s_a, s_b),
                                           (p_b, s_b > s_a, s_b < s_a, s_b, s_a)]:
        if p != "선택안함":
            # 해당 방의 해당 선수 인덱스 찾기
            mask = (df_cum['이름'] == p) & (df_cum['방이름'] == room)
            idx_list = df_cum[mask].index
            if not idx_list.empty:
                idx = idx_list[0]
                df_cum.at[idx, '총경기수'] += 1
                df_cum.at[idx, '승'] += 1 if win else 0
                df_cum.at[idx, '패'] += 1 if lose else 0
                df_cum.at[idx, '득점'] += score
                df_cum.at[idx, '실점'] += opp_score

    # 업데이트된 표를 다시 세션 상태에 저장하여 화면에 반영되게 함
    st.session_state.cum_df = df_cum

    # 4. 상대 전적(Head to Head) 업데이트
    if p_a != "선택안함" and p_b != "선택안함":

        # 상대 전적 표(h2h_df)가 없으면 새로 만듦
        if 'h2h_df' not in st.session_state:
            st.session_state.h2h_df = pd.DataFrame(
                columns=['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])

        h2h = st.session_state.h2h_df

        # ★ [수정 포인트 1] h2h 데이터프레임에 필수 컬럼이 누락되어 KeyError가 발생하는 것을 완벽 방지
        required_h2h_cols = ['방이름', 'Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score']
        for col in required_h2h_cols:
            if col not in h2h.columns:
                h2h[col] = 0 if 'Win' in col or 'Score' in col else None

        # ★ 핵심: A vs B 와 B vs A 가 따로 기록되는 것을 막기 위해 이름을 가나다(알파벳) 순으로 정렬
        p1, p2 = sorted([p_a, p_b])

        # 방이름 조건을 추가하여 다른 클럽 데이터와 섞이지 않게 함
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2) & (h2h['방이름'] == room)

        # 만약 두 사람의 맞대결 기록이 아예 없다면 새로 0승 0패로 만들어줌
        if not mask.any():
            new_row = pd.DataFrame([{
                '방이름': room, 'Player1': p1, 'Player2': p2,
                'P1_Win': 0, 'P2_Win': 0, 'P1_Score': 0, 'P2_Score': 0
            }])

            h2h = pd.concat([h2h, new_row], ignore_index=True)
            # 행 추가 후 다시 마스크 갱신
            mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2) & (h2h['방이름'] == room)

        # 해당 맞대결 기록이 있는 행의 위치(인덱스)를 찾음
        idx = h2h[mask].index[0]

        # p1이 원래 p_a 였는지, p_b 였는지에 따라 점수와 승패를 알맞게 배분하여 더해줌
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

        # 업데이트된 상대 전적 표를 세션 상태에 저장
        st.session_state.h2h_df = h2h


# ==========================================
# 1. 시트 종류별 기준 템플릿(샘플) 정의 함수
# ==========================================
def get_sheet_template(sheet_type):
    """선택한 시트 종류에 맞는 빈 컬럼 구조를 반환합니다."""
    if sheet_type == "선수명단":
        # UI에서 사용하는 '순서', '직책' 등을 포함하여 템플릿을 강화합니다.
        return pd.DataFrame({"순서": [], "이름": [], "참석예정": [], "성별": [], "부수": [],  "부수_조정": [], "직책": [],  "조편성_신청": []})

    elif sheet_type == "누적전적":
        # 🚨 update_cumulative_record 함수에서 실제 사용하는 컬럼명으로 완벽히 일치시킵니다.
        return pd.DataFrame({"방이름": [], "이름": [], "총경기수": [], "승": [], "패": [], "득점": [], "실점": []})

    elif sheet_type == "상대전적":
        return pd.DataFrame(
            {"방이름": [], "Player1": [], "Player2": [], "P1_Win": [], "P2_Win": [], "P1_Score": [], "P2_Score": []})

    return pd.DataFrame()


def generate_excel_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 🔥 [추가된 부분] 선수명단 시트에 들어갈 임의의 더미 데이터 생성
        dummy_data = [
            {
                "순서": i,
                "이름": f"회원{i}",
                "참석예정": random.choice(["Y", "N"]),
                "성별": random.choice(["남", "여"]),
                "부수": f"{random.randint(1, 13)}부",
                "부수_조정": 0.0,
                "직책": "",  # 직책은 빈칸으로 둠
                "조편성_신청": f"{random.randint(1, 6)}조"
            } for i in range(1, 11)
        ]

        # 더미 데이터를 데이터프레임으로 변환
        df_dummy_players = pd.DataFrame(dummy_data)
        # 엑셀 시트에 각각 저장 (선수명단은 더미 데이터, 나머지는 빈 양식)
        df_dummy_players.to_excel(writer, sheet_name="선수명단", index=False)
        # get_sheet_template("선수명단").to_excel(writer, sheet_name="선수명단", index=False)
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


@st.dialog("📊 역대 누적 상대 전적")
def show_h2h_dialog(player_a, player_b):
    """두 선수를 선택했을 때 팝업창으로 역대 전적을 보여주는 함수"""
    p1, p2 = sorted([player_a, player_b])
    h2h = st.session_state.get('h2h_df', pd.DataFrame())

    if not h2h.empty:
        if 'Player1' in h2h.columns and 'Player2' in h2h.columns:
            mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)

            if mask.any():
                record = h2h[mask].iloc[0]
                p1_w, p2_w = record.get('P1_Win', 0), record.get('P2_Win', 0)
                p1_s, p2_s = record.get('P1_Score', 0), record.get('P2_Score', 0)

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
                if st.button("닫기", width='stretch'): st.rerun()
                return

    st.warning("아직 두 선수의 누적 맞대결 기록이 없습니다.")
    if st.button("닫기", width='stretch'): st.rerun()


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

            submit_login = st.form_submit_button("로그인", width='stretch')

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
                        # 해당 구장 전용 시트에서 데이터 로드
                        st.session_state.main_df = conn.read(spreadsheet=target_url, worksheet="선수명단", ttl=0)
                        st.session_state.cum_df = conn.read(spreadsheet=target_url, worksheet="누적전적", ttl=0)
                        st.session_state.h2h_df = conn.read(spreadsheet=target_url, worksheet="상대전적", ttl=0)

                    except Exception as e:
                        # 🔥 [수정 포인트 1] 기존 구장 접속 시 시트가 없으면 강제로 3개의 시트를 생성합니다.
                        st.sidebar.warning("⚠️ 전용 시트가 없거나 비어있습니다. 3개의 시트를 새로 생성합니다.")

                        empty_main = get_sheet_template("선수명단")
                        empty_cum = get_sheet_template("누적전적")
                        empty_h2h = get_sheet_template("상대전적")

                        try:
                            # gspread 클라이언트를 통해 스프레드시트 객체 가져오기
                            # sh = conn.client.open_by_url(target_url)
                            # ✅ 변경할 코드
                            gc = gspread.service_account_from_dict(st.secrets["connections"]["gsheets"])
                            sh = gc.open_by_url(target_url)

                            # 🔥 [추가할 코드] 구글 드라이브에 있는 파일의 제목을 '방이름_DB'로 자동 변경합니다!
                            sh.update_title(f"{new_room_name}_DB")

                            existing_sheets = [ws.title for ws in sh.worksheets()]

                            # 시트가 없으면 물리적으로 탭 추가
                            if "선수명단" not in existing_sheets:
                                sh.add_worksheet(title="선수명단", rows="1000", cols="20")
                            if "누적전적" not in existing_sheets:
                                sh.add_worksheet(title="누적전적", rows="1000", cols="20")
                            if "상대전적" not in existing_sheets:
                                sh.add_worksheet(title="상대전적", rows="1000", cols="20")

                            # 생성된 시트에 기본 컬럼 업데이트
                            conn.update(spreadsheet=target_url, worksheet="선수명단", data=empty_main)
                            conn.update(spreadsheet=target_url, worksheet="누적전적", data=empty_cum)
                            conn.update(spreadsheet=target_url, worksheet="상대전적", data=empty_h2h)
                        except Exception as inner_e:
                            st.sidebar.error(f"시트 자동 생성 중 오류 발생: {inner_e}")

                        st.session_state.main_df = empty_main
                        st.session_state.cum_df = empty_cum
                        st.session_state.h2h_df = empty_h2h
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
            new_room_sheet_url = st.text_input("이 구장에서 사용할 구글 시트 URL (전용)")

            submit_create = st.form_submit_button("새 구장 생성하기", type="primary", width='stretch')

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

                        # 🔥 [수정 포인트 2] 빈 URL에 3개의 시트를 강제로 생성하는 로직 추가
                        try:
                            # sh = conn.client.open_by_url(assigned_url)
                            # ✅ 변경할 코드
                            gc = gspread.service_account_from_dict(st.secrets["connections"]["gsheets"])
                            sh = gc.open_by_url(assigned_url)

                            existing_sheets = [ws.title for ws in sh.worksheets()]

                            # 시트가 없으면 물리적으로 탭 추가
                            if "선수명단" not in existing_sheets:
                                sh.add_worksheet(title="선수명단", rows="1000", cols="20")
                            if "누적전적" not in existing_sheets:
                                sh.add_worksheet(title="누적전적", rows="1000", cols="20")
                            if "상대전적" not in existing_sheets:
                                sh.add_worksheet(title="상대전적", rows="1000", cols="20")

                            # 기본 '시트1'이 남아있다면 깔끔하게 삭제 (선택사항)
                            for ws_name in ["시트1", "Sheet1"]:
                                if ws_name in existing_sheets and len(sh.worksheets()) > 1:
                                    try:
                                        sh.del_worksheet(sh.worksheet(ws_name))
                                    except:
                                        pass
                        except Exception as e:
                            st.error(f"시트 생성 중 오류 발생: {e}")

                        # 생성된 시트에 기본 컬럼 업데이트
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

    if st.sidebar.button("🔒 로그아웃", width='stretch'):
        st.session_state.is_admin = False
        st.rerun()

    st.sidebar.divider()

    st.sidebar.markdown("#### ☁️ 클라우드 동기화")

    if st.sidebar.button("💾 오늘의 최종 결과 구글시트 저장", type="primary", width='stretch'):
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
                        st.sidebar.error("❌ 이 구장의 전용 시트 URL을 찾을 수 정 없습니다. (마스터 DB 확인 필요)")
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
    # 🌟 데이터 관리 (명단/전적 업로드)
    # ==========================================
    with st.sidebar.expander("⚙️ 데이터 관리 (명단/전적 업로드)", expanded=False):

        data_source = st.radio("데이터 가져오기 방식", ["☁️ 구글 시트에서 불러오기", "📁 내 기기에서 파일 업로드"])

        if data_source == "☁️ 구글 시트에서 불러오기":
            st.info("클라우드에 저장된 최신 데이터를 화면으로 불러옵니다.")
            if st.button("구글 시트 데이터 최신화", width='stretch'):
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
                file_name=f"{st.session_state.room_name}_db.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )

            st.markdown("**2. 작성된 파일 업로드 (Excel 또는 CSV)**")
            # 🌟 [수정됨] xlsx 뿐만 아니라 csv 파일도 업로드 가능하도록 허용
            uploaded_file = st.file_uploader("파일 선택 (.xlsx, .csv)", type=['xlsx', 'xls', 'csv'])

            if uploaded_file:
                if st.button("파일 데이터 적용 및 클라우드 저장", type="primary", width='stretch'):
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
                                st.session_state.main_df = align_columns_to_template(xls_data["선수명단"],
                                                                                     get_sheet_template("선수명단"))
                            if "누적전적" in xls_data:
                                st.session_state.cum_df = align_columns_to_template(xls_data["누적전적"],
                                                                                    get_sheet_template("누적전적"))
                            if "상대전적" in xls_data:
                                st.session_state.h2h_df = align_columns_to_template(xls_data["상대전적"],
                                                                                    get_sheet_template("상대전적"))

                            # 클라우드에 즉시 저장
                            target_url = get_current_room_sheet_url(st.session_state.room_name)
                            if target_url:
                                conn.update(spreadsheet=target_url, worksheet="선수명단", data=st.session_state.main_df)
                                conn.update(spreadsheet=target_url, worksheet="누적전적", data=st.session_state.cum_df)
                                conn.update(spreadsheet=target_url, worksheet="상대전적", data=st.session_state.h2h_df)

                                # 🔥 [추가된 부분] 구글 드라이브 상의 파일 이름 변경 로직
                                try:
                                    # 업로드된 파일 이름에서 확장자(.csv, .xlsx)를 제외한 이름 추출
                                    new_file_name = uploaded_file.name.split('.')[0]

                                    # 1. Streamlit secrets에 저장된 구글 서비스 계정 정보를 딕셔너리 형태로 가져옴
                                    credentials_dict = dict(st.secrets["connections"]["gsheets"])

                                    # 2. gspread 라이브러리를 직접 사용하여 인증 (conn.client 우회)
                                    gc = gspread.service_account_from_dict(credentials_dict)

                                    # 3. URL로 시트를 열고 제목 업데이트
                                    spreadsheet = gc.open_by_url(target_url)
                                    spreadsheet.update_title(new_file_name)

                                    st.success(f"✅ 데이터 저장 완료 및 구글 시트 이름이 '{new_file_name}'(으)로 변경되었습니다!")
                                except Exception as title_e:
                                    # 이름 변경에 실패하더라도 데이터 저장은 완료되었음을 알림
                                    st.warning(f"✅ 데이터는 저장되었으나 파일 이름 변경에 실패했습니다: {title_e}")
                                    # sys.exit()
                            else:
                                st.success("✅ 데이터가 성공적으로 적용되었습니다! (클라우드 URL 없음)")

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

attendees_count = (
        st.session_state.main_df[col_date] == 'Y').sum() if col_date in st.session_state.main_df.columns else 0

# ==========================================
# 탭 1: 출석체크 화면 구성
# ==========================================
with tab_home:
    responsive_text(f"📋 {CURRENT_DATE}", pc_size="20px", mobile_size="16px")

    # 원본 데이터를 건드리지 않기 위해 복사본(copy)을 만듭니다.
    df = st.session_state.main_df.copy()

    # 2. [에러 방지] '순서' 컬럼이 없으면 자동으로 생성
    if '순서' not in df.columns:
        df.insert(0, '순서', range(1, len(df) + 1))

    # 3. [핵심 수정] '참석' 상태 처리
    # 사용자의 데이터에는 '참석예정'이 있으므로, 이를 기반으로 '참석' 체크박스용 컬럼을 만듭니다.
    # col_date(오늘 날짜 컬럼)에 데이터가 있으면 그것을 쓰고, 없으면 '참석예정'을 기본값으로 참조합니다.
    target_date_col = col_date if col_date in df.columns else '참석예정'

    # 'Y' 또는 '예'로 되어 있으면 체크박스 True, 아니면 False
    df['참석'] = df[target_date_col].apply(lambda x: True if str(x).upper() in ['Y', '예', '참석'] else False)

    # 4. 화면에 보여줄 컬럼 설정 (실제 존재하는 컬럼만 선택)
    # 알려주신 컬럼명: 순서, 이름, 참석예정, 성별, 부수, 직책 등
    display_cols = [c for c in ['순서', '이름', '참석', '부수'] if c in df.columns]

    # 좌우 분할을 위한 인덱스 계산
    mid_idx = len(df) // 2 + (len(df) % 2)

    # 화면을 정확히 5:5 비율의 두 칸(col1, col2)으로 나눕니다.
    col1, col2 = st.columns(2)

    # st.data_editor: 엑셀처럼 화면에서 직접 데이터를 수정할 수 있게 해주는 강력한 기능입니다.
    with col1:
        edited_left = st.data_editor(
            df.iloc[:mid_idx][display_cols],
            hide_index=True,
            disabled=not is_admin,
            key="editor_left",
            width='stretch'
        )
    with col2:
        edited_right = st.data_editor(
            df.iloc[mid_idx:][display_cols],
            hide_index=True,
            disabled=not is_admin,
            key="editor_right",
            width='stretch'
        )

    # 6. 수정된 데이터 합치기
    edited_df = pd.concat([edited_left, edited_right], ignore_index=True)

    # 7. 실시간 참석자 명단 추출 (체크된 사람만)
    current_checked = edited_df[edited_df['참석'] == True]

    # 참석자들의 이름을 가나다순으로 정렬한 뒤, 쉼표(,)로 연결하여 한 줄의 문장으로 만듭니다.
    live_names = ", ".join(sorted(current_checked['이름'].tolist()))

    # 안내창 표시
    st.info(f"**현재 참석 ({len(current_checked)}명):** \n\n {live_names if live_names else '없음'}")

    # 8. 관리자 전용 확정 버튼
    if is_admin:
        btn_label = "확정 완료 (참석자 저장됨)" if st.session_state.attendance_confirmed else "참석자 확정하기"
        btn_type = "primary" if st.session_state.attendance_confirmed else "secondary"

        # 확정 버튼을 눌렀을 때 실행되는 부분
        if st.button(btn_label, type=btn_type, width='stretch'):
            # 화면의 체크 상태(True/False)를 원본 데이터 형식('Y'/'N')으로 변환하여 저장
            # 오늘 날짜 컬럼(col_date)에 저장합니다.
            st.session_state.main_df[col_date] = edited_df['참석'].apply(lambda x: 'Y' if x else 'N')

            # (선택사항) '참석예정' 컬럼도 동기화하고 싶다면 아래 주석 해제
            st.session_state.attendance_confirmed = True
            st.success("✅ 오늘의 참석자 명단이 시스템에 기록되었습니다.")
            time.sleep(1)
            st.rerun()

        st.divider()
        responsive_text(f"💾 최신 명단 다운로드", pc_size="20px", mobile_size="16px")
        # 현재까지의 모든 데이터(출석 기록 포함)를 CSV 파일 형태로 변환합니다. (한글 깨짐 방지 utf-8-sig)
        csv_main = st.session_state.main_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 최신 명단(CSV) 다운로드",
            data=csv_main,
            file_name=f"{room_name}_최신명단_{CURRENT_DATE}.csv",
            mime="text/csv",
            type="primary",
            width='stretch'
        )

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
        responsive_text(f"👥 조 구성", pc_size="20px", mobile_size="16px")
        # 숫자 입력 위젯 (기본값 4조, 1\~20조까지 설정 가능)
        g_val = st.number_input("편성 조 수", 1, 20, 4, disabled=not is_admin)

        if g_val > 0:
            avg = attendees_count // g_val  # 몫: 한 조에 들어갈 기본 인원
            rem = attendees_count % g_val  # 나머지: 남는 인원

            # 나머지가 있으면 어떤 조는 1명이 더 많아지므로 범위를 보여주고, 딱 떨어지면 고정 인원을 보여줍니다.
            if rem > 0:
                st.info(f"👉 조당 {avg}~{avg + 1}명 배정")
            else:
                st.info(f"👉 조당 {avg}명 배정")

    with c2:
        responsive_text(f"🎾 경기 규칙", pc_size="20px", mobile_size="16px")
        s_g = st.number_input("단식 게임", 0, 10, 2, disabled=not is_admin)
        d_g = st.number_input("복식 게임", 0, 5, 1, disabled=not is_admin)
        set_c = st.selectbox("개인전 선승 세트", [2, 3, 4, 5], index=1, disabled=not is_admin)

    with c3:
        responsive_text(f"⚙️ 환경 설정", pc_size="20px", mobile_size="16px")
        t_val = st.number_input("Table_No.", 1, 20, 3, disabled=not is_admin)

    with c4:
        responsive_text(f"🎲 방식", pc_size="20px", mobile_size="16px")
        # 라디오 버튼으로 둘 중 하나를 선택하게 합니다.
        draw_method = st.radio("방식", ["AI 선정", "제비뽑기", "조편성_신청"], label_visibility="collapsed", disabled=not is_admin)

    with c5:
        responsive_text(f"✅ 실행", pc_size="20px", mobile_size="16px")
        if is_admin:
            btn_label = "설정 확정 완료" if st.session_state.config_confirmed else "설정 확정 및 편성 시작"
            btn_type = "primary" if st.session_state.config_confirmed else "secondary"

            if st.button(btn_label, type=btn_type, width='stretch'):
                # 위에서 설정한 모든 값들을 'config'라는 하나의 딕셔너리(보따리)에 담아 세션에 저장합니다.
                st.session_state.config = {
                    "g": g_val, "t": t_val, "s_games": s_g, "d_games": d_g, "set_count": set_c,
                    "total_g": s_g + d_g, "draw_method": draw_method,
                    # 동점자 처리를 위해 모든 사람에게 0\~1 사이의 랜덤 숫자를 미리 부여해 둡니다.
                    "tie_breakers": {name: random.random() for name in st.session_state.main_df['이름']}
                }
                st.session_state.config_confirmed = True
                st.rerun()
        else:
            st.info("관리자 전용")

    st.markdown('</div>', unsafe_allow_html=True)

    if "config" in st.session_state and st.session_state.config.get('draw_method') == '제비뽑기':

        # 아직 제비뽑기가 완전히 끝나지 않았다면
        if not st.session_state.get('draw_completed', False):
            st.divider()
            cfg = st.session_state.config
            df = st.session_state.main_df

            # 참석자 명단만 추려냅니다.
            attendees = df[df[col_date] == 'Y'].copy()
            # '1부', '2부' 같은 글자에서 숫자만 뽑아냅니다. (정렬을 위해)
            attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
            # 아까 만들어둔 랜덤 숫자를 매칭합니다.
            attendees['Random'] = attendees['이름'].map(cfg['tie_breakers'])

            # 💡 핵심: 실력이 비슷한 사람끼리 묶기 위해 부수 -> 조정부수 -> 랜덤 순으로 줄을 세웁니다.
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

                responsive_text(f"📋 그룹 {level + 1}", pc_size="20px", mobile_size="16px")
                cols = st.columns(cfg['g'])  # 조 개수만큼 화면을 가로로 나눕니다.

                # [상태 1] 이미 제비뽑기가 끝난 과거의 그룹들
                if level < draw_level:
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        with cols[i % cfg['g']]:
                            # 배정된 조를 가져와서 초록색 성공 창으로 보여줍니다.
                            assigned_team = st.session_state.draw_results.get(row['이름'], "-")
                            st.success(f" **{row['이름']}** ➔ **{assigned_team}조**")

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
                                st.session_state.draw_level += 1
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
                    if t_list[j] and t_list[-1 - j]:
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

        # 대진표 데이터 생성
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
            st.info(" **행을 클릭**하면 상세 결과 입력창이 나타납니다.")

        col1, col2 = st.columns(2)
        with col1:
            # on_select="rerun": 표의 특정 줄을 클릭하면 화면이 새로고침되면서 클릭한 정보를 가져옵니다.
            event_left = st.dataframe(df_left.style.apply(highlight_finished, axis=1),
                                      width="stretch",
                                      hide_index=True,
                                      on_select="rerun",
                                      selection_mode="single-row"
                                      )
        with col2:
            event_right = st.dataframe(df_right.style.apply(highlight_finished, axis=1),
                                       width="stretch",
                                       hide_index=True,
                                       on_select="rerun",
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
                st.warning("🔒 관리자 비밀번호를 입력해주세요.")
            else:
                # [A] 개인전일 경우의 점수 입력 UI (간단함)
                if is_ind:
                    # [A] 개인전 로직 (생략 없이 유지)
                    m_idx = selected_match_idx
                    c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 2.5, 1.5, 1.5])
                    with c1:
                        st.markdown(f"<div style='text-align:center;'>{team_a}</div>", unsafe_allow_html=True)

                    with c2:
                        res_type = st.radio(f"결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_ind_res")

                    with c3:
                        scores = [f"{limit}:{i}" for i in range(limit)] if res_type == "승" else [f"{i}:{limit}" for i in
                                                                                                 range(limit)]
                        selected_score = st.radio("스코어", scores, horizontal=True, key=f"m{m_idx}_ind_score")

                    with c4:
                        st.markdown(f"<div style='text-align:center;'>{team_b}</div>", unsafe_allow_html=True)

                    with c5:
                        if st.button("결과 저장", type="primary", key=f"btn_save_ind_{m_idx}"):
                            s_a, s_b = map(int, selected_score.split(':'))
                            st.session_state.matrix.loc[team_a, team_b] = s_a
                            st.session_state.matrix.loc[team_b, team_a] = s_b
                            st.rerun()

                # [B] 단체전(조별 리그)일 경우의 점수 입력 UI (단식/복식 각각 입력)
                else:
                    # [B] 단체전 로직 (단식/복식 인원 분리 핵심)
                    def get_team_players(team_str):
                        match = re.search(r'(\d+)조', str(team_str))
                        if match and 'teams' in st.session_state:
                            t_idx = int(match.group(1))
                            return [p.split('(')[0] for p in st.session_state.teams.get(t_idx, [])]
                        return list(st.session_state.ind_matrix.index)


                    team_a_players = get_team_players(team_a)
                    team_b_players = get_team_players(team_b)
                    m_idx = selected_match_idx

                    # 💡 핵심: 단식용 가용 인원 체크 (단식 선수들끼리만 중복 제거)
                    def get_avail_single(players, current_key):
                        selected = [st.session_state[f"m{m_idx}_s_p{ab}_{s}"]
                                    for ab in ['a', 'b'] for s in range(s_games)
                                    if f"m{m_idx}_s_p{ab}_{s}" in st.session_state
                                    and f"m{m_idx}_s_p{ab}_{s}" != current_key
                                    and st.session_state[f"m{m_idx}_s_p{ab}_{s}"] != "선택안함"]
                        return ["선택안함"] + [p for p in players if p not in selected]

                    # 💡 핵심: 복식용 가용 인원 체크 (단식 인원은 포함시키고, 복식 내부 인원만 중복 제거)
                    def get_avail_double(players, current_key):
                        selected = [st.session_state[f"m{m_idx}_d_p{ab}{num}_{d}"]
                                    for ab in ['a', 'b'] for num in [1, 2] for d in range(d_games)
                                    if f"m{m_idx}_d_p{ab}{num}_{d}" in st.session_state
                                    and f"m{m_idx}_d_p{ab}{num}_{d}" != current_key
                                    and st.session_state[f"m{m_idx}_d_p{ab}{num}_{d}"] != "선택안함"]
                        return ["선택안함"] + [p for p in players if p not in selected]


                    match_results = []
                    set_limit = 3
                    set_win_scores = [f"{set_limit}:{i}" for i in range(set_limit)]
                    set_lose_scores = [f"{i}:{set_limit}" for i in range(set_limit)]

                    # --- 단식 경기 섹션 ---
                    if s_games > 0:
                        st.markdown("#### 👤 단식 경기")
                        for s in range(s_games):
                            c1, c2, c3, c4, c5 = st.columns([1, 2.5, 1.5, 2.5, 2.5])
                            ka, kb = f"m{m_idx}_s_pa_{s}", f"m{m_idx}_s_pb_{s}"

                            with c1: st.write(f"단식 {s + 1}")

                            with c2: p_a = st.selectbox(f"A팀", get_avail_single(team_a_players, ka), key=ka,
                                                        label_visibility="collapsed")

                            with c3: res = st.radio("결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_s_res_{s}",
                                                    label_visibility="collapsed")

                            with c4:
                                sc = st.radio("점수", set_win_scores if res == "승" else set_lose_scores, horizontal=True,
                                              key=f"m{m_idx}_s_sc_{s}", label_visibility="collapsed")
                                s_a, s_b = map(int, sc.split(':'))

                            with c5: p_b = st.selectbox(f"B팀", get_avail_single(team_b_players, kb), key=kb,
                                                        label_visibility="collapsed")
                            match_results.append(("S", p_a, s_a, s_b, p_b))

                    st.write("")

                    # --- 복식 경기 섹션 ---
                    if d_games > 0:
                        # st.markdown("##### 👥 복식 경기")
                        responsive_text(f"👥 복식 경기", pc_size="20px", mobile_size="16px")
                        for d in range(d_games):
                            c1, c2, c3, c4, c5 = st.columns([1, 2.5, 1.5, 2.5, 2.5])
                            ka1, ka2 = f"m{m_idx}_d_pa1_{d}", f"m{m_idx}_d_pa2_{d}"
                            kb1, kb2 = f"m{m_idx}_d_pb1_{d}", f"m{m_idx}_d_pb2_{d}"

                            with c1: st.write(f"복식 {d + 1}")

                            with c2:
                                p_a1 = st.selectbox(f"A1", get_avail_double(team_a_players, ka1), key=ka1,
                                                    label_visibility="collapsed")
                                p_a2 = st.selectbox(f"A2", get_avail_double(team_a_players, ka2), key=ka2,
                                                    label_visibility="collapsed")

                            with c3: res = st.radio("결과", ["승", "패"], horizontal=True, key=f"m{m_idx}_d_res_{d}",
                                                    label_visibility="collapsed")

                            with c4:
                                sc = st.radio("점수", set_win_scores if res == "승" else set_lose_scores, horizontal=True,
                                              key=f"m{m_idx}_d_sc_{d}", label_visibility="collapsed")
                                s_a, s_b = map(int, sc.split(':'))

                            with c5:
                                p_b1 = st.selectbox(f"B1", get_avail_double(team_b_players, kb1), key=kb1,
                                                    label_visibility="collapsed")
                                p_b2 = st.selectbox(f"B2", get_avail_double(team_b_players, kb2), key=kb2,
                                                    label_visibility="collapsed")
                            match_results.append(("D", (p_a1, p_a2), s_a, s_b, (p_b1, p_b2)))

                    if st.button("💾 상세 결과 저장", type="primary", width='stretch'):
                        aw, bw = 0, 0
                        for res in match_results:
                            if res[0] == "S":
                                _, pa, sa, sb, pb = res
                                if pa != "선택안함" and pb != "선택안함":
                                    st.session_state.ind_matrix.loc[pa, pb] = sa
                                    st.session_state.ind_matrix.loc[pb, pa] = sb
                                    update_cumulative_record(pa, pb, sa, sb)
                                if sa > sb:
                                    aw += 1
                                elif sb > sa:
                                    bw += 1
                            else:
                                _, _, sa, sb, _ = res
                                if sa > sb:
                                    aw += 1
                                elif sb > sa:
                                    bw += 1

                        st.session_state.matrix.loc[team_a, team_b] = aw
                        st.session_state.matrix.loc[team_b, team_a] = bw
                        st.success("저장되었습니다!")
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
        room_name = st.session_state.get('room_name', '탁구대회')

        # 글자 크기 초기 설정
        if 'table_font_size' not in st.session_state:
            num_rows = len(st.session_state.labels)
            st.session_state.table_font_size = 20 if num_rows <= 4 else (
                16 if num_rows <= 6 else (13 if num_rows <= 8 else 11))

        # 전체 화면 모드 여부를 기억하는 변수 (기본값: False)
        if 'fullscreen_table' not in st.session_state:
            st.session_state.fullscreen_table = False


        def draw_summary_table():
            # 1. 계산용 매트릭스 복사 및 정규화
            raw_m = st.session_state.matrix.copy()
            current_labels = st.session_state.labels  # 현재 확정된 명단 순서

            # [해결책] 현재 명단 순서에 맞춰 행과 열을 강제로 재배치 (테이블 깨짐 방지 핵심)
            m = raw_m.reindex(index=current_labels, columns=current_labels)

            # 2. 통계용 rank 데이터프레임 생성 (순서 고정)
            rank = pd.DataFrame(index=m.index)

            # 3. .values를 사용하여 인덱스 라벨 불일치 에러 방지 및 승패 계산
            m_val = m.values
            mt_val = m.T.values

            rank['승'] = np.nansum(m_val > mt_val, axis=1).astype(int)
            rank['패'] = np.nansum(m_val < mt_val, axis=1).astype(int)

            # 4. 득실 계산 (결측치는 0으로 처리하여 정수형 유지)
            rank['득점'] = m.sum(axis=1, skipna=True).fillna(0).astype(int)
            rank['실점'] = m.sum(axis=0, skipna=True).fillna(0).astype(int)
            rank['득실차'] = (rank['득점'] - rank['실점']).astype(int)

            # 5. 결과 합치기 및 정렬
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
            .custom-table-wrapper {{ overflow-x: auto; }}
            .custom-table-wrapper table {{ width: 100% !important; border-collapse: collapse !important; font-size: {current_fs}px !important; }}
            .custom-table-wrapper th, .custom-table-wrapper td {{ white-space: nowrap !important; padding: 4px 8px !important; border: 1px solid #dee2e6 !important; }}
            .custom-table-wrapper th {{ background-color: #f8f9fa; }}
            .custom-table-wrapper td:nth-last-child(-n+5) {{ background-color: #fffef0; font-weight: bold; width: 60px !important; }}
            </style>
            """
            st.markdown(css + '<div class="custom-table-wrapper">' + raw_html + '</div>', unsafe_allow_html=True)

        # --- 상단 제어 바 ---
        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([4, 2, 2, 2])

        with col_ctrl1:
            btn_txt = "🔙 이전 화면으로" if st.session_state.fullscreen_table else "📺 전체 화면 모드"
            if st.button(btn_txt, type="primary", width='stretch'):
                st.session_state.fullscreen_table = not st.session_state.fullscreen_table
                st.rerun()

        with col_ctrl2:  # 글자 크기 조절 버튼 (+ / -)
            f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1])
            with f_col1:
                if st.button("➖"): st.session_state.table_font_size = max(8,
                                                                          st.session_state.table_font_size - 1); st.rerun()
            with f_col2:
                st.markdown(
                    f"<div style='text-align:center; padding-top:5px;'><b>{st.session_state.table_font_size}</b></div>",
                    unsafe_allow_html=True)
            with f_col3:
                if st.button("➕"): st.session_state.table_font_size = min(30,
                                                                          st.session_state.table_font_size + 1); st.rerun()

        with col_ctrl3:  # 누적 결과 다운로드
            if 'cum_df' in st.session_state and not st.session_state.cum_df.empty:
                csv_bytes = st.session_state.cum_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 누적 다운로드", data=csv_bytes, file_name=f"{room_name}_누적.csv", mime="text/csv",
                                   width='stretch')

        with col_ctrl4:  # 상대 전적 다운로드
            if 'h2h_df' in st.session_state and not st.session_state.h2h_df.empty:
                h2h_bytes = st.session_state.h2h_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 상대전적 다운로드",
                                   data=h2h_bytes,
                                   file_name=f"{room_name}_상전.csv",
                                   mime="text/csv",
                                   width='stretch'
                                   )

        if st.session_state.fullscreen_table:
            responsive_text(f"🏆 종합 결과 전광판", pc_size="24px", mobile_size="18px")
            draw_summary_table()
        else:
            # 결과 입력 섹션
            responsive_text(f"📋 {'조별' if not is_ind else '개인전'} 점수 입력", pc_size="20px", mobile_size="16px")
            if not is_admin:
                st.warning("🔒 관리자만 입력 가능합니다.")
            else:
                st.info(" 기준이 되는 조(선수)를 선택하고 승/패 및 스코어를 입력하세요. (이미 완료된 경기는 비활성화됩니다.)")
                labels = st.session_state.labels
                limit = cfg.get('set_count', 3) if is_ind else cfg.get('total_g', 5)
                if labels:
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2.5, 1.5])
                    with c1:
                        team_a = st.selectbox("A 선수", labels, key="sb_a")

                    with c2:
                        def f_b(n):
                            # n은 B 선수의 이름(예: '2조(박인규)')입니다.
                            try:
                                # team_a(A 선수)와 n(B 선수)이 매트릭스(행/열)에 모두 존재하는지 확인
                                if (team_a in st.session_state.matrix.index) and (n in st.session_state.matrix.columns):
                                    val = st.session_state.matrix.loc[team_a, n]
                                    # 이미 경기가 끝난 경우 결과(승/패)를 함께 표시
                                    return f"{n} ({val})" if pd.notna(val) and val != "" else n
                                else:
                                    # 매트릭스에 이름이 없으면 그냥 이름만 반환
                                    return n
                            except:
                                return n


                        team_b = st.selectbox("B 선수", [l for l in labels if l != team_a], format_func=f_b, key="sb_b")

                        # --- 수정 후 (안전한 버전) ---
                        is_done = False  # 기본값 설정

                        # 매트릭스가 존재하고, 두 선수가 매트릭스의 인덱스와 컬럼에 모두 있는지 확인
                        if 'matrix' in st.session_state and team_a in st.session_state.matrix.index and team_b in st.session_state.matrix.columns:
                            val = st.session_state.matrix.loc[team_a, team_b]
                            # 값이 NaN이 아니거나 빈 문자열이 아니면 완료된 것으로 판단
                            if pd.notna(val) and val != "":
                                is_done = True
                        else:
                            # 매트릭스에 선수가 없다면 에러를 방지하기 위해 로그를 남기거나 경고 표시 (선택)
                            st.warning(f"⚠️ 대진표 매트릭스에 '{team_a}' 또는 '{team_b}' 선수가 없습니다. 조 편성을 다시 확인해주세요.")

                    with c3:
                        res = st.radio("A 결과", ["승", "패"], horizontal=True, disabled=is_done)
                    with c4:
                        win_s = [f"{s}:{limit - s}" for s in range(limit, -1, -1) if s >= limit - s]
                        lose_s = [f"{s.split(':')[1]}:{s.split(':')[0]}" for s in win_s]
                        scores = win_s if res == "승" else lose_s
                        sel_s = st.radio("스코어", scores, horizontal=True, disabled=is_done)
                    with c5:
                        if st.button("저장", type="primary", width='stretch', disabled=is_done):
                            sa, sb = map(int, sel_s.split(':'))
                            st.session_state.matrix.loc[team_a, team_b] = sa
                            st.session_state.matrix.loc[team_b, team_a] = sb
                            update_cumulative_record(team_a, team_b, sa, sb)
                            st.success("저장되었습니다.");
                            time.sleep(0.5);
                            st.rerun()

            st.divider()
            responsive_text(f"📊 {'조별 리그' if not is_ind else '개인전'} 순위표", pc_size="22px", mobile_size="18px")
            draw_summary_table()

            if not is_ind:
                st.divider()
                responsive_text("👤 개인 성적 관리", pc_size="20px", mobile_size="16px")
                if is_admin:
                    new_ind = st.data_editor(st.session_state.ind_matrix, width="stretch", height=300)
                    if not new_ind.equals(st.session_state.ind_matrix):
                        st.session_state.ind_matrix = new_ind
                        st.rerun()
                else:
                    st.dataframe(st.session_state.ind_matrix.style.format(precision=0, na_rep='-'), width="stretch")

                # 개인별 순위 계산 (정수화 적용)
                im = st.session_state.ind_matrix
                ind_rank = pd.DataFrame(index=im.index)
                ind_rank['개인승'] = (im.values > im.T.values).sum(axis=1).astype(int)
                ind_rank['개인패'] = (im.values < im.T.values).sum(axis=1).astype(int)
                ind_rank['세트득실'] = (im.sum(axis=1) - im.sum(axis=0)).fillna(0).astype(int)

                st.markdown("#### 🥇 개인별 순위 요약")
                st.table(ind_rank.sort_values(['개인승', '세트득실'], ascending=False).head(10))

    else:
        st.info("조 편성이 완료되면 스코어보드가 나타납니다.")

with tab_help:
    lang = st.radio("언어 선택 / Select Language", ["한국어", "English"], horizontal=True)
    show_help_section(lang)
