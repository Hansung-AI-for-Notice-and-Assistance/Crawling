## HANA – Hansung AI for Notice & Assistance (크롤러)

한성대학교 공지 데이터를 자동 수집·가공하여 텍스트 파일로 저장하고, FastAPI 서버로 업로드하는 크롤링 모듈입니다. 

---

### ✨ 주요 기능
- **RSS/HTML 크롤링**: 한성대 공지 RSS를 순회하고 상세 페이지에서 본문/이미지/첨부파일을 수집
- **OCR 기반 이미지 텍스트 추출**: `img2pdf`+`py-zerox`로 이미지→PDF→텍스트 변환
- **기간 추출**: 본문에서 신청 기간 추출
- **중복/중단 로직**: 일일 적재시 `crawled_id.txt`로 중복 방지, 초기 적재 시 오래된 공지에서 자동 중단
- **카테고리 필터/정규화**: 불필요한 카테고리 제외 및 대표 카테고리 맵핑
- **결과 저장/전송**: 구조화 텍스트를 `notice_db.txt`로 저장 후, FastAPI로 업로드

---

### 🚀 시작하는 방법

로컬(Windows)와 서버(Linux) 기준으로 설치 및 실행 방법을 분리 안내합니다. OCR은 [zerox](https://github.com/getomni-ai/zerox)를 사용하며, zerox가 내부적으로 Poppler에 의존하므로 Poppler를 설치해야 합니다.

#### Windows (로컬)
1) Python 3.11+ 설치 후 가상환경(권장) 생성/활성화 및 의존성 설치
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Poppler 설치(수동 설치)
- [Poppler for Windows 릴리스](https://github.com/oschwartz10612/poppler-windows/releases/)에서 다운로드 후, 설치 경로의 `bin` 디렉터리를 PATH에 추가

3) 환경 변수 설정(`.env` 파일 생성)
```bash
OPENAI_API_KEY=your_openai_api_key
```

4) 실행
- 데이터 초기화 후 실행(초기 크롤링)
```bash
python hana_start.py reset
python hana_start.py
```
- 일반 실행(일일 크롤링)
```bash
python hana_start.py
```

#### Linux (서버)
1) 시스템 의존성 설치(Poppler)
```bash
sudo apt update && sudo apt install -y poppler-utils
```

2) Python 3.11+ 가상환경 및 의존성 설치
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

3) 환경 변수 설정(예: .env 파일)
```bash
echo OPENAI_API_KEY=your_openai_api_key > .env
```

4) 스케줄링(크론)
```bash
mkdir logs
crontab -e
```
크론 예시(매일 01:00 실행):
```bash
0 1 * * * (echo "--- Log Start: $(date) ---" && cd /home/ubuntu/Crawling && venv/bin/python hana_start.py) >> /home/ubuntu/Crawling/logs/cron_$(date +'\%Y-\%m-\%d').log 2>&1
```

설정 후 크론에 의해 주기적으로 실행되며, 결과는 `notice_db.txt`로 생성/갱신되고 FastAPI 서버로 업로드됩니다.

---

### 📦 파일 구조(해당 모듈 기준)
```
.
├── db.py                      # 텍스트 파일 기반 간단 DB (`notice_db.txt`에 저장)
├── hana_crawler_config.py     # 크롤러/AI/OCR/업로드 등 전역 설정
├── hana_crawling.py           # RSS/HTML 크롤링, OCR, 기간 추출 메인 로직
├── hana_start.py              # 실행 엔트리포인트(초기/일일 크롤링 분기, 업로드 트리거)
├── hana_utils.py              # OCR·AI 호출, 파일/상태 관리 유틸리티
├── requirements.txt           # 의존성 목록
├── notice_db.txt              # 수집 결과(출력물)
└── crawled_id.txt             # 마지막으로 본 최신 공지 ID(중복 방지)
```

---

### 🧠 동작 흐름
1. `hana_start.py`에서 초기/일일 크롤링 모드 결정 및 실행 시작
2. `hana_crawling.rss_crawl`이 RSS로 공지 목록을 수집하고, 각 공지 상세 페이지를 파싱(`html_crawl`)
3. 본문이 없거나, 본문이 짧고 이미지가 있으면 `hana_utils.image_urls_to_text`로 이미지→PDF→OCR 텍스트 추출
4. 최종 본문에서 `hana_utils.get_application_period`가 신청 기간(JSON) 추출
5. `db.FileDB.save_notice`로 `notice_db.txt`에 구조화 저장(이미지/첨부 포함)
6. 실행 종료 시 `hana_utils.send_to_file`로 FastAPI 서버에 결과 파일 업로드

---



### 🧩 핵심 모듈들 설명
- `db.FileDB`
  - `save_notice(...)`: 공지 1건을 사람이 읽기 쉬운 형태로 `notice_db.txt`에 저장
- `hana_crawling.html_crawl`
  - 상세 페이지에서 본문(마크다운), 이미지 URL, 첨부파일(이름 | 다운로드 URL) 추출
- `hana_crawling.rss_crawl`
  - RSS 수집→필터→상세 파싱→OCR/AI→저장 전 과정을 순회(중복/중단 제어 포함)
- `hana_utils.image_urls_to_text`
  - 이미지 묶음→PDF→`zerox` OCR로 텍스트 생성 및 반환(실패 시 빈 문자열)
- `hana_utils.get_application_period`
  - 본문에서 `{has_period, start_date, end_date}` JSON 추출 및 반환
- `hana_utils.send_to_file`
  - FastAPI로 `notice_db.txt` 업로드(성공/실패 로그 출력)

---

### 🧾 출력 포맷 예시(요약)
```text
ID: 271xxx
제목: ...
링크: https://www.hansung.ac.kr/bbs/hansung/143/271xxx/artclView.do?layout=unknown
게시 날짜: YYYY-MM-DD hh:mm:ss
카테고리: 한성공지 | 학사 | 비교과 | 진로 및 취·창업 | 장학 | 국제
시작일: YYYY-MM-DD 또는 없음
종료일: YYYY-MM-DD 또는 없음
이미지 URL:
	- https://...
첨부파일:
	- 파일명.pdf | https://.../download.do
내용:
...공지 본문 마크다운...

--------------------------------------------------
```

---

### ⚙️ 요구 사항
- Python 3.11+
- `requirements.txt`
  - requests, beautifulsoup4, lxml, openai, py-zerox, img2pdf, markdownify, python-dotenv, ipykernel

---

### 🔒 환경/비용 유의사항
- OpenAI/zerox 호출은 과금이 발생할 수 있습니다. 키/쿼터를 관리하세요.
- `AI_CALL_DELAY`, `OCR_DELAY`는 레이트리밋·서버 부하 방지를 위한 값입니다.
- 업로드 대상 서버(`FASTAPI_BASE_URL`, `FASTAPI_PORT`, `FASTAPI_PATH`)는 운영 환경에 맞게 변경하세요.

---

