# 🏓 리그 운영 시스템 (Club League Management System)

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## 📖 소개 (Introduction)
**[KOR]** **동호회 리그 운영 시스템**은 탁구, 배드민턴, 테니스 등 다양한 스포츠 동호회의 복잡한 리그 운영을 한 번에 해결해 주는 스마트 웹 애플리케이션입니다. 출석 체크부터 공정한 조 편성, 실시간 경기 진행, 스코어 기록 및 누적 전적(승률, 랭킹) 관리까지 모임 운영진의 수고를 덜어주고 회원들에게는 실제 대회와 같은 즐거운 경기 환경을 제공합니다.

**[ENG]** The **Club League Management System** is a smart web application designed to streamline the complex league operations of sports clubs such as table tennis, badminton, and tennis. From attendance tracking and fair group formation to real-time match progression, score recording, and cumulative history (win rates, rankings) management, it reduces the burden on organizers and provides an enjoyable, tournament-like environment for members.

## ✨ 주요 기능 (Key Features)
* <strong>📱 실시간 데이터 동기화 (Real-time Synchronization):</strong> 
  * [KOR] 동일한 '구장명(방 이름)'을 입력한 모든 기기(스마트폰, PC, 태블릿)에서 실시간으로 점수와 대진표가 공유됩니다.
  * [ENG] Scores and brackets are shared in real-time across all devices (smartphones, PCs, tablets) that enter the same 'Venue Name (Room Name)'.
* <strong>👥 스마트 조 편성 (Smart Group Formation):</strong> 
  * `AI 자동 편성 (AI Auto-matching)`: 참가자들의 부수(실력) 총합이 최대한 균등해지도록 시스템이 자동으로 조를 분배합니다. / The system automatically distributes members so the total skill level of each group is as balanced as possible.
  * `랜덤 제비뽑기 (Random Draw)`: 실력과 무관하게 무작위로 조를 편성합니다. / Groups are formed completely at random, regardless of skill level.
* <strong>📊 실시간 스코어보드 (상황판) (Real-time Scoreboard):</strong> 
  * [KOR] 현재 진행 중인 모든 경기의 현황과 조별 순위를 한눈에 파악할 수 있으며, 대형 모니터 출력을 위한 '전체 화면 모드'를 지원합니다.
  * [ENG] View the status of all ongoing matches and group standings at a glance. Supports 'Full Screen Mode' optimized for large monitors.
* <strong>📈 누적 전적 및 랭킹 관리 (Cumulative History & Rankings):</strong> 
  * [KOR] 모임 종료 후 결과를 CSV로 다운로드하고, 다음 모임 때 업로드하여 역대 누적 승률과 랭킹을 지속적으로 관리할 수 있습니다.
  * [ENG] Download results as a CSV after the meeting and upload them at the next meeting to continuously track all-time win rates and rankings.
* <strong>🔐 권한 분리 (Role-based Access):</strong> 
  * [KOR] 비밀번호를 통한 '관리자 모드(운영진용)'와 비밀번호 없이 접속하는 '일반 회원 모드(조회 전용)'를 지원하여 안전하게 데이터를 관리합니다.
  * [ENG] Securely manage data with a password-protected 'Admin Mode' for organizers and a password-free 'View-Only Mode' for regular members.

## 🚀 시작하기 (Getting Started)

### 설치 및 실행 (Installation & Run)
```bash
# 1. 필요 패키지 설치 (Install required packages)
pip install streamlit pandas

# 2. 애플리케이션 실행 (Run the application)
streamlit run app.py
