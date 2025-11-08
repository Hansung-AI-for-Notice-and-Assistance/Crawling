# HANA – Hansung AI for Notice & Assistance

> 한성대학교 공지사항 자동 수집 및 AI 기반 데이터 가공 시스템

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

**HANA**는 한성대학교 공지사항을 자동으로 수집하고, AI를 활용하여 신청 기간을 추출하며, OCR로 이미지 기반 공지도 텍스트로 변환하는 크롤링 시스템입니다.

---

## ✨ 주요 기능

### 🔍 **자동 크롤링**
- RSS 피드와 HTML 파싱을 통한 공지사항 수집
- 본문, 이미지, 첨부파일 자동 추출
- 카테고리별 필터링 및 정규화

### 🤖 **AI 기반 데이터 추출**
- OpenAI GPT를 활용한 신청 기간 자동 추출
- 시작일/종료일 구조화된 JSON 형식으로 반환

### 📸 **OCR 이미지 처리**
- 이미지 기반 공지사항 텍스트 변환 (py-zerox)
- 자동 PDF 변환 후 Vision AI로 텍스트 추출

### 🔄 **중복 방지 및 최적화**
- 초기 크롤링: 1년치 데이터 수집
- 일일 크롤링: 최신 공지만 수집 (중복 제거)
- API 호출 최적화 (지연 시간 자동 조절)

### 💾 **유연한 저장 방식**
- 텍스트 파일 기반 간단한 DB
- FastAPI 서버로 자동 업로드 (선택사항)

---

## 📦 프로젝트 구조

```
Crawling/
├── crawler_config.py       # 전역 설정 (CSS 클래스, 패턴, AI 옵션 등)
├── db.py                   # TextFileDB 클래스 (텍스트 파일 저장)
├── crawling.py             # RSS/HTML 크롤링 메인 로직
├── utils.py                # AI, OCR, 상태 관리 유틸리티
├── start.py                # 실행 엔트리포인트
├── requirements.txt        # 의존성 목록
├── .env                    # 환경 변수 (API 키, URL 등, git 제외)
├── .gitignore              # Git 제외 파일 목록
├── notice_db.txt           # 크롤링 결과 저장 (자동 생성)
└── crawled_id.txt          # 마지막 크롤링 ID (자동 생성)
```

### 📂 주요 모듈 설명

#### `crawler_config.py`
크롤링 시스템의 모든 설정을 중앙에서 관리
- CSS 클래스명, 정규식 패턴, 파일명
- OpenAI API 설정, AI 프롬프트
- 카테고리 매핑, OCR 설정, 지연 시간 등
- ※ URL과 도메인은 `.env`에서 로드

#### `db.py`
텍스트 파일 기반 데이터베이스
- `TextFileDB`: 공지사항을 구조화된 형식으로 저장

#### `crawling.py`
크롤링 핵심 로직
- `html_crawl()`: 공지사항 상세 페이지 파싱
- `rss_crawl()`: RSS 피드 순회 및 데이터 수집

#### `utils.py`
유틸리티 함수 모음
- AI 기반 신청기간 추출
- 이미지 OCR 처리
- 크롤링 상태 관리
- FastAPI 서버 연동

#### `start.py`
실행 진입점
- 초기/일일 크롤링 모드 자동 감지
- 크롤링 시간 측정 및 결과 리포트

---

## 🚀 시작하기

### 1️⃣ 사전 준비

