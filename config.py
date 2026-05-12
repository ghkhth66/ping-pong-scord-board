# UX/UI 개선을 위한 커스텀 CSS (버튼 색상, 테이블 너비, 정렬 등 디자인 요소 변경)
main_markdown_text = """
<style>
    /* =========================================
       1. 전체 화면 및 레이아웃 여백 조정
       ========================================= */
    
    /* 메인 화면(우측)의 상하 여백 줄이기 */
    /* 기본값(4\~6rem)이 너무 넓어 화면 상단이 비어 보이는 것을 방지합니다. */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important;
    }
    
    /* 사이드바(좌측)의 상단 여백 줄이기 */
    /* 메인 화면과 사이드바의 시작 높이를 비슷하게 맞추기 위해 사용합니다. */
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }
    
    /* 다단(Column) 레이아웃 내부 요소들의 수직 중앙 정렬 */
    /* st.columns()를 썼을 때, 양쪽 컬럼의 내용물 높이가 달라도 세로 중앙에 예쁘게 맞춰집니다. */
    [data-testid="column"] { 
        display: flex;             /* Flexbox 레이아웃 활성화 */
        flex-direction: column;    /* 내부 요소들을 위에서 아래로(세로로) 배치 */
        justify-content: center;   /* 세로 기준 '중앙'에 오도록 정렬 */
    }
    
    
    /* =========================================
       2. 버튼(Button) 디자인 및 간격 설정
       ========================================= */
    
    /* 모든 버튼의 상하 여백 미세 조정 */
    /* 버튼들이 위아래 요소와 너무 딱 붙거나 멀어지지 않게 간격을 통일합니다. */
    .stButton > button {
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }
    
    /* Primary(주요) 버튼 스타일 변경 */
    /* st.button("확인", type="primary") 처럼 사용된 강조 버튼의 색상을 바꿉니다. */
    div.stButton > button[kind="primary"] { 
        background-color: #28a745 !important; /* 배경색을 초록색으로 강제 적용 */
        color: white !important;              /* 글자색을 흰색으로 강제 적용 */
    }
    
    /* Secondary(보조/일반) 버튼 스타일 변경 */
    /* type을 지정하지 않은 일반 버튼들의 색상을 바꿉니다. */
    div.stButton > button[kind="secondary"] { 
        background-color: #dc3545 !important; /* 배경색을 빨간색으로 강제 적용 */
        color: white !important;              /* 글자색을 흰색으로 강제 적용 */
    }
    
    
    /* =========================================
       3. 기본 위젯(탭, 라디오, 알림창 등) 스타일
       ========================================= */
    
    /* 탭(Tabs) 내부의 상단 여백 줄이기 */
    /* 탭 메뉴를 클릭했을 때, 아래 뜨는 내용물이 탭 제목과 너무 멀어지지 않게 당겨줍니다. */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 10px !important; 
    }
    
    /* 라디오 버튼(Radio) 가로 정렬 및 간격 축소 */
    /* 기본적으로 세로로 나열되는 라디오 버튼을 가로로 예쁘게 나열합니다. */
    div.row-widget.stRadio > div { 
        flex-direction: row; /* 세로(column) 배치를 가로(row) 배치로 변경 */
        gap: 10px;           /* 동그라미 항목들 사이의 간격을 10px로 좁게 설정 */
        align-items: center; /* 동그라미와 글자가 삐뚤어지지 않게 수직 중앙 정렬 */
    }
    
    /* 알림창(st.info, st.warning, st.success 등) 상하 여백 조절 */
    /* 알림창이 차지하는 불필요한 위아래 공간을 줄여줍니다. */
    .stAlert {
        margin-top: 10px !important;
        margin-bottom: 10px !important;
    }
    
    /* Expander(접기/펴기 메뉴) 헤더 간격 조절 */
    /* st.expander()의 제목 부분 위아래 여백을 줄여서 공간을 절약합니다. */
    .streamlit-expanderHeader {
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }
    
    
    /* =========================================
       4. 커스텀 클래스 (사용자 정의 요소)
       ========================================= */
    
    /* 특정 배너(알림창, 설정창 등)를 꾸미는 디자인 */
    /* st.markdown("<div class='setting-banner'>내용</div>", unsafe_allow_html=True) 형태로 사용합니다. */
    .setting-banner { 
        background-color: #f8f9fa; /* 배경색을 아주 연한 회색으로 설정 */
        border: 2px solid #28a745; /* 테두리를 2px 두께의 초록색 실선으로 설정 */
        border-radius: 12px;       /* 모서리를 둥글게 처리 (숫자가 클수록 더 둥글어짐) */
        padding: 20px;             /* 테두리 안쪽 여백을 20px 주어 글자가 테두리에 붙지 않게 함 */
        margin-bottom: 20px;       /* 배너 아래쪽 바깥 여백을 20px 주어 다음 요소와 간격을 띄움 */
    }
    
    /* 커스텀 테이블을 감싸는 영역의 너비 설정 */
    /* HTML로 직접 만든 테이블이 화면 가로 길이에 꽉 차도록 만들어 줍니다. */
    .custom-table-wrapper { 
        width: 100%; 
    }
</style>
"""

