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


# 세부 카테고리를 대표 카테고리로 통일하기 위한 매핑 테이블
CATEGORY_MAP = {
    # 취업 관련 카테고리
    "강소기업채용": "취업",
    "채용정보": "취업",
    "인턴쉽": "취업",
    "교육프로그램": "취업",
    "고시반": "취업",
    "기타": "취업",

    # 장학 관련 카테고리
    "국가장학금": "장학",
    "교외장학금": "장학",
    "교내장학금": "장학",
    "면학근로": "장학",
    "학자금대출": "장학",
    "국가근로": "장학",
    "공모전 등": "장학",
    "비교과장학": "장학",

    # 창업 관련 카테고리
    "창업정보": "창업",
    "창업공모전": "창업",
    "창업행사": "창업",
    "기타": "창업",
}


# OpenAI API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 사용할 OpenAI 모델명
MODEL = "gpt-4o-mini"
# AI 응답 생성 시 사용할 온도 (0.0 ~ 1.0, 낮을수록 일관성 높음)
TEMPERATURE = 0.1
# AI 응답 최대 토큰 수
MAX_TOKENS = 300


# 기본 크롤링 페이지 수 (1페이지 = 30개 공지사항)
DEFAULT_MAX_PAGES = 1
# HTTP 요청 타임아웃 (초)
REQUEST_TIMEOUT = 30
# OCR 처리 전 대기 시간 (초) - 서버 부하 방지
OCR_DELAY = 2
# OCR 적용을 위한 최소 텍스트 길이 (이 길이보다 짧으면 OCR도 시도)
MIN_TEXT_LENGTH = 200


# 신청기간 추출을 위한 AI 프롬프트
# {content}: 공지사항 본문 내용
# {current_year}: 현재 연도
PROMPT = """
    지시:
        - 다음 공지사항에서 신청기간의 시작일과 종료일을 찾아주세요.

    본문:
        {content}

    응답 형식:
        반드시 다음 JSON 형식으로만 응답하세요:

        {{
            "has_period": true 또는 false,
            "start_date": "{current_year}-MM-DD" 또는 null,
            "end_date": "{current_year}-MM-DD" 또는 null
        }}

    예시(Examples):
        ## 예시 1
        - 본문: "모집 기간은 9월 16일부터 10월 5일까지입니다."
        - JSON:
        {{
            "has_period": true,
            "start_date": "2025-09-16",
            "end_date": "2025-10-05"
        }}

        ## 예시 2
        - 본문: "관심 있는 분들의 많은 지원 바랍니다."
        - JSON:
        {{
            "has_period": false,
            "start_date": null,
            "end_date": null
        }}

        ## 예시 3
        - 본문: "본 채용은 상시모집으로 진행됩니다."
        - JSON:
        {{
            "has_period": false,
            "start_date": null,
            "end_date": null
        }}

        ## 예시 4
        - 본문: "선착순 마감이므로 서두르세요. (마감일: ~9.30)"
        - JSON:
        {{
            "has_period": true,
            "start_date": null,
            "end_date": "2025-09-30"
        }}

    규칙:
        - 신청기간이 없으면 has_period: false, start_date: null, end_date: null
        - 신청기간이 있으면 has_period: true, end_date는 반드시 필요, start_date는 없으면 null
        - 날짜는 {current_year}년 기준으로 YYYY-MM-DD 형식
        - 반드시 순수한 JSON 형식으로만 응답하세요 (```json, ``` 등 마크다운 문법 사용 금지)
        - 다른 설명이나 텍스트는 절대 포함하지 마세요
"""
