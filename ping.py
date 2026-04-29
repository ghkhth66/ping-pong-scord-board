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

from streamlit_autorefresh import st_autorefresh
# 구글 스프레드시트 연동 라이브러리 (DB 역할)
try:
    from streamlit_gsheets import GSheetsConnection

except ImportError:
    # 라이브러리가 없을 경우 에러 메시지 출력
    st.error("⚠️ 'st-gsheets-connection' 라이브러리가 설치되지 않았습니다."
             " 터미널에서 'pip install st-gsheets-connection'을 실행해주세요.")

from Program_User_Guide import show_help_section

# auro_refresh_count = st_autorefresh(interval=10 * 60 * 1000, limit=100, key="data_refresh")

# st.markdown("<h1 style='font-size: 20px;'>실시간 데이터 모니터링</h1>", unsafe_allow_html=True)
# st.write(f"현재 화면 새로고침 횟수: {auro_refresh_count}회")
# st.write(f"마지막 업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
    page_title="리그 운영 시스템",
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
    /* ========================================== */
    /* 7. 화면 맨 위쪽 여백 줄이기 (새로 추가된 부분) */
    /* ========================================== */
    
    /* 메인 화면(오른쪽)의 위쪽 여백 조절 */
    .block-container {
        padding-top: 2.5rem; /* 숫자를 줄일수록 위로 올라갑니다 (기본값 약 6rem) */
    }
    
    /* 사이드바(왼쪽)의 맨 위쪽 여백 조절 */
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True) # HTML과 CSS 태그가 문자열 그대로 출력되지 않고 실제 웹페이지에 적용되도록 허용하는 옵션

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
            # 3. 파일 읽기, "rb"는 Read Binary의 약자로, 바이너리 파일을 읽겠다는 의미
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
             # "나이": random.randint(20, 75),
             "부수": f"{random.randint(1, 13)}부",
             # "부수_조정1": 0.0, "부수_조정2": 0.0, "부수_조정3": 0.0,
             "조편성_신청" : random.choice(["토끼", "여우", "곰", "호랑이" ]),
             "참석예정": random.choice(["Y", "N"])} for i in range(1, 51)]
    return pd.DataFrame(data)

def update_cumulative_record(p_a, p_b, s_a, s_b):
    """경기가 끝날 때마다 선수들의 누적 전적(승, 패, 득점, 실점)과 상대 전적을 업데이트하는 함수
       - p_a, p_b: 선수 A와 선수 B의 이름
       - s_a, s_b: 선수 A와 선수 B의 점수(Score)
    """
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

#########################################
#
#########################################
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

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 안전한 실행을 위한 try-except 구문 시작
try:
    db_df = conn.read(spreadsheet=SHEET_URL, worksheet="시트1", ttl=0)

except Exception as e:
    st.error(f"⚠️ DB(구글시트) 연결 실패. secrets.toml 설정을 확인하세요 \n {e}")
    db_df = pd.DataFrame(columns=["방이름", "관리자이름", "이메일", "비밀번호", "생성일자"])

is_admin = st.session_state.is_admin
room_name = st.session_state.room_name

# ==========================================
# 🔴 [로그인 전] 관리자가 아닐 때 보여지는 사이드바 화면
# ==========================================
if not is_admin:
    st.sidebar.markdown("### 🏟️ 구장 접속 및 생성")
    # 사이드바 안에 '기존 구장 접속'과 '새 구장 만들기'라는 2개의 탭(Tab)을 만듭니다.
    tab_login, tab_create = st.sidebar.tabs(["🔑 기존 구장 접속", "➕ 새 구장 만들기"])

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

            if st.sidebar.button("🔄 최신 경기결과 불러오기", type="primary"):
                # 이전 질문에서 설명했던 load_room_state 함수를 실행하여 pkl 파일에서 데이터를 복구
                if load_room_state(room_name):
                    st.sidebar.success(f"'{room_name}' 구장의 데이터를 불러왔습니다.")
                else:
                    st.sidebar.warning("저장된 구장 데이터가 없습니다.")

            st.sidebar.divider()

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

