# Suno AI music player

### 래퍼 jyaenugu가 작사한 AI노래를 감상할 수 있는 음악 감상 프로그램

단순히 음원을 공개하는 것이 아니라, 음악 게임 형식의 앨범으로 출시할 계획입니다. 

기존의 일방적인 음원 공개를 넘어, 게임 플레이를 통해 음악을 직접 경험하고 즐길 수 있는 새로운 방식의 앨범을 선보이고자 합니다.

---
## 주요 기능

- WAV 음악 파일 재생
- 노래별 가사 연동 
- 셔플/이전/다음/반복/슬라이더 등 기본 컨트롤 지원
- 곡 순서 드래그&드롭 변경
- 회원 인증(로그인/로그아웃)

---


## 기술 스택
- Python 3.12.7
- PyQt5
- SQLite (기본 데이터베이스)

---



## 환경 정보

> 이 프로젝트는 Ubuntu 24.04.2 LTS (코드네임: noble) 기반 리눅스 환경에서 개발 및 테스트되었습니다.  
> Windows, MacOS에서도 실행 가능하지만, 일부 명령어는 다를 수 있으니 참고해 주세요.

---

## 설치 및 실행 방법

```bash
# 1. 가상환경 생성 및 활성화
python3 -m venv game-env
source game-env/bin/activate   # Windows는 'game-env\Scripts\activate'

# 2. 필수 라이브러리 설치
pip install PyQt5 opencv-python-headless
pip install qdarkstyle
pip install qt-material

# 3. 프로젝트 디렉터리로 이동
cd music_player

# 4. 게임 실행
python -m music.main

````
---
