import streamlit as st
import pandas as pd
import os
import numpy as np
import random
import re
from datetime import datetime
import math

# ==========================================
# 1. Streamlit 페이지 레이아웃 설정
# ==========================================
# st.set_page_config: 웹 브라우저 탭 제목, 레이아웃 너비, 사이드바 초기 상태 등을 정의합니다.
st.set_page_config(
    page_title="동호회 운영 시스템",
    layout="wide",           # 화면 전체 너비 사용
    initial_sidebar_state="expanded" # 사이드바를 기본적으로 열어둠
)

FILE_NAME = 'member_list.csv'

CUMULATIVE_FILE = 'cumulative_records.csv'

# ==========================================
# 2. UI 렌더링 함수 (HTML/CSS 연계)
# ==========================================
def get_info_html(live_count, live_names_display, cfg=None):
    """
    Python의 변수를 HTML 문자열에 삽입(F-string)하여
    Streamlit 화면에 커스텀 디자인을 출력하기 위한 함수입니다.
    """
    if cfg:
        # 경기 설정(cfg) 유무에 따라 조건부 렌더링
        is_individual = cfg.get('is_individual')
        mode_text = "개인전(3선승제)" if is_individual else f"단체전(단식 {cfg['s_games']} / 복식 {cfg['d_games']})"
        criteria_text = "3세트 선승" if is_individual else f"{cfg['total_g']}경기 합산"

        return f"""
         <div class="info-bar">
            <h4 style="margin:0; color:#007bff;"> 오늘의 정보</h4>
            <div style="margin:10px 0; color:#333; font-size: 1.2rem; font-weight: bold;"> 
                현재 체크된 인원 ({live_count}명)
                <div style="font-weight: normal; color: #007bff; margin-top: 5px; line-height: 1.5; word-break: keep-all;">
                    {live_names_display if live_names_display else "없음"}
                </div>
            </div>
            <hr style="margin:10px 0; border:0; border-top:1px solid #ccc;">
            <span style="font-size:1.1rem;">
                <b>진행 방식:</b> {mode_text} | 
                <b>기준:</b> {criteria_text} | <b>탁구대:</b> {cfg['t']}대 가동
            </span>
        </div>
        """
    else:
        # 설정 정보가 없을 때의 기본 인원 표시 바
        if live_count > 0:
            return f"""
            <div style="background-color: #e8f4f9; padding: 15px; border-radius: 8px;
             border-left: 5px solid #17a2b8; color: #31333F; margin-bottom: 15px; word-break: keep-all;">
                <div style="font-size: 16px; margin-bottom: 8px;"><b>현재 체크된 인원 ({live_count}명):</b></div>
                <div style="font-size: 24px; font-weight: bold; color: #007bff; line-height: 1.6;">
                    {live_names_display}
                </div>
            </div>
            """
        else:
            return """
            <div style="background-color: #e8f4f9; padding: 15px; border-radius: 8px;
             border-left: 5px solid #17a2b8; color: #31333F; margin-bottom: 15px; word-break: keep-all;">
                **현재 체크된 인원 (0명):** 없음
            </div>
            """

# [파일 관리] 일일 경기 결과 저장 함수 (중복 제거 및 통합)
def save_daily_results(save_file_name):
    """현재 세션의 조별 매트릭스와 개인별 매트릭스를 일일 CSV 파일로 저장합니다."""
    with open(save_file_name, 'w', encoding='utf-8-sig') as f:
        f.write(f"--- 경기 일자: {CURRENT_DATE} ---\n")
        f.write("\n[조별/단체전 결과]\n")
        st.session_state.matrix.to_csv(f)
        f.write("\n[개인별 통합 성적]\n")
        st.session_state.ind_matrix.to_csv(f)


# [파일 관리] 개인별 누적 실적 업데이트 함수 (신규 추가)
def update_cumulative_record(p_a, p_b, s_a, s_b):
    """
    개인 경기(단식/복식) 결과가 입력될 때마다 누적 실적 파일(cumulative_records.csv)을 업데이트합니다.
    이를 통해 동호회원들의 장기적인 승률 및 랭킹 관리가 가능해집니다.
    """
    # 누적 파일이 없으면 기본 구조로 생성
    if not os.path.exists(CUMULATIVE_FILE):
        df_cum = pd.DataFrame(columns=['이름', '총경기수', '승', '패', '득점', '실점'])
    else:
        df_cum = pd.read_csv(CUMULATIVE_FILE, encoding='utf-8-sig')

    # 선수 데이터가 없으면 추가하는 내부 함수
    def ensure_player(df, player_name):
        if player_name not in df['이름'].values:
            new_row = pd.DataFrame([{'이름': player_name, '총경기수': 0, '승': 0, '패': 0, '득점': 0, '실점': 0}])
        df = pd.concat([df, new_row], ignore_index=True)
        return df

    df_cum = ensure_player(df_cum, p_a)
    df_cum = ensure_player(df_cum, p_b)

    # 선수 A 업데이트
    idx_a = df_cum[df_cum['이름'] == p_a].index[0]
    df_cum.at[idx_a, '총경기수'] += 1
    df_cum.at[idx_a, '승'] += 1 if s_a > s_b else 0
    df_cum.at[idx_a, '패'] += 1 if s_a < s_b else 0
    df_cum.at[idx_a, '득점'] += s_a
    df_cum.at[idx_a, '실점'] += s_b

    # 선수 B 업데이트
    idx_b = df_cum[df_cum['이름'] == p_b].index[0]
    df_cum.at[idx_b, '총경기수'] += 1
    df_cum.at[idx_b, '승'] += 1 if s_b > s_a else 0
    df_cum.at[idx_b, '패'] += 1 if s_b < s_a else 0
    df_cum.at[idx_b, '득점'] += s_b
    df_cum.at[idx_b, '실점'] += s_a

    # 파일 저장
    df_cum.to_csv(CUMULATIVE_FILE, index=False, encoding='utf-8-sig')

# ==========================================
# 3. 사이드바 및 인증 로직 (상태 관리)
# ==========================================
st.sidebar.markdown("### 관리자 메뉴")
# st.sidebar.text_input: 사이드바에 입력창 배치. type="password"로 마스킹 처리
admin_password = st.sidebar.text_input("관리자 비밀번호를 입력하세요.  admin123 ", type="password")

MASTER_PW = "admin123"
# 입력값과 설정된 PW를 비교하여 True/False 반환 (이후 UI의 비활성화 여부 결정)
is_admin = (admin_password == MASTER_PW)

if is_admin:
    st.sidebar.success(" 관리자 모드 활성화됨\n(점수 입력 및 설정 가능)")
else:
    if admin_password:
        st.sidebar.error(" 비밀번호가 틀렸습니다.")
    st.sidebar.info(" 일반 접속자 모드입니다.\n(결과표 조회만 가능)")

# ==========================================
# 4. 레이아웃 분할 및 동적 위젯
# ==========================================
# st.columns: 화면을 4:1 비율로 분할하여 배치
col_info, col_date_input = st.columns([4, 1])

# .empty(): 나중에 내용을 채우기 위한 빈 공간 확보 (실시간 업데이트용)
info_placeholder = col_info.empty()

with col_date_input:
    # st.date_input: 달력 위젯. disabled 속성에 관리자 권한 여부 연계
    selected_date = st.date_input(" 시합 일자 선택", datetime.now(), disabled=not is_admin)
    CURRENT_DATE = selected_date.strftime('%Y-%m-%d')
    SAVE_FILE_NAME = f"{CURRENT_DATE}_경기결과.csv"
    save_btn_placeholder = col_date_input.empty()

selected_adj = st.sidebar.selectbox(
    " 부수 조정 기준 선택",
    ["부수_조정1","부수_조정2","부수_조정3"],
    disabled=not is_admin,
    help="선택한 조정값이 조 편성에 반영됩니다."
)