else:
    # 로그인/생성 탭은 사라지고, 현재 접속 중인 구장 이름과 로그아웃 버튼만 보임
    st.sidebar.markdown(f"### 🏟️ {room_name} 구장")
    st.sidebar.success("👑 관리자 모드로 접속 중입니다.")

    # 로그아웃 버튼
    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state.is_admin = False  # 관리자 권한 박탈
        st.rerun()  # 새로고침하여 다시 [로그인 전] 화면으로 돌아감

    # 체크박스를 만들어 사용자가 켜고 끌 수 있게 합니다. (기본값은 False로 꺼둠)
    auto_refresh = st.sidebar.checkbox("자동 새로고침 켜기 (PC 전광판용)")

    if auto_refresh:
        # 5분(5 * 60 * 1000 = 300,000 밀리초)마다 새로고침
        # limit=None으로 설정하면 무한으로 새로고침 됩니다.
        st_autorefresh(interval=5 * 60 * 1000, limit=None, key="dashboard_refresh")
        st.sidebar.info("🟢 현재 5분마다 화면이 자동 갱신 중입니다. \n\n⚠️ 데이터 입력/수정 중에는 이 기능을 꺼주세요!")

    # 2. 간격을 비정상적으로 확 좁히고 싶을 때 (마이너스 값 사용)
    # Streamlit의 기본 여백을 무시하고 위로 바짝 붙입니다.
    # 💡 수정: 사이드바의 간격을 좁히기 위해 st.sidebar.markdown 사용
    # st.sidebar.markdown("<div style='margin-top: -170px;'></div>", unsafe_allow_html=True)
    # st.sidebar.divider()
    # st.sidebar.markdown("<div style='margin-top: -170px;'></div>", unsafe_allow_html=True)
    # st.sidebar.divider() 와 마이너스 여백 코드들을 전부 지우고, 아래 한 줄만 넣습니다.
    # margin: 10px 0px; 에서 10px 숫자를 줄이면(예: 5px) 위아래 간격이 더 좁아집니다.
    st.sidebar.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

    # 💡 개선 1 & 3: 중복된 if is_admin 제거 및 Expander(접기/펴기) 사용
    with st.sidebar.expander("📁 데이터 파일 업로드 (클릭하여 열기)", expanded=False):

        # 💡 개선 2: type=['csv'] 옵션을 주어 CSV 파일만 선택 가능하도록 강제
        uploaded_file = st.file_uploader("1. 명단 파일(CSV) 업로드", type=['csv'])
        if uploaded_file:
            if st.button("명단 적용하기", use_container_width=True):
                st.session_state.main_df = load_data(uploaded_file)
                st.success("새로운 명부가 적용되었습니다.")
                time.sleep(1)
                st.rerun()

        cum_file = st.file_uploader("2. 기존 누적 결과(CSV) 업로드", type=['csv'])
        if cum_file:
            if st.button("누적 데이터 적용", use_container_width=True):
                st.session_state.cum_df = pd.read_csv(cum_file, encoding='utf-8-sig')
                st.success("누적 데이터가 연동되었습니다.")
                time.sleep(1)
                st.rerun()

        h2h_file = st.file_uploader("3. 누적 상대전적(CSV) 업로드", type=['csv'])
        if h2h_file:
            if st.button("상대전적 데이터 적용", use_container_width=True):
                st.session_state.h2h_df = pd.read_csv(h2h_file, encoding='utf-8-sig')
                st.success("상대전적 데이터가 연동되었습니다.")
                time.sleep(1)
                st.rerun()

# ---------------------------------------------------------
# 3. 메인 화면 데이터 처리 (날짜 및 출석/조편성)
# ---------------------------------------------------------
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

# 👇 [수정 부분 1] 여기에 "조편성_신청" 컬럼 확인 및 자동 생성 코드를 추가합니다. 👇
if '조편성_신청' not in st.session_state.main_df.columns:
    # 💡 개선 5: 함수 정의 대신 lambda를 사용하여 코드를 간결하게 만들고 속도 향상
    st.session_state.main_df['조편성_신청'] = st.session_state.main_df[col_date].apply(
        lambda x: str(random.randint(1, 4)) if x == 'Y' else ""
    )

    # # 생성 후 파일로 저장하여 사용자가 다운로드 후 수정할 수 있게 함
    if is_admin:
        save_room_state(room_name)