#### Python 설치
- Python 3.11 이상 필요
- [Python 공식 웹사이트](https://www.python.org/)에서 다운로드

#### Poppler 설치 (OCR 기능 사용 시 필수)

**Windows:**
1. [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) 다운로드
2. 압축 해제 (예: `C:\poppler`)
3. 환경 변수 PATH에 `C:\poppler\Library\bin` 추가

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install -y poppler-utils
```

**macOS:**
```bash
brew install poppler
```

### 2️⃣ 프로젝트 설정

#### 1. 저장소 클론
```bash
git clone <repository-url>
cd Crawling
```

#### 2. 가상환경 생성 및 활성화

**Windows:**
```bash
python -m venv venv_crawling
venv_crawling\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv_crawling
source venv_crawling/bin/activate
```

#### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 4. 환경 변수 설정

프로젝트 루트에 `.env` 파일 생성:

```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here

# 크롤링 대상 설정
RSS_URL=https://www.hansung.ac.kr/bbs/hansung/143/rssList.do?page={}
BASE_DOMAIN=https://www.hansung.ac.kr
```

**OpenAI API 키 발급:**
1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. 생성된 키를 `.env` 파일에 입력

### 3️⃣ 실행

#### 초기 크롤링 (처음 실행 시)
```bash
python start.py
```
- DB 파일이 없으면 자동으로 초기 크롤링 모드로 실행
- 최대 100페이지 (약 3000개)의 공지사항 수집, 1년 전 데이터 도달 시 자동 중단

#### 일일 크롤링 (정기 실행)
```bash
python start.py
```
- DB 파일이 있으면 자동으로 일일 크롤링 모드로 실행
- 최대 2페이지 (약 60개)의 최신 공지사항만 수집 (중복 제거)

#### DB 초기화
```bash
python start.py reset
```
- 모든 크롤링 기록 삭제 (`notice_db.txt`, `crawled_id.txt`)

---

## 🔄 동작 흐름

```
┌─────────────────┐
│   start.py      │  초기/일일 크롤링 모드 감지
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  rss_crawl()    │  RSS 피드 순회
└────────┬────────┘
         │
         ├─► html_crawl()          # HTML 파싱 (본문, 이미지, 첨부파일)
         │
         ├─► image_urls_to_text()  # OCR (이미지 → 텍스트)
         │
         ├─► get_application_period()  # AI (신청기간 추출)
         │
         └─► TextFileDB.save_notice()  # 저장
                    │
                    ▼
            ┌─────────────────┐
            │  notice_db.txt  │  결과 파일
            └─────────────────┘
                    │
                    ▼
            ┌─────────────────┐
            │ FastAPI 업로드   │  (선택사항)
            └─────────────────┘
```

---

## 📊 출력 형식 예시

```text
ID: 271234
제목: 2025학년도 1학기 수강신청 안내
링크: https://www.hansung.ac.kr/bbs/hansung/143/271234/artclView.do?layout=unknown
게시 날짜: 2025-01-15 14:30:00
카테고리: 학사
시작일: 2025-01-20
종료일: 2025-01-25
이미지 URL: 없음
첨부파일:
	- 수강신청_안내문.pdf | https://www.hansung.ac.kr/.../download.do
내용:
2025학년도 1학기 수강신청 일정을 안내드립니다.

**수강신청 기간**
- 2025년 1월 20일(월) 09:00 ~ 1월 25일(토) 18:00

...

--------------------------------------------------
```

---

## ⚙️ 설정 커스터마이징

### `crawler_config.py` 주요 설정

```python
# 카테고리 필터 (원하는 카테고리만 선택)
ALLOWED_CATEGORIES = [
    "한성공지",
    "학사",
    "비교과",
    "진로 및 취·창업",
    "장학",
    "국제",
]

# AI 모델 설정
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.1
MAX_TOKENS = 200

# OCR 최소 텍스트 길이 (이 길이보다 짧으면 OCR 시도)
MIN_TEXT_LENGTH = 250

# API 호출 간격 (초)
AI_CALL_DELAY = 3
OCR_DELAY = 3
```

---

## 🛠️ 개발 환경

### 요구 사항
- Python 3.11+
- Poppler (OCR 기능 사용 시)
- OpenAI API 키

### 의존성 라이브러리
```
requests~=2.32.3
beautifulsoup4~=4.12.2
lxml>=5.0.0
openai~=1.102.0
py-zerox~=0.0.7
img2pdf~=0.6.1
markdownify~=1.2.0
python-dotenv~=1.1.1
ipykernel~=6.30.1
```

### 주요 기술 스택
- [OpenAI API](https://openai.com/) - GPT 기반 신청기간 추출
- [py-zerox](https://github.com/getomni-ai/zerox) - Vision AI 기반 OCR
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML 파싱
- [Requests](https://docs.python-requests.org/) - HTTP 요청
- [python-dotenv](https://github.com/theskumar/python-dotenv) - 환경 변수 관리

---

## 📅 자동 실행 (Cron)

### Linux 서버에서 정기 실행

#### 1. 크론 작업 편집
```bash
crontab -e
```

#### 2. 매일 새벽 1시 실행 예시
```bash
0 1 * * * cd /path/to/Crawling && /path/to/venv_crawling/bin/python start.py >> logs/crawling.log 2>&1
```

#### 3. 로그 디렉토리 생성
```bash
mkdir -p logs
```

---

## 🔐 보안 및 비용 관리

### 환경 변수 관리
- `.env` 파일은 절대 Git에 커밋하지 마세요
- `.gitignore`에 이미 포함되어 있습니다

### API 비용 최적화
- `AI_CALL_DELAY`로 호출 빈도 조절
- `MIN_TEXT_LENGTH`로 불필요한 OCR 호출 방지
- OpenAI API 사용량 모니터링: https://platform.openai.com/usage

### 레이트 리밋 관리
- 지연 시간(`AI_CALL_DELAY`, `OCR_DELAY`) 설정으로 제어
- 대량 크롤링 시 페이지 수 조절 권장

---

## 🐛 트러블슈팅

### 1. Poppler 관련 오류
```
Unable to get page count. Is poppler installed and in PATH?
```
**해결:** Poppler를 설치하고 PATH에 추가하세요. (위 설치 가이드 참고)

### 2. OpenAI API 키 오류
```
Error code: 401 - Incorrect API key provided
```
**해결:** `.env` 파일에 올바른 API 키를 입력했는지 확인하세요.

### 3. lxml 설치 오류 (Windows)
```
ERROR: Failed building wheel for lxml
error: Microsoft Visual C++ 14.0 or greater is required
```
**해결:**
1. **Microsoft C++ Build Tools 설치**
   - https://visualstudio.microsoft.com/visual-cpp-build-tools/ 접속
   - "Build Tools 다운로드" 클릭
   - 설치 시 "C++ 빌드 도구" 체크박스 선택
   - 설치 후 터미널 재시작
2. **또는** requirements.txt가 `lxml>=5.0.0`으로 설정되어 있는지 확인
   - Python 3.13+는 미리 컴파일된 wheel이 제공됨