# ==========================================
# 5. 데이터 로딩 및 Pandas 연계
# ==========================================
# 데이터를 불러오거나 처음 실행 시 가짜(Dummy) 데이터를 만드는 함수
# def load_data():
def load_data(uploaded_file=None):
    """
    1. 사용자가 파일을 업로드하면 해당 파일을 읽습니다.
    2. 업로드된 파일이 없으면 기존 로컬 'member_list.csv'를 찾습니다.
    3. 둘 다 없으면 기본 더미 데이터를 생성합니다.
    """
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            return pd.read_csv(uploaded_file, encoding='cp949')

    if os.path.exists(FILE_NAME):
        try:
            return pd.read_csv(FILE_NAME, encoding='utf-8-sig')
        except:
            return pd.read_csv(FILE_NAME, encoding='cp949')

    # 기본 더미 데이터 생성 (기존 로직 유지)
    data = []
    for i in range(1, 31):
        g_val = random.randint(1, 13)
        data.append({
            "순서": i, "이름": f"회원{i}", "성별": random.choice(["남", "여"]),
            "나이": random.randint(20, 75), "부수": f"{g_val}부",
            "부수_조정1": 0.0, "부수_조정2": 0.0, "부수_조정3": 0.0,
            f"출석_{CURRENT_DATE}": 'N'
        })
    return pd.DataFrame(data)
    # """
    # CSV 파일을 읽어 Pandas DataFrame으로 변환합니다.
    # 파일이 없으면 초기 샘플 데이터를 생성합니다.
    # """
    # if not os.path.exists(FILE_NAME):
    #     # 파일이 없을 경우 더미 데이터 생성 로직
    #     data = []
    #     for i in range(1, 31):
    #         g_val = random.randint(1, 13)
    #         data.append({
    #              "순서": i,
    #              "이름": f"회원{i}",
    #              "성별": random.choice(["남", "여"]),
    #              "나이": random.randint(20, 75),
    #              "부수": f"{g_val}부",
    #              "부수_조정1": 0.0,
    #              "부수_조정2": 0.0,
    #              "부수_조정3": 0.0,
    #              f"출석_{CURRENT_DATE}": random.choice(['Y', 'N'])
    #         })
    #     df_n = pd.DataFrame(data)
    #     # utf-8-sig: 엑셀에서 한글 깨짐 방지를 위한 인코딩
    #     df_n.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
    #     return df_n
    #
    # try:
    #     return pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    # except UnicodeDecodeError:
    #     return pd.read_csv(FILE_NAME, encoding='cp949')

# 데이터 로드 실행
# [중요] 앱 시작 시 가장 먼저 실행되어야 함
# 세션 스테이트에 main_df가 없으면 즉시 로드하여 할당
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()
# df = load_data()

# ==========================================
# 6. 데이터 전처리 (st.session_state.main_df 사용)
# ==========================================

# 기존에 df 라고 되어 있던 부분을 모두 아래처럼 변경합니다.
if '이름' in st.session_state.main_df.columns:
    # dropna: 이름이 없는 행(Null) 제거
    st.session_state.main_df = st.session_state.main_df.dropna(subset=['이름'])

    # 불필요한 공백이나 잘못된 문자열 정제
    st.session_state.main_df = st.session_state.main_df[
        st.session_state.main_df['이름'].astype(str).str.lower() != 'nan'
        ]
    st.session_state.main_df = st.session_state.main_df[
        st.session_state.main_df['이름'].astype(str).str.strip() != ''
        ]

# 선택된 날짜에 맞는 출석 열이 없으면 새로 생성
col_date = f"출석_{CURRENT_DATE}"
if col_date not in st.session_state.main_df.columns:
    st.session_state.main_df[col_date] = 'N'

# ==========================================
# 7. 커스텀 CSS 주입
# ==========================================
# st.markdown: HTML/CSS를 직접 주입하여 Streamlit 기본 디자인을 커스터마이징
st.markdown("""
     <style>
     .info-bar { background-color: #e9ecef; border-radius: 10px; padding: 15px; margin-bottom: 20px; border-left: 5px solid #007bff; }
     .setting-banner { background-color: #f8f9fa; border: 2px solid #28a745; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
     .team-card { background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 12px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
     .stTabs [data-baseweb="tab"] { font-size: 18px !important; font-weight: bold; }
     </style>
     """, unsafe_allow_html=True) # unsafe_allow_html 필수

# ==========================================
# 8. 유틸리티 함수 (정규표현식 연계)
# ==========================================
def extract_busu(busu_str):
    """문자열(예: '5부')에서 숫자만 추출하여 계산 가능한 float 타입으로 변환"""
    try:
        nums = re.findall(r'\d+', str(busu_str))
        return float(nums[0]) if nums else 9.0
    except:
        return 9.0

tab_home, tab_config, tab_team, tab_match, tab_score = st.tabs([" 출석체크", " 운영 설정", " 조 편성 결과", " 경기 배정", " 스코어보드"])

if 'attendees_count' not in st.session_state:
    st.session_state.attendees_count = 0

# ==========================================
# 탭 1: 출석체크 (Interactivity & Data Editing)
# ==========================================
@st.fragment
def attendance_check_fragment():
# with tab_home:
    st.markdown("### 📂 클럽 회원 명부 관리")

# [추가] 클럽별 파일 업로드 기능
    # 이 부분을 통해 각 클럽은 자신의 PC에 있는 CSV를 불러올 수 있습니다.
    up_col1, up_col2 = st.columns([3, 1])
    with up_col1:
        uploaded_file = st.file_uploader("클럽 회원 명부(CSV)를 업로드하세요", type=['csv'], help="기존 양식과 동일한 CSV 파일을 선택하세요.")
    with up_col2:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 업로드 파일 적용", use_container_width=True):
            if uploaded_file:
                st.session_state.main_df = load_data(uploaded_file)
                st.success("새로운 회원 명부가 적용되었습니다.")
                st.rerun()

    st.divider()
    st.markdown(f"### 📋 {CURRENT_DATE} 참석 현황")

    # 세션에 저장된 데이터를 사용하도록 변경
    working_df = st.session_state.main_df.copy()

    # 데이터 전처리 (이름 없는 행 제거)
    working_df = working_df.dropna(subset=['이름'])
    working_df = working_df[working_df['이름'].astype(str).str.strip() != '']

    # 날짜별 출석 컬럼 확인
    col_date = f"출석_{CURRENT_DATE}"
    if col_date not in working_df.columns:
        working_df[col_date] = 'N'

    # 체크박스용 True/False 변환
    working_df['참석'] = working_df[col_date].apply(lambda x: True if x == 'Y' else False)

    # [Pandas] 원본 데이터프레임을 복사하여 편집용 데이터프레임 생성


    # [수정 포인트] 전역 변수 df 대신 세션 스테이트의 데이터를 가져옵니다.
    if 'main_df' in st.session_state:
        display_df = st.session_state.main_df.copy()
    else:
        # 혹시라도 데이터가 없을 경우를 대비한 안전장치
        st.error("데이터를 불러올 수 없습니다. 메인 페이지를 새로고침 하세요.")
        return
    # CSV의 'Y/N' 문자열을 Streamlit 체크박스에서 인식할 수 있도록 True/False로 변환
    display_df['참석'] = display_df[col_date].apply(lambda x: True if x == 'Y' else False)

    # [UI 디자인] 화면 공간 활용을 위해 인원 리스트를 절반으로 나누어 2열로 배치
    mid_idx = len(display_df) // 2 + (len(display_df) % 2)
    df_left = display_df.iloc[:mid_idx].copy()
    df_right = display_df.iloc[mid_idx:].copy()

    col1, col2 = st.columns(2)

    with col1:
        # st.data_editor: 사용자가 웹상에서 표를 직접 수정할 수 있게 함
        edited_left = st.data_editor(
            df_left[['순서', '이름', '참석', '부수', selected_adj]],
            hide_index=True,
            width="stretch",
            # column_config: 특정 열을 체크박스 형태의 인터페이스로 설정
            column_config={"참석": st.column_config.CheckboxColumn("오늘 참석", default=False)},
            key="editor_left"  # 위젯의 고유 키 (중복 방지)
        )

    with col2:
        edited_right = st.data_editor(
            df_right[['순서', '이름', '부수', selected_adj, '참석']],
            hide_index=True,
            width="stretch",
            column_config={"참석": st.column_config.CheckboxColumn("오늘 참석", default=False)},
            key="editor_right"
        )

    # [Pandas] 양쪽 열에서 수정된 데이터를 다시 하나의 데이터프레임으로 합침
    edited_df = pd.concat([edited_left, edited_right], ignore_index=True)

    # 실시간 참석 인원 계산 (True인 행의 개수)
    current_checked = edited_df[edited_df['참석'] == True]
    live_count = len(current_checked)

    # 다른 탭(운영 설정 등)에서 참조할 수 있도록 전역 변수 성격으로 할당
    # attendees_count = live_count
    st.session_state.attendees_count = live_count

    # [문자열 처리] 참석자 명단을 가나다순 정렬 후, 10명씩 끊어서 화면에 표시하기 위한 HTML 생성
    sorted_names = sorted(current_checked['이름'].tolist())
    chunked_names = [", ".join(sorted_names[i:i + 10]) for i in range(0, len(sorted_names), 10)]
    live_names_display = "".join([f"<div>{chunk}</div>" for chunk in chunked_names])

    # ==========================================
    # 상단 정보창(col_info) 실시간 업데이트 (State Management)
    # ==========================================
    # st.session_state: 새로고침 시에도 설정값이 유지되도록 세션 상태를 확인
    cfg = st.session_state.config if "config" in st.session_state else None

    # 이전에 정의한 get_info_html 함수를 호출하여 최신 참석 현황 반영
    info_html = get_info_html(live_count, live_names_display, cfg)

    # empty()로 확보해둔 자리에 실시간 업데이트된 HTML 내용을 채워넣음
    info_placeholder.markdown(info_html, unsafe_allow_html=True)

    # ==========================================
    # 우측 상단(col_date_input)에 저장 버튼 배치 (File I/O)
    # ==========================================
    if is_admin:  # 관리자 권한이 있을 때만 버튼 노출
        save_col1, save_col2 = st.columns(2)

        with save_col1:
            if st.button("💾 서버/PC에 즉시 저장", type="primary", use_container_width=True, help="서버의 member_list.csv를 갱신합니다."):
                # 데이터 동기화
                st.session_state.main_df[col_date] = edited_df['참석'].apply(lambda x: 'Y' if x else 'N')
                for col in ['이름', '부수', selected_adj]:
                    st.session_state.main_df[col] = edited_df[col]

                st.session_state.main_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
                st.success("파일 저장 완료!")
                st.rerun()

        with save_col2:
            # [추가] 모바일 사용자를 위한 CSV 다운로드 기능
            # 스마트폰에서 조작 후 결과가 포함된 파일을 본인 폰으로 소장할 수 있게 합니다.
            csv_data = st.session_state.main_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 현재 명부 내 폰으로 다운로드",
                data=csv_data,
                file_name=f"클럽명부_{CURRENT_DATE}.csv",
                mime="text/csv",
                use_container_width=True
            )
        # if st.button("출석 정보 최종 저장", type="primary", use_container_width=True):
        #     # 편집된 데이터(edited_df)의 값을 원본(df)에 동기화
        #     df[col_date] = edited_df['참석'].apply(lambda x: 'Y' if x else 'N')
        #     # 수정
        #     for col in ['이름', '부수', selected_adj]:
        #         df[col] = edited_df[col]
        #
        #     # [Python] 최종 변경 내용을 다시 CSV 파일로 물리적 저장
        #     df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
        #
        #     # 성공 메시지 출력 후 페이지 재실행(st.rerun)을 통해 화면 갱신
        #     st.success("저장 완료! '운영 설정' 탭으로 이동하세요.")
        #     st.rerun()

