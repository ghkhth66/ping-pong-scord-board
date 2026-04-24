import streamlit as st


def show_help_section(lang):
    # 언어에 따른 텍스트 설정
    if lang == "한국어":
        # 이전 대화(인사말) 반영
        greeting = "👋 **안녕하세요! 무엇을 도와드릴까요?** 동호회 리그 운영 시스템에 오신 것을 환영합니다."

        title = "🏓 동호회 리그 운영 시스템 상세 사용 설명서"
        desc = ("본 시스템은 탁구, 배드민턴, 테니스 등 다양한 동호회의 복잡한 리그 운영을 돕는 스마트 플랫폼입니다.<br>"
                "출석 체크부터 공정한 조 편성, 실시간 경기 진행, 스코어 기록 및 누적 전적(승률, 랭킹) 관리까지 <br>"
                "모임 운영진의 수고를 덜어주고 회원들에게는 즐거운 경기 환경을 제공합니다.")
        tip = "💡 **운영 꿀팁:** 스마트폰이나 태블릿으로 접속하여 점수를 입력하고, 진행석의 노트북을 HDMI 포트로 대형 TV나 모니터에 연결해 스코어보드(상황판)를 띄워두시면 실제 대회 같은 분위기를 연출할 수 있습니다."

        sec1_title = "🔐 1. 시작하기 (접속 및 권한 관리)"
        sec1_body = {
            "구장명": "<strong>[필수] 구장명(방 이름) 입력:</strong> <br> 좌측 사이드바(>>>) 상단에 모임 이름이나 구장명을 입력하세요. <b>동일한 구장명을 입력한 모든 기기(스마트폰, PC)는 실시간으로 데이터와 화면이 동기화</b>됩니다.",
            "관리자": "<strong>👑 관리자 모드 (운영진용):</strong> <br> 최초 접속 시 원하는 비밀번호를 설정하면 관리자 권한이 부여됩니다. 관리자는 선수 명단 업로드, 조 편성, 점수 입력 및 수정, 데이터 다운로드 등 모든 기능을 사용할 수 있습니다.",
            "일반": "<strong>👀 일반 회원 모드 (조회용):</strong> <br> 비밀번호 입력 없이 구장명만 입력하고 접속하면 '조회 전용'으로 입장됩니다. 본인의 조 편성 결과와 실시간 경기 점수, 현재 순위를 확인할 수 있습니다."
        }

        sec2_title = "📁 2. 사전 준비 (데이터 업로드)"
        sec2_warn = "⚠️ 이 기능은 **관리자 권한<strong>이 있어야 활성화됩니다."
        sec2_body = {
            "명단": "</strong>기본 명단 업로드:<strong> <br> 동호회 회원의 '이름, 부수(실력 등급), 성별, 기본 참석 여부'가 적힌 CSV 파일을 업로드합니다. 엑셀에서 작성 후 'CSV(쉼표로 분리)' 형식으로 저장하시면 됩니다.",
            "누적": "<strong>누적 전적 데이터 (선택):</strong> <br> 이전 모임에서 다운로드했던 전적 데이터(승, 무, 패, 득실차 등)를 업로드하면, 오늘 경기 결과가 기존 전적에 누적되어 전체 랭킹이 계산됩니다."
        }

        sec3_title = "🚀 3. 단계별 진행 가이드 (운영 프로세스)"
        tabs = {
            "1": ["1️⃣ 출석체크 (참석자 확정)",
                  "- 업로드된 명단에서 오늘 참석한 인원만 체크박스로 선택합니다.\n- 지각자나 현장 방문객이 있다면 하단의 '새 멤버 추가' 기능을 통해 즉석에서 추가할 수 있습니다.\n- 완료 후 반드시 </strong>[참석자 확정하기]** 버튼을 눌러주세요."],
            "2": ["2️⃣ 운영 설정 (조 편성 방식 결정)",
                  "- **조 개수 및 인원 설정:** 총 참석 인원에 맞춰 몇 개의 조로 나눌지 설정합니다.\n- **편성 방식:<strong> \n  1) `AI 자동 편성`: 각 조의 총합 부수(실력)가 최대한 균등해지도록 시스템이 자동으로 분배합니다.\n  2) `랜덤 제비뽑기`: 실력과 무관하게 완전 무작위로 조를 편성합니다.\n- 설정 완료 후 </strong>[설정 확정]**을 누르세요."],
            "3": ["3️⃣ 조 편성 결과 확인",
                  "- 완성된 조별 명단과 각 조의 총합 부수를 확인합니다.\n- 특정 회원의 조를 변경해야 할 경우 관리자가 수동으로 드래그 앤 드롭(또는 선택)하여 조정할 수 있습니다.\n- 확정된 대진표를 회원들에게 안내합니다."],
            "4": ["4️⃣ 경기 배정 및 점수 입력",
                  "- 대진표 탭에서 현재 진행할 경기를 클릭합니다.\n- 각 세트별 점수(예: 11:9, 8:11)를 입력하거나, 최종 세트 스코어(예: 2:0)를 입력합니다.\n- **[상세 결과 저장]**을 누르는 즉시 모든 기기의 스코어보드에 점수가 반영됩니다."],
            "5": ["5️⃣ 스코어보드 (실시간 상황판)",
                  "- 현재 진행 중인 모든 경기의 현황과 조별 순위를 한눈에 봅니다.\n- 우측 상단의 '전체 화면 모드'를 켜면 대형 모니터에 띄우기 최적화된 UI로 변경됩니다."]
        }

        sec4_title = "💾 4. 모임 종료 후 마무리 (데이터 백업)"
        sec4_info = "모든 경기가 종료되면 [스코어보드] 탭 상단에서 **[누적 결과 다운로드]**와 **[상대전적 다운로드]<strong> 버튼을 눌러 CSV 파일을 개인 PC나 스마트폰에 저장하세요. 이 파일은 다음 모임 때 '누적 데이터'로 업로드하여 랭킹을 이어가는 데 사용됩니다."

        faq_title = "❓ 자주 묻는 질문 (FAQ)"
        faqs = {
            "Q1": ["Q. 다른 사람 핸드폰에서도 점수를 실시간으로 볼 수 있나요?",
                   "네! 모든 회원이 각자의 스마트폰으로 접속하여 동일한 '구장명'을 입력하면 됩니다. 화면 상단의 </strong>[🔄 최신 경기결과 불러오기]**를 누르거나 일정 시간마다 자동으로 동기화되어 실시간 점수를 확인할 수 있습니다."],
            "Q2": ["Q. 점수나 승패를 잘못 입력했어요. 수정할 수 있나요?",
                   "네, 가능합니다. 관리자 모드로 접속한 상태에서 [스코어보드] 탭 하단에 있는 '개인 성적표' 또는 '경기 기록' 표를 더블 클릭하면 엑셀처럼 직접 숫자를 수정할 수 있습니다. 수정 후 엔터를 치면 즉시 반영됩니다."],
            "Q3": ["Q. 관리자 비밀번호를 잊어버렸어요. 어떻게 초기화하나요?",
                   "보안을 위해 시스템 내에서 직접 초기화는 불가능합니다. 시스템 관리자(서버 호스팅 담당자)에게 문의하여 서버에 저장된 해당 구장의 `_pw.txt` 파일을 삭제 요청하시면, 다음 접속 시 새로운 비밀번호를 설정할 수 있습니다."]
        }

    else:  # 영어 버전 (English Version)
        # Greeting from previous context
        greeting = "👋 **Hello! How can I help you?** Welcome to the Club League Management System."

        title = "🏓 Club League Management System Detailed Guide"
        desc = (
            "This system is a smart operation platform designed to simplify complex league management for clubs (Table Tennis, Badminton, Tennis, etc.).<br>"
            "From attendance tracking and fair group formation to real-time match progression, score recording, and cumulative history (win rates, rankings) management, <br>"
            "it reduces the burden on organizers and provides an enjoyable competitive environment for members.")
        tip = "💡 **Pro Tip:** Access the system via smartphone to input scores, and connect a laptop at the control desk to a large TV or monitor via HDMI to display the Scoreboard. This creates a real tournament atmosphere!"

        sec1_title = "🔐 1. Getting Started (Access & Permissions)"
        sec1_body = {
            "구장명": "<strong>[Required] Enter Venue Name (Room Name):</strong> <br> Enter your club or venue name in the top left sidebar (>>>). <b>All devices (smartphones, PCs) entering the exact same name will sync data and screens in real-time.</b>",
            "관리자": "<strong>👑 Admin Mode (For Organizers):</strong> <br> Set a password on your first visit to gain admin privileges. Admins can upload rosters, form groups, input/edit scores, and download data.",
            "일반": "<strong>👀 Regular Member Mode (View-Only):</strong> <br> Access without a password by just entering the venue name. You will enter in 'View-Only' mode to check your group, real-time scores, and current standings."
        }

        sec2_title = "📁 2. Preparation (Data Upload)"
        sec2_warn = "⚠️ This feature is only active for users with **Admin privileges<strong>."
        sec2_body = {
            "명단": "</strong>Upload Basic Roster:** <br> Upload a CSV file containing members' 'Name, Tier (Skill Level), Gender, and Default Attendance'. Create this in Excel and save as 'CSV (Comma delimited)'.",
            "누적": "<strong>Cumulative Data (Optional):</strong> <br> Upload the match history data (wins, draws, losses, point differentials) downloaded from the previous meeting. Today's results will be added to this to calculate overall rankings."
        }

        sec3_title = "🚀 3. Step-by-Step Guide (Operation Process)"
        tabs = {
            "1": ["1️⃣ Attendance Check (Confirm Participants)",
                  "- Check the boxes only for members present today from the uploaded roster.\n- If there are latecomers or guests, use the 'Add New Member' feature at the bottom to add them on the spot.\n- Be sure to click **[Confirm Attendance]** when done."],
            "2": ["2️⃣ Operation Settings (Group Formation Method)",
                  "- **Number of Groups & Size:** Set how many groups to divide the total participants into.\n- **Formation Method:** \n  1) `AI Auto-matching`: The system automatically distributes members so the total skill level of each group is as balanced as possible.\n  2) `Random Draw`: Groups are formed completely at random, regardless of skill level.\n- Click **[Confirm Settings]** after configuring."],
            "3": ["3️⃣ Check Group Results",
                  "- Review the finalized group rosters and the total skill level of each group.\n- If a specific member needs to be moved, admins can manually adjust them via drag-and-drop (or selection).\n- Announce the finalized bracket to the members."],
            "4": ["4️⃣ Match Assignment & Score Input",
                  "- Click on the match to be played in the Bracket tab.\n- Enter the score for each set (e.g., 11:9, 8:11) or the final set score (e.g., 2:0).\n- As soon as you click **[Save Detailed Results]**, the scores are reflected on all devices' scoreboards."],
            "5": ["5️⃣ Scoreboard (Real-time Dashboard)",
                  "- View the status of all ongoing matches and group standings at a glance.\n- Turn on 'Full Screen Mode' in the top right for an optimized UI to display on large monitors."]
        }

        sec4_title = "💾 4. After the Meeting (Data Backup)"
        sec4_info = "When all matches are finished, be sure to click the **[Download Cumulative Results]** and **[Download Head-to-Head Records]<strong> buttons at the top of the [Scoreboard] tab to save the CSV files to your PC or smartphone. You will upload these files as 'Cumulative Data' at the next meeting to continue the rankings."

        faq_title = "❓ Frequently Asked Questions (FAQ)"
        faqs = {
            "Q1": ["Q. Can other people see the scores in real-time on their phones?",
                   "Yes! All members just need to access the site on their smartphones and enter the same 'Venue Name'. They can click </strong>[🔄 Load Latest Results]** at the top of the screen or wait for the automatic sync to see real-time scores."],
            "Q2": ["Q. I entered a score or result incorrectly. Can I edit it?",
                   "Yes. While logged in as an Admin, double-click the 'Individual Scoreboard' or 'Match Records' table at the bottom of the [Scoreboard] tab. You can edit the numbers directly like in Excel. Press Enter to apply immediately."],
            "Q3": ["Q. I forgot the admin password. How do I reset it?",
                   "For security reasons, direct resets within the system are not possible. Please contact the system administrator (server host) and request the deletion of the `_pw.txt` file for your venue. You can then set a new password on your next visit."]
        }

    # ---------------------------------------------------------
    # 화면 출력 실행 (UI Rendering)
    # ---------------------------------------------------------

    # 인사말 출력 (이전 대화 반영)
    st.success(greeting)

    st.markdown(f"### {title}")
    st.markdown(desc, unsafe_allow_html=True)
    st.info(tip)
    st.divider()

    st.markdown(f"#### {sec1_title}")
    for key in sec1_body:
        st.markdown(sec1_body[key], unsafe_allow_html=True)
    st.write("")  # 여백

    st.markdown(f"#### {sec2_title}")
    st.warning(sec2_warn)
    for key in sec2_body:
        st.markdown(sec2_body[key], unsafe_allow_html=True)
    st.write("")

    st.markdown(f"#### {sec3_title}")
    for key in tabs:
        with st.expander(tabs[key][0]):
            # 줄바꿈(\n)이 마크다운에서 잘 보이도록 처리
            st.markdown(tabs[key][1].replace("\n", "<br>"), unsafe_allow_html=True)
    st.write("")

    st.markdown(f"#### {sec4_title}")
    st.error(sec4_info)  # 중요도를 높이기 위해 error(빨간색) 또는 warning 박스 사용 권장

    st.divider()
    st.markdown(f"#### {faq_title}")
    for key in faqs:
        with st.expander(faqs[key][0]):
            st.write(faqs[key][1])
