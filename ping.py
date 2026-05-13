# =====================================================================
# [1단계] 라이브러리 임포트, 전역 설정 및 세션 초기화
# =====================================================================
# 1-1. 파이썬 내장 라이브러리
import os
import json
import math
import io
import time
import hashlib
import hmac  # 🌟 [보안성 개선] 더 강력한 해싱을 위해 추가
import logging  # 🌟 [운영성 개선] 시스템 로그 기록을 위해 추가
import re
import random
import uuid  # 🌟 [추가] 일반 사용자 고유 세션 ID 발급용
from datetime import datetime
from datetime import datetime as dt  # 안전한 시간 포맷을 위해 별칭(dt)으로도 확보
from io import StringIO

# 1-2. 데이터 처리 및 서드파티 라이브러리
import numpy as np
import pandas as pd
import gspread  # 🔥 구글 시트 탭(워크시트)을 직접 생성하고 제어하기 위해 추가

# 1-3. Streamlit 및 관련 확장 라이브러리
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1-4. 로컬 모듈 (사용자 정의 파일)
from Program_User_Guide import show_help_section
import config

# ---------------------------------------------------------------------
# Streamlit 페이지 기본 설정 (⚠️ 다른 모든 st 명령어보다 먼저 와야 함)
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="리그 운영 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------
# 로깅 및 전역 상수 설정
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEV_MODE = False
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')

# 파일 기반 저장 구조 상수
HISTORY_FILE = "league_history.json"
ROOM_STATES_FILE = "room_states.json"
VIEWER_FILE = "viewer_sessions.json"  # 🌟 [추가] 일반 사용자 세션 관리 파일
MAX_VIEWERS = 30  # 🌟 [추가] 시스템 부하 방지를 위한 방당 최대 일반 사용자 수

# ---------------------------------------------------------------------
# Secrets 로드 및 보안 설정
# ---------------------------------------------------------------------
SHEET_URL = st.secrets["sheet_url"]
SHEET_informal_URL = st.secrets["sheet_informal_url"]
PRE_MADE_URLS = st.secrets["pre_made_urls"]
MASTER_PASSWORD = st.secrets["master_password"]

def hash_password(password):
    """비밀번호를 안전하게 보관하기 위해 SHA-256 방식으로 암호화하는 함수"""
    return hashlib.sha256(password.encode()).hexdigest()

# def hash_password_old(password):
#     """비밀번호를 안전하게 보관하기 위해 SHA-256 방식으로 암호화하는 함수"""
#     return hashlib.sha256(password.encode()).hexdigest()
#
# def hash_password_new(password):
#     """
#     HMAC과 Salt를 사용하여 비밀번호를 안전하게 해싱합니다.
#     Args:
#         password (str): 원문 비밀번호
#     Returns:
#         str: 해싱된 비밀번호 문자열
#     """
#     salt = st.secrets.get("pw_salt", "default_secure_salt_value").encode('utf-8')
#     return hmac.new(salt, password.encode('utf-8'), hashlib.sha256).hexdigest()
#
#
# # --- 로그인 검증 로직 ---
# admin_password = st.sidebar.text_input("관리자 비밀번호", type="password")
# saved_password = str(room_data['비밀번호'].values[0]).strip()  # DB에 저장된 암호문
#
# # 마스터 비밀번호 해싱 (신버전 사용)
# HASHED_MASTER_PW = hash_password_new(MASTER_PASSWORD)
#
# if admin_password:
#     # 입력한 비밀번호를 두 가지 방식으로 모두 변환해봄
#     input_hash_old = hash_password_old(admin_password)
#     input_hash_new = hash_password_new(admin_password)
#
#     # 1. 마스터 비밀번호와 일치하는지 확인 (신버전 해시 비교)
#     # 2. 또는 DB에 저장된 방 비밀번호(구버전 or 신버전)와 일치하는지 확인
#     if input_hash_new == HASHED_MASTER_PW or saved_password == input_hash_old or saved_password == input_hash_new:
#         st.sidebar.success("👑 관리자 모드로 접속 중입니다.")
#         # 관리자 로직 실행...
#     else:
#         st.sidebar.error("❌ 비밀번호가 틀렸습니다.")
# 수정 후 (정상 동작)
# HASHED_MASTER_PW = hash_password_new(MASTER_PASSWORD)
HASHED_MASTER_PW = hash_password(MASTER_PASSWORD)

# ---------------------------------------------------------------------
# 확장 라이브러리 초기화 (쿠키 매니저, GSheets)
# ---------------------------------------------------------------------
# 스마트폰 등에서 이전 방(세션)을 기억하기 위한 쿠키 매니저 라이브러리 임포트 및 예외 처리
try:
    from streamlit_cookies_manager import EncryptedCookieManager
except ImportError:
    st.error("⚠️ 'streamlit-cookies-manager' 라이브러리가 설치되지 않았습니다.")
    logging.error("ImportError: streamlit-cookies-manager not found.")

# 구글 시트 연동 라이브러리 임포트 및 예외 처리
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("⚠️ 'st-gsheets-connection' 라이브러리가 설치되지 않았습니다.")
    logging.error("ImportError: st-gsheets-connection not found.")

# # 🌟 [보안성 개선] 하드코딩된 fallback 비밀번호 제거 (보안 취약점 제거)
cookie_password = st.secrets.get("cookie_password")

if not cookie_password:
    st.error("⚠️ 시스템 설정 오류: cookie_password가 secrets에 설정되지 않았습니다.")
    st.stop()
# 쿠키 매니저 객체 생성
cookies = EncryptedCookieManager(password=cookie_password)
# 쿠키가 아직 준비되지 않았다면(초기 로딩 중) 아래 코드의 실행을 멈추고 대기합니다.
if not cookies.ready():
    st.stop()