with tab_home:
    attendance_check_fragment()

# ==========================================
# 탭 2: 운영 설정 (Configuration & Session State)
# ==========================================
@st.fragment
def config_setup_fragment():
# with tab_config:
    # 커스텀 CSS 클래스(.setting-banner)를 적용한 div 박스 시작
    st.markdown('<div class="setting-banner">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5])

    with c1:
        st.markdown(f"#### 조 구성")
        # st.number_input: 숫자 입력 위젯. (라벨, 최소, 최대, 기본값) 순서
        g_val = st.number_input("편성 조 수", 1, 20, 4, disabled=not is_admin)
        avg_members = st.session_state.attendees_count // g_val if g_val > 0 else 0
        if g_val > 0:
            # [Python 산술 연산] 참석 인원수에 따른 조당 평균 인원 계산
            # avg_members = attendees_count // g_val
            remainder = st.session_state.attendees_count % g_val
            if remainder > 0:
                st.info(f" 조당 인원: 약 {avg_members} ~ {avg_members + 1}명")
            else:
                st.info(f" 조당 인원: {avg_members}명")
        else:
            avg_members = 0

    with c2:
        st.markdown("#### 경기 규칙")
        # 인원수가 부족할 경우(avg_members < 2) 위젯을 비활성화(disabled=True) 처리
        if avg_members < 2:
            s_g = st.number_input("단식 게임", min_value=0, max_value=10, value=1, disabled=True)
            d_g = st.number_input("복식 게임", min_value=0, max_value=5, value=0, disabled=True)
        else:
            s_g = st.number_input("단식 게임", 0, 10, 2)
            d_g = st.number_input("복식 게임", 0, 5, 1)

        # st.selectbox: 리스트 중 하나를 선택하는 드롭다운 메뉴
        set_c = st.selectbox("개인전 선승 세트", [2, 3, 4, 5], index=1)

    with c3:
        st.markdown("#### 환경 설정")
        t_val = st.number_input("Table_No.", 1, 20, 3)

    with c4:
        st.markdown("#### 조 편성 방법")
        # st.radio: 라디오 버튼. label_visibility="collapsed"로 라벨을 숨겨 디자인 깔끔하게 유지
        draw_method = st.radio("방식 선택", ["AI 선정", "제비뽑기"], label_visibility="collapsed")

    with c5:
        st.markdown("#### 실행")
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

        btn_label = "설정 확정 및 조 편성" if draw_method == "AI 선정" else "설정 확정 및 제비뽑기 시작"

        # [Streamlit 권한 제어] 관리자(is_admin)일 때만 실행 버튼 노출
        if is_admin:
            # [추가] 함수 내부에서 사용할 df를 세션 스테이트에서 가져옵니다.
            if 'main_df' not in st.session_state:
                st.error("데이터가 로드되지 않았습니다.")
                return

            df = st.session_state.main_df  # 이 줄을 추가하면 아래 코드들을 수정할 필요가 없습니다.

            if st.button(btn_label, width="stretch", type="primary"):
                # st.session_state: 페이지가 재실행되어도 유지해야 할 설정값들을 딕셔너리 형태로 저장
                attendees = df[df[col_date] == 'Y'].copy()
                tie_breakers = {name: random.random() for name in attendees['이름']}

                st.session_state.config = {
                    "g": g_val, "t": t_val, "s_games": s_g,
                    "d_games": d_g, "set_count": set_c, "total_g": s_g + d_g,
                    "draw_method": draw_method,
                    "selected_adj": selected_adj,
                    "tie_breakers": tie_breakers
                }
                # 제비뽑기 관련 초기화 (이전 기록 삭제)
                st.session_state.matrix = None
                st.session_state.ind_matrix = None
                st.session_state.draw_level = 0
                st.session_state.draw_results = {}
                st.session_state.draw_completed = False

                # 기존 세션에 남은 이전 조 선택값(key)들을 깔끔하게 삭제
                for key in list(st.session_state.keys()):
                    if key.startswith("group_selections_") or key.startswith("select_"):
                        del st.session_state[key]
                st.rerun()  # 설정 반영을 위해 페이지 강제 재실행
        else:
            st.info("관리자가 설정 중입니다.")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 제비뽑기 로직 (Dynamic UI & Interactivity)
# ==========================================
@st.fragment
def draw_process_fragment():
    if "config" in st.session_state and st.session_state.config.get('draw_method') == '제비뽑기':
        if not st.session_state.get('draw_completed', False):
            st.divider()
            cfg = st.session_state.config

            adj_col = cfg['selected_adj']
            # [Pandas] 참석자('Y')만 추출 후 부수(실력) 순으로 정렬하여 밸런스 유지 준비
            attendees = df[df[col_date] == 'Y'].copy()
            attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)

            attendees['Random'] = attendees['이름'].map(cfg['tie_breakers'])

            sorted_members = attendees.sort_values(
                ['부수_숫자', adj_col, 'Random'],
                ascending=True
            ).reset_index(drop=True)

            # [Python] 전체 그룹 수 계산 (부수별로 잘라서 제비뽑기 진행)
            total_levels = math.ceil(len(sorted_members) / cfg['g'])
            draw_level = st.session_state.get('draw_level', 0)

            st.markdown("### 제비뽑기 진행 현황")
            st.info("실력(부수) 순으로 그룹을 나누어 제비뽑기를 진행합니다. 조 번호를 선택하면 다른 인원의 번호가 자동으로 바뀝니다(중복 방지).")

            # 그룹별 반복문 (실력순으로 끊어서 처리)
            for level in range(total_levels):
                start_idx = level * cfg['g']
                end_idx = min((level + 1) * cfg['g'], len(sorted_members))
                current_group = sorted_members.iloc[start_idx:end_idx]
                group_members = current_group['이름'].tolist()

                st.markdown(f"#### 그룹 {level + 1}")
                # st.markdown(f"#### 그룹 {level + 1} (상위 {start_idx + 1} ~ {end_idx}위)")
                cols = st.columns(cfg['g'])

                # 상황 1: 이미 완료된 그룹 (결과만 표시)
                if level < draw_level:
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        with cols[i % cfg['g']]:
                            assigned_team = st.session_state.draw_results[row['이름']]
                            st.success(f" **{row['이름']}** ➔ **{assigned_team}조**")

                # 상황 2: 현재 진행 중인 그룹 (선택 위젯 표시)
                elif level == draw_level:
                    available_options = list(range(1, cfg['g'] + 1))
                    state_key = f"group_selections_{level}"

                    # 세션 상태에 현재 그룹의 조 선택 현황 초기화
                    if state_key not in st.session_state:
                        st.session_state[state_key] = {name: available_options[i] for i, name in
                                                       enumerate(group_members)}
                        st.session_state[f"{state_key}_prev"] = st.session_state[state_key].copy()

                    # [Streamlit Callback] 조 번호 선택 시 중복을 방지하는 알고리즘
                    # A 회원이 1번 조를 선택하면, 기존에 1번이었던 B 회원의 조를 A의 이전 번호로 맞바꿈(Swap)
                    def on_selection_change(changed_member, lvl):
                        s_key = f"group_selections_{lvl}"
                        prev_selections = st.session_state[f"{s_key}_prev"]
                        current_selections = st.session_state[s_key]

                        new_val = st.session_state[f"select_{lvl}_{changed_member}"]
                        old_val = prev_selections[changed_member]

                        if new_val != old_val:
                            # 중복된 번호를 가진 다른 멤버를 찾아 값을 스왑(Swap)
                            for other_member, val in prev_selections.items():
                                if other_member != changed_member and val == new_val:
                                    st.session_state[f"select_{lvl}_{other_member}"] = old_val
                                    current_selections[other_member] = old_val
                                    break

                            current_selections[changed_member] = new_val
                            st.session_state[f"{s_key}_prev"] = current_selections.copy()

                    # 각 멤버별 조 선택 드롭다운 생성
                    for i, (idx, row) in enumerate(current_group.iterrows()):
                        name = row['이름']
                        with cols[i % cfg['g']]:
                            st.markdown(f" **{name}**")
                            # st.markdown(f" **{name}** ({row['부수']})")
                            current_val = st.session_state[state_key][name]
                            st.selectbox(
                                "조 선택",
                                options=available_options,
                                index=available_options.index(current_val),
                                key=f"select_{level}_{name}",  # 개별 위젯의 고유 키
                                on_change=on_selection_change,  # 값이 바뀔 때 스왑 함수 실행
                                args=(name, level),
                                label_visibility="collapsed",
                                disabled=not is_admin  # 관리자만 제비뽑기 조작 가능
                            )

                    st.write("")
                    if is_admin:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            # if st.button(f" 그룹 {level + 1} 랜덤 자동 배정", type="secondary", width="stretch"):
                            if st.button(f" 그룹 {level + 1} 랜덤 배정"):
                                # [Python] random.shuffle을 이용한 무작위 셔플링
                                shuffled_options = available_options[:len(group_members)]
                                random.shuffle(shuffled_options)
                                for i, name in enumerate(group_members):
                                    st.session_state.draw_results[name] = shuffled_options[i]
                                st.session_state.draw_level += 1
                                st.rerun()

                        with btn_col2:
                            if st.button(f" 그룹 {level + 1} 제비뽑기 완료 및 다음 진행", type="primary", width="stretch"):
                            # if st.button(f" 그룹 {level + 1} 제비뽑기 완료"):
                                for name in group_members:
                                    st.session_state.draw_results[name] = st.session_state[f"select_{level}_{name}"]
                                st.session_state.draw_level += 1
                                st.rerun()

                # 상황 3: 아직 도달하지 않은 대기 그룹
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
# 탭 3: 조 편성 결과 (Data Processing & Matrix Generation)
# ==========================================
with tab_team:
    # 1. 방어 로직 (Error Handling)
    # 설정 데이터가 없거나 제비뽑기가 미완료된 경우 경고 메시지 출력
    if "config" not in st.session_state:
        st.warning("먼저 '운영 설정'을 완료해주세요.")
    else:
        cfg = st.session_state.config

        if cfg.get('draw_method') == '제비뽑기' and not st.session_state.get('draw_completed', False):
            st.warning(" '운영 설정' 탭 하단에서 제비뽑기를 모두 완료해야 결과를 볼 수 있습니다.")
        else:
            # 2. 데이터 준비 (Pandas Data Prep)
            # [수정] 세션에 저장된 메인 데이터를 df라는 이름으로 꺼내옵니다.
            df = st.session_state.main_df
            # 참석자만 필터링하여 실력(부수) 순으로 정렬
            attendees = df[df[col_date] == 'Y'].copy()
            attendees['부수_숫자'] = attendees['부수'].apply(extract_busu)
            sorted_members = attendees.sort_values(['부수_숫자', '부수_조정1'], ascending=True).reset_index(drop=True)

            # 결과를 담을 Python 딕셔너리 초기화
            teams = {i: [] for i in range(1, cfg['g'] + 1)}
            team_stats = {i: {"sum": 0.0, "count": 0} for i in range(1, cfg['g'] + 1)}
            all_member_names = []

            # 3. 분배 알고리즘 (Sorting Algorithms)
            if cfg.get('draw_method', 'AI 선정') == 'AI 선정':
                # [S-Curve/Snake Draft 알고리즘]
                # 실력자가 특정 조에 쏠리지 않도록 1->2->3->3->2->1 순으로 지그재그 배정
                for idx, row in sorted_members.iterrows():
                    r_idx = idx // cfg['g']  # 몇 번째 라운드인지
                    pos_idx = idx % cfg['g']  # 라운드 내 순서
                    # 짝수 라운드는 정방향, 홀수 라운드는 역방향 배정
                    t_idx = (pos_idx + 1) if r_idx % 2 == 0 else (cfg['g'] - pos_idx)

                    teams[t_idx].append(f"{row['이름']}({row['부수']})")
                    all_member_names.append(row['이름'])
                    team_stats[t_idx]["sum"] += row['부수_숫자']
                    team_stats[t_idx]["count"] += 1
            else:
                # [제비뽑기 결과 연동] 사용자가 직접 선택하여 st.session_state.draw_results에 저장된 데이터를 불러옴
                for idx, row in sorted_members.iterrows():
                    name = row['이름']
                    t_idx = st.session_state.draw_results.get(name, 1)

                    teams[t_idx].append(f"{row['이름']}({row['부수']})")
                    all_member_names.append(row['이름'])
                    team_stats[t_idx]["sum"] += row['부수_숫자']
                    team_stats[t_idx]["count"] += 1

            # 4. 경기 모드 자동 판별 (Logic Switching)
            # 조당 평균 인원이 1.5명 이하면 개인전, 그 이상이면 단체전으로 판별
            avg_p = sum(t["count"] for t in team_stats.values()) / cfg['g']
            st.session_state.config['is_individual'] = True if avg_p <= 1.5 else False

            # 개인전은 세트 수, 단체전은 총 경기 수(단식+복식)를 점수 한도로 설정
            st.session_state.config['max_score_limit'] = cfg['set_count'] if st.session_state.config[
                'is_individual'] else cfg['total_g']

            # 라벨 생성 (예: "1조(홍길동)")
            st.session_state.labels = [f"{i}조({teams[i][0].split('(')[0]})" for i in range(1, cfg['g'] + 1) if teams[i]]
            st.session_state.teams = teams

            # 5. 시각화 (UI Rendering)
            st.markdown("### 조별 최종 구성 및 부수 합계")

            # 인원이 배정된 유효한 조만 리스트로 추출
            valid_teams = [t_num for t_num in range(1, cfg['g'] + 1) if teams[t_num]]

            # 한 줄에 표시할 열(Column) 개수 계산 (최대 5개, 5개 이하면 편성 조 수만큼)
            num_cols = min(len(valid_teams), 5)

            if num_cols > 0:
                # num_cols 단위로 끊어서 줄바꿈 처리
                for i in range(0, len(valid_teams), num_cols):
                    chunk = valid_teams[i:i + num_cols]
                    cols = st.columns(num_cols)  # 항상 동일한 비율의 컬럼 생성 (카드 사이즈 유지)

                    for j, t_num in enumerate(chunk):
                        with cols[j]:
                            # 팀원 목록을 <br> 태그로 연결하여 세로로 줄바꿈되도록 설정
                            members_html = "<br>".join(teams[t_num])

                            st.markdown(f"""
                                        <div class="team-card" style="font-size: 1rem;">
                                            <!-- ① 상단 요약 박스 (조, 인원, 부수합계) -->
                                            <div style="background-color:#f8f9fa; padding:8px; margin-bottom:10px; border-radius:5px; border:1px solid #eee;">
                                                <b>{t_num}조 _ {len(teams[t_num])}명 : {int(team_stats[t_num]['sum'])}부</b>
                                            </div>
                                            <!-- ② 하단 이름 목록 박스 -->
                                            <div style="line-height: 1.6;">
                                                {members_html}
                                            </div>
                                        </div>""", unsafe_allow_html=True)

            # 6. 매트릭스 생성 (Data Structure for Scoring)
            # [Pandas] 조별 리그 결과를 기록하기 위한 0으로 채워진 데이터프레임 생성
            if st.session_state.get('matrix') is None:
                st.session_state.matrix = pd.DataFrame(0.0, index=st.session_state.labels,
                                                       columns=st.session_state.labels)
                # 본인 조와의 대결은 계산 제외 (NaN 처리)
                for l in st.session_state.labels: st.session_state.matrix.loc[l, l] = np.nan

            # 개인전용 점수판 매트릭스 생성
            if st.session_state.get('ind_matrix') is None:
                all_member_names = sorted(list(set(all_member_names)))
                st.session_state.ind_matrix = pd.DataFrame(0.0, index=all_member_names, columns=all_member_names)
                for m in all_member_names: st.session_state.ind_matrix.loc[m, m] = np.nan

