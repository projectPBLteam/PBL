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