# CSS 스타일 정의
css_responsive_text = """
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

css_tab_score = """
<style>
.custom-table-wrapper {{ overflow-x: auto; }}
.custom-table-wrapper table {{ width: 100% !important; border-collapse: collapse !important; font-size: {current_fs}px !important; }}
.custom-table-wrapper th, .custom-table-wrapper td {{ white-space: nowrap !important; padding: 4px 8px !important; border: 1px solid #dee2e6 !important; }}
.custom-table-wrapper th {{ background-color: #f8f9fa; }}
.custom-table-wrapper td:nth-last-child(-n+5) {{ background-color: #fffef0; font-weight: bold; width: 60px !important; }}
</style>
"""

# ==========================================
# HTML / CSS 디자인 템플릿 모음
# ==========================================

TEAM_CARD_TEMPLATE = """
<div class="team-card" style="font-size: 1rem;">
    <div style="background-color:#f8f9fa; padding:8px; margin-bottom:10px; border-radius:5px; border:1px solid #eee;">
        <b>{t_num}조 _ {team_len}명 : {team_sum}부</b>
    </div>
    <div style="line-height: 1.6;">{members_html}</div>
</div>
"""
# ==========================================
# config.py (기존 내용 아래에 추가해 주세요)
# ==========================================

# 1. 데이터프레임(표) 컬럼 구조 정의
# 선수명단, 누적전적, 상대전적 시트의 기본 뼈대가 되는 컬럼명들입니다.
COL_PLAYER_LIST = ["순서", "이름", "참석예정", "성별", "부수", "부수_조정", "직책", "조편성_신청"]
COL_CUMULATIVE = ["방이름", "이름", "총경기수", "승", "패", "득점", "실점"]
COL_H2H = ["방이름", "Player1", "Player2", "P1_Win", "P2_Win", "P1_Score", "P2_Score"]

# 2. 시스템 공통 메시지 및 기본값
MSG_NO_SELECTION = "선택안함"  # 부전승 등 선수가 매칭되지 않았을 때의 텍스트
DEFAULT_ROOM_NAME = "기본방"   # 방 이름이 설정되지 않았을 때 들어갈 기본값
MSG_NO_H2H_RECORD = "아직 두 선수의 누적 맞대결 기록이 없습니다."
BTN_CLOSE = "닫기"

# 3. 세션 상태(Session State) 초기화 대상 키 목록
# 설정을 초기화할 때 지워야 할 데이터 목록입니다.
KEYS_TO_DELETE_ON_RESET = ['matrix', 'ind_matrix', 'teams', 'draw_results']

# 🌟 [추가된 부분] 로그아웃 시 현재 방의 임시 데이터를 모두 삭제하여 다른 방에 영향 주지 않기
keys_to_clear_is_admin = ['config', 'config_confirmed', 'attendance_confirmed', 'labels', 'teams',
                          'draw_results', 'draw_completed', 'draw_level', 'matrix', 'ind_matrix',
                          'main_df', 'cum_df', 'h2h_df']

# 🌟 [추가된 부분] 새 방에 들어가기 전에 기존 세션 찌꺼기 완벽 초기화
keys_to_clear_tab_login = ['config', 'config_confirmed', 'attendance_confirmed', 'labels', 'teams',
                           'draw_results', 'draw_completed', 'draw_level', 'matrix', 'ind_matrix']

# 1. 현재 경기의 진행 상태와 관련된 세션 변수들만 골라서 삭제합니다.
keys_to_reset = [
    'config_confirmed', 'attendance_confirmed', 'labels', 'teams',
    'draw_results', 'draw_completed', 'draw_level', 'matrix', 'ind_matrix',
    'main_matrix_editor', 'ind_matrix_editor'
]
