import streamlit as st


def show_help_section(lang):
    # 언어에 따른 텍스트 설정
    if lang == "한국어":
        title = "🏓 동호회 리그 운영 시스템 사용 설명서"
        desc = ("본 시스템은 동호회(탁구, 배드민턴 등)의 출석 체크, "
                "조 편성, 경기 진행, 스코어 기록 및 누적 전적관리를 <br>"
                "한 번에 해결해 주는 스마트 운영 플랫폼입니다.")
        tip = "💡 **Tip:** 스마트폰에서 접속 후 HDMI 포트를 통해 대형 모니터에 연결하여 사용하시면 더욱 좋습니다."

        sec1_title = "🔐 1. 시작하기 (접속 및 권한)"
        sec1_body = {
            "구장명": "**구장명(방 이름) 입력:** <br> 좌측 사이드바(>>>)에서 구장명을 입력하세요. 같은 구장명을 입력한 기기끼리는 실시간으로 화면이 공유됩니다.",
            "관리자": "**관리자 모드:** <br> 최초 접속 시 비밀번호를 설정하면, 이후 해당 비밀번호로 관리자 권한이 활성화됩니다.",
            "일반": "**일반 회원:** <br> 비밀번호 입력 없이 접속 시 조회 전용으로만 사용 가능합니다."
        }

        sec2_title = "📁 2. 사전 준비 (데이터 업로드)"
        sec2_warn = "⚠️ 이 기능은 **관리자만** 가능합니다."
        sec2_body = {
            "명단": "**명단 업로드:** <br> 회원의 이름, 부수, 참석 여부가 적힌 CSV 파일을 업로드합니다.",
            "누적": "**누적 데이터:** <br> 이전 모임의 전적 데이터를 업로드하여 역대 전적을 이어갈 수 있습니다."
        }

        sec3_title = "🚀 3. 단계별 진행 가이드"
        tabs = {
            "1": ["1️⃣ 출석체크", "명단에서 참석자를 체크하고 [참석자 확정하기]를 누릅니다."],
            "2": ["2️⃣ 운영 설정", "조 구성, 경기 규칙 등을 설정합니다. AI 자동 편성 또는 제비뽑기를 선택 후 [설정 확정]을 누르세요."],
            "3": ["3️⃣ 조 편성 결과", "완성된 조별 명단과 총합 부수를 확인하고 회원들에게 안내합니다."],
            "4": ["4️⃣ 경기 배정 및 입력", "대진표에서 진행할 경기를 클릭하여 점수를 입력하고 [상세 결과 저장]을 누르면 즉시 스코어보드에 반영됩니다."],
            "5": ["5️⃣ 스코어보드 (상황판)", "전체 화면 모드를 지원합니다. 상세 기록을 확인하세요."]
        }

        sec4_title = "💾 4. 모임 종료 후 마무리"
        sec4_info = "모임 종료 시 [스코어보드] 탭 상단에서 **[누적 결과 다운로드]**와 **[상대전적 다운로드]**를 반드시 진행하여 데이터를 백업하세요."

        faq_title = "❓ 자주 묻는 질문 (FAQ)"
        faqs = {
            "Q1": ["Q. 다른 사람 핸드폰에서도 점수를 볼 수 있나요?", "네! 같은 구장명을 입력하고 [🔄 최신 경기결과 불러오기]를 누르면 실시간으로 동기화됩니다."],
            "Q2": ["Q. 점수를 잘못 입력했어요. 수정할 수 있나요?", "관리자 모드일 경우 [스코어보드] 탭 하단 '개인 성적표' 표를 더블 클릭하여 직접 수정이 가능합니다."],
            "Q3": ["Q. 비밀번호를 잊어버렸어요.", "시스템 관리자에게 문의하여 해당 구장의 `_pw.txt` 파일을 삭제 요청하세요."]
        }

    else:  # 영어 버전
        title = "🏓 Club League Management System User Guide"
        desc = ("This system is a smart operation platform that handles "
                "attendance, group formation, match play, score recording, <br>"
                "and cumulative history management for clubs (Table Tennis, Badminton, etc.) all at once.")
        tip = "💡 **Tip:** We recommend connecting to a large monitor via HDMI port after accessing from your smartphone."

        sec1_title = "🔐 1. Getting Started (Access & Permissions)"
        sec1_body = {
            "구장명": "**Enter Venue Name:** <br> Enter the venue name in the left sidebar (>>>). Devices entering the same name will share the screen in real-time.",
            "관리자": "**Admin Mode:** <br> Set a password on your first visit to enable admin privileges (score input, data management).",
            "일반": "**Regular Member:** <br> Access without a password to use in 'View-Only' mode."
        }

        sec2_title = "📁 2. Preparation (Data Upload)"
        sec2_warn = "⚠️ This feature is for **Admins only**."
        sec2_body = {
            "명단": "**Upload Roster:** <br> Upload a CSV file containing member names, skill levels, and attendance status.",
            "누적": "**Cumulative Data:** <br> Upload previous match history to continue the records."
        }

        sec3_title = "🚀 3. Step-by-Step Guide"
        tabs = {
            "1": ["1️⃣ Attendance", "Check attendance in the roster and click [Confirm Attendance]."],
            "2": ["2️⃣ Settings", "Configure groups and match rules. Select AI Auto-matching or Draw, then [Confirm]."],
            "3": ["3️⃣ Group Results", "Check the finalized groups and total skill levels."],
            "4": ["4️⃣ Match Input", "Click the match in the bracket, input scores, and save."],
            "5": ["5️⃣ Scoreboard", "Supports full-screen mode. View detailed history and match-ups."]
        }

        sec4_title = "💾 4. After the Meeting"
        sec4_info = "Upon finishing, please download the **[Cumulative Results]** and **[Head-to-Head Records]** from the [Scoreboard] tab to back up your data."

        faq_title = "❓ FAQ"
        faqs = {
            "Q1": ["Q. Can others see the scores on their phones?",
                   "Yes! Enter the same venue name and click [🔄 Load Latest Results]."],
            "Q2": ["Q. Can I edit scores if entered incorrectly?",
                   "If in Admin Mode, double-click the 'Individual Scoreboard' table at the bottom of the [Scoreboard] tab."],
            "Q3": ["Q. I forgot my password.",
                   "Please ask the system administrator to delete the `_pw.txt` file for that venue."]
        }

    # 출력 실행
    st.markdown(f"### {title}")
    st.markdown(desc, unsafe_allow_html=True)
    st.markdown(tip)
    st.divider()

    st.markdown(f"#### {sec1_title}")
    for key in sec1_body: st.markdown(sec1_body[key], unsafe_allow_html=True)

    st.markdown(f"#### {sec2_title}")
    st.warning(sec2_warn)
    for key in sec2_body: st.markdown(sec2_body[key], unsafe_allow_html=True)

    st.markdown(f"#### {sec3_title}")
    for key in tabs:
        with st.expander(tabs[key][0]):
            st.write(tabs[key][1])

    st.markdown(f"#### {sec4_title}")
    st.info(sec4_info)

    st.divider()
    st.markdown(f"#### {faq_title}")
    for key in faqs:
        with st.expander(faqs[key][0]):
            st.write(faqs[key][1])