# 6. 전역 CSS 및 UI 스타일 적용 (Global Styles, 버튼 색상, 테이블 너비, 정렬 등 디자인 요소 변경)
# unsafe_allow_html=True 옵션을 통해 HTML과 CSS 태그가 문자열 그대로 출력되지 않고 실제 웹페이지에 적용되도록 허용합니다.
st.markdown(config.main_markdown_text, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 세션 상태(Session State) 초기화
# ---------------------------------------------------------------------
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'room_name' not in st.session_state:
    st.session_state.room_name = "생활_탁구장"
if 'game_round' not in st.session_state:
    st.session_state.game_round = 1
if 'attendance_confirmed' not in st.session_state:
    st.session_state.attendance_confirmed = False
if 'config_confirmed' not in st.session_state:
    st.session_state.config_confirmed = False
if 'is_viewer' not in st.session_state:
    st.session_state.is_viewer = False
if 'viewer_id' not in st.session_state:
    st.session_state.viewer_id = None

# =====================================================================
# [2단계] 유틸리티(Helper) 및 공통 함수
# =====================================================================
def extract_busu(busu_str):
    """'3부', '4부' 같은 문자열에서 숫자(3, 4)만 추출하여 계산에 사용할 수 있게 int(정수)로 변환"""
    try:
        nums = re.findall(r'\d+', str(busu_str))
        return int(nums[0]) if nums else 9
    except Exception as e:
        logging.warning(f"부수 추출 실패 ({busu_str}): {e}")
        return 9

def align_columns_to_template(uploaded_df, template_df):
    """
    업로드된 데이터프레임이 템플릿의 필수 컬럼을 모두 포함하도록 맞춥니다.
    Args:
        uploaded_df (pd.DataFrame): 업로드된 데이터
        template_df (pd.DataFrame): 기준 템플릿 데이터
    Returns:
        pd.DataFrame: 컬럼이 보정된 데이터프레임
    """
    expected_columns = template_df.columns.tolist()
    for col in expected_columns:
        if col not in uploaded_df.columns:
            uploaded_df[col] = None
    return uploaded_df

def reset_config_state():
    """설정을 초기화할 때 기존에 만들어진 조 편성, 대진표 등의 데이터를 삭제하는 함수"""
    st.session_state.config_confirmed = False

    # config.py에 정의된 삭제 대상 키 목록을 불러와서 세션에서 안전하게 삭제합니다.
    for k in config.KEYS_TO_DELETE_ON_RESET:
        if k in st.session_state:
            del st.session_state[k]

def atomic_write_json(filepath, data):
    """
    저장 중 서버 다운 시 데이터 유실을 막기 위해 원자적 쓰기(Atomic Write)를 수행합니다.
    Args:
        filepath (str): 저장할 파일 경로
        data (dict): 저장할 JSON 데이터
    """
    temp_file = f"{filepath}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(temp_file, filepath)
    except Exception as e:
        logging.error(f"JSON 파일 저장 실패 ({filepath}): {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

def v_space(height=10):
    """수직 여백(간격)을 추가합니다."""
    st.markdown(f"<div style='height: {height}px;'></div>", unsafe_allow_html=True)

def responsive_text(text, pc_size="28px", mobile_size="18px", font_weight="bold", color="inherit"):
    """PC와 모바일에서 글자 크기가 자동으로 변하는 반응형 텍스트를 출력합니다."""
    class_name = f"resp-text-{pc_size}-{mobile_size}".replace("px", "").replace(" ", "")
    completed_css = config.css_responsive_text.format(
        class_name=class_name, pc_size=pc_size, font_weight=font_weight,
        color=color, mobile_size=mobile_size
    )
    st.markdown(completed_css, unsafe_allow_html=True)
    st.markdown(f'<div class="{class_name}">{text}</div>', unsafe_allow_html=True)

# =====================================================================
# 🌟 [추가] 일반 사용자(뷰어) 세션 관리 함수
# =====================================================================
def clean_and_get_viewers(room_name):
    """만료된 세션(5분 이상 응답 없음)을 정리하고 현재 접속자 목록 반환"""
    if not os.path.exists(VIEWER_FILE): return {}
    try:
        with open(VIEWER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return {}

    now = time.time()
    room_viewers = data.get(room_name, {})
    # 5분(300초) 이내에 활동한 사용자만 유지
    active_viewers = {sid: t for sid, t in room_viewers.items() if now - t < 300}

    data[room_name] = active_viewers
    atomic_write_json(VIEWER_FILE, data)
    return active_viewers

def update_viewer_session(room_name, session_id):
    """일반 사용자 하트비트 업데이트 (강퇴당했으면 False 반환)"""
    if not os.path.exists(VIEWER_FILE):
        data = {}
    else:
        try:
            with open(VIEWER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}

    room_viewers = data.get(room_name, {})

    # 세션이 없으면 (관리자가 강퇴했거나 최초 접속 시 정원 초과)
    if session_id not in room_viewers and len(room_viewers) >= MAX_VIEWERS:
        return False

    room_viewers[session_id] = time.time()
    data[room_name] = room_viewers
    atomic_write_json(VIEWER_FILE, data)
    return True

def kick_all_viewers(room_name):
    """관리자가 해당 방의 모든 일반 사용자를 강제 퇴출"""
    if os.path.exists(VIEWER_FILE):
        try:
            with open(VIEWER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if room_name in data:
                data[room_name] = {}  # 해당 방 접속자 초기화
                atomic_write_json(VIEWER_FILE, data)
        except:
            pass
# =====================================================================
# [3단계] 데이터베이스 및 템플릿 설정(Setup) 함수
# =====================================================================
# 구글 시트 연결 객체 생성
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_room_list():
    """마스터 구글 시트에서 생성된 방(리그) 목록을 불러오는 함수 (10분간 캐싱하여 속도 향상)"""
    try:
        # SHEET_URL은 전역 변수(st.secrets에서 불러온 값)를 사용합니다.
        db_df = conn.read(spreadsheet=SHEET_URL, worksheet="시트1", ttl=0)
        room_list = db_df['방이름'].tolist() if not db_df.empty else []
        logging.info("마스터 DB 로드 성공")
        return db_df, room_list

    except Exception as e:
        st.error("마스터 DB 연결 실패. 잠시 후 다시 시도해주세요.")
        logging.error(f"마스터 DB 연결 실패: {e}")  # 🌟 [운영성 개선] 상세 에러는 로그로만
        return pd.DataFrame(), []

def get_current_room_sheet_url(target_room):
    """
    특정 방(target_room)의 개별 구글 시트 URL을 찾는 함수
    💡 [수정됨] db_df를 매개변수로 받도록 수정하여 NameError를 방지했습니다.
    """
    try:
        # 캐싱된 load_room_list()를 호출하여 db_df를 가져옵니다.
        # 🌟 [개선] 함수 호출 대신, 이미 로드된 전역 세션 데이터를 사용 (속도 극대화)
        db_df = st.session_state.db_df
        url = db_df.loc[db_df['방이름'] == target_room, '시트URL'].values[0]
        return url
    except Exception as e:
        logging.error(f"방 URL 찾기 실패 ({target_room}): {e}")
        return None

def get_available_url(db_df):
    """미리 생성해둔 구글 시트 URL(PRE_MADE_URLS) 중 아직 사용되지 않은 빈 URL을 찾는 함수"""
    # db_df, _ = load_room_list()
    used_urls = db_df['시트URL'].dropna().tolist() if not db_df.empty else []
    # print(PRE_MADE_URLS,"\n",used_urls)
    for url in PRE_MADE_URLS:
        if url not in used_urls:
            return url
    return None

# 3. 데이터 로드 및 템플릿 생성 (Data & Templates)
# 파일 입출력, 더미 데이터 생성, 빈 양식(템플릿)을 만드는 함수들입니다.

def get_sheet_template(sheet_type):
    """선택한 시트 종류에 맞는 빈 컬럼 구조를 반환합니다. (config.py의 컬럼명 사용)"""
    if sheet_type == "선수명단":
        return pd.DataFrame({col: [] for col in config.COL_PLAYER_LIST})
    elif sheet_type == "누적전적":
        return pd.DataFrame({col: [] for col in config.COL_CUMULATIVE})
    elif sheet_type == "상대전적":
        return pd.DataFrame({col: [] for col in config.COL_H2H})
    return pd.DataFrame()

def generate_dummy_data():
    """테스트용 더미 데이터를 생성하여 반환하는 공통 함수 (매 호출마다 새로운 랜덤값 생성)"""
    return [
        {
            "순서": i,
            "이름": f"회원{i}",
            "참석예정": random.choice(["Y", "N"]),
            "성별": random.choice(["남", "여"]),
            "부수": f"{random.randint(1, 13)}부",
            "부수_조정": 0,
            "직책": "",
            "조편성_신청": f"{random.randint(1, 10)}조"
        } for i in range(1, 11)
    ]

def initialize_default_sheets(target_url, room_name):
    """빈 구글 시트에 3개의 기본 탭을 생성하고 초기화하는 함수"""
    try:
        gc = gspread.service_account_from_dict(st.secrets["connections"]["gsheets"])
        sh = gc.open_by_url(target_url)
        sh.update_title(f"{room_name}_DB")  # 이름 자동 변경

        existing_sheets = [ws.title for ws in sh.worksheets()]

        # 시트 생성
        for sheet_name in ["선수명단", "누적전적", "상대전적"]:
            if sheet_name not in existing_sheets:
                sh.add_worksheet(title=sheet_name, rows="1000", cols="20")
            # 기본 템플릿 데이터 덮어쓰기
            empty_df = get_sheet_template(sheet_name)
            conn.update(spreadsheet=target_url, worksheet=sheet_name, data=empty_df)

        # 불필요한 기본 시트 삭제
        for ws_name in ["시트1", "Sheet1"]:
            if ws_name in existing_sheets and len(sh.worksheets()) > 1:
                sh.del_worksheet(sh.worksheet(ws_name))

        return True
    except Exception as e:
        st.error("시트 초기화 중 오류가 발생했습니다.")
        logging.error(f"시트 초기화 중 오류 발생 ({room_name}): {e}")
        return False

# =====================================================================
# [수정 포인트 1] Caching 적용: 무거운 엑셀 생성 작업을 캐싱하여 속도 향상
# =====================================================================
@st.cache_data
def generate_excel_template():
    """선수명단(더미데이터 포함), 누적전적, 상대전적 시트가 포함된 엑셀 템플릿 파일을 메모리에 생성"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 공통 함수를 호출하여 더미 데이터 생성
        df_dummy_players = pd.DataFrame(generate_dummy_data())

        # 엑셀 시트에 각각 저장
        df_dummy_players.to_excel(writer, sheet_name="선수명단", index=False)
        get_sheet_template("누적전적").to_excel(writer, sheet_name="누적전적", index=False)
        get_sheet_template("상대전적").to_excel(writer, sheet_name="상대전적", index=False)

    return output.getvalue()

def load_data(uploaded_file=None):
    """회원 명단 CSV/Excel 파일을 불러옵니다. 파일이 없으면 더미 데이터를 반환합니다."""
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            return pd.read_csv(uploaded_file, encoding='cp949')

    # 파일이 없으면 공통 함수를 호출하여 더미 데이터 반환
    return pd.DataFrame(generate_dummy_data())

# 파일 기반 저장 구조 함수 정의
HISTORY_FILE = "league_history.json"
ROOM_STATES_FILE = "room_states.json"  # 🌟 [추가] 진행 중인 방 상태를 저장할 파일

# =====================================================================
# [4단계] 핵심 비즈니스 로직 (상태 관리 및 전적 계산)
# =====================================================================
def save_room_state(room_name):
    """🌟 [추가] 현재 방의 진행 상황(세션)을 JSON 파일에 임시 저장합니다."""
    data = {}
    if os.path.exists(ROOM_STATES_FILE):
        try:
            with open(ROOM_STATES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.warning(f"기존 상태 파일 읽기 실패, 새로 생성합니다: {e}")

    # 현재 세션의 핵심 데이터만 추출
    room_data = {
        "config_confirmed": st.session_state.get("config_confirmed", False),
        "attendance_confirmed": st.session_state.get("attendance_confirmed", False),
        # 🌟 [추가] 현재 몇 차전인지도 저장합니다.
        "game_round": st.session_state.get("game_round", 1),
        "config": st.session_state.get("config", {}),
        "labels": st.session_state.get("labels", []),
        "teams": st.session_state.get("teams", {}),
        "draw_results": st.session_state.get("draw_results", {}),
        "draw_completed": st.session_state.get("draw_completed", False),
        "draw_level": st.session_state.get("draw_level", 0),
        "matrix": st.session_state.matrix.to_json(
            orient="split") if "matrix" in st.session_state and st.session_state.matrix is not None else None,
        "ind_matrix": st.session_state.ind_matrix.to_json(
            orient="split") if "ind_matrix" in st.session_state and st.session_state.ind_matrix is not None else None
    }
    data[room_name] = room_data
    atomic_write_json(ROOM_STATES_FILE, data)  # 🌟 원자적 쓰기 함수 호출

def load_room_state(room_name):
    """🌟 [추가] 방 이름으로 저장된 진행 상황을 불러와 세션에 복구합니다."""
    if not os.path.exists(ROOM_STATES_FILE): return False
    try:
        with open(ROOM_STATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"상태 파일 로드 실패: {e}")
        return False

    if room_name in data:
        room_data = data[room_name]
        st.session_state.config_confirmed = room_data.get("config_confirmed", False)
        st.session_state.attendance_confirmed = room_data.get("attendance_confirmed", False)
        # 🌟 [추가] 저장된 회차를 불러옵니다. 없으면 1차전으로 세팅.
        st.session_state.game_round = room_data.get("game_round", 1)

        if room_data.get("config"):
            st.session_state.config = room_data["config"]

        if room_data.get("labels"): st.session_state.labels = room_data["labels"]
        if room_data.get("teams"):
            # JSON은 딕셔너리 키를 문자열로 바꾸므로, 다시 정수(int)로 변환
            st.session_state.teams = {int(k): v for k, v in room_data["teams"].items()}
        if room_data.get("draw_results"): st.session_state.draw_results = room_data["draw_results"]

        st.session_state.draw_completed = room_data.get("draw_completed", False)
        st.session_state.draw_level = room_data.get("draw_level", 0)

        # 🌟 [수정된 부분] DataFrame을 불러올 때 인덱스와 컬럼을 명확히 문자열(str)로 고정합니다.
        if room_data.get("matrix"):
            df_m = pd.read_json(StringIO(room_data["matrix"]), orient="split")
            df_m.index = df_m.index.astype(str)
            df_m.columns = df_m.columns.astype(str)
            st.session_state.matrix = df_m

        if room_data.get("ind_matrix"):
            df_ind = pd.read_json(StringIO(room_data["ind_matrix"]), orient="split")
            df_ind.index = df_ind.index.astype(str)
            df_ind.columns = df_ind.columns.astype(str)
            st.session_state.ind_matrix = df_ind
        return True
    return False

def save_league_history(key_name, labels, matrix_df, ind_matrix_df, config):
    """현재 리그 데이터를 로컬 JSON 파일에 저장합니다."""
    data = {}
    # 기존 저장된 데이터 로드
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.warning(f"히스토리 파일 읽기 실패: {e}")

    # 데이터프레임을 JSON 저장 가능한 dict 구조로 변환
    data[key_name] = {
        "saved_at": str(datetime.now()),
        "labels": list(labels),
        "matrix": matrix_df.to_json(orient="split"),
        "ind_matrix": ind_matrix_df.to_json(orient="split") if ind_matrix_df is not None else None,
        "config": config
    }

    atomic_write_json(HISTORY_FILE, data)  # 🌟 원자적 쓰기 함수 호출

def get_history_keys():
    """저장된 전체 리그 목록을 가져옵니다."""

    if not os.path.exists(HISTORY_FILE): return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return list(data.keys())
    except Exception as e:
        logging.error(f"히스토리 키 로드 실패: {e}")
        return []

def load_league_history(key_name):
    """선택한 리그 데이터를 JSON 파일에서 불러와 세션 상태에 반영합니다."""
    # HISTORY_FILE 변수는 전역에 정의되어 있다고 가정합니다.

    if not os.path.exists(HISTORY_FILE): return False
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"히스토리 로드 실패: {e}")
        return False

    if key_name in data:
        target = data[key_name]
        st.session_state.labels = target["labels"]

        # StringIO를 사용하여 문자열을 파일 객체처럼 다룸으로써 FileNotFoundError 원천 차단
        st.session_state.matrix = pd.read_json(StringIO(target["matrix"]), orient="split")

        if target.get("ind_matrix") is not None:
            st.session_state.ind_matrix = pd.read_json(StringIO(target["ind_matrix"]), orient="split")

        st.session_state.config = target["config"]
        return True
    return False

# 4. 핵심 비즈니스 로직 (Core Business Logic)
# 경기 결과를 바탕으로 전적을 계산하고 업데이트하는 핵심 로직입니다.
def update_cumulative_record(p_a, p_b, s_a, s_b):
    """
    경기가 끝날 때마다 선수들의 누적 전적과 상대 전적을 업데이트합니다.
    Args:
        p_a (str): A 선수 이름
        p_b (str): B 선수 이름
        s_a (int): A 선수 점수
        s_b (int): B 선수 점수
    """
    if 'cum_df' not in st.session_state:
        st.session_state.cum_df = get_sheet_template("누적전적")

    df_cum = st.session_state.cum_df
    room = st.session_state.get('room_name', config.DEFAULT_ROOM_NAME)

    def ensure_player(df, name):
        """명단에 없는 새로운 선수면 데이터프레임에 0전 0승 0패로 새로 추가"""
        for col in config.COL_CUMULATIVE:
            if col not in df.columns:
                df[col] = 0 if col in ['총경기수', '승', '패', '득점', '실점'] else None

        mask = (df['이름'] == name) & (df['방이름'] == room)
        if not df[mask].any().any():
            new_row = pd.DataFrame([{
                '방이름': room, '이름': name,
                '총경기수': 0, '승': 0, '패': 0, '득점': 0, '실점': 0
            }])
            df = pd.concat([df, new_row], ignore_index=True)
        return df

    # "선택안함"이 아닌 실제 선수일 경우에만 명단에 추가
    if p_a != config.MSG_NO_SELECTION: df_cum = ensure_player(df_cum, p_a)
    if p_b != config.MSG_NO_SELECTION: df_cum = ensure_player(df_cum, p_b)

    # 2. 개인 성적 업데이트 로직
    for p, win, lose, score, opp_score in [(p_a, s_a > s_b, s_a < s_b, s_a, s_b),
                                           (p_b, s_b > s_a, s_b < s_a, s_b, s_a)]:
        if p != config.MSG_NO_SELECTION:
            mask = (df_cum['이름'] == p) & (df_cum['방이름'] == room)
            idx_list = df_cum[mask].index
            if not idx_list.empty:
                idx = idx_list[0]
                df_cum.at[idx, '총경기수'] += 1
                df_cum.at[idx, '승'] += 1 if win else 0
                df_cum.at[idx, '패'] += 1 if lose else 0
                df_cum.at[idx, '득점'] += score
                df_cum.at[idx, '실점'] += opp_score

    st.session_state.cum_df = df_cum

    # 3. 상대 전적(Head to Head) 업데이트
    if p_a != config.MSG_NO_SELECTION and p_b != config.MSG_NO_SELECTION:
        if 'h2h_df' not in st.session_state:
            st.session_state.h2h_df = get_sheet_template("상대전적")

        h2h = st.session_state.h2h_df

        for col in config.COL_H2H:
            if col not in h2h.columns:
                h2h[col] = 0 if 'Win' in col or 'Score' in col else None

        # A vs B 와 B vs A 가 따로 기록되는 것을 막기 위해 이름을 가나다순 정렬
        p1, p2 = sorted([p_a, p_b])
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2) & (h2h['방이름'] == room)

        if not mask.any():
            new_row = pd.DataFrame([{
                '방이름': room, 'Player1': p1, 'Player2': p2,
                'P1_Win': 0, 'P2_Win': 0, 'P1_Score': 0, 'P2_Score': 0
            }])
            h2h = pd.concat([h2h, new_row], ignore_index=True)
            mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2) & (h2h['방이름'] == room)

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

@st.dialog("📊 역대 누적 상대 전적")
def show_h2h_dialog(player_a, player_b):
    """두 선수를 선택했을 때 팝업창으로 역대 전적을 보여주는 함수"""
    p1, p2 = sorted([player_a, player_b])
    h2h = st.session_state.get('h2h_df', pd.DataFrame())

    if not h2h.empty and 'Player1' in h2h.columns and 'Player2' in h2h.columns:
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
            if st.button(config.BTN_CLOSE, width='stretch'): st.rerun()
            return

    st.warning(config.MSG_NO_H2H_RECORD)
    if st.button(config.BTN_CLOSE, width='stretch'): st.rerun()

# =====================================================================
# [수정 포인트 2] Fragment 적용: 출석체크 화면 부분 재실행
# =====================================================================
@st.fragment
def render_attendance_tab(df, col_date, is_admin, live_names):
    """출석 체크 UI만 독립적으로 실행되도록 Fragment를 적용합니다."""
    target_date_col = col_date if col_date in df.columns else '참석예정'
    df['참석'] = df[target_date_col].apply(lambda x: True if str(x).upper() in ['Y', '예', '참석'] else False)
    display_cols = [c for c in ['순서', '이름', '참석', '부수'] if c in df.columns]
    mid_idx = len(df) // 2 + (len(df) % 2)

    col1, col2 = st.columns(2)
    with col1:
        edited_left = st.data_editor(df.iloc[:mid_idx][display_cols], hide_index=True, disabled=not is_admin,
                                     key="editor_left", width='stretch')
    with col2:
        edited_right = st.data_editor(df.iloc[mid_idx:][display_cols], hide_index=True, disabled=not is_admin,
                                      key="editor_right", width='stretch')

    edited_df = pd.concat([edited_left, edited_right], ignore_index=True)
    current_checked = edited_df[edited_df['참석'] == True]
    live_names = ", ".join(sorted(current_checked['이름'].tolist()))
    st.info(f"**현재 참석 ({len(current_checked)}명):** \n\n {live_names if live_names else '없음'}")

    if is_admin:
        btn_label = "확정 완료 (참석자 저장됨)" if st.session_state.attendance_confirmed else "참석자 확정하기"
        btn_type = "primary" if st.session_state.attendance_confirmed else "secondary"

        if st.button(btn_label, type=btn_type, width='stretch'):
            st.session_state.main_df[col_date] = edited_df['참석'].apply(lambda x: 'Y' if x else 'N')
            st.session_state.attendance_confirmed = True
            st.session_state.show_success_msg = f" 오늘의 참석자 명단이 시스템에 기록되었습니다.!"
            st.rerun()  # 확정 시에는 전체 화면 갱신

# =====================================================================
# [수정 포인트 3] Fragment 적용: 제비뽑기 화면 부분 재실행
# =====================================================================
@st.fragment
def render_draw_process(cfg, sorted_members, total_levels, draw_level):
    """제비뽑기 조 선택 시 전체 코드가 재실행되지 않도록 Fragment를 적용합니다."""
    for level in range(total_levels):
        start_idx = level * cfg['g']
        end_idx = min((level + 1) * cfg['g'], len(sorted_members))
        current_group = sorted_members.iloc[start_idx:end_idx]
        group_members = current_group['이름'].tolist()

        responsive_text(f"📋 그룹 {level + 1}", pc_size="20px", mobile_size="16px")
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
                st.session_state[state_key] = {name: available_options[i] for i, name in enumerate(group_members)}
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
                    st.selectbox("조 선택", options=available_options, index=available_options.index(current_val),
                                 key=f"select_{level}_{name}", on_change=on_selection_change,
                                 args=(name, level), label_visibility="collapsed",
                                 disabled=not st.session_state.is_admin)
            st.write("")

            if st.session_state.is_admin:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button(f" 그룹 {level + 1} 랜덤 배정"):
                        shuffled_options = available_options[:len(group_members)]
                        random.shuffle(shuffled_options)
                        for i, name in enumerate(group_members):
                            st.session_state.draw_results[name] = shuffled_options[i]
                        st.session_state.draw_level += 1
                        save_room_state(st.session_state.room_name)
                        # st.rerun()
                with btn_col2:
                    if st.button(f" 그룹 {level + 1} 제비뽑기 완료 및 다음 진행", type="primary", width="stretch"):
                        for name in group_members:
                            st.session_state.draw_results[name] = st.session_state[f"select_{level}_{name}"]
                        st.session_state.draw_level += 1
                        save_room_state(st.session_state.room_name)
                        # st.rerun()
        else:
            for i, (idx, row) in enumerate(current_group.iterrows()):
                with cols[i % cfg['g']]:
                    st.markdown(
                        f"<div style='color:#999; padding:10px; border:1px dashed #ccc; border-radius:5px;'> {row['이름']} ({row['부수']}) - 대기중</div>",
                        unsafe_allow_html=True)
        st.divider()

    if draw_level >= total_levels:
        st.session_state.draw_completed = True
        st.rerun()

# 6. 세션 초기화 (Session State Initialization)
# 앱이 처음 실행될 때 필요한 기본 변수들을 세션에 저장합니다.
# ---------------------------------------------------------------------
# 기본 데이터 로드 및 세션 동기화
# ---------------------------------------------------------------------
if 'main_df' not in st.session_state:
    st.session_state.main_df = get_sheet_template("선수명단")
if 'cum_df' not in st.session_state:
    st.session_state.cum_df = get_sheet_template("누적전적")
if 'h2h_df' not in st.session_state:
    st.session_state.h2h_df = get_sheet_template("상대전적")

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# 🟢 메인 로직 시작
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# 개선: 세션에 없거나 비어있을 때만 최초 1회 로드 (또는 명시적 새로고침 시)
if "db_df" not in st.session_state or "room_list" not in st.session_state:
    st.session_state.db_df, st.session_state.room_list = load_room_list()

# 이후 코드에서는 함수를 부르지 않고 세션 데이터를 변수에 담아 사용
db_df = st.session_state.db_df
room_list = st.session_state.room_list

# 🌟 [추가할 부분] 성공 메시지가 세션에 남아있다면 토스트(Toast)로 띄우고 즉시 삭제합니다.
if "show_success_msg" in st.session_state:
    st.toast(st.session_state.show_success_msg, icon="✅")
    del st.session_state.show_success_msg

is_admin = st.session_state.is_admin
room_name = st.session_state.room_name

# 🌟 [수정 1] 새로고침(F5) 대비 Auto-Load 추가
# 관리자로 로그인된 상태인데 세션 데이터(config 등)가 날아갔다면 즉시 복구합니다.
if is_admin and room_name:
    if "config" not in st.session_state or st.session_state.get("matrix") is None:
        load_room_state(room_name)

# ---------------------------------------------------------------------
# 비로그인 상태 (구장 접속 및 생성 화면)
# ---------------------------------------------------------------------
# 🌟 [수정] 관리자도 아니고 일반 사용자도 아닐 때만 로그인 화면 노출
if not is_admin and not st.session_state.get('is_viewer'):

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
                else:
                    # 🌟 [추가] db_df가 비어있거나 '방이름' 컬럼이 없는 경우의 방어 로직
                    if db_df.empty or '방이름' not in db_df.columns:
                        st.sidebar.error("❌ 데이터베이스 연결 오류 또는 '방이름' 컬럼이 없습니다.")
                    elif login_room_name in db_df['방이름'].values:
                        saved_pw = db_df.loc[db_df['방이름'] == login_room_name, '비밀번호'].values[0]
                        if hashed_pw == saved_pw:
                            is_valid_admin = True
                            st.sidebar.success(f"✅ '{login_room_name}' 관리자 모드 활성화")
                        else:
                            st.sidebar.error("❌ 비밀번호가 틀렸습니다.")
                    else:
                        st.sidebar.error("❌ 존재하지 않는 구장입니다.")
            else:
                # 🌟 [수정] 비밀번호가 없으면 일반 사용자(뷰어)로 접속 시도
                active_viewers = clean_and_get_viewers(login_room_name)
                if len(active_viewers) >= MAX_VIEWERS:
                    st.sidebar.error(f"❌ 현재 접속자가 많아 입장할 수 없습니다. (최대 {MAX_VIEWERS}명)")
                    st.stop()
                else:
                    st.session_state.is_viewer = True
                    st.session_state.viewer_id = str(uuid.uuid4())
                    update_viewer_session(login_room_name, st.session_state.viewer_id)
                    st.sidebar.success("👁️ 일반 사용자 모드로 접속 중입니다.")

            # 관리자이거나 일반 사용자 접속에 성공한 경우 데이터 로드
            if is_valid_admin or st.session_state.get('is_viewer'):
                if is_valid_admin: st.session_state.is_admin = True

                for k in config.keys_to_clear_tab_login:
                    if k in st.session_state: del st.session_state[k]

                cookies["last_room"] = login_room_name
                cookies.save()

                target_url = get_current_room_sheet_url(login_room_name)

                # 🌟 [추가] 로그인 성공 시 이전 진행 상황 불러오기
                if load_room_state(login_room_name):
                    st.sidebar.success("📂 이전 진행 상황을 성공적으로 불러왔습니다!")
                else:
                    st.sidebar.info("새로운 세션입니다. 설정을 시작해주세요.")

                if target_url:
                    try:
                        # 해당 구장 전용 시트에서 데이터 로드
                        st.session_state.main_df = conn.read(spreadsheet=target_url, worksheet="선수명단", ttl=0)
                        st.session_state.cum_df = conn.read(spreadsheet=target_url, worksheet="누적전적", ttl=0)
                        st.session_state.h2h_df = conn.read(spreadsheet=target_url, worksheet="상대전적", ttl=0)

                    except Exception as e:
                        # 🔥 [수정 포인트 1] 기존 구장 접속 시 시트가 없으면 강제로 3개의 시트를 생성합니다.
                        st.sidebar.warning("⚠️ 전용 시트가 없거나 비어있습니다. 3개의 시트를 새로 생성합니다.")
                        logging.error(f"시트 로드 실패, 초기화 진행 ({login_room_name}): {e}")
                        # 함수 호출 (login_room_name을 넘겨주어 버그 해결)
                        initialize_default_sheets(target_url, login_room_name)

                        # 세션 상태에는 빈 템플릿을 즉시 할당
                        st.session_state.main_df = get_sheet_template("선수명단")
                        st.session_state.cum_df = get_sheet_template("누적전적")

                st.rerun()

    # ------------------------------------------
    # ➕ 2. 새 구장 만들기
    # ------------------------------------------
    with tab_create:
        st.markdown("#### ✨ 새로운 구장 등록")

        with st.form(key="create_room_form"):
            new_room_name = st.text_input(" 구장명 (중복 불가)")
            admin_name = st.text_input("관리자 이름 (대표자명)")
            # admin_email = st.text_input("관리자 이메일 (비밀번호 분실 시 필요)")
            admin_email = st.text_input("관리자 이메일 ")
            new_room_pw = st.text_input("새 구장 비밀번호 설정", type="password")
            new_room_sheet_url = st.text_input("구장 구글 시트 URL (전용)")

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

                    # 1. 함수 캐시 삭제
                    load_room_list.clear()

                    # 🌟 [개선] 2. 세션 데이터 강제 삭제 (다음 rerun 시 최상단에서 최신 DB를 다시 불러오도록 유도)
                    if "db_df" in st.session_state:
                        del st.session_state["db_df"]
                    if "room_list" in st.session_state:
                        del st.session_state["room_list"]

                    st.session_state.room_name = new_room_name
                    st.session_state.is_admin = True
                    cookies["last_room"] = new_room_name
                    cookies.save()

                    with st.spinner("데이터베이스를 초기화 중입니다... (약 5\~10초 소요)"):
                        # 🔥 [개선됨] 유틸리티 함수 호출로 대체
                        initialize_default_sheets(assigned_url, new_room_name)

                        # 세션 상태에는 빈 템플릿을 즉시 할당
                        st.session_state.main_df = get_sheet_template("선수명단")
                        st.session_state.cum_df = get_sheet_template("누적전적")
                        st.session_state.h2h_df = get_sheet_template("상대전적")

                    # 수정 후 (sleep 제거, 즉시 전환)
                    logging.info(f"새 구장 생성 완료: {new_room_name}")
                    st.session_state.show_success_msg = f" '{new_room_name}' 구장이 생성되었습니다!"
                    st.rerun()

                except Exception as e:
                    st.error("DB 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
                    logging.error(f"새 구장 DB 저장 실패: {e}")

# ---------------------------------------------------------------------
# 로그인 상태 (관리자 모드 및 메인 화면)
# ---------------------------------------------------------------------
else:
    # 🌟 [추가] 일반 사용자 하트비트 및 강퇴 체크
    if st.session_state.get('is_viewer'):
        is_active = update_viewer_session(room_name, st.session_state.viewer_id)
        if not is_active:
            st.session_state.is_viewer = False
            st.session_state.viewer_id = None
            st.warning("🚨 관리자에 의해 강제 퇴출되었거나 세션이 만료되었습니다.")
            time.sleep(2)
            st.rerun()

    # 사이드바 구성
    st.sidebar.markdown(f"### 🏟️ {room_name} 구장")

    if is_admin:
        st.sidebar.success("👑 관리자 모드로 접속 중입니다.")

        # 🌟 [추가] 관리자용 접속자 모니터링 및 강퇴 기능
        st.sidebar.divider()
        st.sidebar.markdown("#### 👥 일반 접속자 관리")
        active_viewers = clean_and_get_viewers(room_name)
        st.sidebar.info(f"현재 일반 접속자: <strong>{len(active_viewers)}명</strong> / 최대 {MAX_VIEWERS}명")

        if st.sidebar.button("🚨 전체 일반 사용자 강제 퇴출", type="primary", width='stretch'):
            kick_all_viewers(room_name)
            st.sidebar.success("모든 일반 사용자를 퇴출했습니다.")
            st.rerun()
    else:
        st.sidebar.info("👁️ 일반 사용자 모드 (조회 전용)")

    if st.sidebar.button("🔒 로그아웃", width='stretch'):
        for k in config.keys_to_clear_is_admin:
            if k in st.session_state: del st.session_state[k]

        st.session_state.is_admin = False
        st.session_state.is_viewer = False  # 🌟 뷰어 상태도 초기화
        logging.info(f"관리자 로그아웃: {room_name}")
        st.rerun()

    st.sidebar.divider()

    # =====================================================================
    # [1단계] 사이드바: 관리자 전용 기능 (클라우드, 초기화, 데이터 관리)
    # =====================================================================
    if is_admin:
        st.sidebar.markdown("#### ☁️ 클라우드 동기화")

        # 1-1. 구글 시트 수동 저장
        if st.sidebar.button("💾 오늘의 최종 결과 구글시트 저장", type="primary", width='stretch'):
            if "room_name" in st.session_state and st.session_state.room_name:
                with st.spinner("해당 구장 전용 시트에 저장 중..."):
                    try:
                        target_sheet_url = get_current_room_sheet_url(st.session_state.room_name)

                        if target_sheet_url:
                            # 🌟 [기능성 및 성능 개선] 네트워크 오류 대비 예외 처리 강화
                            conn.update(spreadsheet=target_sheet_url, worksheet="선수명단", data=st.session_state.main_df)
                            conn.update(spreadsheet=target_sheet_url, worksheet="누적전적", data=st.session_state.cum_df)
                            conn.update(spreadsheet=target_sheet_url, worksheet="상대전적", data=st.session_state.h2h_df)
                            st.sidebar.success(f"✅ {st.session_state.room_name} 전용 시트 저장 완료!")
                            logging.info(f"구글 시트 수동 저장 완료: {st.session_state.room_name}")
                        else:
                            st.sidebar.error("❌ 이 구장의 전용 시트 URL을 찾을 수 없습니다. (마스터 DB 확인 필요)")
                    except Exception as e:
                        st.sidebar.error("❌ 저장 실패: 네트워크 상태를 확인해주세요.")
                        logging.error(f"구글 시트 수동 저장 실패 ({st.session_state.room_name}): {e}")
            else:
                st.sidebar.warning("⚠️ 접속된 구장 정보가 없습니다. 다시 로그인해 주세요.")

        st.sidebar.divider()

        # 1-2. 자동 새로고침 (전광판용)
        auto_refresh = st.sidebar.checkbox("자동 새로고침 켜기 (PC 전광판용)")
        if auto_refresh:
            st_autorefresh(interval=5 * 60 * 1000, limit=None, key="dashboard_refresh")
            st.sidebar.info("🟢 현재 5분마다 화면이 자동 갱신 중입니다. \n\n⚠️ 데이터 입력/수정 중에는 이 기능을 꺼주세요!")

        st.sidebar.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        # ==========================================
        # 🌟 [추가된 기능] 새로운 경기 시작 (New Game)
        # ==========================================
        with st.sidebar.expander("🔄 새로운 경기 시작 (New Game)", expanded=False):
            st.warning("⚠️ 현재 진행 중인 경기 결과(조 편성, 점수판 등)가 모두 초기화됩니다. \n\n(단, 누적 전적과 선수 명단 DB는 유지됩니다.)")

            # 이중 확인 장치 추가
            confirm_reset = st.checkbox("초기화에 동의합니다.")
            if confirm_reset:
                if st.button("🆕 새 경기 시작하기", type="primary", width='stretch'):
                    with st.spinner("기존 데이터를 초기화하고 최신 명단을 불러오는 중..."):
                        for k in config.keys_to_reset:
                            if k in st.session_state: del st.session_state[k]

                        # 2. 제비뽑기 진행 중 생성된 임시 변수들도 모두 삭제합니다.
                        for key in list(st.session_state.keys()):
                            if key.startswith("group_selections_") or key.startswith("select_") or key.startswith("m"):
                                del st.session_state[key]

                        # 🌟 [핵심 추가] 3. 다음 회차로 넘어가기 (1차전 -> 2차전)
                        st.session_state.game_round += 1

                        # 🌟 [추가된 핵심 로직] 3. 구글 시트에서 최신 DB(선수명단, 전적) 다시 불러오기
                        target_url = get_current_room_sheet_url(st.session_state.room_name)

                        if target_url:
                            try:
                                st.session_state.main_df = conn.read(spreadsheet=target_url, worksheet="선수명단", ttl=0)
                                st.session_state.cum_df = conn.read(spreadsheet=target_url, worksheet="누적전적", ttl=0)
                                st.session_state.h2h_df = conn.read(spreadsheet=target_url, worksheet="상대전적", ttl=0)
                                st.toast("✅ 최신 구글 시트 데이터를 성공적으로 불러왔습니다!", icon="🔄")
                            except Exception as e:
                                st.error("구글 시트 데이터를 불러오는 중 오류가 발생했습니다.")
                                logging.error(f"새 경기 시작 중 시트 로드 실패: {e}")
                        else:
                            st.toast("⚠️ 연결된 구글 시트 URL이 없어 기존 로컬 명단이 유지됩니다.", icon="⚠️")

                        # 3. 초기화된 상태를 파일에 덮어써서 저장합니다.
                        save_room_state(st.session_state.room_name)

                        # 알림 메시지에 몇 차전인지 표시
                        st.session_state.show_success_msg = f"✨ 초기화 완료! {st.session_state.game_round}차전 세팅을 진행해 주세요."
                        logging.info(f"새 경기 시작 ({st.session_state.game_round}차전): {st.session_state.room_name}")
                        st.rerun()

        st.sidebar.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        # 데이터 관리 (최초 세팅 및 동기화)
        with st.sidebar.expander("⚙️ 데이터 관리", expanded=False):
            # 🌟 [핵심 수정 포인트] 현재 선수명단에 데이터가 있는지 확인 (초기 세팅 여부 자동 판단)
            # 데이터가 없거나 비어있으면 True (최초 상태)
            is_initial_setup = st.session_state.main_df.empty or len(st.session_state.main_df) == 0

            if is_initial_setup:
                # ---------------------------------------------------
                # [최초 세팅] 데이터가 없을 때만 파일 업로드 화면 표시
                # ---------------------------------------------------
                st.warning("⚠️ 현재 등록된 선수 데이터가 없습니다.\n최초 1회 파일을 업로드하여 구장을 세팅해주세요.")

                st.markdown("**1. 양식 다운로드 및 작성**")
                st.caption("아래 버튼을 눌러 빈 엑셀 양식을 다운로드하고, PC나 스마트폰에서 내용을 채워주세요.")

                excel_data = generate_excel_template()

                st.download_button(
                    label="📥 표준 엑셀 템플릿 다운로드",
                    data=excel_data,
                    file_name=f"{st.session_state.room_name}_db.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )

                st.markdown("**2. 작성된 파일 업로드 (Excel or CSV)**")
                uploaded_file = st.file_uploader("파일 선택 (.xlsx, .csv)", type=['xlsx', 'xls', 'csv'])

                if uploaded_file:
                    if st.button("파일 데이터 적용 및 클라우드 저장", type="primary", width='stretch'):
                        try:
                            with st.spinner("파일을 읽고 클라우드에 저장하는 중..."):
                                file_ext = uploaded_file.name.split('.')[-1].lower()
                                xls_data = {}

                                # CSV 파일일 경우 여러 인코딩을 순회하며 에러 없이 읽어들임
                                if file_ext == 'csv':
                                    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin1']
                                    df_loaded = None
                                    for enc in encodings:
                                        try:
                                            uploaded_file.seek(0)
                                            df_loaded = pd.read_csv(uploaded_file, encoding=enc)
                                            break
                                        except:
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

                                # 엑셀 파일일 경우
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
                                            st.error("엑셀 파일 읽기 오류가 발생했습니다.")
                                            logging.error(f"엑셀 업로드 실패: {e}")
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

                                    # 구글 드라이브 상의 파일 이름 변경 로직
                                    try:
                                        new_file_name = uploaded_file.name.split('.')[0]
                                        credentials_dict = dict(st.secrets["connections"]["gsheets"])
                                        gc = gspread.service_account_from_dict(credentials_dict)
                                        spreadsheet = gc.open_by_url(target_url)
                                        spreadsheet.update_title(new_file_name)

                                        st.toast(f"✅ 데이터 저장 및 시트 이름 변경 완료!", icon="🎉")
                                    except Exception as title_e:
                                        st.toast(f"⚠️ 데이터는 저장되었으나 이름 변경 실패", icon="⚠️")
                                        logging.warning(f"시트 이름 변경 실패: {title_e}")
                                else:
                                    st.toast("✅ 데이터 적용 완료! (클라우드 URL 없음)", icon="✅")

                            # 대기 시간 없이 즉시 새로고침하여 메뉴 닫기
                            st.rerun()
                        except Exception as e:
                            st.error("파일 처리 중 오류가 발생했습니다.")
                            logging.error(f"파일 업로드 처리 중 오류: {e}")

            else:
                # ---------------------------------------------------
                # [일상 운영] 데이터가 이미 존재하면 '최신화' 버튼만 표시
                # ---------------------------------------------------
                st.success("✅ 구글 시트와 연동되어 운영 중입니다.")
                st.info("💡 선수 추가/수정은 구글 시트에서 직접 진행하신 후, 아래 버튼을 눌러 앱에 반영해주세요.")

                if st.button("☁️ 구글 시트 데이터 최신화", type="primary", width='stretch'):
                    with st.spinner("클라우드에서 최신 데이터를 가져오는 중..."):
                        target_url = get_current_room_sheet_url(st.session_state.room_name)

                        if target_url:
                            try:
                                st.session_state.main_df = conn.read(spreadsheet=target_url, worksheet="선수명단", ttl=0)
                                st.session_state.cum_df = conn.read(spreadsheet=target_url, worksheet="누적전적", ttl=0)
                                st.session_state.h2h_df = conn.read(spreadsheet=target_url, worksheet="상대전적", ttl=0)
                                st.toast("✅ 구글 시트 동기화 완료!", icon="🔄")
                                st.rerun()
                            except Exception as e:
                                st.error("동기화 중 오류가 발생했습니다.")
                                logging.error(f"수동 동기화 실패: {e}")
                        else:
                            st.error("URL을 찾을 수 없습니다.")

    # ---------------------------------------------------------------------
    # 메인 화면 데이터 처리 및 탭 구성
    # ---------------------------------------------------------------------
    selected_date = st.date_input("일자 선택", datetime.now(), disabled=not is_admin)
    CURRENT_DATE = selected_date.strftime('%Y-%m-%d')
    col_date = f"출석_{CURRENT_DATE}_{st.session_state.game_round}차전"

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

    # 🌟 [수정] 권한에 따라 노출되는 탭을 다르게 구성합니다.
    if is_admin:
        tabs = st.tabs([" 출석체크", " 운영 설정", " 조 편성 결과", " 경기 배정", " 스코어보드", "사용설명서", "경품추첨"])
        tab_home, tab_config, tab_team, tab_match, tab_score, tab_help, tab_raffle = tabs
    else:
        # 일반 사용자는 3개의 탭만 노출
        tabs = st.tabs([" 운영설정 결과", " 조 편성 결과", " 스코어보드"])
        tab_config, tab_team, tab_score = tabs
        tab_home = tab_match = tab_help = tab_raffle = None  # 에러 방지용 더미 변수

    # ==========================================
    # 탭 1: 출석체크 화면 구성
    # ==========================================
    if tab_home is not None:
        with tab_home:
            responsive_text(f"📋 {CURRENT_DATE}", pc_size="20px", mobile_size="16px")

            # 원본 데이터를 건드리지 않기 위해 복사본(copy)을 만듭니다.
            df = st.session_state.main_df.copy()

            # 2. [에러 방지] '순서' 컬럼이 없으면 자동으로 생성
            if '순서' not in df.columns:
                df.insert(0, '순서', range(1, len(df) + 1))

            # Fragment 호출 (이 안에서 일어나는 체크박스 클릭은 전체 코드를 재실행하지 않음)
            render_attendance_tab(df, col_date, is_admin, "")

            if is_admin:
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
        # 🌟 [추가된 핵심 로직] Fragment 밖에서도 참석자 명단을 알 수 있도록 DB(main_df)에서 직접 계산합니다.
        df_temp = st.session_state.main_df
        target_col = col_date if col_date in df_temp.columns else '참석예정'

        # 'Y', '예', '참석' 등으로 표시된 사람만 필터링
        attendees_df = df_temp[df_temp[target_col].astype(str).str.upper().isin(['Y', '예', '참석'])]
        attendees_count = len(attendees_df)
        live_names = ", ".join(sorted(attendees_df['이름'].tolist()))

        # 출석체크 탭에서 계산된 총 참석 인원을 파란색 정보창으로 띄워줍니다.
        st.info(f"👥 현재 확정된 참석 인원: **{attendees_count}명** \n\n {live_names if live_names else '없음'}")

        # 🌟 [수정 1] 세션에 저장된 config 데이터가 있는지 확인하고 가져옵니다.
        saved_cfg = st.session_state.get("config", {})

        # 🌟 [수정 포인트 4] Bypass 로직: 설정이 확정되었으면 입력창을 숨기고 경고창 띄움
        if st.session_state.config_confirmed:
            st.success("✅ 운영 설정 및 조 편성이 확정되었습니다. (수정 불가 상태)")

            # 🌟 [추가된 부분] 조당 인원수 계산 로직
            g_val_saved = saved_cfg.get('g', 4)
            if g_val_saved > 0:
                avg_saved = attendees_count // g_val_saved
                rem_saved = attendees_count % g_val_saved
                per_group_text = f"{avg_saved}~{avg_saved + 1}명" if rem_saved > 0 else f"{avg_saved}명"
            else:
                per_group_text = "-"

            st.markdown(f"""
                **[현재 설정 요약]**
                * 편성 조 수: {saved_cfg.get('g')}조 _ ** (조당 {per_group_text}) **
                * 경기 방식: 단식 {saved_cfg.get('s_games')} / 복식 {saved_cfg.get('d_games')} (선승: {saved_cfg.get('set_count')}세트)
                * 조 편성 방식: {saved_cfg.get('draw_method')}
                """)

            # [관리자 전용] 설정 잠금 해제 버튼
            if is_admin:
                st.warning("⚠️ 설정을 변경하면 현재 진행 중인 조 편성과 대진표가 모두 초기화됩니다.")
                if st.button("🔓 설정 잠금 해제 및 다시 하기", type="secondary"):
                    st.session_state.config_confirmed = False
                    st.session_state.teams_generated = False
                    st.rerun()

        # 설정이 확정되지 않은 경우 (입력 화면)
        else:
            if is_admin:
                # [관리자 전용] 설정 입력 폼
                st.markdown('<div class="setting-banner">', unsafe_allow_html=True)
                c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5])

                with c1:
                    responsive_text(f"👥 조 구성", pc_size="20px", mobile_size="16px")
                    default_g = saved_cfg.get("g", 4)
                    g_val = st.number_input("편성 조 수", min_value=1, max_value=20, value=default_g, disabled=not is_admin)

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
                    # 주석을 해제하여 변수가 정상적으로 할당되도록 수정
                    default_s_g = saved_cfg.get("s_games", 2)
                    default_d_g = saved_cfg.get("d_games", 1)
                    default_set_c = saved_cfg.get("set_count", 3)

                    s_g = st.number_input("단식 게임", min_value=0, max_value=10, value=default_s_g, disabled=not is_admin)
                    d_g = st.number_input("복식 게임", min_value=0, max_value=5, value=default_d_g, disabled=not is_admin)

                    set_options = [2, 3, 4, 5]
                    set_c = st.selectbox("개인전 선승 세트", options=set_options,
                                         index=set_options.index(saved_cfg.get("set_count", 3)) if saved_cfg.get(
                                             "set_count", 3) in set_options else 1)

                with c3:
                    responsive_text(f"⚙️ 환경 설정", pc_size="20px", mobile_size="16px")
                    # 🌟 [수정 4] 테이블 번호 이전 설정값 불러오기
                    default_t = saved_cfg.get("t", 3)
                    t_val = st.number_input("Table_No.", min_value=1, max_value=20, value=default_t, disabled=not is_admin)

                with c4:
                    responsive_text(f"🎲 방식", pc_size="20px", mobile_size="16px")
                    # 🌟 [수정 5] 조 편성 방식 이전 설정값 불러오기
                    default_draw = saved_cfg.get("draw_method", "AI 선정")
                    draw_options = ["AI 선정", "제비뽑기", "조편성_신청"]
                    draw_index = draw_options.index(default_draw) if default_draw in draw_options else 0

                    draw_method = st.radio("방식", options=draw_options, index=draw_index, label_visibility="collapsed",
                                           disabled=not is_admin)

                with c5:
                    responsive_text(f"✅ 실행", pc_size="20px", mobile_size="16px")
                    if st.button("설정 확정 및 편성 시작", type="primary", width='stretch'):
                        st.session_state.config = {
                            "g": g_val, "t": t_val, "s_games": s_g, "d_games": d_g, "set_count": set_c,
                            "total_g": s_g + d_g, "draw_method": draw_method,
                            "tie_breakers": {name: round(random.random(), 3) for name in st.session_state.main_df['이름']}
                        }
                        st.session_state.config_confirmed = True
                        st.session_state.teams_generated = False
                        save_room_state(st.session_state.room_name)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # [일반 사용자] 관리자가 설정 중일 때 안내 메시지
                st.info("⏳ 관리자가 대회 운영 설정을 진행하고 있습니다. 잠시만 기다려주세요.")

        # 제비뽑기 로직 (Fragment 호출)
        if "config" in st.session_state and st.session_state.config.get('draw_method') == '제비뽑기':
            if not st.session_state.get('draw_completed', False):
                st.divider()
                cfg = st.session_state.config
                df = st.session_state.main_df
                attendees = df[df[col_date] == 'Y'].copy()
                attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
                attendees['Random'] = attendees['이름'].map(cfg['tie_breakers'])
                sorted_members = attendees.sort_values(['부수_숫자', 'Random'], ascending=True).reset_index(drop=True)
                total_levels = math.ceil(len(sorted_members) / cfg['g'])
                draw_level = st.session_state.get('draw_level', 0)

                responsive_text(f"📋 제비뽑기 진행 현황", pc_size="20px", mobile_size="16px")
                render_draw_process(cfg, sorted_members, total_levels, draw_level)
            else:
                st.divider()
                st.success("✅ 제비뽑기가 모두 완료되었습니다! 상단의 <strong>'조 편성 결과'</strong> 탭으로 이동하여 결과를 확인해주세요.")
                if is_admin and not st.session_state.config_confirmed:
                    if st.button("🔄 제비뽑기 다시 하기", type="secondary"):
                        st.session_state.draw_level = 0
                        st.session_state.draw_results = {}
                        st.session_state.draw_completed = False
                        for key in list(st.session_state.keys()):
                            if key.startswith("group_selections_") or key.startswith("select_"):
                                del st.session_state[key]
                        save_room_state(st.session_state.room_name)
                        st.rerun()

    # ---------------------------------------------------------------------
    # 탭 3: 조 편성 결과 (공통 조회)
    # ---------------------------------------------------------------------
    with tab_team:
        if not st.session_state.config_confirmed:
            st.warning("먼저 '운영 설정' 탭에서 설정을 확정해주세요.")
        else:
            st.info(f"👥 현재 확정된 참석 인원: **{attendees_count}명**")
            cfg = st.session_state.config

            # 조 편성 연산 (최초 1회만 실행)
            if not st.session_state.get('teams_generated', False):
                df = st.session_state.main_df
                attendees = df[df[col_date] == 'Y'].copy()
                attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
                sorted_members = attendees.sort_values(['부수_숫자'], ascending=True).reset_index(drop=True)

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

                elif cfg.get('draw_method') == '조편성_신청':
                    attendees['조편성_신청'] = attendees['조편성_신청'].fillna('미지정').astype(str).str.strip().str.upper()
                    unique_groups = attendees['조편성_신청'].unique()
                    group_to_team_map = {g_name: (i % cfg['g']) + 1 for i, g_name in enumerate(unique_groups)}
                    for idx, row in attendees.iterrows():
                        t_idx = group_to_team_map[row['조편성_신청']]
                        teams[t_idx].append(f"{row['이름']}({row['부수']})")
                        all_member_names.append(row['이름'])
                        team_stats[t_idx]["sum"] += row['부수_숫자']
                        team_stats[t_idx]["count"] += 1

                else:  # 제비뽑기
                    for idx, row in sorted_members.iterrows():
                        t_idx = st.session_state.draw_results.get(row['이름'], 1)
                        teams[t_idx].append(f"{row['이름']}({row['부수']})")
                        all_member_names.append(row['이름'])
                        team_stats[t_idx]["sum"] += row['부수_숫자']
                        team_stats[t_idx]["count"] += 1

                avg_p = sum(t["count"] for t in team_stats.values()) / cfg['g'] if cfg['g'] > 0 else 0
                st.session_state.config['is_individual'] = True if avg_p <= 1.5 else False
                st.session_state.labels = [f"{i}조({teams[i][0].split('(')[0]})" for i in range(1, cfg['g'] + 1) if teams[i]]

                st.session_state.teams = teams
                st.session_state.team_stats = team_stats
                st.session_state.all_member_names = all_member_names
                st.session_state.teams_generated = True

                st.session_state.matrix = pd.DataFrame(np.nan, index=st.session_state.labels,
                                                       columns=st.session_state.labels)
                all_member_names = sorted(list(set(all_member_names)))
                st.session_state.ind_matrix = pd.DataFrame(np.nan, index=all_member_names, columns=all_member_names)
                save_room_state(st.session_state.room_name)

            # [공통] 화면 출력부 (누구나 볼 수 있음)
            teams = st.session_state.teams
            team_stats = st.session_state.team_stats

            responsive_text(f"📋 조별 최종 구성 및 부수 합계", pc_size="20px", mobile_size="16px")
            valid_teams = [t_num for t_num in range(1, cfg['g'] + 1) if teams[t_num]]
            num_cols = min(len(valid_teams), 5)

            if num_cols > 0:
                for i in range(0, len(valid_teams), num_cols):
                    chunk = valid_teams[i:i + num_cols]
                    cols = st.columns(num_cols)
                    for j, t_num in enumerate(chunk):
                        with cols[j]:
                            formatted_members = [re.sub(r'\((\d+)(?:\.\d+)?\)', r'(\1부)', m) for m in teams[t_num]]
                            members_html = "<br>".join(formatted_members)
                            card_html = config.TEAM_CARD_TEMPLATE.format(
                                t_num=t_num, team_len=len(teams[t_num]),
                                team_sum=int(team_stats[t_num]['sum']), members_html=members_html
                            )
                            st.markdown(card_html, unsafe_allow_html=True)

            if st.session_state.get('matrix') is None or list(st.session_state.matrix.index) != st.session_state.labels:
                st.session_state.matrix = pd.DataFrame(np.nan, index=st.session_state.labels,
                                                       columns=st.session_state.labels)

            if st.session_state.get('ind_matrix') is None:
                all_member_names = sorted(list(set(all_member_names)))
                st.session_state.ind_matrix = pd.DataFrame(np.nan, index=all_member_names, columns=all_member_names)
                save_room_state(st.session_state.room_name)

    # ---------------------------------------------------------------------
    # 탭 4: 경기 배정 (관리자 전용)
    # ---------------------------------------------------------------------
    if tab_match is not None:
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

                # 🌟 [개선 1] 대진표 연산 캐싱: 매번 계산하지 않고 세션에 저장해두어 속도 향상
                if 'all_matches' not in st.session_state or st.session_state.get('match_labels') != st.session_state.labels:
                    st.session_state.all_matches = get_matches(st.session_state.labels)
                    st.session_state.match_labels = st.session_state.labels.copy()

                all_matches = st.session_state.all_matches

                cfg = st.session_state.config
                # print(cfg)
                t_count = cfg['t']
                s_games = cfg.get('s_games', 0)
                d_games = cfg.get('d_games', 0)
                is_ind = cfg.get('is_individual', False)

                # 💡 [핵심 규칙] 단식 또는 복식 게임 수의 '합'이 정확히 1인 경우만 체크하도록 수정
                is_single_or_double_one_game = (s_games + d_games == 1)

                set_rule = cfg.get('set_count', 3)

                # 개인전이거나 단/복식이 1게임인 경우에는 개인전 선승 세트수('set_count')를 가져옵니다.
                if is_ind or is_single_or_double_one_game:
                    limit = cfg.get('set_count', 3)

                else:
                    limit = cfg.get('total_g', 5)  # 일반 단체전 세트수

                match_info = "개인전" if is_ind else f"단식 {s_games} / 복식 {d_games}"

                # 대진표 데이터 생성
                m_data = []
                for i, (a, b) in enumerate(all_matches):
                    s1, s2 = 0, 0
                    # 점수판(matrix)에 이미 입력된 점수가 있는지 확인
                    if a in st.session_state.matrix.index and b in st.session_state.matrix.columns:
                        s1, s2 = st.session_state.matrix.loc[a, b], st.session_state.matrix.loc[b, a]

                    # # 점수가 1점이라도 입력되어 있으면 '종료', 아니면 '대기' 상태로 표시
                    # 🌟 [수정] 점수가 1점이라도 나야 종료가 아니라, 값(NaN이 아님)이 입력되어 있으면 '종료'로 표시
                    # 🌟 [수정 핵심] 값이 정상적인 숫자이고, 두 점수의 합이 0보다 클 때만 '종료'로 판정
                    try:
                        s1_val, s2_val = float(s1), float(s2)
                        is_finished = pd.notna(s1_val) and pd.notna(s2_val) and (s1_val + s2_val > 0)

                    except (ValueError, TypeError):
                        is_finished = False
                        s1_val, s2_val = 0, 0

                    status = " 종료" if is_finished else " 대기"

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

                # 🌟 [개선 2] 상세 결과 입력창을 Fragment로 분리하여 입력 중 전체 화면 지연 방지
                @st.fragment
                def render_match_details(m_idx, team_a, team_b):
                    st.divider()
                    # st.markdown(f"### 🎯 {team_a} VS {team_b} 상세 결과 입력")
                    responsive_text(f"🎯 {team_a} VS {team_b} 상세 결과 입력", pc_size="20px", mobile_size="16px")

                    if not is_admin:
                        st.warning("🔒 관리자 비밀번호를 입력해주세요.")
                        return

                    if is_ind:
                        # 🌟 [개선 3] 개인전은 st.form으로 묶어서 클릭 지연 완벽 제거
                        with st.form(key=f"form_ind_{m_idx}"):
                            c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 2.5, 1.5, 1.5])
                            with c1: st.markdown(f"<div style='text-align:center;'>{team_a}</div>", unsafe_allow_html=True)
                            with c2: res_type = st.radio(f"결과", ["승", "패"], horizontal=True)
                            with c3:
                                scores = [f"{set_rule}:{i}" for i in range(set_rule)] if res_type == "승" else [f"{i}:{set_rule}"
                                                                                                               for i in
                                                                                                               range(set_rule)]
                                selected_score = st.radio("스코어", scores, horizontal=True)
                            with c4: st.markdown(f"<div style='text-align:center;'>{team_b}</div>", unsafe_allow_html=True)
                            with c5:
                                submit_ind = st.form_submit_button("결과 저장", type="primary", use_container_width=True)

                            if submit_ind:
                                s_a, s_b = map(int, selected_score.split(':'))
                                st.session_state.matrix.loc[team_a, team_b] = s_a
                                st.session_state.matrix.loc[team_b, team_a] = s_b
                                save_room_state(st.session_state.room_name)
                                st.session_state.show_success_msg = "결과가 저장되었습니다."
                                st.rerun()
                    else:
                        # 단체전 로직 (Fragment 내부에서만 동작하므로 선수 선택 시 지연 없음)
                        def get_team_players(team_str):
                            match = re.search(r'(\d+)조', str(team_str))
                            if match and 'teams' in st.session_state:
                                t_idx = int(match.group(1))
                                return [p.split('(')[0] for p in st.session_state.teams.get(t_idx, [])]
                            return list(st.session_state.ind_matrix.index)

                        team_a_players = get_team_players(team_a)
                        team_b_players = get_team_players(team_b)

                        def get_avail_single(players, current_key):
                            selected = [st.session_state[f"m{m_idx}_s_p{ab}_{s}"]
                                        for ab in ['a', 'b'] for s in range(s_games)
                                        if f"m{m_idx}_s_p{ab}_{s}" in st.session_state
                                        and f"m{m_idx}_s_p{ab}_{s}" != current_key
                                        and st.session_state[f"m{m_idx}_s_p{ab}_{s}"] != "선택안함"]
                            return ["선택안함"] + [p for p in players if p not in selected]

                        def get_avail_double(players, current_key):
                            selected = [st.session_state[f"m{m_idx}_d_p{ab}{num}_{d}"]
                                        for ab in ['a', 'b'] for num in [1, 2] for d in range(d_games)
                                        if f"m{m_idx}_d_p{ab}{num}_{d}" in st.session_state
                                        and f"m{m_idx}_d_p{ab}{num}_{d}" != current_key
                                        and st.session_state[f"m{m_idx}_d_p{ab}{num}_{d}"] != "선택안함"]
                            return ["선택안함"] + [p for p in players if p not in selected]

                        match_results = []
                        set_limit = set_rule
                        set_win_scores = [f"{set_limit}:{i}" for i in range(set_limit)]
                        set_lose_scores = [f"{i}:{set_limit}" for i in range(set_limit)]

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

                        if d_games > 0:
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
                            set_score_a, set_score_b = 0, 0
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
                                    set_score_a, set_score_b = sa, sb
                                else:
                                    _, _, sa, sb, _ = res
                                    if sa > sb:
                                        aw += 1
                                    elif sb > sa:
                                        bw += 1
                                    set_score_a, set_score_b = sa, sb

                                if is_single_or_double_one_game:
                                    st.session_state.matrix.loc[team_a, team_b] = set_score_a
                                    st.session_state.matrix.loc[team_b, team_a] = set_score_b
                                else:
                                    st.session_state.matrix.loc[team_a, team_b] = aw
                                    st.session_state.matrix.loc[team_b, team_a] = bw

                            save_room_state(st.session_state.room_name)
                            st.session_state.show_success_msg = "상세 결과가 저장되었습니다!"
                            st.rerun()

                if selected_match_idx is not None:
                    team_a, team_b = all_matches[selected_match_idx]
                    render_match_details(selected_match_idx, team_a, team_b)

            else:
                st.info("조 편성이 완료되면 경기 배정표가 나타납니다.")

    # ---------------------------------------------------------------------
    # 탭 5: 스코어보드 (공통 조회 / 관리자 수정)
    # ---------------------------------------------------------------------
    with tab_score:
        # [관리자 전용] 리그 히스토리 관리
        if is_admin:
            with st.expander("💾 리그 데이터 저장 및 불러오기 (일자별 관리)", expanded=False):
                col_save, col_load = st.columns(2)
                current_room = st.session_state.get('room_name', '리그')

                with col_save:
                    st.markdown("##### **현재 결과 저장하기**")
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_title = st.text_input("저장할 리그명/일자 입력", value=f"[{current_room}] {now_str} 저장본")
                    has_data_to_save = 'labels' in st.session_state and st.session_state.get('matrix') is not None

                    if st.button("현재 상태 저장하기", type="primary", use_container_width=True, disabled=not has_data_to_save):
                        current_matrix = st.session_state.matrix
                        ind_matrix_to_save = st.session_state.get('ind_matrix', None)

                        is_duplicate = False
                        if 'last_saved_matrix' in st.session_state:
                            if st.session_state.last_saved_matrix.equals(current_matrix):
                                if ind_matrix_to_save is not None and 'last_saved_ind_matrix' in st.session_state:
                                    if st.session_state.last_saved_ind_matrix.equals(ind_matrix_to_save):
                                        is_duplicate = True
                                elif ind_matrix_to_save is None:
                                    is_duplicate = True

                        if is_duplicate:
                            st.warning("⚠️ 변경된 스코어가 없습니다. (가장 최근에 저장한 내용과 동일합니다)")
                        else:
                            save_league_history(save_title, st.session_state.labels, current_matrix, ind_matrix_to_save,
                                                st.session_state.config)
                            st.session_state.last_saved_matrix = current_matrix.copy()
                            if ind_matrix_to_save is not None:
                                st.session_state.last_saved_ind_matrix = ind_matrix_to_save.copy()
                            st.session_state.show_success_msg = f"🎉 '{save_title}' 데이터가 안전하게 저장되었습니다!"
                            st.rerun()

                with col_load:
                    st.markdown("##### <strong>과거 결과 불러오기 (로드)</strong>")
                    all_saved_keys = get_history_keys()
                    room_saved_keys = [key for key in all_saved_keys if f"[{current_room}]" in key]

                    if room_saved_keys:
                        room_saved_keys.sort(reverse=True)
                        selected_key = st.selectbox("불러올 과거 리그 선택", room_saved_keys)
                        if st.button("선택한 리그 불러오기 (덮어쓰기)", type="secondary", use_container_width=True):
                            if load_league_history(selected_key):
                                st.session_state.show_success_msg = f"📂 '{selected_key}' 데이터를 성공적으로 불러왔습니다!"
                                st.rerun()
                            else:
                                st.error("데이터 로드에 실패했습니다.")
                    else:
                        st.info("현재 방에 저장된 과거 리그 내역이 없습니다.")
            st.divider()

        # [공통] 스코어보드 렌더링
        if 'labels' in st.session_state and st.session_state.get('matrix') is not None:
            cfg = st.session_state.config
            is_ind = cfg.get('is_individual', False)
            room_name = st.session_state.get('room_name', '탁구대회')
            s_games, d_games = cfg.get('s_games', 0), cfg.get('d_games', 0)
            is_single_or_double_one_game = (s_games + d_games == 1)
            set_rule = cfg.get('set_count', 3)
            limit = cfg.get('set_count', 3) if is_ind or is_single_or_double_one_game else cfg.get('total_g', 5)

            if 'table_font_size' not in st.session_state:
                num_rows = len(st.session_state.labels)
                st.session_state.table_font_size = 20 if num_rows <= 4 else (
                    16 if num_rows <= 6 else (13 if num_rows <= 8 else 11))

            if 'fullscreen_table' not in st.session_state:
                st.session_state.fullscreen_table = False

            @st.fragment
            def draw_summary_table(editable=False):
                raw_m = st.session_state.matrix.copy()
                current_labels = st.session_state.labels
                m = raw_m.reindex(index=current_labels, columns=current_labels)

                rank = pd.DataFrame(index=m.index)
                m_numeric = m.apply(pd.to_numeric, errors='coerce')
                m_val, mt_val = m_numeric.values, m_numeric.T.values

                rank['승'] = np.nansum(m_val > mt_val, axis=1).astype(int)
                rank['패'] = np.nansum(m_val < mt_val, axis=1).astype(int)
                rank['득점'] = m_numeric.sum(axis=1, skipna=True).fillna(0).astype(int)
                rank['실점'] = m_numeric.sum(axis=0, skipna=True).fillna(0).astype(int)
                rank['득실차'] = (rank['득점'] - rank['실점']).astype(int)

                combined_df = pd.concat([m, rank[['승', '패', '득점', '실점', '득실차']]], axis=1)
                display_df = combined_df.reindex(index=current_labels) if editable else combined_df.sort_values(
                    ['승', '득실차'], ascending=False)
                view_df = display_df.copy()

                for col in current_labels:
                    if col in view_df.columns: view_df[col] = view_df[col].astype(object)

                for r in current_labels:
                    for c in current_labels:
                        if r not in view_df.index or c not in view_df.columns: continue
                        if r == c:
                            view_df.loc[r, c] = "None"
                        else:
                            val = view_df.loc[r, c]
                            if pd.isna(val) or str(val).strip() == "":
                                view_df.loc[r, c] = "-"
                            else:
                                try:
                                    view_df.loc[r, c] = str(int(float(val)))
                                except:
                                    view_df.loc[r, c] = str(val)

                # [관리자 전용] 편집 모드
                if editable and is_admin:
                    st.info("💡 <strong>아래 표의 대결 셀(Cell)을 더블 클릭</strong>하여 세트 스코어(점수)를 입력한 뒤, 하단의 **[변경사항 적용]** 버튼을 눌러주세요.")
                    disabled_cols = ['승', '패', '득점', '실점', '득실차']
                    edited_df = st.data_editor(view_df, use_container_width=True, disabled=disabled_cols,
                                               key="main_matrix_editor", row_height=35)

                    original_matrix_part = view_df.loc[current_labels, current_labels]
                    edited_matrix_part = edited_df.loc[current_labels, current_labels]

                    has_valid_change, has_invalid_diagonal_change = False, False
                    for r in current_labels:
                        for c in current_labels:
                            if str(original_matrix_part.loc[r, c]) != str(edited_matrix_part.loc[r, c]):
                                if r == c:
                                    has_invalid_diagonal_change = True
                                else:
                                    has_valid_change = True

                    if has_invalid_diagonal_change and not has_valid_change:
                        if "main_matrix_editor" in st.session_state: del st.session_state["main_matrix_editor"]
                        st.rerun()

                    if has_valid_change:
                        if st.button("💾 변경사항 적용하기", type="primary"):
                            for r in current_labels:
                                for c in current_labels:
                                    if r == c: continue
                                    val = edited_matrix_part.loc[r, c]
                                    try:
                                        if pd.isna(val) or str(val).strip() in ["", "-", "None"]:
                                            st.session_state.matrix.loc[r, c] = np.nan
                                        else:
                                            st.session_state.matrix.loc[r, c] = float(val)
                                    except (ValueError, TypeError):
                                        st.session_state.matrix.loc[r, c] = np.nan

                            if "main_matrix_editor" in st.session_state: del st.session_state["main_matrix_editor"]
                            save_room_state(st.session_state.room_name)
                            st.session_state.show_success_msg = "전광판 스코어가 성공적으로 저장되었습니다."
                            st.rerun()

                # [공통] 일반 보기 모드
                else:
                    current_fs = st.session_state.table_font_size
                    ROW_HEIGHT = f"{current_fs + 25}px"
                    styled_df = view_df.style.format(precision=0, na_rep='-').set_properties(**{
                        'text-align': 'center', 'vertical-align': 'middle', 'height': ROW_HEIGHT,
                    }).set_table_styles([{'selector': 'th',
                                          'props': [('text-align', 'center'), ('vertical-align', 'middle'),
                                                    ('height', ROW_HEIGHT)]}])

                    raw_html = styled_df.to_html().replace('\n', '')
                    completed_css_tab_score = config.css_tab_score.format(current_fs=current_fs)
                    st.markdown(completed_css_tab_score + '<div class="custom-table-wrapper">' + raw_html + '</div>',
                                unsafe_allow_html=True)

            # 상단 제어 바 (공통)
            col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([4, 2, 2, 2])
            with col_ctrl1:
                btn_txt = "🔙 이전 화면으로" if st.session_state.fullscreen_table else "📺 전체 화면 모드"
                if st.button(btn_txt, type="primary", width='stretch'):
                    st.session_state.fullscreen_table = not st.session_state.fullscreen_table
                    st.rerun()

            with col_ctrl2:
                f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1])
                with f_col1:
                    if st.button("➖"):
                        st.session_state.table_font_size = max(8, st.session_state.table_font_size - 1)
                        st.rerun()
                with f_col2:
                    st.markdown(
                        f"<div style='text-align:center; padding-top:5px;'><b>{st.session_state.table_font_size}</b></div>",
                        unsafe_allow_html=True)
                with f_col3:
                    if st.button("➕"):
                        st.session_state.table_font_size = min(30, st.session_state.table_font_size + 1)
                        st.rerun()

            with col_ctrl3:
                if 'cum_df' in st.session_state and not st.session_state.cum_df.empty:
                    csv_bytes = st.session_state.cum_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(label="📥 누적 다운로드", data=csv_bytes, file_name=f"{room_name}_누적.csv", mime="text/csv",
                                       width='stretch')

            with col_ctrl4:
                if 'h2h_df' in st.session_state and not st.session_state.h2h_df.empty:
                    h2h_bytes = st.session_state.h2h_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(label="📥 상대전적 다운로드", data=h2h_bytes, file_name=f"{room_name}_상전.csv",
                                       mime="text/csv", width='stretch')

            # 화면 출력 분기
            if st.session_state.fullscreen_table:
                responsive_text(f"🏆 종합 결과 전광판", pc_size="24px", mobile_size="18px")
                draw_summary_table(editable=False)
            else:
                @st.fragment
                def render_manual_score_input():
                    responsive_text(f"📋 {'조별' if not is_ind else '개인전'} 점수 입력", pc_size="20px", mobile_size="16px")

                    # [관리자 전용] 수동 점수 입력
                    if not is_admin:
                        st.info("🔒 점수 입력 및 수정은 관리자만 가능합니다.")
                        return

                    st.info(" 기준이 되는 조(선수)를 선택하고 승/패 및 스코어를 입력하세요. (이미 완료된 경기는 비활성화됩니다.)")
                    labels = st.session_state.labels
                    if labels:
                        c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2.5, 1.5])
                        with c1:
                            team_a = st.selectbox("A 선수", labels, key="sb_a")
                        with c2:
                            def f_b(n):
                                try:
                                    if (team_a in st.session_state.matrix.index) and (n in st.session_state.matrix.columns):
                                        val = st.session_state.matrix.loc[team_a, n]
                                        return f"{n} ({int(val)})" if pd.notna(val) and val != "" else n
                                    return n
                                except:
                                    return n

                            team_b = st.selectbox("B 선수", [l for l in labels if l != team_a], format_func=f_b, key="sb_b")
                            is_done = False
                            if 'matrix' in st.session_state and team_a in st.session_state.matrix.index and team_b in st.session_state.matrix.columns:
                                val_a, val_b = st.session_state.matrix.loc[team_a, team_b], st.session_state.matrix.loc[
                                    team_b, team_a]
                                try:
                                    if pd.notna(val_a) and pd.notna(val_b) and (
                                            float(val_a) + float(val_b) > 0): is_done = True
                                except (ValueError, TypeError):
                                    pass
                            else:
                                st.warning(f"⚠️ 대진표 매트릭스에 '{team_a}' 또는 '{team_b}' 선수가 없습니다.")

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
                                st.session_state.show_success_msg = f" 저장되었습니다. "
                                st.rerun()

                render_manual_score_input()

                st.divider()
                responsive_text(f"📊 {'조별 리그' if not is_ind else '개인전'} 순위표", pc_size="22px", mobile_size="18px")

                # 관리자면 편집 가능, 일반 사용자면 보기 전용으로 렌더링
                draw_summary_table(editable=is_admin)

                # 개인 성적 관리 (단체전일 경우)
                if not is_ind:
                    st.divider()
                    responsive_text("👤 개인 성적 관리", pc_size="20px", mobile_size="16px")

                    @st.fragment
                    def render_ind_matrix_editor():
                        view_ind_df = st.session_state.ind_matrix.copy()
                        for col in view_ind_df.columns: view_ind_df[col] = view_ind_df[col].astype(object)

                        for r in view_ind_df.index:
                            for c in view_ind_df.columns:
                                val = view_ind_df.loc[r, c]
                                if pd.isna(val) or str(val).strip() in ["", "None"]:
                                    view_ind_df.loc[r, c] = "-"
                                else:
                                    try:
                                        view_ind_df.loc[r, c] = str(int(float(val)))
                                    except:
                                        view_ind_df.loc[r, c] = str(val)

                        # [관리자 전용] 개인 성적 수정
                        if is_admin:
                            edited_ind_matrix = st.data_editor(view_ind_df, use_container_width=True, height=320,
                                                               key="ind_matrix_editor")
                            if not edited_ind_matrix.equals(view_ind_df):
                                if st.button("💾 개인 성적표 변경사항 적용", type="primary"):
                                    new_ind_matrix = st.session_state.ind_matrix.copy()
                                    for r in edited_ind_matrix.index:
                                        for c in edited_ind_matrix.columns:
                                            val = edited_ind_matrix.loc[r, c]
                                            try:
                                                if pd.isna(val) or str(val).strip() in ["", "-", "None"]:
                                                    new_ind_matrix.loc[r, c] = np.nan
                                                else:
                                                    new_ind_matrix.loc[r, c] = float(val)
                                            except (ValueError, TypeError):
                                                new_ind_matrix.loc[r, c] = np.nan

                                    st.session_state.ind_matrix = new_ind_matrix
                                    save_room_state(st.session_state.room_name)
                                    st.session_state.show_success_msg = "개인 성적표가 수정 및 저장되었습니다."
                                    st.rerun()
                        # [공통] 일반 사용자는 보기 전용
                        else:
                            st.dataframe(view_ind_df.style.format(precision=0, na_rep='-'), width="stretch")

                        # 개인별 순위 요약 (공통)
                        im = st.session_state.ind_matrix.copy()
                        im_values = pd.to_numeric(im.stack(), errors='coerce').unstack().fillna(0).values
                        ind_rank = pd.DataFrame(index=im.index)

                        ind_rank['개인승'] = (im_values > im_values.T).sum(axis=1).astype(int)
                        ind_rank['개인패'] = (im_values < im_values.T).sum(axis=1).astype(int)
                        sum_gain = im.sum(axis=1, skipna=True).fillna(0).astype(int)
                        sum_loss = im.sum(axis=0, skipna=True).fillna(0).astype(int)
                        ind_rank['세트득실'] = (sum_gain - sum_loss).astype(int)

                        st.markdown("#### 🥇 개인별 순위 요약 (실시간 계산)")
                        st.table(ind_rank.sort_values(['개인승', '세트득실'], ascending=False).head(10))

                    render_ind_matrix_editor()
        else:
            st.info("조 편성이 완료되면 스코어보드가 나타납니다.")

    # ---------------------------------------------------------------------
    # 탭 6: 사용설명서 (관리자 전용)
    # ---------------------------------------------------------------------
    if tab_help is not None:
        with tab_help:
            lang = st.radio("언어 선택 / Select Language", ["한국어", "English"], horizontal=True)
            show_help_section(lang)

    # ---------------------------------------------------------------------
    # 탭 7: 경품추첨 (관리자 전용)
    # ---------------------------------------------------------------------
    if tab_raffle is not None:
        with tab_raffle:
            st.header("🎁 행운의 경품 추첨")

            # 1. 설정이 완료되어 tie_breakers(경품 번호)가 존재하는지 확인
            if 'config' in st.session_state and 'tie_breakers' in st.session_state.config:

                # 참가자 이름과 부여된 번호 딕셔너리 가져오기
                raffle_data = st.session_state.config['tie_breakers']
                total_players = len(raffle_data)

                st.info(f"✅ 현재 총 **{total_players}명**의 참가자에게 추첨 번호가 부여되어 있습니다.")

                # 2. 당첨자 수 입력받기
                num_winners = st.number_input(
                    "당첨자 수를 기입해주세요:",
                    min_value=1,
                    max_value=total_players,
                    value=3,  # 기본값 3명
                    step=1
                )

                # 3. 추첨 버튼 및 결과 출력
                if st.button("🎉 추첨 시작!", type="primary", use_container_width=True):
                    st.balloons()  # 축하 폭죽 애니메이션 효과

                    # 딕셔너리(이름:번호)를 리스트로 변환하여 랜덤으로 당첨자 수만큼 뽑기
                    winners = random.sample(list(raffle_data.items()), num_winners)

                    # 번호 순서대로 정렬할지, 뽑힌 순서대로 보여줄지 결정 (여기서는 뽑힌 순서대로 1등, 2등...)
                    st.subheader("🎊 당첨을 축하합니다! 🎊")

                    # 결과를 예쁘게 출력
                    for i, (name, number) in enumerate(winners, 1):
                        st.success(f"🏆 **{i}번째 당첨:** 참가번호 **{number}번** 👉 **{name}**님")

            else:
                # 아직 '설정 확정 및 편성 시작' 버튼을 누르지 않은 경우
                st.warning("⚠️ 아직 대회 설정이 완료되지 않았습니다. 설정 탭에서 편성을 완료한 후 추첨을 진행해주세요.")