# 👆 ------------------------------------------------------------------------ 👆

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
         edited_left = st.data_editor(df.iloc[:mid_idx][['순서', '이름', '참석', '부수']],
                                     hide_index=True, disabled=not is_admin)
    with col2:
        edited_right = st.data_editor(df.iloc[mid_idx:][['순서', '이름', '참석', '부수']],
                                      hide_index=True, disabled=not is_admin)

    # 사용자가 화면에서 체크박스를 껐다 켰다 수정한 좌/우 데이터를 다시 하나의 표로 합칩니다.
    edited_df = pd.concat([edited_left, edited_right], ignore_index=True)

    # 참석(True)으로 체크된 사람만 골라냅니다.
    current_checked = edited_df[edited_df['참석'] == True]

    # 참석자들의 이름을 가나다순으로 정렬한 뒤, 쉼표(,)로 연결하여 한 줄의 문장으로 만듭니다.
    live_names = ", ".join(sorted(current_checked['이름'].tolist()))

    # 파란색 정보창에 총 참석 인원과 명단을 실시간으로 보여줍니다.
    st.info(f"**현재 참석 ({len(current_checked)}명):** \n\n {live_names}")

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
        # st.markdown("#### 💾 최신 명단 다운로드")
        responsive_text(f"💾 최신 명단 다운로드", pc_size="20px", mobile_size="16px")
        # 현재까지의 모든 데이터(출석 기록 포함)를 CSV 파일 형태로 변환합니다. (한글 깨짐 방지 utf-8-sig)
        csv_main = st.session_state.main_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

        # 다운로드 버튼 생성 (클릭 시 사용자의 PC로 파일이 다운로드됨)
        st.download_button(label="📥 최신 명단(CSV) 다운로드", data=csv_main,
                           file_name=f"{room_name}_최신명단_{CURRENT_DATE}.csv",
                           mime="text/csv", type="primary", use_container_width=True)

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
        set_c = st.selectbox("개인전 선승 세트", [2, 3, 4, 5], index=1, disabled=not is_admin)  # index=1은 '3'을 기본값으로

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
                st.session_state.config_confirmed = True  # 설정 완료 플래그 켜기
                save_room_state(room_name)  # 파일로 영구 저장
                st.rerun()  # 새로고침
        else:
            st.info("관리자 전용")  # 일반 사용자에게는 버튼 대신 안내문구 표시

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
                            st.success(f" **{row['이름']}** ➔ **{assigned_team}조**")

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

with tab_team:
    if "config" not in st.session_state:
        st.warning("먼저 '운영 설정'을 완료해주세요.")
    else:
        st.info(f"👥 현재 확정된 참석 인원: **{attendees_count}명**")
        cfg = st.session_state.config
        df = st.session_state.main_df
        attendees = df[df[col_date] == 'Y'].copy()
        attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
        # sorted_members = attendees.sort_values(['부수_숫자', '부수_조정1'], ascending=True).reset_index(drop=True)
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

            # 3. 고유한 팀 이름들을 실제 생성할 조 번호(1 ~ cfg['g'])에 매핑
            # (만약 신청된 팀 종류가 설정한 조 개수보다 많으면 1조부터 다시 순환 배정)
            group_to_team_map = {}
            for i, g_name in enumerate(unique_groups):
                team_idx = (i % cfg['g']) + 1
                group_to_team_map[g_name] = team_idx

            # 4. 매핑된 조 번호에 맞게 인원 배정
            for idx, row in attendees.iterrows():
                g_name = row['조편성_신청']
                t_idx = group_to_team_map[g_name]

                teams[t_idx].append(f"{row['이름']}({row['부수']})")
                all_member_names.append(row['이름'])
                team_stats[t_idx]["sum"] += row['부수_숫자']
                team_stats[t_idx]["count"] += 1
        # 👆 -------------------------------------------------------- 👆

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
                            match_results.append(("S", p_a, s_a, s_b, p_b))  # 단식(S) 결과 임시 저장

                    # 복식 입력창 생성 (단식과 원리는 같으나 선수를 2명씩 고름)
                    if d_games > 0:
                        # st.markdown("##### 👥 복식 경기")
                        responsive_text(f"👥 복식 경기", pc_size="20px", mobile_size="16px")
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
                                save_room_state(room_name)
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

                # st.markdown("#### 🔍 역대 누적 상대 전적 검색")
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
                            # 두 선수를 선택하고 버튼을 누르면 팝업창(Dialog)을 띄워 전적을 보여줍니다.
                            show_h2h_dialog(search_p1, search_p2)

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