# import streamlit as st
#
# def show_help_section():
#     st.markdown("### 🏓 동호회 리그 운영 시스템 사용 설명서")
#     text = (
#         "본 시스템은 동호회(탁구, 배드민턴 등)의 출석 체크,"
#         "조 편성, 경기 진행, 스코어 기록 및 누적 전적관리를 <br>"
#         "한 번에 해결해 주는 스마트 운영 플랫폼입니다."
#     )
#     st.markdown(text, unsafe_allow_html=True)
#     st.markdown("💡 **Tip:** 스마트폰에서 접속 후 HDMI 포트를 통해 대형 모니터에 연결하여 사용하시면 더욱 좋습니다.")
#
#     st.divider()
#
#     # 1. 시작하기
#     st.markdown("#### 🔐 1. 시작하기 (접속 및 권한)")
#     st.markdown("- **구장명(방 이름) 입력:** <br>"
#                  " 좌측 사이드바(>>>)에서 구장명을 입력하세요.  같은 구장명을 입력한 기기끼리는 실시간으로 화면이 공유됩니다.", unsafe_allow_html=True)
#     st.markdown("- **관리자 모드:** <br>"
#                 " 최초 접속 시 비밀번호를 설정하면, 이후 해당 비밀번호로 관리자 권한(점수 입력, 데이터 관리)이 활성화됩니다.", unsafe_allow_html=True)
#     st.markdown("- **일반 회원:** <br> "
#                 "비밀번호 입력 없이 접속 시 조회 전용으로만 사용 가능합니다.", unsafe_allow_html=True)
#
#     # 2. 사전 준비
#     st.markdown("#### 📁 2. 사전 준비 (데이터 업로드)")
#     st.warning("⚠️ 이 기능은 **관리자만** 가능합니다.")
#     st.markdown("- **명단 업로드:** <br>"
#                 "회원의 이름, 부수, 참석 여부가 적힌 CSV 파일을 업로드합니다.", unsafe_allow_html=True)
#     st.markdown("- **누적 데이터:** <br>"
#                 "이전 모임의 전적 데이터를 업로드하여 역대 전적을 이어갈 수 있습니다.", unsafe_allow_html=True)
#
#     # 3. 진행 가이드
#     st.markdown("#### 🚀 3. 단계별 진행 가이드")
#
#     with st.expander("1️⃣ 출석체크"):
#         st.write("명단에서 참석자를 체크하고 [참석자 확정하기]를 누릅니다. 모임 후 [최신 명단 다운로드]로 출석 현황을 저장하세요.")
#     with st.expander("2️⃣ 운영 설정"):
#         st.write("조 구성, 경기 규칙 등을 설정합니다. AI 자동 편성 또는 제비뽑기를 선택 후 [설정 확정]을 누르세요.")
#     with st.expander("3️⃣ 조 편성 결과"):
#         st.write("완성된 조별 명단과 총합 부수를 확인하고 회원들에게 안내합니다.")
#     with st.expander("4️⃣ 경기 배정 및 입력"):
#         st.write("대진표에서 진행할 경기를 클릭하여 점수를 입력하고 [상세 결과 저장]을 누르면 즉시 스코어보드에 반영됩니다.")
#     with st.expander("5️⃣ 스코어보드 (상황판)"):
#         st.write("전체 화면 모드를 지원합니다. 특정 선수의 행을 클릭하면 상세 히스토리가 나오고, 두 선수를 선택해 역대 맞대결 전적도 확인 가능합니다.")
#
#     # 4. 종료
#     st.markdown("#### 💾 4. 모임 종료 후 마무리")
#     st.info("모임 종료 시 [스코어보드] 탭 상단에서 **[누적 결과 다운로드]**와 **[상대전적 다운로드]**를 반드시 진행하여 데이터를 백업하세요.")
#
#     # FAQ
#     st.divider()
#     st.markdown("#### ❓ 자주 묻는 질문 (FAQ)")
#
#     with st.expander("Q. 다른 사람 핸드폰에서도 점수를 볼 수 있나요?"):
#         st.write("네! 같은 구장명을 입력하고 [🔄 최신 경기결과 불러오기]를 누르면 실시간으로 동기화됩니다.")
#
#     with st.expander("Q. 점수를 잘못 입력했어요. 수정할 수 있나요?"):
#         st.write("관리자 모드일 경우 [스코어보드] 탭 하단 '개인 성적표' 표를 더블 클릭하여 직접 수정이 가능합니다.")
#
#     with st.expander("Q. 비밀번호를 잊어버렸어요."):
#         st.write("시스템 관리자에게 문의하여 해당 구장의 `_pw.txt` 파일을 삭제 요청하세요. 삭제 후 다시 설정할 수 있습니다.")
