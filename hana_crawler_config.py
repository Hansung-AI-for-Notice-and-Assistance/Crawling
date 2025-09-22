"""
HANA (Hansung AI for Notice & Assistance)
한성대학교 공지사항 크롤링 시스템 설정 파일

이 파일은 한성대학교 공지사항 크롤링 시스템의 모든 설정값을 관리합니다.
- 크롤링 대상 URL 및 도메인 설정
- 데이터베이스 파일명 및 출력 디렉토리 설정
- AI 서비스 설정 (OpenAI API)
- 카테고리 매핑
- 크롤링 동작 설정
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


# 한성대학교 공지사항 RSS 피드 URL ({} 안에는 페이지 번호)
RSS_URL = 'https://www.hansung.ac.kr/bbs/hansung/143/rssList.do?page={}'
# 기본 도메인 (상대 경로를 절대 경로로 변환할 때 사용)
BASE_DOMAIN = "https://www.hansung.ac.kr"


# 데이터베이스 파일명
DB_FILENAME = "notice_db.txt"


# OCR 할 때 임시 PDF 저장 폴더
OUTPUT_DIR = "./pdf"
# 임시 PDF 파일명
PDF_FILENAME = "temp.pdf"
# 임시 PDF 파일 경로
PDF_PATH = os.path.join(OUTPUT_DIR, PDF_FILENAME)


# FastAPI 서버 설정 (결과 파일 업로드용)
FASTAPI_BASE_URL = "http://13.209.9.15" # "http://127.0.0.1"
FASTAPI_PORT = "8000"
FASTAPI_PATH = "/send/file"


# 허용할 대표 카테고리 (이 목록에 없는 카테고리는 크롤링 시 건너뜀)
ALLOWED_CATEGORIES = [
    "한성공지",
    "학사",
    "비교과",
    "진로 및 취·창업",
    "장학",
    "국제",
]

# 세부 카테고리를 대표 카테고리로 통일하기 위한 매핑 테이블
CATEGORY_MAP = {
    "진로": "진로 및 취·창업",

    # 취업 관련 카테고리
    "강소기업채용": "진로 및 취·창업",
    "채용정보": "진로 및 취·창업",
    "인턴쉽": "진로 및 취·창업",
    "교육프로그램": "진로 및 취·창업",
    "고시반": "진로 및 취·창업",
    "기타": "진로 및 취·창업",

    # 창업 관련 카테고리
    "창업정보": "진로 및 취·창업",
    "창업공모전": "진로 및 취·창업",
    "창업행사": "진로 및 취·창업",
    "기타": "진로 및 취·창업",

    # 장학 관련 카테고리
    "국가장학금": "장학",
    "교외장학금": "장학",
    "교내장학금": "장학",
    "면학근로": "장학",
    "학자금대출": "장학",
    "국가근로": "장학",
    "공모전 등": "장학",
    "비교과장학": "장학",
}


# OpenAI API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 사용할 OpenAI 모델명
MODEL = "gpt-4o-mini"
# AI 응답 생성 시 사용할 온도 (0.0 ~ 1.0, 낮을수록 일관성 높음)
TEMPERATURE = 0.1
# AI 응답 최대 토큰 수
MAX_TOKENS = 200


# 기본 크롤링 페이지 수 (1페이지 = 30개 공지사항)
DEFAULT_MAX_PAGES = 1
# HTTP 요청 타임아웃 (초)
REQUEST_TIMEOUT = 30
# OCR 처리 전 대기 시간 (초) - 서버 부하 방지
OCR_DELAY = 3
# OCR 적용을 위한 최소 텍스트 길이 (이 길이보다 짧으면 OCR도 시도)
MIN_TEXT_LENGTH = 250

# OpenAI 호출 간 지연 (초) - 레이트리밋 방지
AI_CALL_DELAY = 3


# 신청기간 추출을 위한 AI 프롬프트
# {content}: 공지사항 본문 내용
PROMPT = """
    너는 주어진 본문에서 신청 기간의 시작일과 종료일을 추출하여 JSON 형식으로 반환하는 AI야.

    # 규칙
    - 본문 내용을 분석해서 신청 기간을 찾아.
    - 결과는 반드시 지정된 JSON 형식으로만 응답해야 해. 다른 설명은 절대 추가하지 마.
    - 응답 시 ```json, ``` 등 마크다운 문법은 절대 사용하지 마.

    # 응답 형식 (JSON)
    - 날짜는 항상 "YYYY-MM-DD" 형식으로 작성해줘.
    - 기간을 찾을 수 없으면 "has_period"는 false, 날짜는 모두 null로 처리해.
    - 기간을 찾았다면 "has_period"는 true로 하고, "end_date"는 반드시 값이 있어야 해. "start_date"는 없으면 null로 처리해.
    {{
        "has_period": boolean,
        "start_date": "YYYY-MM-DD" or null,
        "end_date": "YYYY-MM-DD" or null
    }}

    # 예시
    1. 본문: "모집 기간은 9월 16일부터 10월 5일까지입니다."
    JSON: {{"has_period": true, "start_date": "2025-09-16", "end_date": "2025-10-05"}}

    2. 본문: "접수 마감은 2025년 9월 30일 18:00까지입니다."
    JSON: {{"has_period": true, "start_date": null, "end_date": "2025-09-30"}}

    3. 본문: "본 채용은 상시 모집으로 진행됩니다."
    JSON: {{"has_period": false, "start_date": null, "end_date": null}}

    # 본문
    {content}
"""
