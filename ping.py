import streamlit as st
import os
import numpy as np
import random
import pandas as pd
import re
from datetime import datetime
import math
import io, time
import pickle
import hashlib

# 구글 스프레드시트 연동 라이브러리 (DB 역할)
try:
    from streamlit_gsheets import GSheetsConnection

except ImportError:
    # 라이브러리가 없을 경우 에러 메시지 출력
    st.error("⚠️ 'st-gsheets-connection' 라이브러리가 설치되지 않았습니다."
             " 터미널에서 'pip install st-gsheets-connection'을 실행해주세요.")

from Program_User_Guide import show_help_section

# ==========================================
# 1. 환경 설정 및 전처리 (Config & CSS)
# ==========================================
DEV_MODE = False
# 관리자 마스터 비밀번호 설정 (secrets 설정에서만 가져옴)
MASTER_PASSWORD = st.secrets["master_password"]
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')  # 오늘 날짜
SHEET_URL = "https://docs.google.com/spreadsheets/d/1x26ijdrwI9BKPXYM7IJAkTUVYZBgSqST6X9sVgwvhcE/edit"  # 구글 시트 주소

# Streamlit 페이지 기본 설정 (브라우저 탭 이름, 넓은 화면 모드 등)
st.set_page_config(
    page_title="동호회 운영 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
</style>
""", unsafe_allow_html=True) # HTML과 CSS 태그가 문자열 그대로 출력되지 않고 실제 웹페이지에 적용되도록 허용하는 옵션

# st.markdown(..., unsafe_allow_html=True)
# Streamlit은 기본적으로 보안을 위해 HTML/CSS 태그를 텍스트로 취급합니다.
# 하지만 unsafe_allow_html=True 옵션을 주면 작성한
# <style> 태그가 실제 웹 브라우저의 CSS로 작동하게 되어 디자인을 바꿀 수 있습니다.
# !important의 역할
# 버튼 색상을 지정할 때 사용된 !important는 Streamlit이 기본적으로 가지고 있는 테마 스타일을 무시하고,
# 내가 작성한 이 CSS를 최우선으로 적용하라는 강제 명령입니다.

# [data-testid="column"]
# Streamlit에서 st.columns()를 사용해 화면을 분할할 때,
# 내부적으로 생성되는 HTML 요소의 이름(속성)입니다.
# 이 속성을 찾아내어 justify-content: center;를 주었기 때문에,
# 양쪽 컬럼의 높이가 달라도 내용물이 세로 중앙에 예쁘게 맞춰지게 됩니다.

# 색상 코드 참고
# #28a745: 부트스트랩(Bootstrap) 등에서 자주 쓰이는 안정적인 느낌의 초록색(Success)입니다.
# #dc3545: 경고나 취소 등을 나타낼 때 자주 쓰이는 빨간색(Danger)입니다.
# #f8f9fa: 눈이 편안한 아주 연한 회색(Light)입니다.

# ==========================================
# 2. 공통 함수 모음 (Functions)
# ==========================================
def hash_password(password):
    """비밀번호를 안전하게 보관하기 위해 SHA-256 방식으로 암호화하는 함수"""
    return hashlib.sha256(password.encode()).hexdigest()

# 마스터 비밀번호 암호화 저장
HASHED_MASTER_PW = hash_password(MASTER_PASSWORD)


def save_room_state(room_name):
    """현재 구장의 모든 진행 상황(세션 상태)을 pkl 파일로 저장하여 새로고침해도 날아가지 않게 함"""
    # 1. 저장할 데이터들을 딕셔너리(Dictionary) 형태로 모음
    # st.session_state.get('키')를 사용해 현재 메모리에 있는 데이터를 안전하게 가져옵니다.
    state_to_save = {
        'main_df': st.session_state.get('main_df'),  # 메인 데이터프레임
        'config': st.session_state.get('config'),  # 설정값
        'teams': st.session_state.get('teams'),  # 팀 정보
        'matrix': st.session_state.get('matrix'),  # 대진표/결과 매트릭스
        'ind_matrix': st.session_state.get('ind_matrix'),  # 개인별 매트릭스
        'cum_df': st.session_state.get('cum_df'),  # 누적 데이터프레임
        'h2h_df': st.session_state.get('h2h_df'),  # 상대 전적(Head-to-Head) 데이터
        'labels': st.session_state.get('labels'),  # 라벨 정보
        'attendance_confirmed': st.session_state.get('attendance_confirmed'),  # 출석 확인 여부
        'config_confirmed': st.session_state.get('config_confirmed'),  # 설정 완료 여부
        'draw_results': st.session_state.get('draw_results'),  # 추첨 결과
        'draw_completed': st.session_state.get('draw_completed')  # 추첨 완료 여부
    }

    try:
        # 2. pkl 파일 생성 및 데이터 쓰기
        # f"{room_name}_state.pkl" 형식으로 파일명 생성 (예: 구장A_state.pkl)
        # "wb"는 Write Binary의 약자로, 텍스트가 아닌 바이너리(이진) 형태로 파일을 쓰겠다는 의미
        with open(f"{room_name}_state.pkl", "wb") as f:
            pickle.dump(state_to_save, f)  # state_to_save 딕셔너리를 파일(f)에 압축/변환하여 저장

    except Exception as e:
        # 3. 예외 처리: 저장 중 예상치 못한 오류가 발생하면 사이드바에 붉은색 에러 메시지 출력
        st.sidebar.error(f"상태 저장 오류: {e}")

def load_room_state(room_name):
    """저장된 pkl 파일에서 구장 데이터를 불러와 세션 상태를 복구하는 함수"""

    # 1. 불러올 파일 이름 지정
    file_name = f"{room_name}_state.pkl"

    # 2. 해당 파일이 실제로 존재하는지 확인 (파일이 없는데 읽으려 하면 에러가 나기 때문)
    if os.path.exists(file_name):
        try:
            # 3. 파일 읽기
            # "rb"는 Read Binary의 약자로, 바이너리 파일을 읽겠다는 의미
            with open(file_name, "rb") as f:
                state = pickle.load(f)  # 파일(f)에서 데이터를 읽어와 state 변수(딕셔너리)에 저장

                # 4. 읽어온 데이터를 Streamlit 세션 상태에 복구
                for k, v in state.items():  # 딕셔너리의 키(k)와 값(v)을 하나씩 꺼냄
                    if v is not None:  # 값이 비어있지 않은(None이 아닌) 경우에만
                        st.session_state[k] = v  # 현재 세션 상태에 덮어쓰기(복구)

            return True  # 성공적으로 불러왔음을 알림 (True 반환)

        except Exception as e:
            # 5. 예외 처리: 불러오기 중 오류가 발생하면 사이드바에 에러 메시지 출력
            st.sidebar.error(f"데이터 불러오기 실패: {e}")

    # 파일이 존재하지 않거나, 불러오기에 실패한 경우 False 반환
    return False

# st.session_state와 .get() 메서드
# Streamlit은 버튼을 누르거나 값을 입력할 때마다 코드가 위에서부터 아래로 재실행되는 특징이 있습니다.
# 이때 변수들이 초기화되는 것을 막기 위해 st.session_state라는 특수한 저장 공간을 사용합니다.
# .get('키')를 사용하는 이유는,
# 만약 해당 데이터가 아직 생성되지 않았을 때 에러를 발생시키는 대신
# 안전하게 None(빈 값)을 반환하게 만들기 위해서입니다.
# pickle 모듈
# 파이썬에서 사용하는 데이터프레임(Pandas), 리스트, 딕셔너리 등의 복잡한 객체를
# 그 형태 그대로 파일로 저장하고 불러올 수 있게 해주는 도구입니다.
# pickle.dump(데이터, 파일): 데이터를 파일로 저장합니다.
# pickle.load(파일): 파일에서 데이터를 불러옵니다.
# "wb"와 "rb" (바이너리 모드)
# 일반적인 메모장 텍스트 파일(.txt)은 "w", "r"로 열지만,
# pickle은 파이썬 객체를 컴퓨터가 읽기 쉬운 이진 데이터(0과 1)로 변환하여 저장합니다.
# 따라서 반드시 Write Binary("wb")와 Read Binary("rb") 모드를 사용해야 합니다.
# with open(...) as f: 구문
# 파일을 열고 나서 작업이 끝나면 자동으로 파일을 닫아주는(Close) 파이썬의 안전한 문법입니다.
# 만약 파일을 닫지 않으면 메모리 누수가 발생하거나 다른 프로그램에서 해당 파일을 수정하지 못하는 문제가 생길 수 있습니다.
# os.path.exists(file_name)
# 파일을 불러오기 전에 해당 이름의 파일이 폴더에 실제로 존재하는지 먼저 검사합니다.
# 처음 구장을 만들었을 때는 저장된 .pkl 파일이 없으므로,
# 이 검사 과정이 없으면 프로그램이 멈추는 에러가 발생합니다.

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
    """회원 명단 CSV 파일을 불러오는 함수. 파일이 없으면 테스트용 더미 데이터를 생성함"""
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            return pd.read_csv(uploaded_file, encoding='cp949')
    # 더미 데이터 생성
    data = [{"순서": i, "이름": f"회원{i}", "성별": random.choice(["남", "여"]),
             "나이": random.randint(20, 75), "부수": f"{random.randint(1, 13)}부",
             "부수_조정1": 0.0, "부수_조정2": 0.0, "부수_조정3": 0.0,
             "참석예정": random.choice(["Y", "N"])} for i in range(1, 11)]
    return pd.DataFrame(data)


def update_cumulative_record(p_a, p_b, s_a, s_b):
    """경기가 끝날 때마다 선수들의 누적 전적(승, 패, 득점, 실점)과 상대 전적을 업데이트하는 함수
       - p_a, p_b: 선수 A와 선수 B의 이름
       - s_a, s_b: 선수 A와 선수 B의 점수(Score)
    """
    # ==========================================
    # 1. 개인별 누적 전적(cum_df) 업데이트 부분
    # ==========================================

    # 세션 상태에 누적 전적 데이터프레임(cum_df)이 없으면 빈 표를 새로 만듭니다.
    if 'cum_df' not in st.session_state:
        st.session_state.cum_df = pd.DataFrame(columns=['이름', '총경기수', '승', '패', '득점', '실점'])
    df_cum = st.session_state.cum_df  # 코드를 짧게 쓰기 위해 변수에 할당

    # 내부 함수: 명단에 없는 새로운 선수면 데이터프레임에 0전 0승 0패로 새로 추가하는 역할
    def ensure_player(df, name):
        if name not in df['이름'].values:  # 해당 이름이 표의 '이름' 열에 없다면
            # 새로운 선수의 초기 데이터를 딕셔너리 형태로 만듦
            new_row = pd.DataFrame([{'이름': name, '총경기수': 0, '승': 0, '패': 0, '득점': 0, '실점': 0}])
            # 기존 표(df) 아래에 새로운 행(new_row)을 이어 붙임 (ignore_index=True로 인덱스 번호 재배열)
            df = pd.concat([df, new_row], ignore_index=True)
        return df

    # "선택안함"(부전승 등 빈 자리)이 아닌 실제 선수일 경우에만 명단에 추가/확인
    if p_a != "선택안함": df_cum = ensure_player(df_cum, p_a)
    if p_b != "선택안함": df_cum = ensure_player(df_cum, p_b)

    # 승패 및 점수 계산 후 누적 데이터에 반영
    # 선수 A와 선수 B의 데이터를 한 번씩 반복문(for)으로 처리하여 코드를 줄임
    # (선수이름, 승리여부, 패배여부, 내점수, 상대점수) 형태로 묶어서 처리
    for p, win, lose, score, opp_score in [(p_a, s_a > s_b, s_a < s_b, s_a, s_b),
                                           (p_b, s_b > s_a, s_b < s_a, s_b, s_a)]:
        if p != "선택안함":  # 실제 선수인 경우에만 기록 업데이트
            # 해당 선수가 있는 행의 위치(인덱스 번호)를 찾음
            idx = df_cum[df_cum['이름'] == p].index[0]

            # .at[행, 열]을 사용하여 해당 선수의 기록에 값을 더해줌 (+=)
            df_cum.at[idx, '총경기수'] += 1
            df_cum.at[idx, '승'] += 1 if win else 0  # 이겼으면 1을 더하고, 아니면 0을 더함
            df_cum.at[idx, '패'] += 1 if lose else 0  # 졌으면 1을 더하고, 아니면 0을 더함
            df_cum.at[idx, '득점'] += score  # 내가 낸 점수를 득점에 누적
            df_cum.at[idx, '실점'] += opp_score  # 상대가 낸 점수를 실점에 누적

    # 업데이트된 표를 다시 세션 상태에 저장하여 화면에 반영되게 함
    st.session_state.cum_df = df_cum

    # ==========================================
    # 2. 1:1 상대 전적(H2H, Head-to-Head) 업데이트 부분
    # ==========================================

    # 두 자리 모두 실제 선수가 배정된 정상적인 경기일 때만 상대 전적을 기록
    if p_a != "선택안함" and p_b != "선택안함":

        # 상대 전적 표(h2h_df)가 없으면 새로 만듦
        if 'h2h_df' not in st.session_state:
            st.session_state.h2h_df = pd.DataFrame(
                columns=['Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score'])
        h2h = st.session_state.h2h_df

        # ★ 핵심: A vs B 와 B vs A 가 따로 기록되는 것을 막기 위해 이름을 가나다(알파벳) 순으로 정렬
        p1, p2 = sorted([p_a, p_b])

        # 표에서 Player1이 p1이고, Player2가 p2인 행을 찾는 조건(마스크) 생성
        mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)

        # 만약 두 사람의 맞대결 기록이 아예 없다면 새로 0승 0패로 만들어줌
        if not mask.any():
            new_row = pd.DataFrame(
                [{'Player1': p1, 'Player2': p2, 'P1_Win': 0, 'P2_Win': 0, 'P1_Score': 0, 'P2_Score': 0}])
            h2h = pd.concat([h2h, new_row], ignore_index=True)
            mask = (h2h['Player1'] == p1) & (h2h['Player2'] == p2)  # 행을 추가했으니 조건을 다시 갱신

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

# pd.concat([df, new_row], ignore_index=True)
# Pandas(데이터 분석 라이브러리)에서 기존 표(DataFrame)에
# 새로운 데이터(행)를 추가하는 가장 표준적인 방법입니다.
# ignore_index=True를 넣지 않으면 기존 인덱스 번호가 꼬일 수 있으므로,
# 0, 1, 2, 3... 순서대로 번호를 깔끔하게 다시 매기기 위해 사용합니다.
# sorted([p_a, p_b]) (이름순 정렬의 마법)
# 이 코드에서 가장 똑똑한 트릭 중 하나입니다.
# 만약 '철수'와 '영희'가 경기를 했다면,
# 어떤 날은 p_a가 철수고 어떤 날은 p_b가 철수일 수 있습니다.
# 이를 그대로 저장하면 '철수 vs 영희' 기록과 '영희 vs 철수' 기록이 두 줄로 나뉘어 버립니다.
# sorted()를 쓰면 무조건 가나다순으로 정렬되어 p1은 항상 '영희', p2는 항상 '철수'가 됩니다.
# 덕분에 두 사람의 맞대결 기록을 무조건 한 줄(하나의 행)로 깔끔하게 누적할 수 있습니다.
# mask = (조건1) & (조건2) (마스킹 기법)
# Pandas에서 특정 조건에 맞는 데이터를 찾을 때 사용하는 방법입니다.
# h2h['Player1'] == p1 (첫 번째 선수가 p1이고) & (그리고) h2h['Player2'] == p2 (두 번째 선수가 p2인)
# 행을 찾으라는 의미입니다.
# mask.any()는 이 조건에 맞는 행이 "하나라도 존재하는가?"를 묻는 함수입니다.
# not mask.any()이므로 "하나도 없다면(처음 맞붙는 거라면)"이라는 뜻이 됩니다.
# .at[idx, '컬럼명']
# Pandas 표에서 특정 행(idx)과 특정 열('컬럼명')이 교차하는 딱 하나의 셀(Cell)을 콕 집어서 값을 가져오거나 수정할 때 사용합니다.
# 속도가 매우 빠르기 때문에 값을 업데이트할 때 자주 쓰입니다.
# 1 if win else 0 (삼항 연산자)
# 파이썬에서 코드를 짧게 쓰는 문법입니다.
# win이 참(True)이면 1을 반환하고, 거짓(False)이면 0을 반환하라는 뜻입니다.
# 즉, 이겼을 때만 승리 횟수를 1 올려줍니다.


# @st.dialog는 Streamlit에서 화면 위에 뜨는 '팝업창(모달)'을 만들어주는 특수한 기능(데코레이터)입니다.
@st.dialog("📊 역대 누적 상대 전적")
def show_h2h_dialog(player_a, player_b):
    """두 선수를 선택했을 때 팝업창으로 역대 전적을 보여주는 함수"""

    # 1. 데이터 검색을 위한 이름 정렬
    # 이전 코드에서 저장할 때 가나다순으로 정렬했으므로, 불러올 때도 똑같이 정렬해야 데이터를 찾을 수 있습니다.
    p1, p2 = sorted([player_a, player_b])

    # 2. 세션 상태에서 상대 전적 표(h2h_df) 불러오기
    # 만약 데이터가 아예 없다면 에러가 나지 않도록 빈 표(pd.DataFrame())를 기본값으로 가져옵니다.
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
                unsafe_allow_html=True)  # 초록색 글씨로 'A vs B' 출력 (vs는 회색)

            st.markdown(
                f"<p style='text-align: center; font-size:1.1rem;'>총 <b>{p1_w + p2_w}</b>전 맞대결</p>",
                unsafe_allow_html=True)  # 두 사람의 승수를 더해 '총 N전 맞대결' 출력

            # 5. 화면을 좌우 2개의 단(Column)으로 나누기
            c1, c2 = st.columns(2)

            # 왼쪽 단(c1)에는 p1의 기록을 파란색/회색 톤의 정보창(st.info)으로 출력
            with c1:
                st.info(
                    f"<div style='text-align:center; font-size:1.2rem;'><b>{p1}</b><br><br>🏆 <b>{p1_w}</b> 승<br>🎯 {p1_s} 득점</div>",
                    unsafe_allow_html=True)

            # 오른쪽 단(c2)에는 p2의 기록을 붉은색 톤의 경고창(st.error)으로 출력하여 시각적 대비를 줌
            with c2:
                st.error(
                    f"<div style='text-align:center; font-size:1.2rem;'><b>{p2}</b><br><br>🏆 <b>{p2_w}</b> 승<br>🎯 {p2_s} 득점</div>",
                    unsafe_allow_html=True)

            st.write("")  # 약간의 빈 줄(여백) 추가

            # 6. 닫기 버튼
            # use_container_width=True를 주어 버튼이 팝업창 가로 길이에 꽉 차게 만듦
            if st.button("닫기", use_container_width=True):
                st.rerun()  # 버튼을 누르면 화면을 새로고침하여 팝업창을 닫음

            return  # 전적을 성공적으로 보여줬으므로 여기서 함수를 종료함

    # 7. 만약 표가 비어있거나, 두 사람의 맞대결 기록이 없을 경우 실행되는 부분
    st.warning("아직 두 선수의 누적 맞대결 기록이 없습니다.")  # 노란색 경고창 출력
    if st.button("닫기", use_container_width=True):
        st.rerun()

# @st.dialog("제목") (데코레이터)
# 파이썬에서 @ 기호로 시작하는 것을 데코레이터(Decorator)라고 부릅니다.
# 함수 위에 모자처럼 씌워서 해당 함수에 특별한 능력을 부여합니다.
# Streamlit에서 이 데코레이터를 함수 위에 붙이면,
# 해당 함수가 실행될 때 일반적인 화면에 그려지는 것이 아니라
# 화면 중앙에 떠오르는 팝업창(모달창) 형태로 나타나게 됩니다.
# h2h[mask].iloc[0]
# h2h[mask]는 조건에 맞는 행들만 걸러낸 결과물(데이터프레임)입니다.
# .iloc[0]은 "Index Location 0"의 약자로,
# 걸러진 결과물 중 첫 번째 행의 데이터만 쏙 뽑아내어 1차원 데이터(Series) 형태로 가져오라는 뜻입니다.
# 맞대결 기록은 무조건 한 줄만 존재하도록 이전 코드에서 설계했기 때문에 [0]을 사용해 안전하게 데이터를 꺼낼 수 있습니다.
# st.columns(2)와 with 구문
# 화면을 세로로 분할할 때 사용합니다. c1, c2 = st.columns(2)는 화면을 정확히 5:5 비율의 두 칸으로 나눕니다.
# with c1: 아래에 들여쓰기 된 코드는 왼쪽 칸에, with c2: 아래에 작성된 코드는 오른쪽 칸에 그려집니다.
# 이를 통해 두 선수의 전적을 나란히 비교할 수 있습니다.
# st.info()와 st.error()의 시각적 활용
# 원래 st.info()는 정보 전달용(파란색 계열), st.error()는 에러 발생용(빨간색 계열) 알림창입니다.
# 하지만 여기서는 에러가 났다는 뜻이 아니라,
# 두 선수의 데이터를 시각적으로 명확하게 구분(청코너 vs 홍코너 느낌)하기 위해 색상이 다른
# 두 컴포넌트를 디자인적 요소로 활용한 센스 있는 코드입니다.
# st.rerun()
# Streamlit 앱을 강제로 처음부터 다시 실행(새로고침)하는 명령어입니다.
# 팝업창(@st.dialog) 내부에서 st.rerun()이 실행되면,
# 태가 초기화되면서 자연스럽게 팝업창이 닫히는 효과를 낼 수 있습니다.

# ==========================================
# 3. 세션 상태 초기화 (Session State Init)
# ==========================================
# 💡 [상세 설명] Streamlit은 버튼을 누를 때마다 코드를 맨 위부터 다시 읽습니다.
# 이때 'is_admin'이나 'room_name' 같은 정보가 날아가지 않도록 'st.session_state'라는 기억장치에 보관합니다.
# 'not in'을 써서 프로그램이 처음 켜졌을 때 딱 한 번만 기본값을 세팅하게 만듭니다.

# ==========================================
# Streamlit 세션 상태(Session State) 초기화
# 앱이 처음 실행되거나 새로고침될 때, 데이터가 날아가지 않도록 기본값을 세팅하는 과정입니다.
# ==========================================

# 1. 관리자 권한 여부 초기화
# 세션 상태에 'is_admin'이라는 데이터가 없다면 (즉, 앱을 처음 켰다면)
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False  # 처음엔 관리자가 아닌 일반 사용자 모드(False)로 설정

# 2. 구장(방) 이름 초기화
if 'room_name' not in st.session_state:
    st.session_state.room_name = "생활_탁구장"  # 기본 방 이름을 "생활_탁구장"으로 설정

# 3. 메인 선수 명단 데이터 초기화
# load_data() 함수를 호출하여 엑셀이나 CSV 파일 등에서 기본 선수 명단을 불러와 저장
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# 4. 진행 상태(플래그) 초기화
# 출석 체크가 완료되었는지 여부를 저장 (처음엔 안 했으므로 False)
if 'attendance_confirmed' not in st.session_state:
    st.session_state.attendance_confirmed = False

# 게임 설정(코트 수, 경기 방식 등)이 완료되었는지 여부를 저장 (처음엔 안 했으므로 False)
if 'config_confirmed' not in st.session_state:
    st.session_state.config_confirmed = False

# 5. 개인별 누적 전적 표 초기화
# 누적 전적 표가 없다면, 빈 데이터프레임(표)의 뼈대(컬럼명)만 미리 만들어 둠
if 'cum_df' not in st.session_state:
    st.session_state.cum_df = pd.DataFrame(
        columns=['이름', '총경기수', '승', '패', '득점', '실점']
    )

# 6. 1:1 상대 전적(H2H) 표 초기화
# 상대 전적 표가 없다면, 빈 데이터프레임의 뼈대만 미리 만들어 둠
if 'h2h_df' not in st.session_state:
    st.session_state.h2h_df = pd.DataFrame(
        columns=['Player1', 'Player2', 'P1_Win', 'P2_Win', 'P1_Score', 'P2_Score']
    )

# st.session_state (세션 상태)란?
#
# Streamlit은 사용자가 버튼을 누르거나 글자를 입력할 때마다
# 파이썬 코드를 위에서부터 아래로 처음부터 다시 실행하는 독특한 특징이 있습니다.
# 만약 일반적인 변수(예: is_admin = False)를 사용하면,
# 버튼을 누를 때마다 코드가 재실행되면서 기껏 바꿔놓은 값이 다시 False로 초기화되어 버립니다.
# 이를 막기 위해 "앱이 실행되는 동안 절대 지워지지 않는 특별한 보관함"을 제공하는데,
# 이것이 바로 st.session_state입니다.
# if '키' not in st.session_state: 패턴의 중요성
#
# 이 코드는 Streamlit 프로그래밍에서 가장 중요하고 가장 많이 쓰이는 공식 같은 문법입니다.
# "보관함에 이 데이터가 없을 때만(처음 켰을 때만) 기본값을 넣어라"라는 뜻입니다.
# 이 조건문이 없다면, 사용자가 출석 체크를 완료해서 attendance_confirmed를 True로 바꿨더라도,
# 화면이 새로고침될 때마다 다시 False로 덮어씌워지는 대참사가 발생합니다.

# 상태 변수(Flag)의 활용 (False / True)
#
# attendance_confirmed나 config_confirmed 같은 변수들은
# 프로그램의 진행 단계를 제어하는 스위치(Flag) 역할을 합니다.
# 예를 들어, 코드 어딘가에 if st.session_state.attendance_confirmed: 라는 조건문을 걸어두면,
# "출석 체크가 완료된 후에만 다음 화면(대진표 짜기 등)을 보여줘라"와 같은
# 단계별 화면 전환을 아주 쉽게 구현할 수 있습니다.

# 빈 데이터프레임(pd.DataFrame(columns=[...])) 미리 만들기
#
# cum_df와 h2h_df에 빈 표를 미리 만들어두는 이유는 에러를 방지하기 위해서입니다.
# 만약 이 뼈대를 미리 만들어두지 않으면,
# 나중에 경기 결과를 저장하거나 화면에 표를 그리려고 할 때 "그런 표는 존재하지 않습니다"라는 에러가 발생합니다.
# 컬럼(열 이름)만 미리 세팅해 두면, 나중에 데이터가 들어올 때 해당 칸에 맞춰서 차곡차곡 쌓이게 됩니다.



# ==========================================
# 4. DB 연결 (Google Sheets)
# ==========================================
# 1. 구글 시트(Google Sheets)와 연결하는 객체 생성
# Streamlit의 내장 연결 기능(st.connection)을 사용하여 'gsheets'라는 이름의 연결 통로를 만듭니다.
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 안전한 실행을 위한 try-except 구문 시작
try:
    # 3. 구글 시트에서 데이터 읽어오기 (정상 작동 시)
    # 지정된 주소(SHEET_URL)의 "시트1" 워크시트에서 데이터를 읽어와 데이터프레임(db_df)으로 저장합니다.
    # ttl=0은 데이터를 임시 저장(캐시)하지 않고, 매번 최신 상태로 새로고침해서 가져오겠다는 뜻입니다.
    db_df = conn.read(spreadsheet=SHEET_URL, worksheet="시트1", ttl=0)

except Exception as e:
    # 4. 예외 처리: 인터넷 끊김, 권한 없음 등으로 연결에 실패했을 때 실행되는 부분
    # 화면에 붉은색 에러 메시지(st.error)를 띄우고, 파이썬이 알려주는 실제 에러 원인({e})도 함께 보여줍니다.
    st.error(f"⚠️ DB(구글시트) 연결 실패. secrets.toml 설정을 확인하세요 \n {e}")

    # 5. 프로그램 연쇄 붕괴(Crash)를 막기 위한 임시(빈) 데이터프레임 생성
    # DB 연결에 실패하더라도 이후의 코드가 에러 없이 돌아갈 수 있도록,
    # 원래 구글 시트에 있어야 할 열(컬럼) 이름들만 가진 '빈 표'를 대신 만들어 줍니다.
    db_df = pd.DataFrame(columns=["방이름", "관리자이름", "이메일", "비밀번호", "생성일자"])

# st.connection과 GSheetsConnection
# Streamlit에서 외부 데이터베이스(SQL, 구글 시트 등)와 안전하게 연결하기 위해 제공하는 최신 기능입니다.
# GSheetsConnection은 구글 시트를 마치 데이터베이스(DB)처럼 사용할 수 있게 해주는 전용 연결 방식입니다.
# 이를 통해 엑셀 파일을 다운로드할 필요 없이 실시간으로 클라우드 데이터를 읽고 쓸 수 있습니다.
# ttl=0 (Time To Live)
# ttl은 데이터를 메모리에 얼마나 오래 기억해 둘 것인지(캐싱)를 결정하는 옵션입니다.
# 만약 ttl=600이라고 쓰면 10분(600초) 동안은 구글 시트에 다시 접속하지 않고 기억해 둔 데이터를 보여줍니다(속도 향상).
# 하지만 여기서는 **ttl=0**을 주었습니다.
# 이는 "기억하지 말고, 코드가 실행될 때마다 무조건 구글 시트에서 최신 데이터를 가져와라"라는 뜻입니다.
# 회원가입이나 방 생성 등 실시간 반영이 중요한 데이터이기 때문입니다.
# try ... except Exception as e: (예외 처리)
# 외부 인터넷(구글 서버)과 통신하는 코드는 언제든 에러가 발생할 위험이 있습니다.
# (인터넷 끊김, 시트 삭제됨, 비밀번호 틀림 등)
# 이 구문이 없다면 에러 발생 시 화면이 하얗게 변하며 프로그램이 완전히 뻗어버립니다.
# 하지만 try-except로 감싸두면, 에러가 나더라도 프로그램이 죽지 않고 except 아래의 코드를 실행하며 부드럽게 대처할 수 있습니다.
# secrets.toml 이란?
# 에러 메시지에 언급된 secrets.toml은 Streamlit에서 비밀번호나 API 키를 안전하게 숨겨두는 금고 역할을 하는 파일입니다.
# 구글 시트에 접근하려면 구글 서비스 계정의 인증 정보(JSON 키)가 필요한데,
# 이 정보가 secrets.toml에 제대로 입력되어 있지 않으면 연결에 실패하므로 확인하라는 안내 메시지를 넣은 것입니다.
# 빈 데이터프레임(pd.DataFrame(columns=[...]))을 만드는 이유 (안전장치)
# 만약 구글 시트 연결에 실패해서 db_df라는 변수 자체가 아예 생성되지 않으면,
# 그 아래에 있는 코드들(예: if user in db_df['관리자이름']:)이 "db_df가 뭔지 모르겠다"며
# 2차 에러(NameError)를 일으킵니다.
# 따라서 연결에 실패하더라도 내용물만 비어있고 뼈대(컬럼)는 똑같이 생긴 가짜 표를 쥐여줌으로써,
# 이후의 코드들이 에러 없이 "아, 가입된 사람이 0명이구나"라고 자연스럽게 인식하고 넘어가도록 만드는
# 아주 훌륭한 방어적 프로그래밍 기법입니다.

# ---------------------------------------------------------
# 🔴 [로그인 전] 사이드바 화면 (탭 2개가 보임)
# ---------------------------------------------------------
# 💡 [상세 설명] 세션 상태(기억장치)에 저장된 값을 꺼내서 변수에 담아줍니다.
# 이렇게 해야 화면이 새로고침 되어도 로그인 상태가 유지됩니다.

# 세션 상태에서 현재 관리자 여부와 접속 중인 구장 이름을 가져와 변수에 저장합니다.
is_admin = st.session_state.is_admin
room_name = st.session_state.room_name

# ==========================================
# 🔴 [로그인 전] 관리자가 아닐 때 보여지는 사이드바 화면
# ==========================================
if not is_admin:
    st.sidebar.markdown("### 🏟️ 구장 접속 및 생성")

    # 사이드바 안에 '기존 구장 접속'과 '새 구장 만들기'라는 2개의 탭(Tab)을 만듭니다.
    tab_login, tab_create = st.sidebar.tabs(["🔑 기존 구장 접속", "➕ 새 구장 만들기"])

    # ---------------------------------
    # [로그인 탭] 기존에 만든 구장에 접속할 때
    # ---------------------------------
    with tab_login:
        # 구장 이름과 비밀번호를 입력받습니다. (비밀번호는 type="password"로 설정해 별표(*)로 가려짐)
        login_room_name = st.text_input("구장명 (방 이름)", value="생활_탁구장", key="login_room")
        admin_password = st.text_input("관리자 비밀번호 (조회 시 생략 가능)", type="password", key="login_pw")

        # 로그인 버튼을 누르면 실행됨 (use_container_width=True로 버튼을 가로로 꽉 차게 만듦)
        if st.button("로그인 / 접속", use_container_width=True):
            st.session_state.room_name = login_room_name  # 입력한 방 이름을 세션에 저장

            if admin_password:  # 비밀번호를 입력했다면 (관리자 접속 시도)
                hashed_pw = hash_password(admin_password)  # 입력한 비밀번호를 암호화(해시) 처리

                # 1. 마스터 비밀번호(개발자용 만능 키)와 일치하는지 확인
                if hashed_pw == HASHED_MASTER_PW:
                    st.session_state.is_admin = True
                    st.sidebar.success("👑 마스터 권한으로 접속했습니다.")
                    time.sleep(1)  # 메시지를 읽을 수 있게 1초 대기
                    st.rerun()  # 💡 화면을 새로고침하여 관리자용 사이드바로 변경!

                # 2. DB(구글시트)에 해당 방 이름이 존재하는지 확인
                elif login_room_name in db_df['방이름'].values:
                    # 해당 방의 저장된 비밀번호를 DB에서 가져옴
                    saved_pw = db_df.loc[db_df['방이름'] == login_room_name, '비밀번호'].values[0]

                    if hashed_pw == saved_pw:  # 비밀번호가 일치하면
                        st.session_state.is_admin = True  # 관리자 권한 부여
                        st.sidebar.success(f"✅ '{login_room_name}' 관리자 모드 활성화")
                        time.sleep(1)
                        st.rerun()  # 💡 화면 새로고침!
                    else:
                        st.sidebar.error("❌ 비밀번호가 틀렸습니다.")
                else:
                    st.sidebar.warning("⚠️ 존재하지 않는 방입니다. [새 방 만들기] 탭을 이용해주세요.")
            else:
                # 비밀번호를 입력하지 않고 버튼을 누르면 일반 사용자(조회 전용) 모드로 접속
                st.sidebar.info("👀 현재 조회 전용(Read-only) 모드입니다.")

    # ---------------------------------
    # [생성 탭] 새로운 구장을 만들 때
    # ---------------------------------
    with tab_create:
        st.markdown("#### ✨ 새로운 구장 등록")
        # 새 구장 정보를 입력받음
        new_room_name = st.text_input("새로 만들 구장명 (중복 불가)")
        admin_name = st.text_input("관리자 이름 (대표자명)")
        admin_email = st.text_input("관리자 이메일 (비밀번호 분실 시 필요)")
        new_room_pw = st.text_input("새 구장 비밀번호 설정", type="password", key="create_pw")

        # type="primary"를 주어 버튼 색상을 눈에 띄게(파란색/빨간색 등 테마색) 만듦
        if st.button("새 구장 생성하기", type="primary", use_container_width=True):
            # 빈칸이 하나라도 있는지 검사
            if not new_room_name or not admin_name or not admin_email or not new_room_pw:
                st.warning("모든 정보를 빠짐없이 입력해주세요.")
            # 이미 존재하는 방 이름인지 검사
            elif new_room_name in db_df['방이름'].values:
                st.error(f"⚠️ '{new_room_name}'(은)는 이미 존재하는 구장입니다.")
            else:
                # 모든 검사를 통과하면 비밀번호를 암호화하고 새 데이터를 표(DataFrame) 형태로 만듦
                hashed_pw = hash_password(new_room_pw)
                new_data = pd.DataFrame([{
                    "방이름": new_room_name, "관리자이름": admin_name, "이메일": admin_email,
                    "비밀번호": hashed_pw, "생성일자": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                # 기존 DB 표(db_df) 아래에 새 데이터를 이어 붙임
                updated_df = pd.concat([db_df, new_data], ignore_index=True)

                try:
                    # 구글 시트에 업데이트된 표를 덮어쓰기하여 저장
                    conn.update(spreadsheet=SHEET_URL, worksheet="시트1", data=updated_df)

                    # 방금 만든 방으로 세션 상태를 변경하고 관리자 권한 부여
                    st.session_state.room_name = new_room_name
                    st.session_state.is_admin = True
                    st.success(f"✅ '{new_room_name}' 구장이 생성되었습니다! 자동으로 관리자 모드로 입장합니다.")

                    time.sleep(1.5)  # 사용자가 성공 메시지를 읽을 수 있도록 1.5초 대기
                    st.rerun()  # 화면을 새로고침하여 즉시 관리자 모드 화면으로 진입!

                except Exception as e:
                    st.error(f"DB 저장 중 오류가 발생했습니다: {e}")

# ==========================================
# 🟢 [로그인 후] 관리자일 때 보여지는 사이드바 화면
# ==========================================
else:
    # 로그인/생성 탭은 사라지고, 현재 접속 중인 구장 이름과 로그아웃 버튼만 보임
    st.sidebar.markdown(f"### 🏟️ {room_name} 구장")
    st.sidebar.success("👑 관리자 모드로 접속 중입니다.")

    # 로그아웃 버튼
    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state.is_admin = False  # 관리자 권한 박탈
        st.rerun()  # 새로고침하여 다시 [로그인 전] 화면으로 돌아감

# 사이드바에 가로줄(구분선) 긋기
st.sidebar.divider()

# ==========================================
# 🔵 공통 기능: 최신 데이터 불러오기 (관리자/일반인 모두 보임)
# ==========================================
if st.sidebar.button("🔄 최신 경기결과 불러오기", type="primary"):
    # 이전 질문에서 설명했던 load_room_state 함수를 실행하여 pkl 파일에서 데이터를 복구
    if load_room_state(room_name):
        st.sidebar.success(f"'{room_name}' 구장의 데이터를 불러왔습니다.")
    else:
        st.sidebar.warning("저장된 구장 데이터가 없습니다.")

st.sidebar.divider()

# ==========================================
# 🟡 관리자 전용 기능: 데이터 파일(CSV) 수동 업로드
# ==========================================
if is_admin:
    st.sidebar.markdown("### 📁 데이터 파일 업로드")

    # 1. 명단 파일 업로드
    # st.file_uploader를 사용해 사용자 컴퓨터에서 파일을 선택할 수 있는 버튼 생성
    uploaded_file = st.sidebar.file_uploader("1. 명단 파일(CSV) 업로드")
    # 파일이 정상적으로 올라왔고, 확장자가 .csv로 끝나는지 확인
    if uploaded_file and uploaded_file.name.lower().endswith('.csv'):
        if st.sidebar.button("명단 적용하기"):
            st.session_state.main_df = load_data(uploaded_file)  # 파일을 읽어 세션에 저장
            st.sidebar.success("새로운 명부가 적용되었습니다.")
            st.rerun()  # 새로고침하여 화면에 반영

    # 2. 누적 결과 업로드
    cum_file = st.sidebar.file_uploader("2. 기존 누적 결과(CSV) 업로드")
    if cum_file and cum_file.name.lower().endswith('.csv'):
        if st.sidebar.button("누적 데이터 적용"):
            # 한글 깨짐 방지를 위해 encoding='utf-8-sig' 옵션을 주어 CSV 파일을 읽음
            st.session_state.cum_df = pd.read_csv(cum_file, encoding='utf-8-sig')
            st.sidebar.success("누적 데이터가 연동되었습니다.")
            st.rerun()

    # 3. 상대 전적 업로드
    h2h_file = st.sidebar.file_uploader("3. 누적 상대전적(CSV) 업로드")
    if h2h_file and h2h_file.name.lower().endswith('.csv'):
        if st.sidebar.button("상대전적 데이터 적용"):
            st.session_state.h2h_df = pd.read_csv(h2h_file, encoding='utf-8-sig')
            st.sidebar.success("상대전적 데이터가 연동되었습니다.")
            st.rerun()


# 상태에 따른 UI 동적 변경 (if not is_admin: vs else:)
# Streamlit의 가장 강력한 특징 중 하나입니다.
# is_admin 변수가 False일 때는 로그인/회원가입 화면을 보여주고,
# True가 되는 순간 코드가 재실행되면서 로그인 화면은 싹 사라지고
# 관리자 전용 메뉴(로그아웃, 파일 업로드 등)가 나타납니다.
# 마치 웹사이트에서 로그인 전후로 상단 메뉴바가 바뀌는 것과 완벽히 동일한 원리입니다.
# st.sidebar.tabs([...]) (탭 기능)
# 사이드바 공간은 좁기 때문에 모든 입력창을 세로로 나열하면 스크롤이 너무 길어집니다.
# tabs를 사용하면 "로그인"과 "새 구장 만들기"를 겹쳐놓고 클릭할 때마다 화면이 전환되게 만들어,
# 좁은 공간을 아주 효율적이고 깔끔하게 사용할 수 있습니다.
# hash_password(admin_password) (비밀번호 암호화)
# 사용자가 입력한 비밀번호(예: 1234)를 구글 시트에 그대로 저장하면,
# 관리자나 해커가 시트를 열어봤을 때 남의 비밀번호를 훔쳐볼 수 있습니다.
# 이를 막기 위해 hash_password 함수를 거쳐 a8f5f167f4... 같은 복잡한 문자열로 변환(해싱)하여 저장하고,
# 로그인할 때도 입력한 값을 똑같이 변환해서 두 복잡한 문자열이 일치하는지만 비교합니다.
# (보안의 기본 원칙)
# time.sleep(1)과 st.rerun()의 환상적인 콤보 (UX 패턴)
# 로그인이나 방 생성에 성공했을 때 바로 st.rerun()을 해버리면,
# 화면이 너무 빨리 새로고침되어 사용자는 "성공했습니다!"라는 초록색 메시지를 읽을 새도 없이 화면이 넘어가 버립니다.
# 그래서 time.sleep(1)을 주어 1초 동안 코드를 멈춰서 사용자가 성공 메시지를 읽고 안도감을 느끼게 한 뒤
# , st.rerun()으로 화면을 전환하는 아주 디테일한 사용자 경험(UX) 설계입니다.
# st.file_uploader (파일 업로드)
# 사용자의 PC에 있는 엑셀/CSV 파일을 웹 브라우저로 끌어다 놓거나 클릭해서 업로드할 수 있게 해주는 기능입니다.
# 업로드된 파일은 pd.read_csv(파일, encoding='utf-8-sig')를 통해 즉시 데이터프레임(표)으로 변환됩니다.
# 여기서 utf-8-sig는 엑셀에서 만든 한글 CSV 파일이 파이썬에서 글자가 깨지지 않도록 막아주는 마법의 옵션입니다.


# 시합 일자 및 부수 조정 기준 선택
# ==========================================
# 시합 일자 및 부수 조정 기준 선택
# ==========================================

# 달력 위젯을 띄워 시합 날짜를 선택합니다. (기본값: 오늘 날짜)
# disabled=not is_admin: 관리자가 아니면(일반 사용자면) 날짜를 바꿀 수 없게 비활성화(회색 처리)합니다.
selected_date = st.date_input("시합 일자 선택", datetime.now(), disabled=not is_admin)

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

# 사이드바에서 부수(핸디캡)를 조정할 기준을 선택합니다. (관리자만 선택 가능)
selected_adj = st.sidebar.selectbox("부수 조정 기준", ["부수_조정1", "부수_조정2", "부수_조정3"], disabled=not is_admin)

# ==========================================
# 메인 화면 UI (Tabs 구성)
# ==========================================
# 화면 상단에 6개의 탭(메뉴)을 만들어 각각의 변수에 할당합니다.
tab_home, tab_config, tab_team, tab_match, tab_score, tab_help = st.tabs(
    [" 출석체크", " 운영 설정", " 조 편성 결과", " 경기 배정", " 스코어보드", "사용설명서"])

# 오늘 날짜 열(col_date)에서 값이 'Y'인 사람의 수를 세어 현재 참석 인원을 계산합니다.
attendees_count = (
        st.session_state.main_df[col_date] == 'Y').sum() if col_date in st.session_state.main_df.columns else 0

# ==========================================
# 탭 1: 출석체크 화면 구성
# ==========================================
with tab_home:
    st.markdown(f"### 📋 {CURRENT_DATE} 참석 현황")

    # 원본 데이터를 건드리지 않기 위해 복사본(copy)을 만듭니다.
    df = st.session_state.main_df.copy()

    # 화면에 체크박스(☑️)로 보여주기 위해 'Y'/'N' 문자를 파이썬의 True/False(참/거짓)로 바꿉니다.
    df['참석'] = df[col_date].apply(lambda x: True if x == 'Y' else False)

    # 명단이 너무 길면 스크롤이 힘드므로, 화면을 좌/우 두 줄로 나누기 위해 중간 지점(인덱스)을 계산합니다.
    # len(df) % 2 를 더해주는 이유는, 총인원이 홀수일 때 왼쪽 줄에 한 명을 더 배치하기 위함입니다.
    mid_idx = len(df) // 2 + (len(df) % 2)

    # 화면을 정확히 5:5 비율의 두 칸(col1, col2)으로 나눕니다.
    col1, col2 = st.columns(2)

    # st.data_editor: 엑셀처럼 화면에서 직접 데이터를 수정할 수 있게 해주는 강력한 기능입니다.
    with col1:
        # 처음부터 중간(mid_idx)까지의 사람들을 왼쪽에 배치
        edited_left = st.data_editor(df.iloc[:mid_idx][['순서', '이름', '참석', '부수', selected_adj]],
                                     hide_index=True, disabled=not is_admin)
    with col2:
        # 중간부터 끝까지의 사람들을 오른쪽에 배치
        edited_right = st.data_editor(df.iloc[mid_idx:][['순서', '이름', '참석', '부수', selected_adj]],
                                      hide_index=True, disabled=not is_admin)

    # 사용자가 화면에서 체크박스를 껐다 켰다 수정한 좌/우 데이터를 다시 하나의 표로 합칩니다.
    edited_df = pd.concat([edited_left, edited_right], ignore_index=True)

    # 참석(True)으로 체크된 사람만 골라냅니다.
    current_checked = edited_df[edited_df['참석'] == True]

    # 참석자들의 이름을 가나다순으로 정렬한 뒤, 쉼표(,)로 연결하여 한 줄의 문장으로 만듭니다.
    live_names = ", ".join(sorted(current_checked['이름'].tolist()))

    # 파란색 정보창에 총 참석 인원과 명단을 실시간으로 보여줍니다.
    st.info(f"<strong>현재 참석 ({len(current_checked)}명):</strong> {live_names}")

    # ------------------------------------------
    # 관리자 전용 기능: 출석 확정 및 다운로드
    # ------------------------------------------
    if is_admin:
        # 이미 확정 버튼을 눌렀다면 버튼 이름과 색상(primary/secondary)을 바꿉니다.
        btn_label = "확정 완료 (참석자 저장됨)" if st.session_state.attendance_confirmed else "참석자 확정하기"
        btn_type = "primary" if st.session_state.attendance_confirmed else "secondary"

        # 확정 버튼을 눌렀을 때 실행되는 부분
        if st.button(btn_label, type=btn_type, use_container_width=True):
            # 화면에서 수정한 True/False 값을 다시 원본 데이터용 'Y'/'N'으로 되돌려 저장합니다.
            st.session_state.main_df[col_date] = edited_df['참석'].apply(lambda x: 'Y' if x else 'N')
            st.session_state.attendance_confirmed = True  # 출석 확정 상태로 변경
            save_room_state(room_name)  # 변경된 데이터를 파일(pkl)로 영구 저장
            st.rerun()  # 화면 새로고침

        st.divider()  # 가로줄 긋기
        st.markdown("#### 💾 최신 명단 다운로드")

        # 현재까지의 모든 데이터(출석 기록 포함)를 CSV 파일 형태로 변환합니다. (한글 깨짐 방지 utf-8-sig)
        csv_main = st.session_state.main_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

        # 다운로드 버튼 생성 (클릭 시 사용자의 PC로 파일이 다운로드됨)
        st.download_button(label="📥 최신 명단(CSV) 다운로드", data=csv_main,
                           file_name=f"{room_name}_최신명단_{CURRENT_DATE}.csv",
                           mime="text/csv", type="primary", use_container_width=True)

# disabled=not is_admin (권한 제어)
# Streamlit의 입력 위젯(날짜 선택, 체크박스, 버튼 등)에는 disabled라는 옵션이 있습니다.
# 이 값이 True가 되면 위젯이 회색으로 변하며 클릭할 수 없게 됩니다.
# is_admin이 False(일반 사용자)일 때 not is_admin은 True가 되므로,
# 일반 사용자는 화면을 볼 수는 있지만 날짜를 바꾸거나 출석 체크박스를 누를 수는 없게
# 완벽히 통제하는 아주 깔끔한 코드입니다.
# apply(lambda x: ...) (데이터 정제 마법사)
# 엑셀로 명단을 취합하다 보면 사람마다 참석 표시를 'Y', 'O', '1', '참석' 등 제멋대로 적는 경우가 많습니다.
# lambda x:는 표의 각 칸에 있는 데이터를 하나씩 꺼내서 검사하는 한 줄짜리 미니 함수입니다.
# .strip().upper()를 통해 띄어쓰기를 없애고 모두 대문자로 바꾼 뒤,
# 우리가 지정한 리스트 ['Y', 'O', '1', 'TRUE', '참석'] 안에 그 글자가 포함되어 있으면
# 무조건 깔끔한 'Y'로 통일해 주는 훌륭한 전처리 기법입니다.
# st.data_editor (인터랙티브 데이터 표)
# 단순히 표를 보여주기만 하는 st.dataframe과 달리,
# 사용자가 엑셀처럼 화면에서 직접 값을 수정할 수 있게 해주는 Streamlit의 핵심 기능입니다.
# 특히 데이터가 True/False(Boolean) 형태일 경우, Streamlit이 알아서 이를 체크박스(☑️) 모양으로 바꿔서 보여줍니다.
# 덕분에 복잡한 코딩 없이도 아주 직관적인 출석체크 UI를 만들 수 있습니다.
# mid_idx = len(df) // 2 + (len(df) % 2) (화면 분할 수학)
# 명단이 30명이면 세로로 너무 길어지므로 15명씩 좌우로 나누기 위한 계산입니다.
# //는 나눗셈의 몫, %는 나머지를 구합니다.
# 만약 총 31명이라면? 31 // 2는 15이고, 31 % 2는 1입니다. 둘을 더하면 16이 됩니다.
# 즉, 왼쪽 줄에 16명, 오른쪽 줄에 15명을 배치하여 홀수일 때도 에러 없이 예쁘게 화면을 나눌 수 있습니다.
# st.download_button과 utf-8-sig
# 웹에서 만들어진 데이터를 사용자의 컴퓨터로 다운로드하게 해주는 버튼입니다.
# 파이썬에서 만든 CSV 파일을 한국의 윈도우 엑셀(Excel)에서 열면 한글이 외계어처럼 깨지는 현상이 자주 발생합니다.
# 이를 막기 위해 .encode('utf-8-sig')라는 특별한 인코딩 방식을 씌워주면
# 엑셀에서도 한글이 완벽하게 보이게 됩니다.


# ------------------------------------------
# 탭 2: 운영 설정
# ------------------------------------------
# ==========================================
# 탭 2: 운영 설정 및 제비뽑기 화면
# ==========================================
with tab_config:
    # 출석체크 탭에서 계산된 총 참석 인원을 파란색 정보창으로 띄워줍니다.
    st.info(f"👥 현재 확정된 참석 인원: **{attendees_count}명**")

    # CSS 스타일을 적용하기 위해 HTML div 태그를 엽니다.
    st.markdown('<div class="setting-banner">', unsafe_allow_html=True)

    # 화면을 5개의 단(Column)으로 나눕니다.
    # [1.2, 1.2, 1.2, 1.2, 1.5]는 각 단의 가로 비율을 의미합니다. (마지막 버튼 칸을 조금 더 넓게)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5])

    # ------------------------------------------
    # 1. 조 구성 설정 (몇 개의 조로 나눌 것인가?)
    # ------------------------------------------
    with c1:
        st.markdown(f"#### 👥 조 구성")
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

    # ------------------------------------------
    # 2. 경기 규칙 설정 (단식/복식 개수, 몇 세트 선승제?)
    # ------------------------------------------
    with c2:
        st.markdown("#### 🎾 경기 규칙")
        s_g = st.number_input("단식 게임", 0, 10, 2, disabled=not is_admin)
        d_g = st.number_input("복식 게임", 0, 5, 1, disabled=not is_admin)
        set_c = st.selectbox("개인전 선승 세트", [2, 3, 4, 5], index=1, disabled=not is_admin)  # index=1은 '3'을 기본값으로

    # ------------------------------------------
    # 3. 탁구대 수 설정
    # ------------------------------------------
    with c3:
        st.markdown("#### ⚙️ 환경 설정")
        t_val = st.number_input("Table_No.", 1, 20, 3, disabled=not is_admin)

    # ------------------------------------------
    # 4. 조 편성 방식 (AI 자동 vs 제비뽑기)
    # ------------------------------------------
    with c4:
        st.markdown("#### 🎲 방식")
        # 라디오 버튼으로 둘 중 하나를 선택하게 합니다.
        draw_method = st.radio("방식", ["AI 선정", "제비뽑기"], label_visibility="collapsed", disabled=not is_admin)

    # ------------------------------------------
    # 5. 설정 확정 및 저장 버튼
    # ------------------------------------------
    with c5:
        st.markdown("#### ✅ 실행")
        if is_admin:
            btn_label = "설정 확정 완료" if st.session_state.config_confirmed else "설정 확정 및 편성 시작"
            btn_type = "primary" if st.session_state.config_confirmed else "secondary"

            if st.button(btn_label, type=btn_type, use_container_width=True):
                # 위에서 설정한 모든 값들을 'config'라는 하나의 딕셔너리(보따리)에 담아 세션에 저장합니다.
                st.session_state.config = {
                    "g": g_val, "t": t_val, "s_games": s_g, "d_games": d_g, "set_count": set_c,
                    "total_g": s_g + d_g, "draw_method": draw_method, "selected_adj": selected_adj,
                    # 동점자 처리를 위해 모든 사람에게 0\~1 사이의 랜덤 숫자를 미리 부여해 둡니다.
                    "tie_breakers": {name: random.random() for name in st.session_state.main_df['이름']}
                }
                st.session_state.config_confirmed = True  # 설정 완료 플래그 켜기
                save_room_state(room_name)  # 파일로 영구 저장
                st.rerun()  # 새로고침
        else:
            st.info("관리자 전용")  # 일반 사용자에게는 버튼 대신 안내문구 표시

    st.markdown('</div>', unsafe_allow_html=True)  # CSS div 태그 닫기

    # ==========================================
    # 6. 제비뽑기(수동/랜덤 조 편성) 로직
    # ==========================================
    # 설정이 완료되었고, 선택한 방식이 '제비뽑기'일 때만 아래 코드가 실행됩니다.
    if "config" in st.session_state and st.session_state.config.get('draw_method') == '제비뽑기':

        # 아직 제비뽑기가 완전히 끝나지 않았다면
        if not st.session_state.get('draw_completed', False):
            st.divider()
            cfg = st.session_state.config
            adj_col = cfg['selected_adj']
            df = st.session_state.main_df

            # 참석자 명단만 추려냅니다.
            attendees = df[df[col_date] == 'Y'].copy()
            # '1부', '2부' 같은 글자에서 숫자만 뽑아냅니다. (정렬을 위해)
            attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
            # 아까 만들어둔 랜덤 숫자를 매칭합니다.
            attendees['Random'] = attendees['이름'].map(cfg['tie_breakers'])

            # 💡 핵심: 실력이 비슷한 사람끼리 묶기 위해 부수 -> 조정부수 -> 랜덤 순으로 줄을 세웁니다.
            sorted_members = attendees.sort_values(['부수_숫자', adj_col, 'Random'], ascending=True).reset_index(drop=True)

            # 총 몇 개의 실력 그룹(레벨)이 나오는지 계산합니다. (예: 16명이고 4조면 4개의 그룹)
            total_levels = math.ceil(len(sorted_members) / cfg['g'])

            # 현재 몇 번째 그룹(레벨)의 제비뽑기를 진행 중인지 추적합니다. (처음엔 0)
            draw_level = st.session_state.get('draw_level', 0)

            st.markdown("### 제비뽑기 진행 현황")

            # 각 실력 그룹(레벨)별로 반복문을 돌며 화면을 그립니다.
            for level in range(total_levels):
                # 현재 그룹에 속할 사람들의 시작 번호와 끝 번호를 계산하여 잘라냅니다.
                start_idx = level * cfg['g']
                end_idx = min((level + 1) * cfg['g'], len(sorted_members))
                current_group = sorted_members.iloc[start_idx:end_idx]
                group_members = current_group['이름'].tolist()

                st.markdown(f"#### 그룹 {level + 1}")
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
                    available_options = list(range(1, cfg['g'] + 1))  # [1, 2, 3, 4] 조
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
                        new_val = st.session_state[f"select_{lvl}_{changed_member}"]  # 방금 선택한 조
                        old_val = prev_selections[changed_member]  # 원래 가지고 있던 조

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
                                random.shuffle(shuffled_options)  # 조 번호를 마구 섞음
                                for i, name in enumerate(group_members):
                                    st.session_state.draw_results[name] = shuffled_options[i]
                                st.session_state.draw_level += 1  # 다음 그룹으로 넘어감
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
            st.success(" 제비뽑기가 모두 완료되었습니다! 상단의 <strong>'조 편성 결과'</strong> 탭으로 이동하여 결과를 확인해주세요.")

            # 다시 하기 버튼 (모든 제비뽑기 관련 세션 데이터를 초기화함)
            if is_admin and st.button(" 제비뽑기 다시 하기", type="secondary"):
                st.session_state.draw_level = 0
                st.session_state.draw_results = {}
                st.session_state.draw_completed = False
                for key in list(st.session_state.keys()):
                    if key.startswith("group_selections_") or key.startswith("select_"):
                        del st.session_state[key]
                st.rerun()

# st.columns([1.2, 1.2, 1.2, 1.2, 1.5]) (비율 분할)
# 이전에는 st.columns(2)처럼 숫자 하나만 넣어서 5:5로 똑같이 나누었습니다.
# 하지만 리스트 형태로 숫자를 넣으면 원하는 비율대로 화면을 쪼갤 수 있습니다.
# 여기서는 마지막 '실행' 버튼이 들어갈 칸을 다른 칸들보다 조금 더 넓게(1.5 비율)
# 설정하여 디자인적 안정감을 주었습니다.
# st.session_state.config (설정값 보따리)
# 조 개수, 탁구대 수, 경기 방식 등 여러 개의 설정값을 각각 따로 저장하면 관리가 힘듭니다.
# 그래서 config라는 하나의 딕셔너리(Dictionary)를 만들고,
# 그 안에 모든 설정값을 이름표를 붙여 한꺼번에 담아두는 방식을 사용했습니다.
# 이렇게 하면 나중에 cfg = st.session_state.config 한 줄만으로 모든 설정값을 쉽게 꺼내 쓸 수 있습니다.
# 실력별 그룹화 정렬 (sort_values(['부수_숫자', adj_col, 'Random']))
# 이 제비뽑기 시스템의 핵심 로직입니다. 아무나 막 섞어서 조를 짜면 1조에 고수만 몰리는 불상사가 생길 수 있습니다.
# 이를 막기 위해 1차로 부수(실력) 순으로 줄을 세우고,
# 2차로 조정 부수, 3차로 랜덤 숫자(동점자 처리용)를 기준으로 사람들을 일렬로 세웁니다.
# 그리고 위에서부터 4명씩(조 개수만큼) 끊어서 '그룹 1(최상위 고수들)', '그룹 2(중수들)'를 만듭니다.
# 각 그룹 안에서만 제비뽑기를 진행하므로, 모든 조에 고수 1명, 중수 1명, 하수 1명이
# 골고루 분배되는 완벽한 밸런스를 맞출 수 있습니다.
# on_selection_change (중복 선택 방지 콜백 함수)
# 화면에서 드롭다운(Selectbox)으로 조를 선택할 때, 한 그룹 내에서 두 명이 똑같이 '1조'를 선택하면 안 됩니다.
# 이 함수는 "맞교환(Swap)" 로직을 구현한 것입니다.
# 예를 들어 철수가 1조, 영희가 2조를 가지고 있었는데, 철수가 드롭다운을 눌러 '2조'로 바꿔버리면?
# 프로그램이 이를 감지하고 영희의 조를 철수가 원래 가지고 있던 '1조'로 강제로 바꿔버립니다.
# 이를 통해 절대 중복된 조가 발생하지 않도록 막아줍니다.
# 단계별 UI 렌더링 (draw_level)
# draw_level이라는 변수를 통해 현재 몇 번째 그룹이 제비뽑기를 하고 있는지 기억합니다.
# level < draw_level: 이미 끝난 그룹은 초록색 글씨로 결과만 보여줍니다.
# level == draw_level: 현재 진행 중인 그룹은 조를 선택할 수 있는 드롭다운과 버튼을 보여줍니다.
# level > draw_level: 아직 차례가 안 온 그룹은 회색 점선 박스로 대기 중임을 보여줍니다.
# 이러한 조건문을 통해 사용자가 한 단계씩 차근차근 진행하는 듯한 훌륭한 사용자 경험(UX)을 제공합니다.

# ------------------------------------------
# 탭 3: 조 편성 결과
# ------------------------------------------
with tab_team:
    if "config" not in st.session_state:
        st.warning("먼저 '운영 설정'을 완료해주세요.")
    else:
        st.info(f"👥 현재 확정된 참석 인원: **{attendees_count}명**")
        cfg = st.session_state.config
        df = st.session_state.main_df
        attendees = df[df[col_date] == 'Y'].copy()
        attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
        sorted_members = attendees.sort_values(['부수_숫자', '부수_조정1'], ascending=True).reset_index(drop=True)

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

        # 제비뽑기 방식: 저장된 결과대로 배정
        else:
            for idx, row in sorted_members.iterrows():
                name = row['이름']
                t_idx = st.session_state.draw_results.get(name, 1)
                teams[t_idx].append(f"{row['이름']}({row['부수']})")
                all_member_names.append(row['이름'])
                team_stats[t_idx]["sum"] += row['부수_숫자']
                team_stats[t_idx]["count"] += 1

        # 조당 평균 인원이 1.5명 이하이면 '개인전'으로 간주
        avg_p = sum(t["count"] for t in team_stats.values()) / cfg['g'] if cfg['g'] > 0 else 0
        st.session_state.config['is_individual'] = True if avg_p <= 1.5 else False
        st.session_state.labels = [f"{i}조({teams[i][0].split('(')[0]})" for i in range(1, cfg['g'] + 1) if teams[i]]
        st.session_state.teams = teams

        st.markdown("### 조별 최종 구성 및 부수 합계")
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

# ------------------------------------------
# 탭 4: 경기 배정 및 결과 입력
# ------------------------------------------
# ==========================================
# 탭 4: 경기 배정 및 스코어 입력 화면
# ==========================================
with tab_match:
    # 조 편성이 완료되어 세션에 'labels'(조 이름 목록)와 'matrix'(점수판)가 존재할 때만 실행
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:

        # ------------------------------------------
        # 1. 라운드 로빈(풀리그) 대진표 생성 알고리즘 (Circle Method)
        # ------------------------------------------
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


        # 모든 경기 대진표를 생성합니다.
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

        # ------------------------------------------
        # 2. 화면에 보여줄 대진표 데이터(표) 만들기
        # ------------------------------------------
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
            st.markdown("### 경기 배정표")
        with col_info:
            st.info(" <strong>아래 표에서 결과를 입력할 경기의 행(Row)을 클릭</strong>하면 상세 입력창이 나타납니다.")

        # ------------------------------------------
        # 3. 인터랙티브(클릭 가능한) 데이터프레임 렌더링
        # ------------------------------------------
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

        # ------------------------------------------
        # 4. 특정 경기를 클릭했을 때 나타나는 하단 점수 입력창
        # ------------------------------------------
        if selected_match_idx is not None:
            team_a, team_b = all_matches[selected_match_idx]
            st.divider()
            st.markdown(f"### 🎯 {team_a} VS {team_b} 상세 결과 입력")

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

                            save_room_state(room_name)
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

                    # 💡 중복 출전 방지를 위한 고유 키(Key) 목록 생성
                    # 단식 1, 단식 2, 복식 1 등 모든 입력창의 ID를 미리 리스트로 만들어 둡니다.
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
                        st.markdown("##### 👤 단식 경기")
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
                            match_results.append(("S", p_a, s_a, s_b, p_b))  # 단식(S) 결과 임시 저장

                    # 복식 입력창 생성 (단식과 원리는 같으나 선수를 2명씩 고름)
                    if d_games > 0:
                        st.markdown("##### 👥 복식 경기")
                        for d in range(d_games):
                            c1, c2, c3, c4, c5 = st.columns([1, 2.5, 1.5, 2.5, 2.5])
                            with c1: st.markdown(f"<div style='font-weight:bold; color:#ff7f0e;'>복식 {d + 1}</div>",
                                                 unsafe_allow_html=True)
                            with c2:
                                k_a1 = f"m{m_idx}_d_pa1_{d}"
                                p_a1 = st.selectbox(f"{team_a} 선수1", get_avail(team_a_players, k_a1, a_keys), key=k_a1,
                                                    label_visibility="collapsed")
                                k_a2 = f"m{m_idx}_d_pa2_{d}"
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
                                k_b1 = f"m{m_idx}_d_pb1_{d}"
                                p_b1 = st.selectbox(f"{team_b} 선수1", get_avail(team_b_players, k_b1, b_keys), key=k_b1,
                                                    label_visibility="collapsed")
                                k_b2 = f"m{m_idx}_d_pb2_{d}"
                                p_b2 = st.selectbox(f"{team_b} 선수2", get_avail(team_b_players, k_b2, b_keys), key=k_b2,
                                                    label_visibility="collapsed")

                            s_a, s_b = map(int, selected_score.split(':'))
                            match_results.append(("D", (p_a1, p_a2), s_a, s_b, (p_b1, p_b2)))  # 복식(D) 결과 임시 저장

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
                                    update_cumulative_record(p_a, p_b, s_a, s_b)  # 누적 전적 업데이트

                                # 조(팀)의 총 승수 계산
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

                        save_room_state(room_name)  # 파일 저장
                        st.success(f"저장 완료! {team_a} ({team_a_wins}) : ({team_b_wins}) {team_b} 결과가 스코어보드에 반영되었습니다.")
                        st.rerun()
    else:
        st.info("조 편성이 완료되면 경기 배정표가 나타납니다.")

# 라운드 로빈 알고리즘 (get_matches 함수)
#
# 모든 팀이 서로 한 번씩 맞붙는 '풀리그' 대진표를 짜는 수학적 방법인
# '서클 메서드(Circle Method)'를 코드로 구현한 것입니다.
# 팀이 1, 2, 3, 4번이 있다면, 1번은 자리에 고정해 두고 나머지 2, 3, 4번을
# 시계 방향으로 한 칸씩 돌려가며 마주 보는 팀끼리 짝을 짓습니다.
# 팀이 홀수(예: 5팀)일 경우, 가상의 팀인 None(부전승)을 하나 추가해서 짝수로 만든 뒤 똑같이 돌립니다.
# 그리고 None과 짝이 된 팀은 그 라운드에서 쉬게 됩니다.
# 인터랙티브 데이터프레임 (on_select="rerun")
#
# 과거의 Streamlit은 표를 단순히 '보여주기만' 할 수 있었습니다.
# 하지만 최근 업데이트로 표의 특정 행(Row)을 클릭할 수 있게 되었습니다.
# on_select="rerun" 옵션을 주면, 사용자가 표에서 '1조 vs 2조' 줄을
# 클릭하는 순간 코드가 처음부터 다시 실행(rerun)됩니다.
# 이때 event_left.selection.rows를 통해 "아, 방금 사용자가 3번째 줄을 클릭했구나!"라는 정보를 알아내고,
# 그 아래에 3번째 경기(1조 vs 2조)의 점수를 입력할 수 있는 상세 UI를
# 짠! 하고 나타나게 만드는 아주 세련된 기법입니다.
# 중복 출전 방지 로직 (get_avail 함수)
#
# 단체전에서 한 선수가 단식 1번에도 나가고,
# 복식 1번에도 나가는 꼼수(중복 출전)를 막기 위한 핵심 로직입니다.
# a_keys라는 리스트에 현재 화면에 떠 있는 모든 드롭다운(선택창)의 고유 ID를 모아둡니다.
# get_avail 함수는 "현재 다른 드롭다운에서 이미 선택된 사람들의 이름을 싹 다 조사한 뒤,
# 그 사람들을 제외한 나머지 명단만 반환"합니다.
# 따라서 관리자가 단식 1번 선수로 '홍길동'을 고르는 순간,
# 복식 1번이나 단식 2번 드롭다운 목록에서는 '홍길동'의 이름이 마법처럼 사라지게 됩니다.
# 두 개의 점수판 (matrix vs ind_matrix)
#
# 이 프로그램은 두 가지 종류의 점수판을 동시에 관리합니다.
# matrix: 조(팀) 대 조의 점수판입니다.
# (예: 1조가 2조를 상대로 총 3승 2패를 거두었다)
# -> 스코어보드 탭에서 순위를 매길 때 사용됩니다.
# ind_matrix: 개인 대 개인의 점수판입니다.
# (예: 1조의 홍길동이 2조의 김철수를 상대로 2:0으로 이겼다)
# -> 개인별 누적 승률이나 1:1 상대 전적을 기록할 때 사용됩니다.
# 단체전 점수를 저장할 때, 단식 결과는 ind_matrix에 넣고,
# 그 승수들을 모두 더한 최종 결과는 matrix에 넣는 식으로
# 데이터를 이원화하여 완벽하게 관리하고 있습니다.
# ------------------------------------------
# 탭 5: 스코어보드 및 누적 결과 다운로드
# ------------------------------------------
# ==========================================
# 탭 5: 스코어보드 및 종합 결과 화면
# ==========================================
with tab_score:
    # 조 편성이 완료되어 세션에 'labels'(조 이름)와 'matrix'(점수판)가 있을 때만 실행
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:
        cfg = st.session_state.config
        is_ind = cfg.get('is_individual', False)  # 개인전인지 단체전인지 확인

        # ------------------------------------------
        # 1. UI 상태 초기화 (글자 크기 및 전체 화면)
        # ------------------------------------------
        # 표 글자 크기 동적 조절: 조 개수가 적으면 글자를 크게, 많으면 작게 기본값을 설정합니다.
        if 'table_font_size' not in st.session_state:
            num_rows = len(st.session_state.labels)
            st.session_state.table_font_size = 20 if num_rows <= 4 else (
                16 if num_rows <= 6 else (13 if num_rows <= 8 else 11))

        # 전체 화면 모드 여부를 기억하는 변수 (기본값: False)
        if 'fullscreen_table' not in st.session_state:
            st.session_state.fullscreen_table = False


        # ------------------------------------------
        # 2. 종합 결과표(매트릭스)를 그리는 핵심 함수
        # ------------------------------------------
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
            }).set_table_styles([
                {'selector': 'th',
                 'props': [('text-align', 'center'), ('vertical-align', 'middle'), ('height', ROW_HEIGHT)]},
            ])

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


        # ------------------------------------------
        # 3. 상단 컨트롤 패널 (전체화면, 글자크기, 다운로드)
        # ------------------------------------------
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

        # ------------------------------------------
        # 4. 화면 렌더링 (전체 화면 vs 일반 모드)
        # ------------------------------------------
        if is_fullscreen:
            # 전체 화면일 때는 다른 입력창 다 숨기고 오직 '결과표'만 크게 보여줍니다. (모니터 띄워놓기 용도)
            st.markdown("### 종합 결과표 (전체 화면 모드)")
            draw_summary_table()
        else:
            # 일반 모드: 수동 점수 입력창 및 종합 결과표 표시
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
                                save_room_state(room_name)
                                st.success(f"저장 완료! {team_a} {s_a} : {s_b} {team_b} 결과가 스코어보드에 반영되었습니다.")
                                st.rerun()

            st.divider()
            st.markdown(f"### {'조별 리그' if not is_ind else '개인전'} 종합 결과표")
            draw_summary_table()  # 위에서 만든 표 그리기 함수 호출

            # ------------------------------------------
            # 5. 단체전일 경우: 하단 개인 성적 관리 영역
            # ------------------------------------------
            if not is_ind:
                st.divider()
                st.markdown("### 개인 성적 관리 및 단식 결과 수동 입력")

                # (중략: 위 조별 수동 입력과 완벽히 동일한 로직으로 개인(ind_matrix) 점수를 수동 입력받는 부분)
                # ...

                st.markdown("#### 개인 성적표 (매트릭스)")
                st.info(" <strong>아래 표에서 특정 선수의 행(Row)을 클릭</strong>하면 오늘 진행된 상세 세트 전적을 확인할 수 있습니다.")

                # 💡 관리자와 일반 유저의 권한 분리 (핵심 UX)
                if is_admin:
                    # 관리자는 st.data_editor를 통해 엑셀처럼 표의 숫자를 직접 더블클릭해서 수정할 수 있습니다.
                    edited_ind_matrix = st.data_editor(st.session_state.ind_matrix, width="stretch", height=400,
                                                       hide_index=False, key="ind_matrix_editor")
                    if not edited_ind_matrix.equals(st.session_state.ind_matrix):
                        st.session_state.ind_matrix = edited_ind_matrix
                        save_room_state(room_name)
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
                            for h in history: st.markdown(h)
                        else:
                            st.info("아직 진행된 경기가 없습니다.")

                st.divider()

                # ------------------------------------------
                # 6. 역대 누적 상대 전적 검색 (H2H)
                # ------------------------------------------
                st.markdown("#### 🔍 역대 누적 상대 전적 검색")
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
                            # 두 선수를 선택하고 버튼을 누르면 팝업창(Dialog)을 띄워 전적을 보여줍니다.
                            show_h2h_dialog(search_p1, search_p2)

                st.divider()

                # ------------------------------------------
                # 7. 개인별 순위 계산 및 출력
                # ------------------------------------------
                im = st.session_state.ind_matrix
                ind_rank = pd.DataFrame(index=im.index)
                ind_rank['개인승'] = (im > im.T).sum(axis=1)  # 승수 계산
                ind_rank['개인패'] = (im < im.T).sum(axis=1)  # 패수 계산
                ind_rank['세트득실'] = im.sum(axis=1, skipna=True) - im.sum(axis=0, skipna=True)  # 득실차 계산
                st.markdown("#### 개인별 순위 (세트 기준)")
                # 승수 -> 세트득실 순으로 정렬하여 표로 보여줍니다.
                st.table(ind_rank.sort_values(['개인승', '세트득실'], ascending=False))
    else:
        st.info("조 편성이 완료되면 스코어보드가 나타납니다.")
        
# 판다스 행렬 계산의 마법 (m > m.T)
# 풀리그(라운드 로빈) 대회에서 승, 패, 득실차를 구하는 것은
# 보통 복잡한 반복문(for문)이 필요합니다.
# 하지만 판다스(Pandas)를 사용하면 아주 우아하게 해결됩니다.
# m은 내가 상대방에게 낸 점수이고, m.T(전치행렬, 표를 대각선으로 뒤집은 것)는 상대방이 나에게 낸 점수입니다.
# 따라서 m > m.T 라고 쓰면 "내가 상대방보다 점수가 높은 칸"만 True(1)가 됩니다.
# 이것을 가로로 다 더해주면(.sum(axis=1)) 그게 바로 나의 총 승수가 됩니다. 코드가 엄청나게 짧고 빠릅니다.
# HTML/CSS를 직접 주입하는 이유 (styled_df.to_html())
# Streamlit이 제공하는 기본 표(st.dataframe)는 데이터를 분석할 때는 좋지만,
# 체육관 모니터에 띄워놓는 '전광판(Scoreboard)' 느낌을 내기에는 디자인적 한계가 있습니다.
# 그래서 판다스의 데이터를 순수한 HTML 표로 변환한 뒤, 
# CSS 스타일(글자 크기, 셀 너비 고정, 가운데 정렬 등)을 강제로 덮어씌워 
# 화면에 꽉 차고 예쁜 전광판을 만들어낸 것입니다.
# 상태 관리로 UI 제어하기 (fullscreen_table, table_font_size)
# 웹페이지에서 버튼을 눌러 글자 크기를 키우거나 전체 화면으로 바꿀 때, 
# 화면이 새로고침되면서 기존 데이터가 날아가면 안 됩니다.
# st.session_state에 글자 크기(예: 20)와 전체화면 여부(True/False)를 저장해두고, 
# 버튼을 누를 때 이 숫자만 +1 하거나 True로 바꾼 뒤 st.rerun()을 호출합니다. 
# 그러면 코드가 다시 위에서부터 실행되면서 바뀐 설정값에 맞춰 화면을 다시 그려줍니다.
# 동적 UI 비활성화 (disabled=is_completed)
# 수동으로 점수를 입력할 때, 이미 1조와 2조의 경기가 끝나서 점수가 입력되어 있다면 
# 실수로 또 입력하는 것을 막아야 합니다.
# 점수판(matrix)을 확인해서 두 팀 간의 점수 합이 0보다 크면(즉, 누군가 점수를 냈다면)
# is_completed를 True로 만듭니다.
# 그리고 라디오 버튼과 저장 버튼의 disabled 옵션에 이 값을 넣어주면, 
# 이미 끝난 경기를 선택하는 순간 입력창들이 회색으로 변하며 클릭이 불가능해지는 훌륭한 방어적 UX가 완성됩니다.
# 관리자 vs 일반 유저의 권한 분리 (st.data_editor vs st.dataframe)
# 관리자(is_admin == True): st.data_editor를 띄워줍니다. 
# 엑셀처럼 표의 숫자를 더블클릭해서 마음대로 점수를 수정할 수 있는 막강한 권한을 줍니다.
# 일반 유저(is_admin == False): st.dataframe을 띄워줍니다. 
# 점수를 수정할 수는 없지만, 표의 특정 줄(예: 홍길동)을 클릭하면 
# 그 아래에 "홍길동 선수는 오늘 김철수에게 2:0으로 이겼습니다" 같은
# 상세 전적을 문장으로 풀어서 보여주는 친절한 조회 기능을 제공합니다.
# ------------------------------------------

# 탭 6: 사용 설명서
# ------------------------------------------
with tab_help:
    lang = st.radio("언어 선택 / Select Language", ["한국어", "English"], horizontal=True)
    show_help_section(lang)
