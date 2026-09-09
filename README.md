# Differential Privacy-based Personal Information Innovation Zone
신뢰구간 상대폭 기반의 차분 프라이버시 기술을 활용해 프라이버시 예산 효율성과 통계적 정확도 사이의 균형을 맞추는 자동 질의 중단 메커니즘입니다.


## 👨‍🏫 프로젝트 소개
연구자의 반복적인 질의가 누적 정보 유출 위험을 증대시키는 문제를 방어하기 위한 자동화된 통제 장치를 구현해보았습니다.


## 🧑‍🤝‍🧑 개발자 소개
+ **임세은**: FrontEnd
+ **정보현**: BackEnd
+ **정수민**: BackEnd

## ⚙️ 기술 스택
+ **Language**: Python 3.11.3
+ **Framework**: Django 5.1.7
+ **Frontend**: React 19.1.1
+ **Database**: MySQL 8.0
+ **ORM** : Django ORM


## 💻 개발환경
+ **IDE**: VS Code
+ **Virtual Env**: venv / Anaconda
+ **Communication**: Discord, Notion


## 📝 프로젝트 아키텍쳐
<img width="400" height="500" alt="image" src="https://github.com/user-attachments/assets/8b6dc92f-2e4f-489c-bc86-70717a843a26" />


## 📌 주요 기능
+ **차분프라이버시 통계 분석**: 선택된 컬럼에 대해 라플라스 메커니즘을 적용한 통계 처리 결과를 산출합니다.
+ **동적 예산 관리**: 신뢰구간 상대폭 알고리즘에 기반하여 남은 쿼리 횟수를 자동으로 조정/제한하여 표시합니다.
  + 데이터 분석 요청이 들어오면, 해당 데이터에 대한 질의를 반복하며 신뢰구간 상대폭 변화를 계산합니다.
상대폭이 임계치 이하로 좁아지고, 그러한 구간이 일정 횟수 이상 유지될 때 통계가 수렴했다고 판정합니다.
계산을 50회 반복하여 나온 평균을 제한 질의 횟수로 설정하며, 해당 중단 시점을 동적으로 분석 환경에 적용합니다.


## ✒️ requirements
설치가 필요한 주요 라이브러리 목록입니다.

Django==5.1.7

mysqlclient==2.2.0

numpy>=1.24.0

scipy>=1.10.0

pandas>=2.0.0

django-cors-headers>=4.0.0

전체 목록은 [requirements.txt](requirements.txt) 참고.


## 🚀 실행 방법

### 0. 사전 준비
- Python 3.10 이상 (requirements.txt의 Django 5.2 / numpy 2.2가 3.10+ 요구)
- MySQL 8.0 (로컬에 설치되어 있고 실행 중이어야 함)
- Node.js 18 이상 (프론트엔드용)
- `mysqlclient` 패키지는 소스에서 빌드되므로 아래 도구가 미리 설치되어 있어야 `pip install`이 성공합니다.
  - Windows: [MySQL Connector/C](https://dev.mysql.com/downloads/connector/c/) 또는 Visual Studio Build Tools
  - macOS: `brew install mysql-client pkg-config`
  - Ubuntu/WSL: `sudo apt install -y python3-dev default-libmysqlclient-dev build-essential pkg-config`

### 1. DB 준비
MySQL에 접속해서 데이터베이스를 하나 만듭니다.
```sql
CREATE DATABASE privacy_db CHARACTER SET utf8mb4;
```

### 2. 백엔드 설정 파일 생성
`PBL/my_settings.py`는 DB 비밀번호 등 민감정보가 들어가서 저장소에 포함하지 않습니다.
[PBL/my_settings.py.example](PBL/my_settings.py.example)을 복사해서 `PBL/my_settings.py`로 만들고,
본인 MySQL 계정 정보로 채워넣으세요.
```bash
cp PBL/my_settings.py.example PBL/my_settings.py
```

### 3. 백엔드 실행
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

cd PBL
python manage.py migrate
python manage.py runserver
```
`http://localhost:8000/` 에서 Django 템플릿 기반 화면을 바로 확인할 수 있습니다.

### 4. 프론트엔드 실행 (React, 디자인 확인용)
```bash
cd frontend
npm install
npm run dev
```
`http://localhost:5173/` 접속. 백엔드 API를 호출하므로 3번의 Django 서버가 함께 켜져 있어야 합니다.