# ==========================================
# 탭 4: 경기 배정 및 결과 입력 (Match Management)
# ==========================================
with tab_match:
    # 데이터가 준비된 경우에만 실행 (방어적 프로그래밍)
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:

        # [Internal Function] 결과를 CSV로 물리적 저장하는 유틸리티 // 제거 가능함 _ 260407
        def auto_save_csv_tab4():
            with open(SAVE_FILE_NAME, 'w', encoding='utf-8-sig') as f:
                f.write(f"--- 경기 일자: {CURRENT_DATE} ---\n")
                f.write("\n[조별/단체전 결과]\n")
                st.session_state.matrix.to_csv(f)  # Pandas DF를 파일 객체에 바로 써넣음
                f.write("\n[개인별 통합 성적]\n")
                st.session_state.ind_matrix.to_csv(f)

        # [Algorithm] 라운드 로빈(Round Robin) 방식의 대진 생성 알고리즘
        def get_matches(teams):
            t_list = list(teams)
            if len(t_list) % 2: t_list.append(None)  # 홀수일 경우 부전승(None) 처리
            res = []
            for _ in range(len(t_list) - 1):
                for j in range(len(t_list) // 2):
                    if t_list[j] and t_list[-1 - j]:
                        res.append((t_list[j], t_list[-1 - j]))
                # 리스트를 회전시켜 다음 라운드 대진 생성
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            return res

        # 대진표 생성 및 설정값 불러오기
        all_matches = get_matches(st.session_state.labels)
        cfg = st.session_state.config
        t_count = cfg['t']  # 탁구대 개수
        s_games = cfg.get('s_games', 0)
        d_games = cfg.get('d_games', 0)

        is_ind = cfg.get('is_individual', False)

        # 경기 타입에 따른 점수 한도(limit) 설정
        if is_ind:
            limit = cfg.get('set_count', 3)
            match_info = "개인전"

        else:
            limit = cfg.get('total_g', 5)
            match_info = f"단식 {cfg.get('s_games', 0)} / 복식 {cfg.get('d_games', 0)}"

        # [Data Prep] 화면에 보여줄 경기 리스트 데이터프레임 생성
        m_data = []
        for i, (a, b) in enumerate(all_matches):
            # st.session_state.matrix에서 현재 점수를 실시간으로 가져옴
            # s1, s2 = st.session_state.matrix.loc[a, b], st.session_state.matrix.loc[b, a]
            # 844라인 수정 제안
            if a in st.session_state.matrix.index and b in st.session_state.matrix.columns:
                s1, s2 = st.session_state.matrix.loc[a, b], st.session_state.matrix.loc[b, a]
            else:
                # 키가 없으면 0이나 빈 값으로 처리
                s1, s2 = 0, 0

            status = " 종료" if (not np.isnan(s1) and (s1 + s2 > 0)) else " 대기"


            m_data.append({
                "순서": i + 1,
                "Table_No": f"{(i % t_count) + 1}번 대",  # 탁구대 번호 순차 배정
                "상태": status,
                "대진": f"{a} VS {b}",
                "경기 구성": match_info,
                "결과": f"{int(s1)} : {int(s2)}" if status == " 종료" else "-"
            })

        df_match = pd.DataFrame(m_data)

        # [Styling] 종료된 경기는 회색으로 표시하는 Pandas Style 정의
        def highlight_finished(row):
            if row['상태'] == ' 종료':
                return ['background-color: rgba(128, 128, 128, 0.15); color: gray;'] * len(row)
            return [''] * len(row)

        # [UI] 화면을 반으로 나눠 대진표 출력 (가독성 향상)
        mid_idx = (len(df_match) + 1) // 2
        df_left = df_match.iloc[:mid_idx].reset_index(drop=True)
        df_right = df_match.iloc[mid_idx:].reset_index(drop=True)

        col_title, col_info = st.columns([3, 7])

        with col_title:
            st.markdown("### 경기 배정표")
        with col_info:
            # 안내 문구의 높이를 제목과 맞추기 위해 상단 여백 보정 없이 info 출력
            st.info(" **아래 표에서 결과를 입력할 경기의 행(Row)을 클릭**하면 상세 입력창이 나타납니다.")

        col1, col2 = st.columns(2)

        with col1:
            styled_left = df_left.style.apply(highlight_finished, axis=1).set_properties(
                **{'font-size': '16px', 'font-weight': 'bold', 'text-align': 'center'})
            event_left = st.dataframe(
                styled_left,
                 width="stretch",
                 hide_index=True,
                 height=400,
                 on_select="rerun",
                 selection_mode="single-row",
                 key="df_left_select"
                 )

        with col2:
            if not df_right.empty:
                styled_right = df_right.style.apply(highlight_finished, axis=1).set_properties(
                    **{'font-size': '16px', 'font-weight': 'bold', 'text-align': 'center'})
                event_right = st.dataframe(
                    styled_right,
                     width="stretch",
                     hide_index=True,
                     height=400,
                     on_select="rerun",
                     selection_mode="single-row",
                     key="df_right_select"
                     )
            else:
                event_right = None

        # [Event Handling] 사용자가 클릭한 경기가 무엇인지 인덱스 파악
        selected_match_idx = None
        if event_left and event_left.selection.rows:
            selected_match_idx = event_left.selection.rows[0]
        elif event_right and event_right.selection.rows:
            selected_match_idx = event_right.selection.rows[0] + mid_idx

        # 사용자가 경기를 선택했을 때 나타나는 상세 입력창
        if selected_match_idx is not None:
            team_a, team_b = all_matches[selected_match_idx]
            st.divider()
            st.markdown(f"### {team_a} VS {team_b} 상세 결과 입력")

            # 관리자만 점수 입력 가능
            if not is_admin:
                st.warning(" 점수 입력은 관리자만 가능합니다. 사이드바에서 관리자 비밀번호를 입력해주세요.")
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
                            res_type = st.radio(f"{team_a} 결과", ["승", "패"], horizontal=True,
                                                 key=f"m{m_idx}_ind_res",
                                                 label_visibility="collapsed")
                        with c3:
                            win_scores = [f"{limit}:{i}" for i in range(limit)]
                            lose_scores = [f"{i}:{limit}" for i in range(limit)]
                            display_scores = win_scores if res_type == "승" else lose_scores
                            selected_score = st.radio("스코어 선택", display_scores, horizontal=True,
                                                 key=f"m{m_idx}_ind_score",
                                                 label_visibility="collapsed")
                        with c4:
                            st.markdown(
                                    f"<div style='margin-top:8px; font-weight:bold; text-align:center;'>{team_b}</div>",
                                            unsafe_allow_html=True)

                        if st.button("결과 저장", type="primary", key=f"btn_save_ind_match_{m_idx}"):
                            s_a, s_b = map(int, selected_score.split(':'))
                            st.session_state.matrix.loc[team_a, team_b] = s_a
                            st.session_state.matrix.loc[team_b, team_a] = s_b
                            auto_save_csv_tab4()
                            # [파일 관리] 일일 결과 및 누적 실적 동시 저장
                            save_daily_results(SAVE_FILE_NAME)
                            # 개인전이므로 조 이름에서 선수 이름만 추출하여 누적 기록 업데이트
                            p_a_name = team_a.split('(')[0].split('조')[-1].strip() if '조' in team_a else team_a
                            p_b_name = team_b.split('(')[0].split('조')[-1].strip() if '조' in team_b else team_b
                            update_cumulative_record(p_a_name, p_b_name, s_a, s_b)

                            st.success("저장 완료! 스코어보드에 반영되었습니다.")
                            st.rerun()
                    else:
                        # 해당 조의 실제 팀원 이름만 정확히 추출하는 함수
                        def get_team_players(team_str):
                            import re
                            match = re.search(r'(\d+)조', str(team_str))
                            if match and 'teams' in st.session_state:
                                t_idx = int(match.group(1))
                                if t_idx in st.session_state.teams:
                                    # '이름(부수)' 형태에서 이름만 분리하여 리스트로 반환
                                    return [p.split('(')[0] for p in st.session_state.teams[t_idx]]
                            return list(st.session_state.ind_matrix.index) # 실패 시 전체 인원 반환

                        team_a_players = get_team_players(team_a)
                        team_b_players = get_team_players(team_b)

                        # 현재 선택된 경기(Match)의 고유 인덱스를 키에 포함 (다른 경기와 충돌 방지)
                        m_idx = selected_match_idx

                        a_keys = [f"m{m_idx}_s_pa_{s}" for s in range(s_games)] + \
                                 [f"m{m_idx}_d_pa1_{d}" for d in range(d_games)] + \
                                 [f"m{m_idx}_d_pa2_{d}" for d in range(d_games)]

                        b_keys = [f"m{m_idx}_s_pb_{s}" for s in range(s_games)] + \
                                 [f"m{m_idx}_d_pb1_{d}" for d in range(d_games)] + \
                                 [f"m{m_idx}_d_pb2_{d}" for d in range(d_games)]

                        # 이미 선택된 인원을 드롭다운 목록에서 제외하는 함수
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
                                    st.markdown(f"<div style='margin-top:8px; font-weight:bold; color:#1f77b4;'>단식 {s + 1}</div>",
                                                unsafe_allow_html=True)
                                with c2:
                                    k_a = f"m{m_idx}_s_pa_{s}"
                                    avail_a = get_avail(team_a_players, k_a, a_keys)
                                    p_a = st.selectbox(f"{team_a} 선수", avail_a, key=k_a, label_visibility="collapsed")
                                with c3:
                                    res_type = st.radio("결과", ["승", "패"], horizontal=True,
                                                        key=f"m{m_idx}_s_res_{s}", label_visibility="collapsed")
                                with c4:
                                    display_scores = set_win_scores if res_type == "승" else set_lose_scores
                                    selected_score = st.radio("스코어", display_scores, horizontal=True,
                                                             key=f"m{m_idx}_s_score_{s}",
                                                             label_visibility="collapsed")
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
                                    p_a1 = st.selectbox(f"{team_a} 선수1", avail_a1, key=k_a1, label_visibility="collapsed")

                                    k_a2 = f"m{m_idx}_d_pa2_{d}"
                                    avail_a2 = get_avail(team_a_players, k_a2, a_keys)
                                    p_a2 = st.selectbox(f"{team_a} 선수2", avail_a2, key=k_a2, label_visibility="collapsed")

                                with c3:
                                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                                    res_type = st.radio("결과", ["승", "패"], horizontal=True,
                                                        key=f"m{m_idx}_d_res_{d}", label_visibility="collapsed")
                                with c4:
                                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                                    display_scores = set_win_scores if res_type == "승" else set_lose_scores
                                    selected_score = st.radio("스코어", display_scores, horizontal=True,
                                                             key=f"m{m_idx}_d_score_{d}",
                                                             label_visibility="collapsed")
                                with c5:
                                    k_b1 = f"m{m_idx}_d_pb1_{d}"
                                    avail_b1 = get_avail(team_b_players, k_b1, b_keys)
                                    p_b1 = st.selectbox(f"{team_b} 선수1", avail_b1, key=k_b1, label_visibility="collapsed")

                                    k_b2 = f"m{m_idx}_d_pb2_{d}"
                                    avail_b2 = get_avail(team_b_players, k_b2, b_keys)
                                    p_b2 = st.selectbox(f"{team_b} 선수2", avail_b2, key=k_b2, label_visibility="collapsed")

                                s_a, s_b = map(int, selected_score.split(':'))
                                match_results.append(("D", (p_a1, p_a2), s_a, s_b, (p_b1, p_b2)))

                        st.write("")
                        if st.button(" 상세 결과 저장 및 스코어보드 반영", type="primary", width="stretch", key=f"btn_save_match_{m_idx}"):
                            team_a_wins = 0
                            team_b_wins = 0

                            for res in match_results:
                                m_type = res[0]
                                if m_type == "S":
                                    _, p_a, s_a, s_b, p_b = res
                                    if p_a != "선택안함" and p_b != "선택안함" and p_a != p_b:
                                        st.session_state.ind_matrix.loc[p_a, p_b] = s_a
                                        st.session_state.ind_matrix.loc[p_b, p_a] = s_b

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

                            auto_save_csv_tab4()
                            # save_daily_results(SAVE_FILE_NAME)
                            st.success(
                                f"저장 완료! {team_a} ({team_a_wins}) : ({team_b_wins}) {team_b} 결과가 스코어보드에 반영되었습니다.")
                            st.rerun()
    else:
        st.info("조 편성이 완료되면 경기 배정표가 나타납니다.")

# ==========================================
# 탭 5: 결과 조회 및 종합 성적표 (Data Analysis & Visualization)
# ==========================================
with tab_score:
    if 'labels' in st.session_state and st.session_state.get('matrix') is not None:
        cfg = st.session_state.config

        is_ind = cfg.get('is_individual', False)
        # --- [추가] 실시간 글자 크기 제어 로직 ---
        if 'table_font_size' not in st.session_state:
            # 초기값 설정 (인원수에 따른 기본값 세팅)
            num_rows = len(st.session_state.labels)
            if num_rows <= 4:
                st.session_state.table_font_size = 20
            elif num_rows <= 6:
                st.session_state.table_font_size = 16
            elif num_rows <= 8:
                st.session_state.table_font_size = 13
            else:
                st.session_state.table_font_size = 11
        # if is_ind:
        #     limit = cfg.get('set_count', 3)
        # else:
        #     limit = cfg.get('total_g', 10)

        # [Internal Function] 결과 저장 로직 (중복 방지를 위한 내부 함수화)
        def auto_save_csv():
            with open(SAVE_FILE_NAME, 'w', encoding='utf-8-sig') as f:
                f.write(f"--- 경기 일자: {CURRENT_DATE} ---\n")
                f.write("\n[조별/단체전 결과]\n")
                st.session_state.matrix.to_csv(f)
                f.write("\n[개인별 통합 성적]\n")
                st.session_state.ind_matrix.to_csv(f)

        # [Logic] 종합 성적 계산 및 테이블 렌더링 함수
        def draw_summary_table():
            """
            Pandas Matrix 데이터를 기반으로 승/패/득점/실점/득실차를 계산하여
            HTML/CSS가 가미된 화려한 성적표를 출력합니다.
            """
            m = st.session_state.matrix
            # 새 결과 데이터프레임 생성
            rank = pd.DataFrame(index=st.session_state.labels)

            # [Pandas 행렬 연산] 전치 행렬(.T)과 비교하여 승/패 자동 계산
            rank['승'] = (m > m.T).sum(axis=1)  # 내가 상대보다 점수가 높은 경우의 수
            rank['패'] = (m < m.T).sum(axis=1)  # 내가 상대보다 점수가 낮은 경우의 수
            rank['득점'] = m.sum(axis=1, skipna=True).astype(int)  # 가로 합계 (나의 득점)
            rank['실점'] = m.sum(axis=0, skipna=True).astype(int)  # 세로 합계 (상대의 득점 = 나의 실점)
            rank['득실차'] = rank['득점'] - rank['실점']

            # 기존 점수판(m) 뒤에 계산된 성적(rank)을 가로로 붙임
            combined_df = pd.concat([m, rank[['승', '패', '득점', '실점', '득실차']]], axis=1)
            # 승수 -> 득실차 순으로 내림차순 정렬 (순위 결정)
            combined_df = combined_df.sort_values(['승', '득실차'], ascending=False)

            # 현재 세션의 폰트 사이즈 가져오기
            current_fs = st.session_state.table_font_size
            ROW_HEIGHT = f"{current_fs + 25}px"  # 글자 크기에 맞춰 행 높이 자동 조절
            # # 2. 인원수에 따른 폰트 및 높이 최적화 (더 촘촘하게 수정)
            # # num_rows = len(combined_df)
            # num_rows = len(m)
            #
            # if num_rows <= 4:
            #     font_size = 20
            #     # FONT_SIZE = "12px"
            #     # ROW_HEIGHT = "35px"
            # elif num_rows <= 6:
            #     font_size = 16
            #     # FONT_SIZE = "14px"
            #     # ROW_HEIGHT = "40px"
            # elif num_rows <= 8:
            #     font_size = 13
            #     # FONT_SIZE = "16px"
            #     # ROW_HEIGHT = "50px"
            # else:
            #     font_size = 11
            #     # FONT_SIZE = "18px"
            #     # ROW_HEIGHT = "60px"
            #
            # ROW_HEIGHT = "50px"

            styled_df = combined_df.style.format(precision=0, na_rep='-').set_properties(**{
                # 'font-size': FONT_SIZE,
                'text-align': 'center',
                'vertical-align': 'middle',
                'height': ROW_HEIGHT,
                # 'white-space': 'nowrap',  # 이름/텍스트 줄바꿈 절대 방지
            }).set_table_styles([
                {'selector': 'th',
                 'props': [('text-align', 'center'),
                    # ('font-size', FONT_SIZE),
                    ('vertical-align', 'middle'),
                    ('height', ROW_HEIGHT)
                ]},
            ])

            # HTML로 변환 후 CSS 클래스 주입 (전체 너비 활용을 위함)
            raw_html = styled_df.to_html().replace('\n', '')

            # 3. 반응형 및 컬럼 폭 고정을 위한 커스텀 CSS
            css = f"""
            <style>
            /*
            width: 100%: 표의 가로 길이를 화면(또는 표가 들어간 칸)의 가로폭에 100% 꽉 차게 맞춥니다.
            table-layout: fixed: 아주 중요한 속성입니다! 원래 표는 안에 들어간 글자 길이에 따라 칸 너비가 고무줄처럼 늘어났다 줄어들었다 합니다.
            이 속성을 넣으면 "내용물 길이에 상관없이 내가 지정한 너비대로 칸을 고정해!"라는 뜻이 됩니다.
            font-size: {current_fs}px: 파이썬에서 계산한 font_size 변수 값을 가져와서 표 안의 글자 크기를 상황에 맞게(동적으로) 조절합니다 
            */
            .custom-table-wrapper table {{
                 width: 100% !important;
                 table-layout: fixed !important;
                 font-size: {current_fs}px !important; /* 동적 폰트 사이즈 적용 */
            }}
            /*
            **th는 표의 제목 칸(헤더), td**는 일반 데이터 칸을 뜻합니다.
            white-space: nowrap: 글자가 길어져도 다음 줄로 줄바꿈(엔터)을 하지 않고 무조건 한 줄로 씁니다.
            overflow: hidden: 글자가 길어서 칸의 너비를 벗어나면, 삐져나온 글자를 안 보이게 숨깁니다.
            **text-overflow: ellipsis: 숨겨진 글자 끝에 말줄임표(...)를 달아줍니다. (예: 이름이 너무 길면 "김스트림릿..." 처럼 표시됨)
            padding: 2px 4px: 칸 안쪽의 위아래 여백을 2px, 좌우 여백을 4px로 아주 작게 설정해서 표를 위아래로 촘촘하고 컴팩트하게 만듭니다.
            */
            /* 모든 셀: 한 줄 표시(nowrap), 넘치면 말줄임표(...) 처리, 여백 최소화 */
            .custom-table-wrapper th, .custom-table-wrapper td {{
                 white-space: nowrap !important;
                 overflow: hidden !important;
                 text-overflow: ellipsis !important;
                 padding: 2px 4px !important; 
            }}

            /* 
            :nth-last-child(-n+5): CSS의 특수 선택자로, **"뒤에서부터 5번째 칸까지"를 의미합니다.
            주석에 적혀있듯 승, 패, 득점, 실점, 득실차 같은 데이터는 보통 1~2자리 숫자이므로 넓은 공간이 필요 없습니다. 
            그래서 이 5개 칸의 너비를 40px로 아주 좁게 고정하여 공간을 절약합니다.
            뒤에서 5개 컬럼 (승, 패, 득점, 실점, 득실차) 폭을 2자리 숫자에 맞게 축소 */
            .custom-table-wrapper th:nth-last-child(-n+5),
            .custom-table-wrapper td:nth-last-child(-n+5) {{
                 width: 70px !important; 
            }}

            /* 첫 번째 컬럼 (조 이름/조장 이름) 폭을 약간 넓게 확보
             :first-child: 표의 "첫 번째 칸"**을 의미합니다. (조 이름이나 조장 이름이 들어가는 곳)
             이름은 숫자보다 길기 때문에, 글자 크기가 작아지더라도 이름이 잘리지 않도록 최소 90px의 넉넉한 너비를 고정으로 확보해 줍니다.
             */
            .custom-table-wrapper th:first-child {{
                 /*width: {current_fs * 4.5}px !important;*/ 
                 /*  width: 110px !important; 폰트가 작아져도 이름 공간은 110px로 유지  */
                 width: {current_fs * 6}px !important; /* 글자 크기의 약 6배 정도로 폭 설정 */
            }}
            </style>
            """

            # CSS와 HTML 결합 후 출력
            full_width_html = css + '<div class="custom-table-wrapper">' + raw_html + '</div>'
            st.markdown(full_width_html, unsafe_allow_html=True)

        # --- 상단 컨트롤 바 (전체화면 & 글자 크기 조절) ---
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([5, 3, 2])

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
            # 글자 크기 조절 버튼 배치
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
            if is_admin and st.button("💾 수동 저장", type="secondary", use_container_width=True):
                auto_save_csv()
                st.success("저장 완료")

        is_fullscreen = st.session_state.get('fullscreen_table', False)

        if is_fullscreen:
            # 전체화면 모드: 다른 위젯을 숨기고 표만 강조
            st.markdown("### 종합 결과표 (전체 화면 모드)")
            if st.button(" 이전 화면으로 돌아가기", type="primary"):
                st.session_state.fullscreen_table = False
                st.rerun()

            st.write("")
            draw_summary_table()

        else:
            # 일반 모드: 결과 입력 창과 결과표를 동시에 표시
            col_btn1, col_btn2 = st.columns([8, 2])
            with col_btn1:
                if st.button(" 종합 결과표만 전체 화면으로 보기", type="primary"):
                    st.session_state.fullscreen_table = True
                    st.rerun()
            with col_btn2:
                if is_admin:  # 관리자만 수동 저장 버튼 노출
                    if st.button(" 결과 CSV 수동 저장", type="secondary", width="stretch"):
                        auto_save_csv()
                        # save_daily_results(SAVE_FILE_NAME)
                        st.success(f"저장 완료: {SAVE_FILE_NAME}")

            st.markdown(f"### {'조별' if not is_ind else '개인전'} 경기 결과 입력")

            # 관리자만 점수 입력 가능
            if not is_admin:
                st.warning(" 점수 입력은 관리자만 가능합니다. 사이드바에서 관리자 비밀번호를 입력해주세요.")
            else:
                st.info(" 기준이 되는 조(선수)를 선택하고 승/패 및 스코어를 입력하세요.")
                labels = st.session_state.labels

                if len(labels) > 0:
                    # 화면을 5개의 칸으로 나누어 한 줄에 배치 (비율 조정)
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2.5, 1.5])

                    with c1:
                        team_a = st.selectbox("기준 조/선수 (A)", labels, key="sb_team_a")
                    with c2:
                        team_b = st.selectbox("상대 조/선수 (B)", [l for l in labels if l != team_a], key="sb_team_b")

                    # if team_a and team_b:
                    if team_a and team_b:
                        with c3:
                            # res_type 선택 (승/패)
                            res_type = st.radio(f"{team_a} 결과", ["승", "패"], horizontal=True, key="sb_res")

                        with c4:
                            # --- 수정된 스코어 생성 로직 ---
                            win_scores = [
                                f"{s_a}:{limit - s_a}"
                                for s_a in range(limit, -1, -1)
                                if s_a >= (limit - s_a)
                            ]

                            # 패배 시: 위 승리 스코어의 앞뒤를 바꾼 리스트
                            lose_scores = [f"{s.split(':')[1]}:{s.split(':')[0]}" for s in win_scores]

                            # 선택된 결과에 따라 표시할 리스트 결정
                            display_scores = win_scores if res_type == "승" else lose_scores

                            selected_score = st.radio("스코어 선택", display_scores, horizontal=True, key="sb_score")

                        with c5:
                            # 입력창들의 라벨(글씨) 높이와 버튼 위치를 수평으로 맞추기 위한 여백
                            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                            # [수정됨] key="btn_save_team" 을 추가하여 중복 에러 방지
                            if st.button(" 저장", type="primary", width="stretch", key="btn_save_team"):
                                s_a, s_b = map(int, selected_score.split(':'))
                                st.session_state.matrix.loc[team_a, team_b] = s_a
                                st.session_state.matrix.loc[team_b, team_a] = s_b
                                auto_save_csv()
                                save_daily_results(SAVE_FILE_NAME)
                                st.success(f"저장 완료! {team_a} {s_a} : {s_b} {team_b} 결과가 스코어보드에 반영되었습니다.")
                                st.rerun()

            st.divider()
            st.markdown(f"### {'조별 리그' if not is_ind else '개인전'} 종합 결과표")

            draw_summary_table()
            # ------------------------------------------
            # 개인 성적 관리 섹션 (단체전 시 별도 운영)
            # ------------------------------------------
            if not is_ind:
                st.divider()
                # 1. 컬럼 비중 설정 (제목 3.5 : 안내/경고 문구 6.5)
                col_title, col_status = st.columns([3.5, 6.5])
                with col_title:
                    st.markdown("### 개인 성적 관리 및 단식 결과 입력")
                # st.markdown("### 개인 성적 관리 및 단식 결과 입력")

                with col_status:
                    if not is_admin:
                        # 관리자가 아닐 때: 경고 문구를 한 줄로 출력
                        st.error("🚫 **권한 없음:** 성적 입력 및 수정은 관리자만 가능합니다.", icon="⚠️")
                    else:
                        # 관리자일 때: 안내 문구를 한 줄로 출력
                        st.success("✅ **관리자 모드:** 입력된 단식 결과가 아래 표에 자동 반영됩니다.", icon="💡")

                        players = list(st.session_state.ind_matrix.index)
                        if len(players) > 0:
                            # 화면을 5개의 칸으로 나누어 한 줄에 배치 (비율 조정)
                            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2.5, 1.5])

                            with c1:
                                p_a = st.selectbox("기준 선수 (A)", players, key="ind_p_a")
                            with c2:
                                p_b = st.selectbox("상대 선수 (B)", [p for p in players if p != p_a], key="ind_p_b")

                            if p_a and p_b:

                                with c3:
                                    res_type_ind = st.radio(f"{p_a} 결과", ["승", "패"], horizontal=True, key="ind_res_radio")

                                with c4:
                                    ind_limit = 3
                                    win_scores_ind = [f"{ind_limit}:{i}" for i in range(ind_limit)]
                                    lose_scores_ind = [f"{i}:{ind_limit}" for i in range(ind_limit)]
                                    display_scores_ind = win_scores_ind if res_type_ind == "승" else lose_scores_ind
                                    selected_score_ind = st.radio("스코어 선택", display_scores_ind, horizontal=True,
                                                                    key="ind_score_radio")

                                with c5:
                                    # 입력창들의 라벨(글씨) 높이와 버튼 위치를 수평으로 맞추기 위한 여백
                                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                                    # [수정됨] key="btn_save_ind" 를 추가하여 중복 에러 방지
                                    if st.button(" 저장", type="primary", width="stretch", key="btn_save_ind"):
                                        s_a, s_b = map(int, selected_score_ind.split(':'))
                                        st.session_state.ind_matrix.loc[p_a, p_b] = s_a
                                        st.session_state.ind_matrix.loc[p_b, p_a] = s_b
                                        auto_save_csv()
                                        # save_daily_results(SAVE_FILE_NAME)
                                        # update_cumulative_record(p_a,p_b,s_a,s_b)
                                        st.success(f"저장 완료! {p_a} {s_a} : {s_b} {p_b} 결과가 반영되었습니다.")
                                        st.rerun()

                col_title, col_info = st.columns([3, 7])

                with col_title:
                    st.markdown("#### 개인 성적표 (매트릭스)")
                with col_info:
                    st.info(" **아래 표에서 특정 선수의 행(Row)을 클릭**하면 해당 선수의 상세 세트 전적을 확인할 수 있습니다.")

                # 관리자일 경우에만 표 직접 수정(data_editor) 활성화
                if is_admin:
                    st.success("마스터 권한 활성화: 표를 더블클릭하여 직접 수정할 수 있습니다.")
                    edited_ind_matrix = st.data_editor(
                         st.session_state.ind_matrix,
                         width="stretch",
                         height=400,
                         hide_index=False,
                         key="ind_matrix_editor"
                    )
                    # 수정 사항 발생 시 실시간 데이터 동기화
                    if not edited_ind_matrix.equals(st.session_state.ind_matrix):
                        st.session_state.ind_matrix = edited_ind_matrix
                        auto_save_csv()
                        # save_daily_results(SAVE_FILE_NAME)
                        st.rerun()
                else:
                    # [Read-only Mode] 일반 사용자는 선택 기능만 제공
                    event_matrix = st.dataframe(
                        st.session_state.ind_matrix.style.format(precision=0, na_rep='-'),
                         width="stretch",
                         height=400,
                         on_select="rerun",
                         selection_mode="single-row",
                         key="ind_matrix_select"
                    )

                    # [Detail View] 선택된 선수의 모든 경기 이력(vs 누구)을 리스트업
                    if event_matrix and event_matrix.selection.rows:
                        selected_idx = event_matrix.selection.rows[0]
                        selected_player = st.session_state.ind_matrix.index[selected_idx]

                        st.markdown(f"##### [{selected_player}] 상세 세트 전적")

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

                im = st.session_state.ind_matrix
                ind_rank = pd.DataFrame(index=im.index)
                ind_rank['개인승'] = (im > im.T).sum(axis=1)
                ind_rank['개인패'] = (im < im.T).sum(axis=1)
                ind_rank['세트득실'] = im.sum(axis=1, skipna=True) - im.sum(axis=0, skipna=True)

                st.markdown("#### 개인별 순위 (세트 기준)")

                styled_ind_rank = ind_rank.sort_values(['개인승', '세트득실'], ascending=False).style.format(precision=0,na_rep='-').set_properties(
                    **{
                         'font-size': '16px',
                         'font-weight': 'bold',
                         'text-align': 'center',
                         'padding': '10px 5px'
                    })
                st.table(styled_ind_rank)
    else:
        st.info("조 편성이 완료되면 스코어보드가 나타납니다.")
